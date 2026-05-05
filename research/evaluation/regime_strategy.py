"""Regime-following swing strategy.

Strategy idea
-------------
Rather than betting on noisy 5-minute directional forecasts, hold positions
for the duration of a *regime block* — enter when the bullish (or bearish)
posterior is strong enough and exit only when the regime flips. Optionally
restrict entries to the top-N names ranked by the Stage-2 forecaster's
expected return inside that regime. This collapses turnover by 1-2 orders
of magnitude relative to the per-bar minute strategy and lets real edge
survive transaction costs.

State machine (per symbol, on 5-min windows)
--------------------------------------------
  flat  -> long   if  p_bull >= entry_long_p   AND symbol is top-N
  flat  -> short  if  p_bear >= entry_short_p  AND symbol is top-N
                  AND short_enabled
  long  -> flat   if  p_bull <  exit_long_p    OR  p_bear >= exit_long_on_bear_p
  short -> flat   if  p_bear <  exit_short_p   OR  p_bull >= exit_short_on_bull_p

Top-N filter applies *only at entry time*. Once a symbol is held, it is
held until its own exit condition triggers — so the realized hold period
is whatever the regime block lasts (median in our data: 30-90 minutes,
sometimes multi-session).

All thresholds are exposed on `RegimeSwingConfig` and persisted alongside
the backtest result so they can be re-tuned without code changes.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class RegimeSwingConfig:
    # Entry
    entry_long_p: float = 0.60          # bullish posterior to enter long
    entry_short_p: float = 0.60         # bearish posterior to enter short
    # Exit
    exit_long_p: float = 0.35           # bullish posterior to exit long
    exit_long_on_bear_p: float = 0.50   # bearish posterior to flip out of long
    exit_short_p: float = 0.35
    exit_short_on_bull_p: float = 0.50
    # Selection
    top_n_per_regime: int = 5           # 0 = all bullish-regime names
    short_enabled: bool = False
    # Execution
    cost_bps_per_side: float = 1.0
    flatten_at_close: bool = True       # close all positions at session end
    # Sizing — equal-weighted by default. To vol-target, divide by realized vol.
    vol_target_annual: float | None = None  # e.g. 0.20 for 20% vol target
    rv_window_min: int = 30


def _bull_col(K: int) -> str:
    return f"regime_p_{K - 1}"


def _bear_col() -> str:
    return "regime_p_0"


def _is_session_close(ts: pd.Timestamp) -> bool:
    """Approximate US RTH close (UTC). 19:55-20:00 UTC during DST, 20:55-21:00 standard.

    We flag the last 5-min window of either schedule.
    """
    minute = ts.hour * 60 + ts.minute
    return minute in (19 * 60 + 55, 20 * 60 + 55, 20 * 60, 21 * 60)


def build_positions(
    panel: pd.DataFrame,
    regime_probs: pd.DataFrame,
    forecaster_pred: pd.Series,
    config: RegimeSwingConfig,
    K: int,
) -> pd.Series:
    """Walk a state machine over (symbol, ts) and return a position series.

    Parameters
    ----------
    panel : MultiIndex (symbol, ts) DataFrame; only its index is used here.
    regime_probs : same MultiIndex; columns must include f"regime_p_0".. f"regime_p_{K-1}".
    forecaster_pred : MultiIndex (symbol, ts) Series of predicted forward return.
    """
    bull = _bull_col(K)
    bear = _bear_col()
    if bull not in regime_probs.columns or bear not in regime_probs.columns:
        raise ValueError(f"regime_probs missing columns {bull} or {bear}")

    # ------------------------------------------------------------------
    # Cross-sectional top-N membership at each timestamp.
    # A symbol is "top-N for entry" if its forecaster_pred is in the top
    # `top_n_per_regime` across symbols at that timestamp (long entry) or
    # in the bottom-N (short entry). top_n_per_regime <= 0 disables the filter.
    # ------------------------------------------------------------------
    if config.top_n_per_regime and config.top_n_per_regime > 0:
        # rank ascending: 1 = lowest, N = highest. We want top-N for long.
        ranks_desc = forecaster_pred.groupby(level="ts").rank(ascending=False, method="first")
        ranks_asc = forecaster_pred.groupby(level="ts").rank(ascending=True, method="first")
        is_top_long = ranks_desc <= config.top_n_per_regime
        is_top_short = ranks_asc <= config.top_n_per_regime
    else:
        is_top_long = pd.Series(True, index=forecaster_pred.index)
        is_top_short = pd.Series(True, index=forecaster_pred.index)

    # Reindex to panel just in case
    is_top_long = is_top_long.reindex(panel.index, fill_value=False)
    is_top_short = is_top_short.reindex(panel.index, fill_value=False)

    pos_chunks: list[pd.Series] = []
    for symbol, group in regime_probs.groupby(level="symbol", sort=False):
        group = group.droplevel("symbol").sort_index()
        long_mask = is_top_long.xs(symbol, level="symbol").reindex(group.index, fill_value=False)
        short_mask = is_top_short.xs(symbol, level="symbol").reindex(group.index, fill_value=False)

        positions = np.zeros(len(group), dtype=np.int8)
        state = 0  # -1, 0, 1
        for i, (ts, row) in enumerate(group.iterrows()):
            p_bull = row[bull]
            p_bear = row[bear]

            # End-of-session forced flatten
            if config.flatten_at_close and state != 0 and _is_session_close(ts):
                state = 0
                positions[i] = 0
                continue

            if state == 0:
                if p_bull >= config.entry_long_p and bool(long_mask.iloc[i]):
                    state = 1
                elif config.short_enabled and p_bear >= config.entry_short_p and bool(short_mask.iloc[i]):
                    state = -1
            elif state == 1:
                if p_bull < config.exit_long_p or p_bear >= config.exit_long_on_bear_p:
                    state = 0
            elif state == -1:
                if p_bear < config.exit_short_p or p_bull >= config.exit_short_on_bull_p:
                    state = 0
            positions[i] = state

        pos_chunks.append(pd.Series(positions, index=group.index, name=symbol))

    # Stack back to (symbol, ts) MultiIndex
    pieces = []
    for s in pos_chunks:
        df = s.to_frame("pos")
        df["symbol"] = s.name
        pieces.append(df.reset_index().rename(columns={s.index.name or "index": "ts"}))
    if not pieces:
        return pd.Series(dtype="int8")
    out = pd.concat(pieces, ignore_index=True).set_index(["symbol", "ts"])["pos"]
    return out.sort_index()


def backtest_regime_swing(
    panel: pd.DataFrame,
    positions: pd.Series,
    config: RegimeSwingConfig,
    target_col: str = "fwd_ret_5m",
) -> dict:
    """Compute PnL given positions and realized forward returns.

    PnL_t = position_t * realized_fwd_ret_t - cost * |Δposition_t|

    Aggregates equal-weight across symbols available at each ts, sums to daily
    equity. Returns headline stats + daily equity series + per-symbol stats.
    """
    realized = panel[target_col]
    aligned = pd.concat(
        [positions.rename("pos"), realized.rename("y")], axis=1
    ).dropna()
    if aligned.empty:
        return {
            "stats": {},
            "daily_equity": pd.Series(dtype="float64"),
            "per_symbol": pd.DataFrame(),
        }

    # vol-target sizing (optional)
    if config.vol_target_annual is not None and "rv" in panel.columns:
        rv = panel["rv"].reindex(aligned.index)
        # rv is per-bar std of 1-min returns scaled by sqrt(window). Convert to
        # annualized estimate: per-bar std * sqrt(390 * 252) for minute bars.
        ann_vol = rv * np.sqrt(390 * 252)
        scale = (config.vol_target_annual / ann_vol).clip(0, 5).fillna(1.0)
        aligned["pos"] = aligned["pos"] * scale

    aligned["turnover"] = aligned.groupby(level="symbol")["pos"].diff().abs().fillna(aligned["pos"].abs())
    aligned["cost"] = aligned["turnover"] * (config.cost_bps_per_side / 1e4)
    aligned["pnl_gross"] = aligned["pos"] * aligned["y"]
    aligned["pnl_net"] = aligned["pnl_gross"] - aligned["cost"]

    # Per-symbol stats
    per_symbol = (
        aligned.groupby(level="symbol")
        .agg(
            n=("pnl_net", "size"),
            n_in_position=("pos", lambda s: int((s != 0).sum())),
            turnover_per_day=("turnover", "mean"),
            total_return=("pnl_net", "sum"),
            avg_return=("pnl_net", "mean"),
            hit_rate=("pnl_net", lambda s: float((s > 0).mean())),
        )
        .sort_values("total_return", ascending=False)
    )

    # Aggregate equally across symbols at each ts (avg PnL of held names)
    by_ts = aligned.groupby(level="ts")[["pnl_net", "pnl_gross", "turnover", "pos"]].mean()
    by_ts.index = pd.to_datetime(by_ts.index)
    daily_pnl = by_ts["pnl_net"].groupby(by_ts.index.date).sum()
    daily_gross = by_ts["pnl_gross"].groupby(by_ts.index.date).sum()
    daily_turnover = by_ts["turnover"].groupby(by_ts.index.date).sum()
    daily_pnl.index = pd.to_datetime(daily_pnl.index)
    daily_gross.index = pd.to_datetime(daily_gross.index)
    daily_turnover.index = pd.to_datetime(daily_turnover.index)

    daily_equity = daily_pnl.cumsum()

    # Stats
    if len(daily_pnl) >= 2 and daily_pnl.std() > 0:
        sharpe = float(np.sqrt(252) * daily_pnl.mean() / daily_pnl.std())
    else:
        sharpe = float("nan")
    max_dd = float((daily_equity - daily_equity.cummax()).min()) if not daily_equity.empty else float("nan")
    avg_holding = float(_avg_holding_period(positions))

    stats = {
        "config": asdict(config),
        "n_days": int(len(daily_pnl)),
        "n_bars_in_position": int((aligned["pos"] != 0).sum()),
        "frac_time_in_position": float((aligned["pos"] != 0).mean()),
        "avg_holding_period_bars": avg_holding,
        "total_return": float(daily_pnl.sum()),
        "total_return_gross": float(daily_gross.sum()),
        "ann_return": float(daily_pnl.mean() * 252),
        "ann_vol": float(daily_pnl.std() * np.sqrt(252)) if daily_pnl.std() > 0 else float("nan"),
        "sharpe": sharpe,
        "max_drawdown": max_dd,
        "calmar": float(daily_pnl.mean() * 252 / abs(max_dd)) if max_dd and max_dd < 0 else float("nan"),
        "hit_rate_daily": float((daily_pnl > 0).mean()),
        "avg_daily_turnover": float(daily_turnover.mean()),
        "n_trades_total": int(aligned["turnover"].sum() / 2),  # round-trips
    }

    return {
        "stats": stats,
        "daily_equity": daily_equity,
        "daily_pnl": daily_pnl,
        "daily_gross_equity": daily_gross.cumsum(),
        "per_symbol": per_symbol,
        "positions": aligned["pos"],
    }


def _avg_holding_period(positions: pd.Series) -> float:
    """Mean number of consecutive non-zero bars per held block, across symbols."""
    blocks = []
    for _, sub in positions.groupby(level="symbol", sort=False):
        s = sub.droplevel("symbol")
        # find runs of non-zero
        nz = (s != 0).astype(int).values
        if nz.sum() == 0:
            continue
        # run-length encode
        diffs = np.diff(np.concatenate([[0], nz, [0]]))
        starts = np.where(diffs == 1)[0]
        ends = np.where(diffs == -1)[0]
        for st, en in zip(starts, ends):
            blocks.append(en - st)
    if not blocks:
        return 0.0
    return float(np.mean(blocks))
