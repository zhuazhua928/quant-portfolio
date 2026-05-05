"""Stage-1 non-parametric regime clusterer: HDBSCAN.

HDBSCAN is non-parametric (no K specified) but we cap effective K by post-hoc
merging the smallest clusters into 'noise' (label -1) until the top-K remain.
Cluster labels are then sorted by mean forward 5-min return like the HMM
bundle, so they share the same downstream interface.

Note: HDBSCAN does not natively support out-of-sample prediction, so we use
``approximate_predict`` which is provided by the prediction-extension API
when fit with ``prediction_data=True``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from research.models.regime_hmm import HMM_FEATURE_COLS

logger = logging.getLogger(__name__)


@dataclass
class HDBScanRegimeBundle:
    scaler: StandardScaler
    clusterer: object  # hdbscan.HDBSCAN
    label_perm: dict[int, int]  # raw cluster id -> sorted regime label (-1 stays -1)
    feature_cols: list[str]
    n_regimes: int

    def predict(self, windows: pd.DataFrame) -> pd.Series:
        import hdbscan

        X = windows[self.feature_cols]
        mask = X.notna().all(axis=1)
        labels = pd.Series(-1, index=windows.index, dtype="int64")
        if mask.any():
            Xs = self.scaler.transform(X.loc[mask].to_numpy())
            raw, _ = hdbscan.approximate_predict(self.clusterer, Xs)
            mapped = np.array([self.label_perm.get(int(r), -1) for r in raw], dtype=np.int64)
            labels.loc[mask] = mapped
        return labels


def fit_hdbscan(
    windows: pd.DataFrame,
    n_regimes: int = 4,
    feature_cols: list[str] | None = None,
    min_cluster_size: int | None = None,
) -> HDBScanRegimeBundle:
    import hdbscan

    cols = [c for c in (feature_cols or HMM_FEATURE_COLS) if c in windows.columns]
    Xdf = windows[cols].dropna()
    if Xdf.empty:
        raise ValueError("no rows to fit HDBSCAN on")

    scaler = StandardScaler().fit(Xdf.to_numpy())
    Xs = scaler.transform(Xdf.to_numpy())

    mcs = min_cluster_size or max(50, len(Xdf) // 200)
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=mcs,
        prediction_data=True,
        cluster_selection_method="eom",
    )
    raw_labels = clusterer.fit_predict(Xs)

    # Keep top-N largest clusters (excluding -1 noise); demote the rest to noise.
    counts = pd.Series(raw_labels)
    counts = counts[counts >= 0].value_counts()
    keep = counts.head(n_regimes).index.tolist()

    fwd = windows.loc[Xdf.index, "fwd_ret_5m"] if "fwd_ret_5m" in windows.columns else None
    if fwd is not None and fwd.notna().any() and keep:
        means = (
            pd.DataFrame({"raw": raw_labels, "fwd": fwd.to_numpy()})
            .query("raw in @keep")
            .groupby("raw")["fwd"].mean()
            .sort_values()
        )
        ordered = means.index.tolist()  # ascending by mean fwd return
    else:
        ordered = keep

    label_perm = {int(raw): i for i, raw in enumerate(ordered)}
    # noise stays as -1; non-kept clusters also become -1
    bundle = HDBScanRegimeBundle(
        scaler=scaler, clusterer=clusterer, label_perm=label_perm,
        feature_cols=cols, n_regimes=len(ordered),
    )
    logger.info("fit HDBSCAN: %d clusters kept of %d raw; perm=%s",
                len(ordered), counts.shape[0], label_perm)
    return bundle


def save_bundle(bundle: HDBScanRegimeBundle, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, path)


def load_bundle(path: Path) -> HDBScanRegimeBundle:
    return joblib.load(path)
