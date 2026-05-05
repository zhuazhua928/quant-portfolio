"""Stage-1 regime classifier: Gaussian Hidden Markov Model.

Fits a GaussianHMM on standardized 5-min window features. After fitting, we
relabel hidden states by the mean forward 5-min return so that label 0 is
the most bearish regime and label K-1 is the most bullish.

Persists: scaler + hmm + label-permutation as a single joblib bundle.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

# Default features fed to the HMM. Tuned to be stationary-ish.
HMM_FEATURE_COLS = [
    "ret_1m_w", "ret_5m_w", "ret_15m_w",
    "rv", "pk_vol", "vwap_dev", "ofi", "beta_t", "spy_ret_5m",
]


@dataclass
class HMMRegimeBundle:
    scaler: StandardScaler
    hmm: object  # hmmlearn.hmm.GaussianHMM
    label_perm: np.ndarray  # maps raw HMM state -> sorted label
    feature_cols: list[str]
    n_components: int

    def predict(self, windows: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame]:
        """Return (state_labels, posterior_probs) aligned to windows.index.

        Rows with any NaN in the feature columns get label = -1 and uniform probs.
        """
        X = windows[self.feature_cols]
        mask = X.notna().all(axis=1)
        labels = pd.Series(-1, index=windows.index, dtype="int64")
        probs = pd.DataFrame(
            np.full((len(windows), self.n_components), 1.0 / self.n_components),
            index=windows.index, columns=[f"p_{i}" for i in range(self.n_components)],
        )
        if mask.any():
            Xs = self.scaler.transform(X.loc[mask].to_numpy())
            raw = self.hmm.predict(Xs)
            post = self.hmm.predict_proba(Xs)
            # remap raw state ids to sorted labels
            remap = self.label_perm
            mapped = remap[raw]
            labels.loc[mask] = mapped
            # permute posterior columns: column i becomes column remap[i]
            permuted = np.zeros_like(post)
            for i in range(self.n_components):
                permuted[:, remap[i]] = post[:, i]
            probs.loc[mask, :] = permuted
        return labels, probs


def fit_hmm(
    windows: pd.DataFrame,
    n_components: int = 4,
    feature_cols: list[str] | None = None,
    n_iter: int = 100,
    random_state: int = 42,
) -> HMMRegimeBundle:
    """Fit a Gaussian HMM and return a persisted-ready bundle.

    Parameters
    ----------
    windows : windowed feature DataFrame from research.features.windowing
    n_components : K, number of latent regimes (3 or 4 per proposal)
    feature_cols : columns to use; defaults to HMM_FEATURE_COLS
    """
    from hmmlearn.hmm import GaussianHMM

    cols = [c for c in (feature_cols or HMM_FEATURE_COLS) if c in windows.columns]
    if not cols:
        raise ValueError("no feature columns present in windows DataFrame")

    Xdf = windows[cols].dropna()
    if len(Xdf) < n_components * 50:
        raise ValueError(f"too few rows ({len(Xdf)}) to fit HMM with K={n_components}")

    scaler = StandardScaler().fit(Xdf.to_numpy())
    Xs = scaler.transform(Xdf.to_numpy())

    hmm = GaussianHMM(
        n_components=n_components,
        covariance_type="full",
        n_iter=n_iter,
        random_state=random_state,
    )
    hmm.fit(Xs)

    # Relabel: sort raw states by mean forward 5-min return (ascending).
    raw_states = hmm.predict(Xs)
    fwd = windows.loc[Xdf.index, "fwd_ret_5m"] if "fwd_ret_5m" in windows.columns else None
    if fwd is not None and fwd.notna().any():
        order = (
            pd.Series(raw_states, index=Xdf.index)
            .to_frame("s")
            .assign(fwd=fwd)
            .groupby("s")["fwd"].mean()
            .sort_values()
            .index.to_numpy()
        )
        # label_perm[raw_state] = sorted_position
        label_perm = np.empty(n_components, dtype=np.int64)
        for sorted_pos, raw in enumerate(order):
            label_perm[int(raw)] = sorted_pos
    else:
        label_perm = np.arange(n_components, dtype=np.int64)

    bundle = HMMRegimeBundle(
        scaler=scaler, hmm=hmm, label_perm=label_perm,
        feature_cols=cols, n_components=n_components,
    )
    logger.info("fit HMM K=%d on %d rows; label_perm=%s", n_components, len(Xdf), label_perm.tolist())
    return bundle


def save_bundle(bundle: HMMRegimeBundle, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, path)


def load_bundle(path: Path) -> HMMRegimeBundle:
    return joblib.load(path)
