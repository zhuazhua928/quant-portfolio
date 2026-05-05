#!/usr/bin/env python3
"""Minimal example: run a full replay session with synthetic data.

Usage:
    python -m monitor.watchlist.rt.run_replay [--bars N] [--update-every M]

This exercises the entire real-time pipeline — regime classification,
feature computation, ranking, and alert generation — using the
MockProvider so no live API connection is needed.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date

from monitor.watchlist.rt.models import WatchlistSnapshot
from monitor.watchlist.rt.providers.mock import MockProvider
from monitor.watchlist.rt.replay import ReplayRunner


def _on_snapshot(snap: WatchlistSnapshot) -> None:
    """Pretty-print each snapshot as it arrives."""
    regime = snap.regime
    top3 = snap.ranked[:3]
    alerts = snap.alerts

    print(f"\n{'─' * 70}")
    print(
        f"  {snap.timestamp.strftime('%H:%M')}  │  "
        f"Regime: {regime.label.upper()} ({regime.confidence:.0%})  │  "
        f"Score: {regime.composite_score:+.3f}"
    )
    print(f"{'─' * 70}")

    if top3:
        print("  Top ranked:")
        for r in top3:
            print(f"    #{r.rank} {r.symbol:<6s}  score={r.composite_score:+.3f}  {r.explanation}")

    if snap.top_bullish:
        bulls = ", ".join(f"{r.symbol}({r.composite_score:+.3f})" for r in snap.top_bullish[:3])
        print(f"  Bullish picks: {bulls}")

    if snap.top_bearish:
        bears = ", ".join(f"{r.symbol}({r.composite_score:+.3f})" for r in snap.top_bearish[:3])
        print(f"  Bearish picks: {bears}")

    if alerts:
        print(f"  Alerts ({len(alerts)}):")
        for a in alerts:
            icon = {"high": "!!", "medium": "! ", "low": ". "}.get(a.severity, "  ")
            print(f"    {icon} [{a.alert_type}] {a.message}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a replay session with mock data")
    parser.add_argument("--bars", type=int, default=60, help="Max bars per symbol (default 60 = first hour)")
    parser.add_argument("--update-every", type=int, default=5, help="Update engine every N bars (default 5)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--json", action="store_true", help="Output final summary as JSON")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(name)-30s %(levelname)-5s %(message)s",
        datefmt="%H:%M:%S",
    )

    session_date = date(2025, 3, 10)  # fixed date for reproducibility

    print(f"\n{'═' * 70}")
    print(f"  REPLAY SESSION — {session_date}  (seed={args.seed})")
    print(f"  Bars: {args.bars} per symbol  |  Update every: {args.update_every} min")
    print(f"{'═' * 70}")

    provider = MockProvider(session_date=session_date, seed=args.seed)
    runner = ReplayRunner(
        provider=provider,
        session_date=session_date,
        update_every=args.update_every,
        on_snapshot=_on_snapshot,
    )

    summary = runner.run(max_bars=args.bars)

    # End-of-session report
    print(f"\n{'═' * 70}")
    print("  SESSION SUMMARY")
    print(f"{'═' * 70}")
    print(f"  Date:             {summary.session_date}")
    print(f"  Total updates:    {summary.total_updates}")
    print(f"  Total alerts:     {summary.total_alerts}")
    if summary.final_regime:
        print(f"  Final regime:     {summary.final_regime.label} ({summary.final_regime.confidence:.0%})")
    if summary.regime_transitions:
        print(f"  Regime shifts:    {len(summary.regime_transitions)}")
        for t in summary.regime_transitions:
            print(f"    {t['timestamp']}: {t['from']} → {t['to']} (conf={t['confidence']:.0%})")
    if summary.alert_breakdown:
        print("  Alert breakdown:")
        for atype, count in sorted(summary.alert_breakdown.items(), key=lambda x: -x[1]):
            print(f"    {atype}: {count}")
    if summary.final_ranking:
        print("  Final ranking:")
        for r in summary.final_ranking[:6]:
            print(f"    #{r.rank} {r.symbol:<6s}  score={r.composite_score:+.3f}")

    if args.json:
        print(f"\n{'─' * 70}")
        print(json.dumps(summary.to_dict(), indent=2, default=str))

    print()


if __name__ == "__main__":
    main()
