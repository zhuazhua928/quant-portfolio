"""Vectorized backtest with proportional transaction costs.

Strategy: long / short / flat per-bar based on a predicted forward return:
  position_t = +1 if pred_t > +threshold
             = -1 if pred_t < -threshold
             =  0 otherwise

Realized PnL_t = position_t * realized_fwd_ret - cost * |position_t - position_{t-1}|
where cost = COST_BPS_PER_SIDE / 1e4 per side.

Aggregates per-symbol, then equally-weights across symbols. Outputs a daily
equity curve and headline stats.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from research import config


@dataclass
class BacktestResult:
    daily_equity: pd.Series
    minute_pnl: pd.Series
    stats: dict


def _positions(pred: pd.Series, threshold_bps: float) -> pd.Series:
    thr = threshold_bps / 1e4
    pos = pd.Series(0, index=pred.index, dtype="int64")
    pos[pred > thr] = 1
    pos[pred < -thr] = -1
    return pos


def backtest_symbol(
    pred: pd.Series,
    realized_fwd_ret: pd.Series,
    cost_bps: float = config.COST_BPS_PER_SIDE,
    threshold_bps: float = config.SIGNAL_THRESHOLD_BPS,
) -> pd.DataFrame:
    df = pd.concat([pred.rename("pred"), realized_fwd_ret.rename("y")], axis=1).dropna()
    if df.empty:
        return pd.DataFrame(columns=["pos", "pnl"])
    df["pos"] = _positions(df["pred"], threshold_bps)
    turnover = df["pos"].diff().abs().fillna(df["pos"].abs())
    cost = turnover * (cost_bps / 1e4)
    df["pnl"] = df["pos"] * df["y"] - cost
    return df[["pos", "pnl"]]


def aggregate(symbol_to_bt: dict[str, pd.DataFrame]) -> BacktestResult:
    if not symbol_to_bt:
        return BacktestResult(pd.Series(dtype="float64"), pd.Series(dtype="float64"), {})

    pnls: list[pd.Series] = []
    for sym, df in symbol_to_bt.items():
        if df.empty:
            continue
        s = df["pnl"].rename(sym)
        pnls.append(s)
    if not pnls:
        return BacktestResult(pd.Series(dtype="float64"), pd.Series(dtype="float64"), {})

    minute_pnl_panel = pd.concat(pnls, axis=1)
    # equal-weight: average across symbols available at each timestamp
    minute_pnl = minute_pnl_panel.mean(axis=1)
    daily_pnl = minute_pnl.groupby(minute_pnl.index.date).sum()
    daily_equity = daily_pnl.cumsum()

    # stats
    if len(daily_pnl) >= 2 and daily_pnl.std() > 0:
        sharpe = float(np.sqrt(252) * daily_pnl.mean() / daily_pnl.std())
    else:
        sharpe = float("nan")
    max_dd = float((daily_equity - daily_equity.cummax()).min()) if not daily_equity.empty else float("nan")
    stats = {
        "n_days": int(len(daily_pnl)),
        "total_return": float(daily_pnl.sum()),
        "ann_return": float(daily_pnl.mean() * 252),
        "ann_vol": float(daily_pnl.std() * np.sqrt(252)) if daily_pnl.std() > 0 else float("nan"),
        "sharpe": sharpe,
        "max_drawdown": max_dd,
        "hit_rate": float((daily_pnl > 0).mean()),
    }
    daily_equity.index = pd.to_datetime(daily_equity.index)
    return BacktestResult(daily_equity=daily_equity, minute_pnl=minute_pnl, stats=stats)
