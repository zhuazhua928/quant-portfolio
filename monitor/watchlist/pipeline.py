"""Orchestrate ingestion and feature computation for the full universe."""

import logging
from datetime import date

import pandas as pd

from .config import WATCHLIST, BENCHMARKS, ALL_SYMBOLS
from .features import compute_all
from .features.returns import compute_returns
from .features.regime import classify_regime, RegimeResult
from .ingest import fetch_today, fetch_range, fetch_recent_days
from .ranker import rank_watchlist, RankingResult

logger = logging.getLogger(__name__)


def _maybe_run_hmm_overlay(data: dict) -> dict | None:
    """Best-effort HMM regime overlay. Returns None if the bundle is missing
    or feature computation fails (e.g., insufficient bar history).

    The overlay is cadence-aware: it only re-predicts when the latest 5-min
    window-end timestamp advances. Calling it on every 60s scheduler tick
    is therefore safe and cheap.
    """
    try:
        from .regime_overlay import get_overlay, serialize_result
    except Exception as exc:
        logger.debug("HMM overlay unavailable: %s", exc)
        return None

    spy_df = data.get("SPY", pd.DataFrame())
    qqq_df = data.get("QQQ", pd.DataFrame())
    if spy_df.empty:
        logger.info("HMM overlay: SPY bars missing, skipping")
        return None

    try:
        overlay = get_overlay()
    except FileNotFoundError as exc:
        logger.info("HMM overlay: %s", exc)
        return None

    out: dict = {"market": None, "per_symbol": {}}
    try:
        if not qqq_df.empty:
            mr = overlay.classify_market(qqq_df, spy_df)
            out["market"] = serialize_result(mr)

        for sym in WATCHLIST:
            sdf = data.get(sym)
            if sdf is None or sdf.empty:
                continue
            sr = overlay.classify_symbol(sym, sdf, spy_df)
            out["per_symbol"][sym] = serialize_result(sr)

        # attach training metadata so the dashboard can show recency
        meta = overlay.meta
        out["trained_at"] = meta.get("trained_at")
        out["n_components"] = meta.get("n_components")
        return out
    except Exception as exc:
        logger.warning("HMM overlay failed: %s", exc)
        return None


def _split_by_day(df: pd.DataFrame) -> list[pd.DataFrame]:
    """Split a multi-day DataFrame into per-day frames."""
    if df.empty:
        return []
    groups = df.groupby(df.index.date)
    return [g for _, g in groups]


def scan_watchlist(
    target_date: date | None = None,
) -> dict:
    """Run one full scan: ingest bars, compute features + regime, return results.

    If *target_date* is None, fetches today's data.

    Returns::

        {
            "regime": RegimeResult,
            "symbols": [dict, ...],  # per-symbol feature dicts
        }
    """
    # --- ingest ----------------------------------------------------------
    if target_date is None:
        data = fetch_today(ALL_SYMBOLS)
    else:
        data = fetch_range(target_date, target_date, ALL_SYMBOLS)

    if not data:
        logger.warning("No data returned for any symbol")
        return {"regime": None, "symbols": [], "ranking": None, "ml_regime": None}

    # --- market regime ---------------------------------------------------
    qqq_df = data.get("QQQ", pd.DataFrame())
    spy_df = data.get("SPY", pd.DataFrame())
    regime = classify_regime(qqq_df, spy_df)
    logger.info("Regime: %s (confidence %.2f)", regime.label, regime.confidence)

    # --- historical volume baseline --------------------------------------
    hist_raw = fetch_recent_days(n_days=5, symbols=ALL_SYMBOLS)
    hist_by_sym: dict[str, list[pd.DataFrame]] = {}
    for sym, hdf in hist_raw.items():
        hist_by_sym[sym] = _split_by_day(hdf)

    # --- benchmark returns -----------------------------------------------
    bench_returns: dict[str, dict[str, float | None]] = {}
    for bench in BENCHMARKS:
        if bench in data:
            bench_returns[bench] = compute_returns(data[bench]["close"])
        else:
            bench_returns[bench] = {}

    # --- compute features per watchlist symbol ---------------------------
    results = []
    for sym in WATCHLIST:
        if sym not in data:
            logger.info("%s: no data, skipping", sym)
            continue
        feat = compute_all(
            symbol=sym,
            df=data[sym],
            benchmark_returns=bench_returns,
            historical_volumes=hist_by_sym.get(sym, []),
        )
        results.append(feat)

    # --- ranking ---------------------------------------------------------
    ranking = rank_watchlist(regime, results)

    # --- ML regime overlay (best-effort; runs on 5-min cadence) ----------
    ml_regime = _maybe_run_hmm_overlay(data)
    if ml_regime is not None:
        market = ml_regime.get("market") or {}
        logger.info(
            "ML regime: market=%s (label %s)",
            market.get("label_name"),
            market.get("label"),
        )

    symbols_done = [r["symbol"] for r in results]
    logger.info("Scan complete: %d symbols — %s", len(results), ", ".join(symbols_done))
    return {
        "regime": regime,
        "symbols": results,
        "ranking": ranking,
        "ml_regime": ml_regime,
    }


def scan_to_dataframe(target_date: date | None = None) -> tuple[RegimeResult | None, pd.DataFrame]:
    """Convenience: run scan and return (regime, DataFrame)."""
    output = scan_watchlist(target_date)
    symbols = output["symbols"]
    if not symbols:
        return output["regime"], pd.DataFrame()
    return output["regime"], pd.DataFrame(symbols).set_index("symbol")
