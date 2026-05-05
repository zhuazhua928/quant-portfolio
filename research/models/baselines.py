"""Baselines for benchmarking the two-stage forecaster.

* NaiveMomentum: predicted_fwd_ret_5m = sign(ret_5m_w) * |ret_5m_w| * decay
  (a simple persistence rule with a 0.5 shrinkage to avoid overshooting).
* SingleStageLGB: a single LightGBM regressor without any regime conditioning.

Both expose `predict_regression(X)` and `predict_proba_up(X)` for parity with
the two-stage bundle.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from research.models.forecaster_lgb import LGB_FEATURE_COLS, _fit_one_classifier, _fit_one_regression

logger = logging.getLogger(__name__)


@dataclass
class NaiveMomentum:
    decay: float = 0.5
    feature_cols: list[str] = field(default_factory=lambda: ["ret_5m_w"])

    def fit(self, *_args, **_kwargs):
        return self

    def predict_regression(self, X: pd.DataFrame, regimes: pd.Series | None = None) -> pd.Series:
        return X["ret_5m_w"].fillna(0.0) * self.decay

    def predict_proba_up(self, X: pd.DataFrame, regimes: pd.Series | None = None) -> pd.Series:
        # logistic-ish mapping of last 5-min return into [0,1]
        z = X["ret_5m_w"].fillna(0.0) / X["rv"].replace(0, np.nan).fillna(X["rv"].median() or 1e-4)
        return 1.0 / (1.0 + np.exp(-z))


@dataclass
class SingleStageLGB:
    reg: object | None = None
    clf: object | None = None
    feature_cols: list[str] = field(default_factory=list)

    def fit(self, panel: pd.DataFrame, target_col: str = "fwd_ret_5m",
            feature_cols: list[str] | None = None) -> "SingleStageLGB":
        cols = [c for c in (feature_cols or LGB_FEATURE_COLS) if c in panel.columns]
        df = panel[cols + [target_col]].dropna()
        if df.empty:
            raise ValueError("no rows for single-stage LGB fit")
        X = df[cols]
        y = df[target_col].to_numpy()
        self.reg = _fit_one_regression(X, y)
        self.clf = _fit_one_classifier(X, (y > 0).astype(int))
        self.feature_cols = cols
        logger.info("fit SingleStageLGB on %d rows", len(df))
        return self

    def predict_regression(self, X: pd.DataFrame, regimes: pd.Series | None = None) -> pd.Series:
        return pd.Series(self.reg.predict(X[self.feature_cols]), index=X.index)

    def predict_proba_up(self, X: pd.DataFrame, regimes: pd.Series | None = None) -> pd.Series:
        return pd.Series(self.clf.predict_proba(X[self.feature_cols])[:, 1], index=X.index)
