"""Feature construction for the daily ARX / Probit models.

Replicates Sec. 3 of Maciejowska, Nitka & Weron (2019):
- Deterministic dummies D_t: constant, Mon, Sat, Sun, Holiday
- Exogenous X_t: subset of {demand_fcst_mean, wind_mean, solar_mean}
  (wind/solar use lag-1 persistence as the in-advance proxy; demand_fcst is
   already a true forecast)
- Lagged endogenous: spread_{t-i} for i in L (default L = {2, 7})
- Lagged P0_{t-1} controls baseline level
"""

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd


DETERMINISTIC = ["const", "is_mon", "is_sat", "is_sun", "is_holiday"]


def _ensure_const(df: pd.DataFrame) -> pd.DataFrame:
    if "const" not in df.columns:
        df = df.copy()
        df["const"] = 1.0
    return df


def build_design(
    daily: pd.DataFrame,
    x_cols: Iterable[str] = ("demand_fcst_mean", "wind_mean"),
    lag_set: Iterable[int] = (2, 7),
    target: str = "spread",
) -> pd.DataFrame:
    """Build a daily feature panel with everything needed for ARX/Probit.

    Returns a frame indexed by date, containing:
      - p0_mean, p1_mean, spread (raw)
      - D: const + dummies (already in `daily`)
      - X: x_cols, where wind_mean / solar_mean are replaced by lag-1
        persistence-forecast ('wind_fcst', 'solar_fcst'). demand_fcst_mean is
        a true forecast so used as-is.
      - lagged spread: spread_lag_{i} for i in lag_set
      - p0_lag1: previous day's p0 mean (the gamma * P0_{t-1} term)
      - y_bin: 1{spread > 0}
    """
    df = _ensure_const(daily.copy())

    # X variables — substitute persistence proxies for wind/solar
    if "wind_mean" in x_cols and "wind_mean" in df.columns:
        df["wind_fcst"] = df["wind_mean"].shift(1)
    if "solar_mean" in x_cols and "solar_mean" in df.columns:
        df["solar_fcst"] = df["solar_mean"].shift(1)

    # Mapping from x_cols name to the actually-usable feature column
    x_use: list[str] = []
    for c in x_cols:
        if c == "wind_mean":
            x_use.append("wind_fcst")
        elif c == "solar_mean":
            x_use.append("solar_fcst")
        else:
            x_use.append(c)

    # Lagged spread
    for i in lag_set:
        df[f"spread_lag_{i}"] = df["spread"].shift(i)

    # Lagged P0
    df["p0_lag1"] = df["p0_mean"].shift(1)

    df["y_bin"] = (df[target] > 0).astype(int)
    df.attrs["x_cols"] = x_use
    df.attrs["lag_cols"] = [f"spread_lag_{i}" for i in lag_set]
    return df


def feature_matrix(
    df: pd.DataFrame,
    include_p0_lag1: bool = True,
) -> tuple[pd.DataFrame, list[str]]:
    """Assemble the regressor matrix Z = [D, X, spread_lags, P0_lag1]."""
    cols = list(DETERMINISTIC) + list(df.attrs["x_cols"]) + list(df.attrs["lag_cols"])
    if include_p0_lag1:
        cols.append("p0_lag1")
    Z = df[cols].astype(float)
    return Z, cols
