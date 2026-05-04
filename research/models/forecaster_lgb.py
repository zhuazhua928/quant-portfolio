"""Stage-2 conditional forecaster: LightGBM per regime.

For each regime label k we train a separate LightGBM regressor of the
forward 5-min log return. A binary classifier (sign prediction) shares the
same features for Brier / log-loss evaluation. At inference time, we route
each row to its regime's model based on Stage-1's predicted label; rows with
label = -1 (noise / NaN) fall back to a global model.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# LightGBM input features. Drops dummies/symbol categoricals (those are added
# in `prepare_X` along with one-hot regime indicators).
LGB_FEATURE_COLS = [
    "ret_1m_w", "ret_5m_w", "ret_15m_w",
    "rv", "pk_vol", "vwap_dev", "amihud", "ofi", "beta_t", "spy_ret_5m",
    "open_drive", "close_drive", "midday", "fomc", "cpi", "nfp",
]


@dataclass
class LGBForecasterBundle:
    per_regime_reg: dict[int, object] = field(default_factory=dict)  # regime -> LGBMRegressor
    global_reg: object | None = None
    per_regime_clf: dict[int, object] = field(default_factory=dict)  # regime -> LGBMClassifier (sign)
    global_clf: object | None = None
    feature_cols: list[str] = field(default_factory=list)
    target_col: str = "fwd_ret_5m"

    def predict_regression(self, X: pd.DataFrame, regimes: pd.Series) -> pd.Series:
        """Predict forward returns. Routes by regime; -1 / unknown uses global model."""
        out = pd.Series(np.nan, index=X.index, dtype="float64")
        for k, mdl in self.per_regime_reg.items():
            mask = (regimes == k)
            if mask.any():
                out.loc[mask] = mdl.predict(X.loc[mask, self.feature_cols])
        rest = out.isna()
        if rest.any() and self.global_reg is not None:
            out.loc[rest] = self.global_reg.predict(X.loc[rest, self.feature_cols])
        return out

    def predict_proba_up(self, X: pd.DataFrame, regimes: pd.Series) -> pd.Series:
        out = pd.Series(0.5, index=X.index, dtype="float64")
        for k, mdl in self.per_regime_clf.items():
            mask = (regimes == k)
            if mask.any():
                out.loc[mask] = mdl.predict_proba(X.loc[mask, self.feature_cols])[:, 1]
        rest = (out == 0.5)
        if rest.any() and self.global_clf is not None:
            out.loc[rest] = self.global_clf.predict_proba(X.loc[rest, self.feature_cols])[:, 1]
        return out


def _fit_one_regression(X: np.ndarray, y: np.ndarray):
    from lightgbm import LGBMRegressor
    mdl = LGBMRegressor(
        n_estimators=400, learning_rate=0.03, max_depth=-1, num_leaves=63,
        min_child_samples=50, subsample=0.85, subsample_freq=1, colsample_bytree=0.85,
        reg_lambda=1.0, random_state=42, n_jobs=-1, verbosity=-1,
    )
    mdl.fit(X, y)
    return mdl


def _fit_one_classifier(X: np.ndarray, y: np.ndarray):
    from lightgbm import LGBMClassifier
    mdl = LGBMClassifier(
        n_estimators=400, learning_rate=0.03, max_depth=-1, num_leaves=63,
        min_child_samples=50, subsample=0.85, subsample_freq=1, colsample_bytree=0.85,
        reg_lambda=1.0, random_state=42, n_jobs=-1, verbosity=-1,
    )
    mdl.fit(X, y)
    return mdl


def fit_two_stage(
    panel: pd.DataFrame,
    regime_labels: pd.Series,
    target_col: str = "fwd_ret_5m",
    feature_cols: list[str] | None = None,
    min_per_regime: int = 500,
) -> LGBForecasterBundle:
    """Fit per-regime LightGBM regressor + classifier and a global fallback.

    Parameters
    ----------
    panel : feature DataFrame indexed identically to regime_labels
    regime_labels : Series of int regime labels (-1 = unknown)
    target_col : forward-return column to regress
    """
    cols = [c for c in (feature_cols or LGB_FEATURE_COLS) if c in panel.columns]
    df = panel[cols + [target_col]].copy()
    df["regime"] = regime_labels.astype("int64")
    df = df.dropna(subset=cols + [target_col])

    if df.empty:
        raise ValueError("no rows available for Stage-2 fit after dropping NaNs")

    bundle = LGBForecasterBundle(feature_cols=cols, target_col=target_col)

    # global fallback (always trained). DataFrames preserve feature names so
    # downstream predict calls don't trigger sklearn's "no feature names" warning.
    Xg = df[cols]
    yg = df[target_col].to_numpy()
    bundle.global_reg = _fit_one_regression(Xg, yg)
    bundle.global_clf = _fit_one_classifier(Xg, (yg > 0).astype(int))
    logger.info("fit GLOBAL regressor on %d rows", len(df))

    # per-regime
    for k, sub in df.groupby("regime"):
        if k < 0 or len(sub) < min_per_regime:
            continue
        Xk = sub[cols]
        yk = sub[target_col].to_numpy()
        bundle.per_regime_reg[int(k)] = _fit_one_regression(Xk, yk)
        bundle.per_regime_clf[int(k)] = _fit_one_classifier(Xk, (yk > 0).astype(int))
        logger.info("fit regime=%d on %d rows", k, len(sub))

    return bundle


def save_bundle(bundle: LGBForecasterBundle, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, path)


def load_bundle(path: Path) -> LGBForecasterBundle:
    return joblib.load(path)
