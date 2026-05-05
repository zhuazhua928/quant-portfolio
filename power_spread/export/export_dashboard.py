"""Build all 7 JSON files for the Next.js page from a backtest result set."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..backtest.pnl import naive_pnl, pnl_from_decisions
from ..backtest.strategy import decide_from_probit, decide_from_spread
from ..backtest.walk_forward import BacktestConfig
from ..config import (
    CALIBRATION_WINDOWS,
    COST_PER_MWH,
    COST_SWEEP,
    DATA_DIR,
    END_DATE,
    HUB,
    OOS_START,
    START_DATE,
    THRESHOLD_SWEEP,
)
from ..evaluation.classification import classification_stats
from ..evaluation.financial import summarize as financial_summary

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def _clean(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return None if np.isnan(obj) else round(float(obj), 6)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, float) and (obj != obj):
        return None
    if isinstance(obj, float):
        return round(obj, 6)
    if isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat()
    return obj


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_clean(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("wrote %s (%d bytes)", path, path.stat().st_size)


# ---------------------------------------------------------------------------
# Decisions and metrics, per config (ARX) / per (config, threshold) (Probit)
# ---------------------------------------------------------------------------

def _is_probit(model: str) -> bool:
    return model == "probit"


def _decision_series(forecasts: pd.DataFrame, model: str, mu: float | None = None) -> pd.Series:
    if _is_probit(model):
        if mu is None:
            raise ValueError("mu required for probit")
        return decide_from_probit(forecasts["prob"], mu)
    return decide_from_spread(forecasts["pred"])


def _per_config_record(
    cfg: BacktestConfig,
    forecasts: pd.DataFrame,
    mu: float | None,
    cost: float,
    avg_da_price: float,
) -> dict:
    y_hat = _decision_series(forecasts, cfg.model, mu)
    spread = forecasts["spread"]
    y_true = (spread > 0).astype("Int64")

    pnl_df = pnl_from_decisions(y_hat, spread, cost)
    cls = classification_stats(y_true, y_hat)
    fin = financial_summary(pnl_df["pnl"], avg_da_price=avg_da_price)
    return {
        "model": cfg.model,
        "window": cfg.window,
        "x_cols": list(cfg.x_cols),
        "lag_set": list(cfg.lag_set),
        "mu": mu if _is_probit(cfg.model) else None,
        "config_id": cfg.id + (f"__mu{mu:.2f}" if _is_probit(cfg.model) and mu is not None else ""),
        **cls,
        **fin,
    }


# ---------------------------------------------------------------------------
# Build the 7 JSONs
# ---------------------------------------------------------------------------

def build_pipeline_json() -> dict:
    """Static description of the 6-stage pipeline, rendered on the Pipeline tab."""
    return {
        "stages": [
            {
                "key": "ingest",
                "name": "Ingest",
                "role": "Pull ERCOT DAM + RTM SPP, EIA-930 demand forecast, wind & solar net generation",
                "files": [
                    "power_spread/sources/ercot_client.py",
                    "power_spread/sources/eia_ba_client.py",
                ],
                "inputs": [
                    "ERCOT NP4-180-ER (DAM SPP, hourly, by year)",
                    "ERCOT NP6-785-ER (RTM SPP, 15-min, by year)",
                    "EIA-930 EBA series: D, DF, NG.WND, NG.SUN at respondent ERCO",
                ],
                "outputs": [
                    "power_spread/_cache/dam_HB_NORTH_{year}.parquet (hourly)",
                    "power_spread/_cache/rtm_HB_NORTH_{year}.parquet (15-min -> hourly mean)",
                    "power_spread/_cache/eia_*.parquet",
                ],
            },
            {
                "key": "panel",
                "name": "Panel",
                "role": "Join DAM, RTM, EIA-930 series into one hourly panel; aggregate to daily means; add Mon/Sat/Sun/Holiday dummies",
                "files": ["power_spread/ingest/build_panel.py"],
                "inputs": ["yearly parquet caches from Ingest"],
                "outputs": [
                    "hourly_panel: ts, da_price, rt_price, spread, demand_fcst, wind_actual, solar_actual",
                    "daily_panel: date, p0_mean, p1_mean, spread, demand_fcst_mean, wind_mean, solar_mean, dummies",
                ],
            },
            {
                "key": "features",
                "name": "Features",
                "role": "Construct deterministic D, exogenous X (with persistence-forecast proxy for wind/solar), spread lags L = {2, 7}, P0_lag1",
                "files": ["power_spread/features/transform.py"],
                "inputs": ["daily_panel"],
                "outputs": [
                    "design matrix Z = [const, is_mon, is_sat, is_sun, is_holiday, X..., spread_lag_2, spread_lag_7, p0_lag1]",
                    "y_bin = 1{spread > 0}",
                ],
            },
            {
                "key": "models",
                "name": "Models",
                "role": "Three model specs from the paper: ARX_levels (fits P0 & P1 separately), ARX_spread (fits ΔP directly), Probit (Pr[ΔP > 0])",
                "files": [
                    "power_spread/models/arx.py",
                    "power_spread/models/probit.py",
                    "power_spread/models/naive.py",
                ],
                "inputs": ["design matrix Z"],
                "outputs": [
                    "spread_hat (ARX) or P(Y=1) (Probit)",
                    "Naive-DA (Y=0 always) and Naive-RT (Y=1 always) baselines",
                ],
            },
            {
                "key": "walkforward",
                "name": "Walk-forward Backtest",
                "role": "For each OOS day t and each calibration window T ∈ {30, 91, 182, 365}: refit on [t-T, t-1], forecast for t, apply decision rule, settle P&L using realized spread minus $0.50/MWh per market-switch",
                "files": [
                    "power_spread/backtest/walk_forward.py",
                    "power_spread/backtest/strategy.py",
                    "power_spread/backtest/pnl.py",
                ],
                "inputs": ["daily panel + features"],
                "outputs": [
                    "per-day forecasts (spread_hat or prob) per config",
                    "per-day decisions Y_hat and per-day P&L",
                ],
            },
            {
                "key": "evaluate",
                "name": "Evaluate",
                "role": "Classification metrics p, q0, q1 (paper Eqs 10-12); financial metrics total profit, annualized return, Sharpe, max drawdown, Calmar, 5% VaR",
                "files": [
                    "power_spread/evaluation/classification.py",
                    "power_spread/evaluation/financial.py",
                ],
                "inputs": ["per-day decisions + realized spreads"],
                "outputs": ["model-comparison grid", "headline summary"],
            },
            {
                "key": "export",
                "name": "Export",
                "role": "Write 7 JSON artifacts into src/data/power-spread/ for the Next.js dashboard to consume",
                "files": ["power_spread/export/export_dashboard.py"],
                "inputs": ["all of the above"],
                "outputs": [
                    "pipeline.json, summary.json, models.json, equity.json,",
                    "decisions.json, sensitivity.json, metadata.json",
                ],
            },
        ],
        "paper": {
            "title": "Day-Ahead vs. Intraday—Forecasting the Price Spread to Maximize Economic Benefits",
            "authors": "Maciejowska, Nitka & Weron",
            "venue": "Energies 12, 631 (2019)",
            "doi": "10.3390/en12040631",
        },
        "scope": {
            "market": f"ERCOT, {HUB}",
            "instruments": "Day-ahead (DAM) vs Real-time (RTM) Settlement Point Prices",
            "window": f"{START_DATE} to {END_DATE}",
            "oos_start": OOS_START,
            "calibration_windows": list(CALIBRATION_WINDOWS),
            "thresholds": list(THRESHOLD_SWEEP),
            "cost_per_mwh": COST_PER_MWH,
            "cost_sweep": list(COST_SWEEP),
        },
    }


def build_models_and_summary(
    daily: pd.DataFrame,
    forecasts: dict[str, pd.DataFrame],
    configs: list[BacktestConfig],
    cost: float = COST_PER_MWH,
) -> tuple[list[dict], dict, pd.Series, pd.Series, pd.Series, dict[str, pd.Series]]:
    """For every config (and threshold for probit), compute classification +
    financial metrics. Return:
        records: list of dicts (one per config x threshold) for models.json
        best: the headline best-by-total-profit record
        equity_best: daily P&L series for the best config
        equity_naive_da, equity_naive_rt: benchmark P&L series
        per_model_equity: dict[model_id -> pnl series] for the equity tab
    """
    oos = daily.loc[daily.index >= pd.Timestamp(OOS_START)]
    spread_oos = oos["spread"]
    avg_da_price = float(oos["p0_mean"].mean())

    records: list[dict] = []
    per_model_pnl: dict[str, pd.Series] = {}

    for cfg in configs:
        f = forecasts[cfg.id]
        if cfg.model == "probit":
            for mu in THRESHOLD_SWEEP:
                rec = _per_config_record(cfg, f, mu, cost, avg_da_price)
                records.append(rec)
                # also store the equity for the headline mu to plot one
                pnl_df = pnl_from_decisions(_decision_series(f, "probit", mu), f["spread"], cost)
                per_model_pnl[rec["config_id"]] = pnl_df["pnl"]
        else:
            rec = _per_config_record(cfg, f, None, cost, avg_da_price)
            records.append(rec)
            pnl_df = pnl_from_decisions(_decision_series(f, cfg.model), f["spread"], cost)
            per_model_pnl[rec["config_id"]] = pnl_df["pnl"]

    # benchmarks
    pnl_da = naive_pnl(spread_oos, cost, "naive_da")
    pnl_rt = naive_pnl(spread_oos, cost, "naive_rt")

    # naive-RT classification stats
    y_true = (spread_oos > 0).astype("Int64")
    cls_da = classification_stats(y_true, pd.Series(0, index=y_true.index))
    cls_rt = classification_stats(y_true, pd.Series(1, index=y_true.index))
    fin_da = financial_summary(pnl_da["pnl"], avg_da_price=avg_da_price)
    fin_rt = financial_summary(pnl_rt["pnl"], avg_da_price=avg_da_price)
    records.append({
        "model": "naive_da", "window": None, "x_cols": [], "lag_set": [], "mu": None,
        "config_id": "naive_da",
        **cls_da, **fin_da,
    })
    records.append({
        "model": "naive_rt", "window": None, "x_cols": [], "lag_set": [], "mu": None,
        "config_id": "naive_rt",
        **cls_rt, **fin_rt,
    })

    # pick best by total profit among non-naive
    candidates = [r for r in records if r["model"] not in ("naive_da", "naive_rt")]
    best = max(candidates, key=lambda r: (r.get("total_profit") or float("-inf")))
    equity_best = per_model_pnl[best["config_id"]]
    return records, best, equity_best, pnl_da["pnl"], pnl_rt["pnl"], per_model_pnl


def build_equity_json(
    equity_best: pd.Series,
    equity_da: pd.Series,
    equity_rt: pd.Series,
    per_model_pnl: dict[str, pd.Series],
    best_id: str,
    forecasts: dict[str, pd.DataFrame],
    configs: list[BacktestConfig],
) -> dict:
    """Build daily PnL + cumulative equity for the chart."""
    # representative (first) config per model type for the model-overlay chart
    rep_by_model: dict[str, pd.Series] = {}
    for cfg in configs:
        if cfg.model not in rep_by_model:
            f = forecasts[cfg.id]
            if cfg.model == "probit":
                pnl_df = pnl_from_decisions(decide_from_probit(f["prob"], 0.5), f["spread"], COST_PER_MWH)
            else:
                pnl_df = pnl_from_decisions(decide_from_spread(f["pred"]), f["spread"], COST_PER_MWH)
            rep_by_model[cfg.model] = pnl_df["pnl"]

    # union of dates
    idx = sorted(set(equity_best.index) | set(equity_da.index) | set(equity_rt.index))
    rows = []
    eq_best = equity_best.cumsum()
    eq_da = equity_da.cumsum()
    eq_rt = equity_rt.cumsum()
    eq_levels = rep_by_model.get("arx_levels", pd.Series(dtype=float)).cumsum()
    eq_spread = rep_by_model.get("arx_spread", pd.Series(dtype=float)).cumsum()
    eq_probit = rep_by_model.get("probit", pd.Series(dtype=float)).cumsum()

    for d in idx:
        rows.append({
            "date": pd.Timestamp(d).date().isoformat(),
            "pnl_best": float(equity_best.get(d, float("nan"))) if d in equity_best.index else None,
            "eq_best": float(eq_best.get(d, float("nan"))) if d in eq_best.index else None,
            "eq_da": float(eq_da.get(d, float("nan"))) if d in eq_da.index else None,
            "eq_rt": float(eq_rt.get(d, float("nan"))) if d in eq_rt.index else None,
            "eq_arx_levels": float(eq_levels.get(d, float("nan"))) if d in eq_levels.index else None,
            "eq_arx_spread": float(eq_spread.get(d, float("nan"))) if d in eq_spread.index else None,
            "eq_probit": float(eq_probit.get(d, float("nan"))) if d in eq_probit.index else None,
        })
    return {
        "best_config_id": best_id,
        "rows": rows,
    }


def build_decisions_json(forecasts: dict[str, pd.DataFrame], best_cfg_id: str, daily: pd.DataFrame) -> dict:
    """Per-day decisions for the calendar heatmap. Best config's Y_hat alongside realized spread."""
    # The best config id may include __mu suffix for probit; strip it to look up forecasts
    if "__mu" in best_cfg_id:
        cfg_key, mu_part = best_cfg_id.split("__mu")
        mu = float(mu_part)
        f = forecasts[cfg_key]
        y_hat = decide_from_probit(f["prob"], mu)
    else:
        cfg_key = best_cfg_id
        f = forecasts[cfg_key]
        y_hat = decide_from_spread(f["pred"])

    spread = f["spread"]
    df = pd.concat([y_hat.rename("y_hat"), spread.rename("spread")], axis=1).dropna()
    df["y_true"] = (df["spread"] > 0).astype(int)
    df["correct"] = (df["y_hat"].astype(int) == df["y_true"]).astype(int)
    rows = [
        {
            "date": pd.Timestamp(d).date().isoformat(),
            "y_hat": int(r["y_hat"]),
            "y_true": int(r["y_true"]),
            "correct": int(r["correct"]),
            "spread": round(float(r["spread"]), 4),
        }
        for d, r in df.iterrows()
    ]
    return {"best_config_id": best_cfg_id, "rows": rows}


def build_sensitivity_json(
    daily: pd.DataFrame,
    forecasts: dict[str, pd.DataFrame],
    best_cfg_id: str,
    configs: list[BacktestConfig],
) -> dict:
    """Two sweeps: probit threshold mu (for the best probit config) and
    transaction cost (for the best overall config).
    """
    oos = daily.loc[daily.index >= pd.Timestamp(OOS_START)]
    avg_da_price = float(oos["p0_mean"].mean())

    # Cost sweep on the best config (strip mu suffix if probit)
    if "__mu" in best_cfg_id:
        cfg_key, mu_part = best_cfg_id.split("__mu")
        mu_best = float(mu_part)
    else:
        cfg_key = best_cfg_id
        mu_best = None
    f = forecasts[cfg_key]

    cost_rows = []
    for c in COST_SWEEP:
        if mu_best is None:
            y_hat = decide_from_spread(f["pred"])
        else:
            y_hat = decide_from_probit(f["prob"], mu_best)
        pnl = pnl_from_decisions(y_hat, f["spread"], c)["pnl"]
        fin = financial_summary(pnl, avg_da_price=avg_da_price)
        cost_rows.append({"cost": c, **fin})

    # Threshold sweep across all probit configs
    threshold_rows = []
    for cfg in configs:
        if cfg.model != "probit":
            continue
        f = forecasts[cfg.id]
        for mu in THRESHOLD_SWEEP:
            y_hat = decide_from_probit(f["prob"], mu)
            pnl = pnl_from_decisions(y_hat, f["spread"], COST_PER_MWH)["pnl"]
            fin = financial_summary(pnl, avg_da_price=avg_da_price)
            cls = classification_stats((f["spread"] > 0).astype("Int64"), y_hat)
            threshold_rows.append({
                "config_id": cfg.id,
                "mu": mu,
                **cls,
                **fin,
            })
    return {
        "cost_sweep": cost_rows,
        "threshold_sweep": threshold_rows,
    }


def build_summary_json(best: dict, n_oos: int, daily: pd.DataFrame) -> dict:
    oos = daily.loc[daily.index >= pd.Timestamp(OOS_START)]
    return {
        "asof": datetime.now(timezone.utc).date().isoformat(),
        "best": best,
        "scope": {
            "market": f"ERCOT {HUB}",
            "window_start": START_DATE,
            "window_end": END_DATE,
            "oos_start": OOS_START,
            "n_oos_days": int(n_oos),
            "avg_da_price": round(float(oos["p0_mean"].mean()), 3),
            "avg_rt_price": round(float(oos["p1_mean"].mean()), 3),
            "avg_spread": round(float(oos["spread"].mean()), 3),
            "spread_std": round(float(oos["spread"].std()), 3),
            "spread_pos_share": round(float((oos["spread"] > 0).mean()), 4),
        },
        "paper_reference": {
            "best_polish_arx_p": 0.573,
            "best_polish_arx_profit_pln": 84191,
            "best_polish_arx_var5_pln": -815,
            "naive_balancing_polish_profit_pln": 82576,
            "note": "Maciejowska et al. (2019) Tables 3-4. Reproduced here as anchor only — markets and currency differ.",
        },
    }


def build_metadata_json(daily: pd.DataFrame, hourly: pd.DataFrame, configs: list[BacktestConfig]) -> dict:
    expected_hours = (pd.Timestamp(END_DATE) - pd.Timestamp(START_DATE)).days * 24 + 24
    return {
        "asof": datetime.now(timezone.utc).isoformat(),
        "data": {
            "n_hourly_rows": int(len(hourly)),
            "expected_hourly_rows": int(expected_hours),
            "missing_hours_pct": round(100.0 * (1 - len(hourly) / expected_hours), 3),
            "n_daily_rows": int(len(daily)),
            "first_date": pd.Timestamp(daily.index.min()).date().isoformat() if len(daily) else None,
            "last_date": pd.Timestamp(daily.index.max()).date().isoformat() if len(daily) else None,
        },
        "configs": [
            {
                "config_id": cfg.id,
                "model": cfg.model,
                "window": cfg.window,
                "x_cols": list(cfg.x_cols),
                "lag_set": list(cfg.lag_set),
            }
            for cfg in configs
        ],
        "wind_solar_caveat": (
            "EIA-930 publishes wind/solar realized net generation but no public day-ahead "
            "forecast series. We substitute lag-1 persistence (yesterday's realized) as the "
            "in-advance proxy. The demand forecast (DF) is a true day-ahead forecast and is "
            "used as-is."
        ),
    }


def export_all(
    daily: pd.DataFrame,
    hourly: pd.DataFrame,
    forecasts: dict[str, pd.DataFrame],
    configs: list[BacktestConfig],
) -> dict[str, Path]:
    paths = {name: DATA_DIR / f"{name}.json" for name in (
        "pipeline", "summary", "models", "equity", "decisions", "sensitivity", "metadata",
    )}

    pipeline_payload = build_pipeline_json()
    records, best, eq_best, eq_da, eq_rt, per_model_pnl = build_models_and_summary(
        daily, forecasts, configs
    )
    equity_payload = build_equity_json(eq_best, eq_da, eq_rt, per_model_pnl, best["config_id"], forecasts, configs)
    decisions_payload = build_decisions_json(forecasts, best["config_id"], daily)
    sensitivity_payload = build_sensitivity_json(daily, forecasts, best["config_id"], configs)
    summary_payload = build_summary_json(best, n_oos=len(eq_best), daily=daily)
    metadata_payload = build_metadata_json(daily, hourly, configs)

    _write(paths["pipeline"], pipeline_payload)
    _write(paths["summary"], summary_payload)
    _write(paths["models"], {"rows": records})
    _write(paths["equity"], equity_payload)
    _write(paths["decisions"], decisions_payload)
    _write(paths["sensitivity"], sensitivity_payload)
    _write(paths["metadata"], metadata_payload)
    return paths
