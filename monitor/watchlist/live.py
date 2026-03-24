"""Live intraday terminal monitor.

Usage:
    python -m monitor.watchlist.live              # scan every 15 min, 9:45–16:05 ET
    python -m monitor.watchlist.live --interval 30
    python -m monitor.watchlist.live --now        # one scan right now (ignore market hours)
"""

from __future__ import annotations

import argparse
import time
from datetime import datetime, timedelta

from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

# ── market-hours constants ──────────────────────────────────────────────
MARKET_OPEN = (9, 30)
FIRST_SCAN = (9, 45)
MARKET_CLOSE = (16, 5)

# ── display helpers ─────────────────────────────────────────────────────

_SEV_TAG = {"high": "[HIGH]", "medium": "[MED] ", "low": "[LOW] "}
_W = 55  # dashboard width


def _hdr(now_et: datetime, next_et: datetime | None) -> str:
    next_str = next_et.strftime("%H:%M") if next_et else "—"
    return (
        f"{'═' * _W}\n"
        f"  LIVE SCAN — {now_et.strftime('%Y-%m-%d %H:%M')} ET"
        f"  |  Next: {next_str}\n"
        f"{'═' * _W}"
    )


def _regime_block(regime) -> str:  # RegimeResult
    label = regime.label.upper()
    conf = regime.confidence * 100
    lines = [f"  REGIME: {label} ({conf:.0f}% confidence)"]
    lines.append(f"  {regime.explanation}")
    return "\n".join(lines)


def _ranking_block(ranking) -> str:  # RankingResult
    lines = ["  RANKING"]
    for rs in ranking.ranked:
        # find matching feature dict later; use what RankedSymbol has
        scores = rs.factor_scores
        lines.append(
            f"  #{rs.rank:<3} {rs.symbol:<6} Score {rs.composite_score:+.2f}  "
            f"{rs.explanation}"
        )
    return "\n".join(lines)


def _ranking_detail_block(ranking, symbols: list[dict]) -> str:
    feat_map = {f["symbol"]: f for f in symbols}
    lines = ["  RANKING"]
    for rs in ranking.ranked:
        f = feat_map.get(rs.symbol, {})
        price = f.get("last_price")
        dtd = f.get("ret_dtd")
        xs = f.get("ret_dtd_xs_qqq")
        rsi = f.get("rsi")
        rvol = f.get("rvol")
        parts = [f"  #{rs.rank:<2} {rs.symbol:<6}"]
        if price is not None:
            parts.append(f"${price:<9.2f}")
        if dtd is not None:
            parts.append(f"DTD {dtd*100:+.1f}%")
        if xs is not None:
            parts.append(f"xs QQQ {xs*100:+.1f}%")
        if rsi is not None:
            parts.append(f"RSI {rsi:.0f}")
        if rvol is not None:
            parts.append(f"RVOL {rvol:.1f}x")
        parts.append(f"Score {rs.composite_score:+.2f}")
        lines.append("  ".join(parts))
    return "\n".join(lines)


def _top_block(ranking) -> str:
    bull = ", ".join(rs.symbol for rs in ranking.top_bullish)
    bear = ", ".join(rs.symbol for rs in ranking.top_bearish)
    return f"  TOP BULLISH: {bull}\n  TOP BEARISH: {bear}"


def _alerts_block(alerts: list[dict]) -> str:
    if not alerts:
        return "  ALERTS: none"
    lines = [f"  ALERTS ({len(alerts)})"]
    for a in alerts:
        tag = _SEV_TAG.get(a["severity"], "[???]")
        lines.append(f"  {tag} {a['symbol']:<6} {a['type']:<6} {a['message']}")
    return "\n".join(lines)


def _generate_alerts(symbols: list[dict]) -> list[dict]:
    """Self-contained alert generation (mirrors export_web logic)."""
    alerts: list[dict] = []
    for feat in symbols:
        sym = feat["symbol"]
        # MOVE
        dtd = feat.get("ret_dtd")
        if dtd is not None and abs(dtd) > 0.02:
            direction = "up" if dtd > 0 else "down"
            alerts.append({"symbol": sym, "type": "MOVE", "severity": "high",
                           "message": f"{direction} {abs(dtd)*100:.1f}% DTD"})
        # CROSS
        if feat.get("golden_cross"):
            alerts.append({"symbol": sym, "type": "CROSS", "severity": "high",
                           "message": "Golden cross MA10/MA20"})
        if feat.get("death_cross"):
            alerts.append({"symbol": sym, "type": "CROSS", "severity": "high",
                           "message": "Death cross MA10/MA20"})
        # ORB
        orb = feat.get("orb_status")
        if orb == "above":
            alerts.append({"symbol": sym, "type": "ORB", "severity": "medium",
                           "message": "Above opening range"})
        elif orb == "below":
            alerts.append({"symbol": sym, "type": "ORB", "severity": "medium",
                           "message": "Below opening range"})
        # RSI
        rsi = feat.get("rsi")
        if rsi is not None:
            if rsi > 70:
                alerts.append({"symbol": sym, "type": "RSI", "severity": "medium",
                               "message": f"RSI {rsi:.0f} — overbought"})
            elif rsi < 30:
                alerts.append({"symbol": sym, "type": "RSI", "severity": "medium",
                               "message": f"RSI {rsi:.0f} — oversold"})
        # VOL
        rvol = feat.get("rvol")
        if rvol is not None and rvol > 1.3:
            alerts.append({"symbol": sym, "type": "VOL", "severity": "low",
                           "message": f"Relative volume {rvol:.2f}x"})
    severity_order = {"high": 0, "medium": 1, "low": 2}
    alerts.sort(key=lambda a: severity_order.get(a["severity"], 3))
    return alerts


# ── core scan + print ───────────────────────────────────────────────────

def run_scan(now_et: datetime, next_et: datetime | None) -> None:
    """Execute one scan cycle and print the dashboard."""
    from monitor.watchlist.pipeline import scan_watchlist

    print(f"\n⏳ Scanning…", flush=True)
    try:
        result = scan_watchlist(target_date=now_et.date())
    except Exception as exc:
        print(f"\n❌ Scan failed: {exc}")
        return

    regime = result["regime"]
    symbols = result["symbols"]
    ranking = result["ranking"]
    alerts = _generate_alerts(symbols)

    sep = f"{'─' * _W}"
    print()
    print(_hdr(now_et, next_et))
    print(_regime_block(regime))
    print(sep)
    print(_ranking_detail_block(ranking, symbols))
    print(sep)
    print(_top_block(ranking))
    print(sep)
    print(_alerts_block(alerts))
    print(f"{'═' * _W}")
    print(flush=True)


# ── scheduling loop ─────────────────────────────────────────────────────

def _next_scan_time(now: datetime, interval: int) -> datetime | None:
    """Return next scan datetime in ET, or None if past market close."""
    close = now.replace(hour=MARKET_CLOSE[0], minute=MARKET_CLOSE[1], second=0, microsecond=0)
    candidate = now + timedelta(minutes=interval)
    if candidate > close:
        return None
    return candidate


def main() -> None:
    parser = argparse.ArgumentParser(description="Live intraday terminal monitor")
    parser.add_argument("--interval", type=int, default=15, help="Minutes between scans (default 15)")
    parser.add_argument("--now", action="store_true", help="Run one scan immediately and exit")
    args = parser.parse_args()

    if args.now:
        now_et = datetime.now(ET)
        run_scan(now_et, None)
        return

    # Loop mode
    now_et = datetime.now(ET)
    first = now_et.replace(hour=FIRST_SCAN[0], minute=FIRST_SCAN[1], second=0, microsecond=0)
    close = now_et.replace(hour=MARKET_CLOSE[0], minute=MARKET_CLOSE[1], second=0, microsecond=0)

    if now_et > close:
        print(f"Market closed (after {MARKET_CLOSE[0]}:{MARKET_CLOSE[1]:02d} ET). Use --now to force a scan.")
        return

    # Wait until first scan time if we're early
    if now_et < first:
        wait = (first - now_et).total_seconds()
        print(f"Waiting until {first.strftime('%H:%M')} ET for first scan ({wait/60:.0f} min)…")
        time.sleep(wait)

    while True:
        now_et = datetime.now(ET)
        if now_et > close:
            print("\nMarket closed. Exiting.")
            break
        next_et = _next_scan_time(now_et, args.interval)
        run_scan(now_et, next_et)
        if next_et is None:
            print("\nNo more scans today. Exiting.")
            break
        wait = (next_et - datetime.now(ET)).total_seconds()
        if wait > 0:
            print(f"💤 Next scan at {next_et.strftime('%H:%M')} ET ({wait/60:.0f} min)")
            time.sleep(wait)


if __name__ == "__main__":
    main()
