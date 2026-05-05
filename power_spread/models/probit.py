"""Probit model — Pr(Y_t = 1 | Omega_{t-1}) = Phi(alpha D + beta X + theta spread_lags + gamma P0_lag1).

Uses statsmodels.discrete.discrete_model.Probit. Returns a probability, not a
binary; the decision threshold mu is applied downstream.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm


def fit_predict_probit(
    train: pd.DataFrame,
    test_row: pd.Series,
    deterministic: list[str],
    x_cols: list[str],
    lag_cols: list[str],
) -> float:
    """Return Phi(z'beta) for the test row. NaN if fit fails or features missing."""
    cols = deterministic + x_cols + lag_cols + ["p0_lag1"]
    train_clean = train.dropna(subset=cols + ["y_bin"])
    if len(train_clean) < max(40, len(cols) + 10):
        return float("nan")
    y = train_clean["y_bin"].to_numpy(dtype=int)
    if y.sum() == 0 or y.sum() == len(y):
        # degenerate — return naive prior probability
        return float(y.mean())

    Z = train_clean[cols].to_numpy(dtype=float)
    z_test = test_row[cols].to_numpy(dtype=float)
    if np.isnan(z_test).any():
        return float("nan")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = sm.Probit(y, Z)
            res = model.fit(disp=False, method="newton", maxiter=50)
        # Phi(z'b)
        score = float(z_test @ res.params)
        from scipy.stats import norm

        return float(norm.cdf(score))
    except Exception:
        return float("nan")
