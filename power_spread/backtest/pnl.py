"""P&L accounting under the paper's decision rule + a per-switch trading cost.

Per day t:
  pi_t = y_hat_t * (spread_t - cost) + (1 - y_hat_t) * 0
       = y_hat_t * (spread_t - cost)

Position size is 1 MWh per hour for 24 hours of the trading day, so the
'daily' values are already 24-MWh-equivalent because spread_t is the daily
mean of the 24 hourly spreads. To express in $ per day per 1 MWh-hour-of-
average-supply (the natural unit), we keep spread_t as-is.

The naive-DA benchmark earns 0 by construction; naive-RT earns
spread_t - cost every day.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def pnl_from_decisions(
    y_hat: pd.Series,
    spread: pd.Series,
    cost_per_mwh: float,
) -> pd.DataFrame:
    """Per-day P&L. Returns a frame with columns: y_hat, spread, pnl, equity."""
    df = pd.concat(
        [y_hat.rename("y_hat"), spread.rename("spread")],
        axis=1,
    ).dropna()
    df["pnl"] = df["y_hat"].astype(float) * (df["spread"] - cost_per_mwh)
    df["equity"] = df["pnl"].cumsum()
    return df


def naive_pnl(
    spread: pd.Series,
    cost_per_mwh: float,
    strategy: str,
) -> pd.DataFrame:
    """`strategy` in {'naive_da', 'naive_rt'}."""
    if strategy == "naive_da":
        y = pd.Series(0, index=spread.index, name="y_hat")
    elif strategy == "naive_rt":
        y = pd.Series(1, index=spread.index, name="y_hat")
    else:
        raise ValueError(strategy)
    return pnl_from_decisions(y, spread, cost_per_mwh)
