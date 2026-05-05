"""ARX models — closed-form OLS via numpy.

Two specifications from Sec 3.1 of the paper:
  ARX_levels: fit P0 and P1 separately on D_t, X_t, lags; spread_hat = P1_hat - P0_hat
  ARX_spread: fit spread directly on D_t, X_t, spread_lags, P0_lag1
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _ols(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Closed-form OLS coefficients via lstsq (numerically stable)."""
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    return coef


def fit_predict_arx_levels(
    train: pd.DataFrame,
    test_row: pd.Series,
    deterministic: list[str],
    x_cols: list[str],
    lag_cols: list[str],
) -> float:
    """Fit P0 and P1 separately on the train window, predict for test_row,
    return the predicted spread (P1_hat - P0_hat).
    """
    cols_p0 = deterministic + x_cols + lag_cols
    cols_p1 = deterministic + x_cols + lag_cols + ["p0_lag1"]
    train_clean = train.dropna(subset=cols_p1 + ["p0_mean", "p1_mean"])
    if len(train_clean) < max(20, len(cols_p1) + 5):
        return float("nan")

    Z0 = train_clean[cols_p0].to_numpy(dtype=float)
    Z1 = train_clean[cols_p1].to_numpy(dtype=float)
    y0 = train_clean["p0_mean"].to_numpy(dtype=float)
    y1 = train_clean["p1_mean"].to_numpy(dtype=float)
    b0 = _ols(Z0, y0)
    b1 = _ols(Z1, y1)

    z0 = test_row[cols_p0].to_numpy(dtype=float)
    z1 = test_row[cols_p1].to_numpy(dtype=float)
    if np.isnan(z0).any() or np.isnan(z1).any():
        return float("nan")
    p0_hat = float(z0 @ b0)
    p1_hat = float(z1 @ b1)
    return p1_hat - p0_hat


def fit_predict_arx_spread(
    train: pd.DataFrame,
    test_row: pd.Series,
    deterministic: list[str],
    x_cols: list[str],
    lag_cols: list[str],
) -> float:
    """Fit spread directly on D, X, spread_lags, P0_lag1."""
    cols = deterministic + x_cols + lag_cols + ["p0_lag1"]
    train_clean = train.dropna(subset=cols + ["spread"])
    if len(train_clean) < max(20, len(cols) + 5):
        return float("nan")
    Z = train_clean[cols].to_numpy(dtype=float)
    y = train_clean["spread"].to_numpy(dtype=float)
    b = _ols(Z, y)
    z = test_row[cols].to_numpy(dtype=float)
    if np.isnan(z).any():
        return float("nan")
    return float(z @ b)
