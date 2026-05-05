"""Export dashboard JSON for the Next.js research project page.

Reads:
  research_artifacts/results/{fold_metrics,agg_metrics}.json
  research_artifacts/results/backtest_curves.parquet
  research_artifacts/results/oof_predictions.parquet

Writes:
  src/data/research/summary.json
  src/data/research/backtest.json
  src/data/research/sessions/<YYYY-MM-DD>.json   (one per recent test date)
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from research import config

logger = logging.getLogger(__name__)


def _load_results():
    rdir = config.RESULTS_DIR
    fm = json.loads((rdir / "fold_metrics.json").read_text()) if (rdir / "fold_metrics.json").exists() else []
    agg = json.loads((rdir / "agg_metrics.json").read_text()) if (rdir / "agg_metrics.json").exists() else {}
    bc = pd.read_parquet(rdir / "backtest_curves.parquet") if (rdir / "backtest_curves.parquet").exists() else pd.DataFrame()
    oof = pd.read_parquet(rdir / "oof_predictions.parquet") if (rdir / "oof_predictions.parquet").exists() else pd.DataFrame()
    swing_stats = json.loads((rdir / "regime_swing_stats.json").read_text()) if (rdir / "regime_swing_stats.json").exists() else {}
    swing_curve = pd.read_parquet(rdir / "regime_swing_curve.parquet") if (rdir / "regime_swing_curve.parquet").exists() else pd.DataFrame()
    swing_per_sym = pd.read_parquet(rdir / "regime_swing_per_symbol.parquet") if (rdir / "regime_swing_per_symbol.parquet").exists() else pd.DataFrame()
    diagnostic = json.loads((rdir / "diagnostic.json").read_text()) if (rdir / "diagnostic.json").exists() else {}
    sweep = json.loads((rdir / "swing_sweep.json").read_text()) if (rdir / "swing_sweep.json").exists() else []
    return fm, agg, bc, oof, swing_stats, swing_curve, swing_per_sym, diagnostic, sweep


def export_summary(fm: list[dict], agg: dict, swing_stats: dict, swing_per_sym: pd.DataFrame,
                   diagnostic: dict, sweep: list, out_path: Path) -> None:
    per_sym_records: list[dict] = []
    if not swing_per_sym.empty:
        for _, row in swing_per_sym.reset_index().iterrows():
            per_sym_records.append({
                "symbol": str(row.get("symbol")),
                "n_in_position": int(row.get("n_in_position", 0)),
                "total_return": float(row.get("total_return", 0.0)),
                "avg_return_bps": float(row.get("avg_return", 0.0)) * 1e4,
                "hit_rate": float(row.get("hit_rate", 0.0)),
                "turnover_per_day": float(row.get("turnover_per_day", 0.0)),
                "n_folds": int(row.get("n_folds", 0)),
            })

    out = {
        "scope": {
            "universe_size": len(config.UNIVERSE),
            "high_beta": config.HIGH_BETA,
            "covariates": config.COVARIATES,
            "start": str(config.START),
            "end": str(config.END),
        },
        "config": {
            "n_splits": config.CV_N_SPLITS,
            "embargo_days": config.CV_EMBARGO_DAYS,
            "window_size_min": config.WINDOW_SIZE_MIN,
            "forecast_horizons_min": list(config.FORECAST_HORIZONS_MIN),
            "cost_bps_per_side": config.COST_BPS_PER_SIDE,
            "signal_threshold_bps": config.SIGNAL_THRESHOLD_BPS,
        },
        "forecast_aggregate": agg,
        "folds": fm,
        "regime_swing": {
            "config": swing_stats.get("config", {}),
            "oos_aggregate": swing_stats.get("oos_aggregate", {}),
            "folds": swing_stats.get("folds", []),
            "per_symbol": per_sym_records,
        },
        "diagnostic": diagnostic,
        "sweep_top": sweep[:12] if isinstance(sweep, list) else [],
        "data_caveat": (
            "Data: Alpaca Markets, IEX free feed. IEX represents ~2-3% of US "
            "consolidated volume — minute-level volume / VWAP for low-liquidity "
            "windows are partial. SIP feed (Algo Trader Plus) gives full tape."
        ),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2))
    logger.info("wrote %s", out_path)


def export_backtest(bc: pd.DataFrame, out_path: Path) -> None:
    if bc.empty:
        out = {"models": [], "series": []}
    else:
        rows = []
        for ts, row in bc.iterrows():
            rec = {"date": pd.Timestamp(ts).strftime("%Y-%m-%d")}
            for c in bc.columns:
                rec[c] = None if pd.isna(row[c]) else float(row[c])
            rows.append(rec)
        out = {"models": list(bc.columns), "series": rows}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2))
    logger.info("wrote %s (%d rows)", out_path, len(out.get("series", [])))


def export_swing_curve(swing_curve: pd.DataFrame, out_path: Path) -> None:
    if swing_curve.empty:
        out = {"columns": [], "series": []}
    else:
        rows = []
        for ts, row in swing_curve.iterrows():
            rec = {"date": pd.Timestamp(ts).strftime("%Y-%m-%d")}
            for c in swing_curve.columns:
                rec[c] = None if pd.isna(row[c]) else float(row[c])
            rows.append(rec)
        out = {"columns": list(swing_curve.columns), "series": rows}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2))
    logger.info("wrote %s (%d rows)", out_path, len(out.get("series", [])))


def export_sessions(oof: pd.DataFrame, out_dir: Path, n_recent: int = 7) -> None:
    """Write per-date snapshots for the dashboard's session viewer."""
    if oof.empty:
        return
    out_dir.mkdir(parents=True, exist_ok=True)

    # oof has MultiIndex (symbol, ts). Pick the most recent N distinct dates.
    ts = oof.index.get_level_values("ts")
    dates = sorted({pd.Timestamp(t).date() for t in ts}, reverse=True)[:n_recent]

    regime_cols = [c for c in oof.columns if c.startswith("regime_p_")]

    for d in dates:
        day = oof[oof.index.get_level_values("ts").map(lambda x: pd.Timestamp(x).date() == d)]
        if day.empty:
            continue

        per_symbol = {}
        for sym, sub in day.groupby(level="symbol"):
            sub = sub.droplevel("symbol")
            pts = []
            for ts_val, row in sub.iterrows():
                rec = {
                    "t": pd.Timestamp(ts_val).strftime("%H:%M"),
                    "regime": int(row["regime"]) if not pd.isna(row.get("regime", float("nan"))) else None,
                    "pred_two_stage_bps": None if pd.isna(row.get("pred_two_stage")) else float(row["pred_two_stage"]) * 1e4,
                    "pred_single_bps": None if pd.isna(row.get("pred_single_stage")) else float(row["pred_single_stage"]) * 1e4,
                    "realized_bps": None if pd.isna(row.get("realized_fwd_ret")) else float(row["realized_fwd_ret"]) * 1e4,
                }
                for c in regime_cols:
                    rec[c] = None if pd.isna(row.get(c)) else float(row[c])
                pts.append(rec)
            per_symbol[sym] = pts

        out = {"date": str(d), "symbols": per_symbol}
        path = out_dir / f"{d}.json"
        path.write_text(json.dumps(out))
        logger.info("wrote %s (%d symbols)", path, len(per_symbol))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--n-recent-sessions", type=int, default=7)
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s | %(message)s")
    config.ensure_dirs()
    fm, agg, bc, oof, swing_stats, swing_curve, swing_per_sym, diagnostic, sweep = _load_results()

    export_summary(fm, agg, swing_stats, swing_per_sym, diagnostic, sweep, config.DASHBOARD_DATA_DIR / "summary.json")
    export_backtest(bc, config.DASHBOARD_DATA_DIR / "backtest.json")
    export_swing_curve(swing_curve, config.DASHBOARD_DATA_DIR / "regime_swing_curve.json")
    export_sessions(oof, config.DASHBOARD_SESSIONS_DIR, n_recent=args.n_recent_sessions)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
