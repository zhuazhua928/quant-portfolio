"""Export a full watchlist scan to src/data/watchlist.json for the website."""

import json
import logging
import sys
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .pipeline import scan_watchlist
from .ingest import fetch_range
from .config import WATCHLIST, ALL_SYMBOLS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "src" / "data"
WEB_JSON = DATA_DIR / "watchlist.json"


# ---------------------------------------------------------------------------
# Charts: build 5-min sampled time-series per symbol
# ---------------------------------------------------------------------------

def _build_charts(bars: dict[str, pd.DataFrame]) -> dict[str, list[dict]]:
    """Build 5-min chart data for each watchlist symbol."""
    charts: dict[str, list[dict]] = {}
    for sym in WATCHLIST:
        df = bars.get(sym)
        if df is None or df.empty:
            charts[sym] = []
            continue

        # Convert to ET for display times
        df_et = df.copy()
        df_et.index = df_et.index.tz_convert("America/New_York")

        # Resample to 5-min
        ohlcv = df_et.resample("5min").agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }).dropna(subset=["close"])

        # Compute VWAP (cumulative)
        if "vwap" in df_et.columns:
            vwap_5m = df_et["vwap"].resample("5min").last().reindex(ohlcv.index)
        else:
            cum_vol = ohlcv["volume"].cumsum()
            typical = (ohlcv["high"] + ohlcv["low"] + ohlcv["close"]) / 3
            cum_tp_vol = (typical * ohlcv["volume"]).cumsum()
            vwap_5m = cum_tp_vol / cum_vol.replace(0, np.nan)

        # Rolling MAs on close
        ma5 = ohlcv["close"].rolling(5, min_periods=1).mean()
        ma20 = ohlcv["close"].rolling(20, min_periods=1).mean()

        points = []
        for ts in ohlcv.index:
            points.append({
                "t": ts.strftime("%H:%M"),
                "c": round(float(ohlcv.loc[ts, "close"]), 2),
                "v": round(float(vwap_5m.loc[ts]), 2) if pd.notna(vwap_5m.get(ts)) else None,
                "m5": round(float(ma5.loc[ts]), 2) if pd.notna(ma5.get(ts)) else None,
                "m20": round(float(ma20.loc[ts]), 2) if pd.notna(ma20.get(ts)) else None,
            })
        charts[sym] = points
    return charts


# ---------------------------------------------------------------------------
# Alerts: generate from feature dicts
# ---------------------------------------------------------------------------

def _generate_alerts(symbols: list[dict]) -> list[dict]:
    """Generate alerts matching the website's expected format."""
    alerts: list[dict] = []
    for feat in symbols:
        sym = feat["symbol"]

        # MOVE: DTD > 2%
        dtd = feat.get("ret_dtd")
        if dtd is not None and abs(dtd) > 0.02:
            direction = "up" if dtd > 0 else "down"
            alerts.append({
                "symbol": sym,
                "type": "MOVE",
                "severity": "high",
                "message": f"{sym} {direction} {abs(dtd)*100:.1f}% day-to-date",
            })

        # CROSS: golden/death
        if feat.get("golden_cross"):
            alerts.append({
                "symbol": sym,
                "type": "CROSS",
                "severity": "high",
                "message": f"{sym} golden cross (MA10 crossed above MA20)",
            })
        if feat.get("death_cross"):
            alerts.append({
                "symbol": sym,
                "type": "CROSS",
                "severity": "high",
                "message": f"{sym} death cross (MA10 crossed below MA20)",
            })

        # ORB: breakout
        orb_status = feat.get("orb_status")
        if orb_status == "above":
            alerts.append({
                "symbol": sym,
                "type": "ORB",
                "severity": "medium",
                "message": f"{sym} trading above opening range",
            })
        elif orb_status == "below":
            alerts.append({
                "symbol": sym,
                "type": "ORB",
                "severity": "medium",
                "message": f"{sym} trading below opening range",
            })

        # RSI extremes
        rsi = feat.get("rsi")
        if rsi is not None:
            if rsi > 70:
                alerts.append({
                    "symbol": sym,
                    "type": "RSI",
                    "severity": "medium",
                    "message": f"{sym} RSI {rsi:.0f} — overbought",
                })
            elif rsi < 30:
                alerts.append({
                    "symbol": sym,
                    "type": "RSI",
                    "severity": "medium",
                    "message": f"{sym} RSI {rsi:.0f} — oversold",
                })

        # VOL: high relative volume
        rvol = feat.get("rvol")
        if rvol is not None and rvol > 1.3:
            alerts.append({
                "symbol": sym,
                "type": "VOL",
                "severity": "low",
                "message": f"{sym} relative volume {rvol:.2f}x (elevated)",
            })

    # Sort: high > medium > low
    severity_order = {"high": 0, "medium": 1, "low": 2}
    alerts.sort(key=lambda a: severity_order.get(a["severity"], 3))
    return alerts


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def _serialize_ranked(ranked_list: list) -> list[dict]:
    """Convert RankedSymbol dataclass instances to JSON-friendly dicts."""
    return [
        {
            "symbol": r.symbol,
            "rank": r.rank,
            "score": r.composite_score,
            "factors": r.factor_scores,
            "explanation": r.explanation,
        }
        for r in ranked_list
    ]


def _serialize_regime(regime) -> dict[str, Any]:
    """Convert RegimeResult to JSON-friendly dict."""
    return {
        "label": regime.label,
        "confidence": regime.confidence,
        "explanation": regime.explanation,
        "details": regime.details,
    }


def _clean_for_json(obj: Any) -> Any:
    """Recursively convert numpy/pandas types to native Python."""
    if isinstance(obj, dict):
        return {k: _clean_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean_for_json(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return None if np.isnan(obj) else round(float(obj), 6)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, float) and (obj != obj):  # NaN check
        return None
    if isinstance(obj, float):
        return round(obj, 6)
    return obj


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def export_session(target_date: date, output_path: Path | None = None) -> dict | None:
    """Run pipeline for a single date and return the web data dict. Optionally write to file."""
    logger.info("Running watchlist scan for %s ...", target_date)

    output = scan_watchlist(target_date=target_date)
    regime = output["regime"]
    symbols = output["symbols"]
    ranking = output["ranking"]
    ml_regime = output.get("ml_regime")

    if not symbols:
        logger.warning("No data returned for %s", target_date)
        return None

    logger.info("Scan returned %d symbols", len(symbols))

    logger.info("Fetching raw bars for charts ...")
    bars = fetch_range(target_date, target_date, ALL_SYMBOLS)
    charts = _build_charts(bars)

    alerts = _generate_alerts(symbols)
    logger.info("Generated %d alerts", len(alerts))

    web_data = {
        "scanDate": target_date.isoformat(),
        "regime": _serialize_regime(regime),
        "mlRegime": ml_regime,
        "ranking": {
            "ranked": _serialize_ranked(ranking.ranked),
            "topBullish": _serialize_ranked(ranking.top_bullish),
            "topBearish": _serialize_ranked(ranking.top_bearish),
        },
        "symbols": symbols,
        "charts": charts,
        "alerts": alerts,
    }
    web_data = _clean_for_json(web_data)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(web_data, indent=2, default=str, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Written to %s", output_path)

    logger.info("Done! scanDate=%s, regime=%s, %d symbols, %d alerts",
                target_date, regime.label, len(symbols), len(alerts))
    return web_data


def main() -> None:
    """CLI: export one or more sessions.

    Usage:
        python -m monitor.watchlist.export_web                  # today's latest
        python -m monitor.watchlist.export_web 2026-03-12       # specific date -> watchlist.json
        python -m monitor.watchlist.export_web --batch           # scan multiple dates for session library
    """
    if len(sys.argv) > 1 and sys.argv[1] == "--batch":
        # Batch mode: scan multiple recent trading days
        from datetime import timedelta
        sessions_dir = DATA_DIR / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)

        # Scan last ~15 trading days (go back 22 calendar days to cover weekends)
        today = date(2026, 3, 12)
        candidates = []
        d = today
        for _ in range(22):
            if d.weekday() < 5:  # weekdays only
                candidates.append(d)
            d -= timedelta(days=1)

        results = []
        for d in sorted(candidates):
            out_path = sessions_dir / f"{d.isoformat()}.json"
            if out_path.exists():
                logger.info("Skipping %s (already exists)", d)
                # Load existing
                existing = json.loads(out_path.read_text(encoding="utf-8"))
                results.append({"date": d.isoformat(), "regime": existing["regime"]["label"]})
                continue
            data = export_session(d, output_path=out_path)
            if data:
                results.append({"date": d.isoformat(), "regime": data["regime"]["label"]})

        print("\n=== Session Summary ===")
        for r in results:
            print(f"  {r['date']}  {r['regime']}")
    else:
        target = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
        export_session(target, output_path=WEB_JSON)


if __name__ == "__main__":
    main()
