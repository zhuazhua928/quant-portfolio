"""Diagnostic: characterize the strategy gap vs benchmarks and zero-cost.

Compares on the same OOS test windows:
  1. Long-only equal-weighted buy-and-hold (the universe benchmark)
  2. Long-only basket *only when bullish regime detected* (no top-N, no LGB)
  3. Regime-swing default config (entry 0.60 / exit 0.35 / top-N 5)
  4. Regime-swing best-config-from-sweep (loaded if available)
  5. All four with cost=0 to isolate the gross signal
  6. Per-regime realized mean fwd return — does the "bullish" regime
     actually have a positive mean fwd return out-of-sample?

Writes:
  research_artifacts/results/diagnostic.json
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from research import config
from research.evaluation.regime_strategy import (
    RegimeSwingConfig,
    backtest_regime_swing,
    build_positions,
)

logger = logging.getLogger(__name__)


def _stats(daily_pnl: pd.Series) -> dict:
    if daily_pnl.empty or daily_pnl.std() == 0 or pd.isna(daily_pnl.std()):
        return {"n_days": int(len(daily_pnl)), "ann_return": 0.0, "sharpe": float("nan"),
                "max_dd": float("nan"), "total_return": float(daily_pnl.sum())}
    equity = daily_pnl.cumsum()
    return {
        "n_days": int(len(daily_pnl)),
        "total_return": float(daily_pnl.sum()),
        "ann_return": float(daily_pnl.mean() * 252),
        "ann_vol": float(daily_pnl.std() * np.sqrt(252)),
        "sharpe": float(np.sqrt(252) * daily_pnl.mean() / daily_pnl.std()),
        "max_dd": float((equity - equity.cummax()).min()),
        "hit_rate_daily": float((daily_pnl > 0).mean()),
    }


def buy_and_hold(panel: pd.DataFrame, oof: pd.DataFrame, cost_bps: float = 0.0) -> dict:
    """Long-only equal-weighted basket of all symbols. Held continuously over OOS folds.

    Costs: only initial entry per fold + final exit (1bp each end). Negligible.
    """
    realized = panel["fwd_ret_5m"].reindex(oof.index)
    by_ts = realized.groupby(level="ts").mean()
    by_ts.index = pd.to_datetime(by_ts.index)
    daily = by_ts.groupby(by_ts.index.date).sum()
    daily.index = pd.to_datetime(daily.index)
    # Cost: roughly two trades per fold (enter at start, exit at end)
    daily.iloc[0] -= cost_bps / 1e4
    daily.iloc[-1] -= cost_bps / 1e4
    return {"daily_pnl": daily, **_stats(daily)}


def basket_when_bullish(
    panel: pd.DataFrame,
    oof: pd.DataFrame,
    K: int,
    entry_p: float = 0.50,
    exit_p: float = 0.30,
    cost_bps: float = 1.0,
) -> dict:
    """Hold the *whole basket* (no top-N) only when the bullish posterior >= entry_p.

    A simpler version of the swing strategy that strips out the LGB ranking.
    """
    cfg = RegimeSwingConfig(
        entry_long_p=entry_p, exit_long_p=exit_p, exit_long_on_bear_p=0.5,
        top_n_per_regime=0, short_enabled=False, cost_bps_per_side=cost_bps,
    )
    cols = [f"regime_p_{j}" for j in range(K) if f"regime_p_{j}" in oof.columns]
    pieces: list[pd.Series] = []
    for fold, sub in oof.groupby("fold"):
        positions = build_positions(panel.loc[sub.index], sub[cols],
                                    sub["pred_two_stage"], cfg, K)
        res = backtest_regime_swing(panel.loc[sub.index], positions, cfg, "fwd_ret_5m")
        if not res["daily_pnl"].empty:
            pieces.append(res["daily_pnl"])
    if not pieces:
        return {"daily_pnl": pd.Series(dtype="float64"), **_stats(pd.Series(dtype="float64"))}
    daily = pd.concat(pieces).sort_index()
    daily = daily.groupby(daily.index).sum()
    return {"daily_pnl": daily, "config": asdict(cfg), **_stats(daily)}


def swing_strategy(
    panel: pd.DataFrame,
    oof: pd.DataFrame,
    K: int,
    cfg: RegimeSwingConfig,
) -> dict:
    cols = [f"regime_p_{j}" for j in range(K) if f"regime_p_{j}" in oof.columns]
    pieces: list[pd.Series] = []
    for fold, sub in oof.groupby("fold"):
        positions = build_positions(panel.loc[sub.index], sub[cols],
                                    sub["pred_two_stage"], cfg, K)
        res = backtest_regime_swing(panel.loc[sub.index], positions, cfg, "fwd_ret_5m")
        if not res["daily_pnl"].empty:
            pieces.append(res["daily_pnl"])
    if not pieces:
        return {"daily_pnl": pd.Series(dtype="float64"), **_stats(pd.Series(dtype="float64"))}
    daily = pd.concat(pieces).sort_index()
    daily = daily.groupby(daily.index).sum()
    return {"daily_pnl": daily, "config": asdict(cfg), **_stats(daily)}


def regime_diagnostics(oof: pd.DataFrame, K: int) -> dict:
    """Per-regime out-of-sample realized mean fwd return and posterior mass."""
    out = {}
    for k in range(K):
        col = f"regime_p_{k}"
        if col not in oof.columns:
            continue
        # Realized fwd return weighted by posterior probability
        weighted_mean = float((oof[col] * oof["realized_fwd_ret"]).sum() / oof[col].sum()) if oof[col].sum() > 0 else float("nan")
        # Hard-assigned (argmax-regime) mean
        hard_mask = oof["regime"] == k
        hard_mean = float(oof.loc[hard_mask, "realized_fwd_ret"].mean()) if hard_mask.any() else float("nan")
        n_hard = int(hard_mask.sum())
        # Persistence: P(regime_t == regime_{t+1} | hard regime k)
        persistence = float("nan")
        if n_hard > 100:
            r = oof["regime"]
            r_next = r.groupby(level="symbol").shift(-1)
            persistence = float((r[hard_mask] == r_next[hard_mask]).mean())
        out[f"regime_{k}"] = {
            "weighted_mean_bps": weighted_mean * 1e4,
            "hard_mean_bps": hard_mean * 1e4,
            "n_hard_assigned": n_hard,
            "frac_of_oos": n_hard / len(oof),
            "persistence_one_step": persistence,
        }
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--panel", default=str(config.WINDOWS_DIR / "panel.parquet"))
    p.add_argument("--oof", default=str(config.RESULTS_DIR / "oof_predictions.parquet"))
    p.add_argument("-K", type=int, default=4)
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s | %(message)s")
    panel = pd.read_parquet(args.panel)
    oof = pd.read_parquet(args.oof)
    logger.info("loaded panel rows=%d, oof rows=%d", len(panel), len(oof))

    output: dict = {}

    # 1. Buy-and-hold benchmark
    bh = buy_and_hold(panel, oof, cost_bps=0.0)
    output["buy_and_hold_zero_cost"] = {k: v for k, v in bh.items() if k != "daily_pnl"}
    logger.info("Buy&Hold: ann=%.2f%% sharpe=%.2f", bh["ann_return"] * 100, bh["sharpe"])

    # 2. Basket when bullish (1bp cost)
    bb = basket_when_bullish(panel, oof, args.K, entry_p=0.50, exit_p=0.30, cost_bps=1.0)
    output["basket_when_bullish_p50"] = {k: v for k, v in bb.items() if k != "daily_pnl"}
    logger.info("Basket@bull≥0.50: ann=%.2f%% sharpe=%.2f", bb["ann_return"] * 100, bb["sharpe"])

    # 3. Default swing config (1bp)
    default_cfg = RegimeSwingConfig()  # default values
    sw = swing_strategy(panel, oof, args.K, default_cfg)
    output["swing_default_1bp"] = {k: v for k, v in sw.items() if k != "daily_pnl"}
    logger.info("Swing default: ann=%.2f%% sharpe=%.2f", sw["ann_return"] * 100, sw["sharpe"])

    # 4. Default swing with zero cost (gross signal)
    free_cfg = RegimeSwingConfig(cost_bps_per_side=0.0)
    sw0 = swing_strategy(panel, oof, args.K, free_cfg)
    output["swing_default_0bp_gross"] = {k: v for k, v in sw0.items() if k != "daily_pnl"}
    logger.info("Swing default GROSS: ann=%.2f%% sharpe=%.2f", sw0["ann_return"] * 100, sw0["sharpe"])

    # 5. Best swing config from sweep (if available)
    sweep_path = config.RESULTS_DIR / "swing_sweep.json"
    if sweep_path.exists():
        sweep = json.loads(sweep_path.read_text())
        # Best by Sharpe
        sweep.sort(key=lambda r: r["agg"].get("sharpe", -1e9), reverse=True)
        best = sweep[0]["config"]
        best_cfg = RegimeSwingConfig(**{k: v for k, v in best.items() if k != "rv_window_min"})
        sb = swing_strategy(panel, oof, args.K, best_cfg)
        output["swing_best_sweep_1bp"] = {k: v for k, v in sb.items() if k != "daily_pnl"}
        logger.info("Swing best from sweep: ann=%.2f%% sharpe=%.2f", sb["ann_return"] * 100, sb["sharpe"])

        sb0 = swing_strategy(panel, oof, args.K,
                             RegimeSwingConfig(**{**{k: v for k, v in best.items() if k != "rv_window_min"},
                                                   "cost_bps_per_side": 0.0}))
        output["swing_best_sweep_0bp_gross"] = {k: v for k, v in sb0.items() if k != "daily_pnl"}
        logger.info("Swing best GROSS: ann=%.2f%% sharpe=%.2f", sb0["ann_return"] * 100, sb0["sharpe"])

    # 6. Per-regime diagnostics
    output["regime_diagnostics"] = regime_diagnostics(oof, args.K)
    for k, v in output["regime_diagnostics"].items():
        logger.info("%s: hard_mean=%.2fbps weighted=%.2fbps n=%d frac=%.1f%% persist=%.2f",
                    k, v["hard_mean_bps"], v["weighted_mean_bps"], v["n_hard_assigned"],
                    v["frac_of_oos"] * 100, v.get("persistence_one_step", float("nan")))

    out_path = config.RESULTS_DIR / "diagnostic.json"
    out_path.write_text(json.dumps(output, indent=2, default=float))
    logger.info("wrote %s", out_path)

    print("\n=== HEADLINE COMPARISON (OOS aggregate, all folds stitched) ===")
    rows = [
        ("Buy & Hold (basket, ~0 cost)", "buy_and_hold_zero_cost"),
        ("Basket only when bullish (1bp)", "basket_when_bullish_p50"),
        ("Swing default (1bp)", "swing_default_1bp"),
        ("Swing default GROSS (0bp)", "swing_default_0bp_gross"),
    ]
    if "swing_best_sweep_1bp" in output:
        rows += [
            ("Swing best-sweep (1bp)", "swing_best_sweep_1bp"),
            ("Swing best-sweep GROSS (0bp)", "swing_best_sweep_0bp_gross"),
        ]
    print(f"{'Strategy':<35} {'AnnRet':>9} {'Sharpe':>7} {'MaxDD':>8} {'Hit%':>6}")
    for name, key in rows:
        s = output[key]
        print(f"  {name:<33} {s['ann_return']*100:>+7.2f}% {s['sharpe']:>+6.2f} {s['max_dd']*100:>+6.2f}% {s.get('hit_rate_daily',float('nan'))*100:>5.1f}%")

    print("\n=== Per-regime out-of-sample diagnostics ===")
    print(f"{'Regime':<10} {'Hard mean (bps)':>16} {'Weighted (bps)':>16} {'N':>10} {'Frac':>7} {'Persist':>8}")
    for k, v in output["regime_diagnostics"].items():
        print(f"  {k:<8} {v['hard_mean_bps']:>15.2f} {v['weighted_mean_bps']:>15.2f} {v['n_hard_assigned']:>10d} {v['frac_of_oos']*100:>6.1f}% {v.get('persistence_one_step',float('nan')):>7.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
