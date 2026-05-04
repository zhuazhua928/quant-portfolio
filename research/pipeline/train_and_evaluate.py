"""End-to-end walk-forward training & evaluation.

For each fold:
  1. Fit Stage-1 (HMM K=4 by default) on the training rows.
  2. Predict regime labels on test rows.
  3. Fit Stage-2 (LightGBM per regime + global) on training rows.
  4. Predict on test, compute metrics, run two backtests:
     a. minute-bar directional backtest (legacy: every-bar position changes)
     b. regime-swing backtest (NEW headline: hold through regime block)

Saves:
  - research_artifacts/results/oof_predictions.parquet
  - research_artifacts/results/fold_metrics.json
  - research_artifacts/results/agg_metrics.json
  - research_artifacts/results/backtest_curves.parquet         (minute-bar)
  - research_artifacts/results/regime_swing_curve.parquet      (regime-swing)
  - research_artifacts/results/regime_swing_stats.json
  - research_artifacts/results/regime_swing_per_symbol.parquet
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
from research.evaluation import backtest as bt
from research.evaluation.metrics import summarize
from research.evaluation.regime_strategy import (
    RegimeSwingConfig,
    backtest_regime_swing,
    build_positions,
)
from research.evaluation.walkforward import walk_forward_splits
from research.models import baselines, forecaster_lgb, regime_hmm

logger = logging.getLogger(__name__)


def _slice_panel(panel: pd.DataFrame, ts_index: pd.DatetimeIndex) -> pd.DataFrame:
    return panel.loc[panel.index.get_level_values("ts").isin(ts_index)]


def run_walkforward(
    panel: pd.DataFrame,
    target_col: str = "fwd_ret_5m",
    n_components: int = 4,
    swing_cfg: RegimeSwingConfig | None = None,
) -> dict:
    config.ensure_dirs()
    swing_cfg = swing_cfg or RegimeSwingConfig()
    ts_index = pd.DatetimeIndex(sorted(panel.index.get_level_values("ts").unique()))

    fold_metrics: list[dict] = []
    oof_rows: list[pd.DataFrame] = []
    backtest_curves: dict[str, list[pd.Series]] = {
        "two_stage_hmm": [], "single_stage_lgb": [], "naive_momentum": [],
    }
    swing_pnls: list[pd.Series] = []
    swing_gross: list[pd.Series] = []
    swing_per_symbol: list[pd.DataFrame] = []
    swing_fold_stats: list[dict] = []

    for split in walk_forward_splits(ts_index, n_splits=config.CV_N_SPLITS,
                                     embargo_days=config.CV_EMBARGO_DAYS):
        train = _slice_panel(panel, split.train_idx)
        test = _slice_panel(panel, split.test_idx)
        if train.empty or test.empty:
            continue

        # --- Stage 1 (HMM, pooled across symbols) -----------------------------
        train_for_hmm = train.dropna(subset=[c for c in regime_hmm.HMM_FEATURE_COLS if c in train.columns])
        if len(train_for_hmm) < n_components * 100:
            logger.warning("fold %d: too few train rows for HMM, skipping", split.fold)
            continue

        hmm_bundle = regime_hmm.fit_hmm(train_for_hmm, n_components=n_components)
        train_lbl, _ = hmm_bundle.predict(train)
        test_lbl, test_probs = hmm_bundle.predict(test)

        # --- Stage 2 (per-regime LightGBM) ------------------------------------
        try:
            two_stage = forecaster_lgb.fit_two_stage(train, train_lbl, target_col=target_col)
        except ValueError as exc:
            logger.warning("fold %d: two-stage fit failed (%s)", split.fold, exc)
            continue

        ts_pred = two_stage.predict_regression(test, test_lbl)
        ts_p_up = two_stage.predict_proba_up(test, test_lbl)

        # --- Baselines --------------------------------------------------------
        ssl = baselines.SingleStageLGB().fit(train, target_col=target_col)
        ssl_pred = ssl.predict_regression(test)
        ssl_p_up = ssl.predict_proba_up(test)

        nm = baselines.NaiveMomentum()
        nm_pred = nm.predict_regression(test)
        nm_p_up = nm.predict_proba_up(test)

        # --- Metrics ----------------------------------------------------------
        y = test[target_col]
        fold_row = {"fold": split.fold,
                    "train_n": int(len(train)), "test_n": int(len(test)),
                    "train_start": str(split.train_idx.min().date()),
                    "test_start": str(split.test_idx.min().date()),
                    "test_end": str(split.test_idx.max().date()),
                    "two_stage_hmm": summarize(y, ts_pred, ts_p_up),
                    "single_stage_lgb": summarize(y, ssl_pred, ssl_p_up),
                    "naive_momentum": summarize(y, nm_pred, nm_p_up)}
        fold_metrics.append(fold_row)
        logger.info("fold %d: two-stage acc=%.3f brier=%.4f | single acc=%.3f | naive acc=%.3f",
                    split.fold,
                    fold_row["two_stage_hmm"]["directional_accuracy"],
                    fold_row["two_stage_hmm"]["brier"],
                    fold_row["single_stage_lgb"]["directional_accuracy"],
                    fold_row["naive_momentum"]["directional_accuracy"])

        # --- OOF predictions --------------------------------------------------
        oof = test[[target_col]].copy()
        oof.columns = ["realized_fwd_ret"]
        oof["pred_two_stage"] = ts_pred
        oof["p_up_two_stage"] = ts_p_up
        oof["pred_single_stage"] = ssl_pred
        oof["p_up_single_stage"] = ssl_p_up
        oof["pred_naive"] = nm_pred
        oof["regime"] = test_lbl
        # Reattach test_probs (which is indexed by ts only inside `test_probs`'s
        # source; we built it on the windowed sub-frame). Align by row position
        # of the test panel.
        # test_probs was returned aligned to `test.index` (full MultiIndex).
        for j in range(n_components):
            col = f"p_{j}"
            if col in test_probs.columns:
                oof[f"regime_{col}"] = test_probs[col].values
        oof["fold"] = split.fold
        oof_rows.append(oof)

        # --- Per-fold minute-bar backtest (legacy) ---------------------------
        for label, pred_col in [
            ("two_stage_hmm", "pred_two_stage"),
            ("single_stage_lgb", "pred_single_stage"),
            ("naive_momentum", "pred_naive"),
        ]:
            sym_to_bt = {}
            for sym, sub in oof.groupby(level="symbol"):
                pred_s = sub[pred_col].droplevel("symbol")
                y_s = sub["realized_fwd_ret"].droplevel("symbol")
                sym_to_bt[sym] = bt.backtest_symbol(pred_s, y_s)
            res = bt.aggregate(sym_to_bt)
            backtest_curves[label].append(res.daily_equity.rename(f"fold{split.fold}"))

        # --- Per-fold regime-swing backtest (HEADLINE) ------------------------
        regime_prob_cols = [f"regime_p_{j}" for j in range(n_components)
                            if f"regime_p_{j}" in oof.columns]
        if regime_prob_cols:
            regime_probs_oof = oof[regime_prob_cols]
            positions = build_positions(
                panel=test,
                regime_probs=regime_probs_oof,
                forecaster_pred=oof["pred_two_stage"],
                config=swing_cfg,
                K=n_components,
            )
            swing_res = backtest_regime_swing(test, positions, swing_cfg, target_col=target_col)
            if swing_res["stats"]:
                fold_swing = dict(swing_res["stats"])
                fold_swing["fold"] = split.fold
                swing_fold_stats.append(fold_swing)
                logger.info(
                    "fold %d swing: ann_ret=%.2f%% sharpe=%.2f hold=%.1fbars in_pos=%.1f%% trades=%d",
                    split.fold,
                    fold_swing["ann_return"] * 100,
                    fold_swing["sharpe"],
                    fold_swing["avg_holding_period_bars"],
                    fold_swing["frac_time_in_position"] * 100,
                    fold_swing["n_trades_total"],
                )
                # store daily PnL & gross PnL (for global stitching)
                swing_pnls.append(swing_res["daily_pnl"])
                swing_gross.append(swing_res["daily_gross_equity"].diff().fillna(swing_res["daily_gross_equity"].iloc[0] if len(swing_res["daily_gross_equity"]) else 0))
                ps = swing_res["per_symbol"].reset_index()
                ps["fold"] = split.fold
                swing_per_symbol.append(ps)

    # ----------------------------------------------------------------------
    # Aggregate & persist
    # ----------------------------------------------------------------------
    results_dir = config.RESULTS_DIR
    results_dir.mkdir(parents=True, exist_ok=True)

    if oof_rows:
        oof_all = pd.concat(oof_rows)
        oof_all.to_parquet(results_dir / "oof_predictions.parquet")

    with open(results_dir / "fold_metrics.json", "w") as f:
        json.dump(fold_metrics, f, indent=2, default=float)

    # stitch minute-bar fold curves
    summary_curves = {}
    for label, curves in backtest_curves.items():
        if not curves:
            continue
        daily_pnls = []
        for c in curves:
            if len(c) == 0:
                continue
            pnl = c.diff()
            pnl.iloc[0] = c.iloc[0]
            daily_pnls.append(pnl)
        if not daily_pnls:
            continue
        merged = pd.concat(daily_pnls).sort_index()
        merged = merged.groupby(merged.index).sum()
        summary_curves[label] = merged.cumsum()
    if summary_curves:
        pd.DataFrame(summary_curves).to_parquet(results_dir / "backtest_curves.parquet")

    # stitch regime-swing fold curves
    swing_summary: dict = {"config": asdict(swing_cfg), "folds": swing_fold_stats}
    if swing_pnls:
        merged = pd.concat(swing_pnls).sort_index()
        merged = merged.groupby(merged.index).sum()
        merged_gross = pd.concat(swing_gross).sort_index().groupby(level=0).sum() if swing_gross else None

        equity = merged.cumsum()
        gross_equity = merged_gross.cumsum() if merged_gross is not None else None

        # OOS aggregate stats across all stitched test windows
        n_days = int(len(merged))
        if n_days >= 2 and merged.std() > 0:
            sharpe = float(np.sqrt(252) * merged.mean() / merged.std())
        else:
            sharpe = float("nan")
        max_dd = float((equity - equity.cummax()).min())
        swing_summary["oos_aggregate"] = {
            "n_days": n_days,
            "total_return": float(merged.sum()),
            "ann_return": float(merged.mean() * 252),
            "ann_vol": float(merged.std() * np.sqrt(252)) if merged.std() > 0 else float("nan"),
            "sharpe": sharpe,
            "max_drawdown": max_dd,
            "calmar": float(merged.mean() * 252 / abs(max_dd)) if max_dd < 0 else float("nan"),
            "hit_rate_daily": float((merged > 0).mean()),
        }

        df = pd.DataFrame({"net_equity": equity})
        if gross_equity is not None:
            df["gross_equity"] = gross_equity.reindex(equity.index).ffill()
        df.to_parquet(results_dir / "regime_swing_curve.parquet")

    if swing_per_symbol:
        ps_all = pd.concat(swing_per_symbol, ignore_index=True)
        ps_agg = ps_all.groupby("symbol").agg(
            n=("n", "sum"),
            n_in_position=("n_in_position", "sum"),
            total_return=("total_return", "sum"),
            avg_return=("avg_return", "mean"),
            hit_rate=("hit_rate", "mean"),
            turnover_per_day=("turnover_per_day", "mean"),
            n_folds=("fold", "nunique"),
        ).sort_values("total_return", ascending=False)
        ps_agg.to_parquet(results_dir / "regime_swing_per_symbol.parquet")

    with open(results_dir / "regime_swing_stats.json", "w") as f:
        json.dump(swing_summary, f, indent=2, default=float)

    # final aggregate metrics across folds (forecast quality, not strategy)
    agg = {}
    if fold_metrics:
        for model in ("two_stage_hmm", "single_stage_lgb", "naive_momentum"):
            keys = [k for k in fold_metrics[0][model].keys() if k != "n"]
            agg[model] = {k: float(np.nanmean([fm[model][k] for fm in fold_metrics])) for k in keys}
    with open(results_dir / "agg_metrics.json", "w") as f:
        json.dump(agg, f, indent=2)

    logger.info("walk-forward complete. results -> %s", results_dir)
    return {"folds": fold_metrics, "agg": agg, "swing": swing_summary}


def _build_swing_cfg_from_args(args) -> RegimeSwingConfig:
    return RegimeSwingConfig(
        entry_long_p=args.entry_long_p,
        entry_short_p=args.entry_short_p,
        exit_long_p=args.exit_long_p,
        exit_long_on_bear_p=args.exit_long_on_bear_p,
        exit_short_p=args.exit_short_p,
        exit_short_on_bull_p=args.exit_short_on_bull_p,
        top_n_per_regime=args.top_n,
        short_enabled=args.short_enabled,
        cost_bps_per_side=args.cost_bps,
        flatten_at_close=not args.allow_overnight,
        vol_target_annual=args.vol_target,
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--panel", default=str(config.WINDOWS_DIR / "panel.parquet"))
    p.add_argument("-K", type=int, default=4, help="HMM number of components")
    p.add_argument("--target", default="fwd_ret_5m")
    # Regime-swing strategy parameters (all configurable for re-tuning)
    p.add_argument("--entry-long-p", type=float, default=0.60)
    p.add_argument("--entry-short-p", type=float, default=0.60)
    p.add_argument("--exit-long-p", type=float, default=0.35)
    p.add_argument("--exit-long-on-bear-p", type=float, default=0.50)
    p.add_argument("--exit-short-p", type=float, default=0.35)
    p.add_argument("--exit-short-on-bull-p", type=float, default=0.50)
    p.add_argument("--top-n", type=int, default=5,
                   help="top-N symbols by Stage-2 prediction allowed to enter (0=disabled)")
    p.add_argument("--short-enabled", action="store_true")
    p.add_argument("--allow-overnight", action="store_true",
                   help="do not flatten positions at session close")
    p.add_argument("--cost-bps", type=float, default=1.0)
    p.add_argument("--vol-target", type=float, default=None,
                   help="annualized vol target (e.g., 0.20). Default: equal-weighted.")
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s | %(message)s")

    panel_path = Path(args.panel)
    if not panel_path.exists():
        logger.error("panel not found: %s — run research.pipeline.build_panel first", panel_path)
        return 1
    panel = pd.read_parquet(panel_path)
    logger.info("loaded panel %s rows=%d", panel_path, len(panel))

    swing_cfg = _build_swing_cfg_from_args(args)
    logger.info("regime-swing config: %s", asdict(swing_cfg))

    run_walkforward(panel, target_col=args.target, n_components=args.K, swing_cfg=swing_cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
