"""Parameter sweep over regime-swing thresholds, reusing saved OOF predictions.

Loads research_artifacts/results/oof_predictions.parquet and the original
windowed panel, then re-applies the regime-swing state machine for each
combination of thresholds in the sweep grid. No model retraining required —
this evaluates *only* the strategy layer.

Writes:
  research_artifacts/results/swing_sweep.json   (full grid + stats)
"""

from __future__ import annotations

import argparse
import itertools
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


def evaluate_config(
    panel: pd.DataFrame,
    oof: pd.DataFrame,
    cfg: RegimeSwingConfig,
    K: int,
) -> dict:
    regime_prob_cols = [f"regime_p_{j}" for j in range(K) if f"regime_p_{j}" in oof.columns]
    regime_probs = oof[regime_prob_cols]
    forecaster = oof["pred_two_stage"]

    # Walk fold by fold so the state machine resets between fold boundaries.
    swing_pnls: list[pd.Series] = []
    folds_stats: list[dict] = []
    for fold, fold_oof in oof.groupby("fold"):
        fold_panel = panel.loc[fold_oof.index]
        fold_probs = regime_probs.loc[fold_oof.index]
        fold_pred = forecaster.loc[fold_oof.index]
        positions = build_positions(fold_panel, fold_probs, fold_pred, cfg, K)
        res = backtest_regime_swing(fold_panel, positions, cfg, target_col="fwd_ret_5m")
        if res["stats"]:
            folds_stats.append({**res["stats"], "fold": int(fold)})
            swing_pnls.append(res["daily_pnl"])

    if not swing_pnls:
        return {"config": asdict(cfg), "agg": {}, "folds": []}

    merged = pd.concat(swing_pnls).sort_index()
    merged = merged.groupby(merged.index).sum()
    if merged.std() > 0:
        sharpe = float(np.sqrt(252) * merged.mean() / merged.std())
    else:
        sharpe = float("nan")
    equity = merged.cumsum()
    max_dd = float((equity - equity.cummax()).min()) if not equity.empty else float("nan")

    return {
        "config": asdict(cfg),
        "agg": {
            "n_days": int(len(merged)),
            "total_return": float(merged.sum()),
            "ann_return": float(merged.mean() * 252),
            "ann_vol": float(merged.std() * np.sqrt(252)) if merged.std() > 0 else float("nan"),
            "sharpe": sharpe,
            "max_drawdown": max_dd,
            "calmar": float(merged.mean() * 252 / abs(max_dd)) if max_dd and max_dd < 0 else float("nan"),
            "hit_rate_daily": float((merged > 0).mean()),
            "avg_n_trades": float(np.mean([fs["n_trades_total"] for fs in folds_stats])) if folds_stats else float("nan"),
            "avg_holding_bars": float(np.mean([fs["avg_holding_period_bars"] for fs in folds_stats])) if folds_stats else float("nan"),
            "avg_frac_in_position": float(np.mean([fs["frac_time_in_position"] for fs in folds_stats])) if folds_stats else float("nan"),
        },
    }


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

    # Sweep grid — kept small but covers the meaningful corners.
    grid = list(itertools.product(
        [0.50, 0.60, 0.70, 0.80],   # entry_long_p
        [0.20, 0.30, 0.40],          # exit_long_p
        [0.40, 0.50, 0.60],          # exit_long_on_bear_p
        [3, 5, 10, 0],               # top_n_per_regime  (0 = all)
    ))
    logger.info("sweep size = %d configs", len(grid))

    results = []
    for i, (e, x, f, t) in enumerate(grid, 1):
        if x >= e:
            continue  # exit threshold must be below entry
        cfg = RegimeSwingConfig(
            entry_long_p=e, exit_long_p=x, exit_long_on_bear_p=f,
            top_n_per_regime=t,
        )
        r = evaluate_config(panel, oof, cfg, args.K)
        agg = r.get("agg", {})
        results.append(r)
        logger.info(
            "[%d/%d] e=%.2f x=%.2f f=%.2f n=%s | ann=%.2f%% sharpe=%.2f dd=%.2f%% trades/fold=%.0f hold=%.0fb",
            i, len(grid), e, x, f, str(t) if t > 0 else "all",
            agg.get("ann_return", float("nan")) * 100,
            agg.get("sharpe", float("nan")),
            agg.get("max_drawdown", float("nan")) * 100,
            agg.get("avg_n_trades", float("nan")),
            agg.get("avg_holding_bars", float("nan")),
        )

    # Sort by Sharpe and persist
    results.sort(key=lambda r: r["agg"].get("sharpe", -1e9), reverse=True)
    out_path = config.RESULTS_DIR / "swing_sweep.json"
    out_path.write_text(json.dumps(results, indent=2, default=float))
    logger.info("wrote %s", out_path)

    print("\n=== Top 8 configurations by Sharpe ===")
    for r in results[:8]:
        c = r["config"]
        a = r["agg"]
        print(f"  e={c['entry_long_p']:.2f}  x={c['exit_long_p']:.2f}  flip={c['exit_long_on_bear_p']:.2f}  N={c['top_n_per_regime']:>3}  "
              f"-> sharpe={a['sharpe']:+.2f}  ann={a['ann_return']*100:+.2f}%  dd={a['max_drawdown']*100:+.2f}%  trades/fold={a['avg_n_trades']:.0f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
