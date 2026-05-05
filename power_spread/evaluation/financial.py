"""Financial performance metrics for $-denominated daily P&L.

Total profit, annualized return, dollar-Sharpe, max drawdown, Calmar, 5% VaR.

Notional: 1 MWh per hour x 24 hours = 24 MWh per day. Returns are reported on
that notional at the average DA price, so a strategy earning $1.20/day on
$24 x avg_DA_price ~ $720 of notional is ~0.17 % per day.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import DAYS_PER_YEAR


def total_profit(daily_pnl: pd.Series) -> float:
    return float(daily_pnl.sum())


def annualized_return_dollars(daily_pnl: pd.Series) -> float:
    if daily_pnl.empty:
        return float("nan")
    return float(daily_pnl.mean() * DAYS_PER_YEAR)


def annualized_return_pct(daily_pnl: pd.Series, avg_da_price: float) -> float:
    if daily_pnl.empty or not np.isfinite(avg_da_price) or avg_da_price <= 0:
        return float("nan")
    notional_per_day = 24.0 * avg_da_price  # 24 MWh x avg DA price ($/MWh)
    daily_ret = daily_pnl / notional_per_day
    return float(daily_ret.mean() * DAYS_PER_YEAR)


def dollar_sharpe(daily_pnl: pd.Series) -> float:
    if len(daily_pnl) < 2:
        return float("nan")
    sd = float(daily_pnl.std())
    if not np.isfinite(sd) or sd == 0:
        return float("nan")
    return float((daily_pnl.mean() / sd) * np.sqrt(DAYS_PER_YEAR))


def max_drawdown(daily_pnl: pd.Series) -> float:
    """Max peak-to-trough drawdown of the cumulative $ equity. Returned as a
    positive number ($-loss); 0 if the curve is monotone non-decreasing."""
    if daily_pnl.empty:
        return float("nan")
    eq = daily_pnl.cumsum()
    dd = (eq - eq.cummax()).min()
    return float(-dd) if dd <= 0 else 0.0


def calmar(daily_pnl: pd.Series) -> float:
    ann = annualized_return_dollars(daily_pnl)
    mdd = max_drawdown(daily_pnl)
    if not np.isfinite(ann) or not np.isfinite(mdd) or mdd == 0:
        return float("nan")
    return float(ann / mdd)


def var_5pct(daily_pnl: pd.Series) -> float:
    if daily_pnl.empty:
        return float("nan")
    return float(np.percentile(daily_pnl, 5))


def hit_rate(daily_pnl: pd.Series) -> float:
    if daily_pnl.empty:
        return float("nan")
    nonzero = daily_pnl[daily_pnl != 0]
    if nonzero.empty:
        return float("nan")
    return float((nonzero > 0).mean())


def summarize(daily_pnl: pd.Series, avg_da_price: float | None = None) -> dict:
    return {
        "n_days": int(len(daily_pnl)),
        "total_profit": total_profit(daily_pnl),
        "ann_return_dollars": annualized_return_dollars(daily_pnl),
        "ann_return_pct": annualized_return_pct(daily_pnl, avg_da_price) if avg_da_price else float("nan"),
        "sharpe": dollar_sharpe(daily_pnl),
        "max_drawdown": max_drawdown(daily_pnl),
        "calmar": calmar(daily_pnl),
        "var_5pct": var_5pct(daily_pnl),
        "hit_rate": hit_rate(daily_pnl),
    }
