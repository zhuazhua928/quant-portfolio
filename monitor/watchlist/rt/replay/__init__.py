"""Replay runner — simulate a real-time session from historical bars.

Feeds bars minute-by-minute through the same SessionEngine used in live
mode, producing identical outputs.  Useful for testing, debugging regime
transitions, and validating alert logic without a live market connection.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable

import pandas as pd

from monitor.watchlist.config import ALL_SYMBOLS
from ..engine import SessionEngine
from ..models import WatchlistSnapshot, SessionSummary
from ..providers import MarketDataProvider

logger = logging.getLogger(__name__)


class ReplayRunner:
    """Drives a SessionEngine using pre-generated or historical bars.

    Parameters
    ----------
    provider : MarketDataProvider
        Data source (typically MockProvider or a historical-file provider).
    session_date : date | None
        The date to simulate.  Defaults to today.
    update_every : int
        Run the engine update cycle every *update_every* bars (minutes).
        Default ``5`` means one update every 5 minutes of simulated time.
    on_snapshot : callable | None
        Optional callback invoked with each ``WatchlistSnapshot`` produced
        by the engine.  Useful for logging, persistence, or streaming to a
        UI.
    """

    def __init__(
        self,
        provider: MarketDataProvider,
        session_date: date | None = None,
        update_every: int = 5,
        on_snapshot: Callable[[WatchlistSnapshot], Any] | None = None,
    ) -> None:
        self.provider = provider
        self.session_date = session_date or date.today()
        self.update_every = max(1, update_every)
        self.on_snapshot = on_snapshot

        self.engine = SessionEngine(provider, self.session_date)
        self.snapshots: list[WatchlistSnapshot] = []

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def run(self, max_bars: int | None = None, symbols: list[str] | None = None) -> SessionSummary:
        """Execute the full replay session.

        Parameters
        ----------
        max_bars : int | None
            Stop after this many bars per symbol.  ``None`` means replay
            the entire session (390 bars for a full day).
        symbols : list[str] | None
            Symbols to stream.  Defaults to ``ALL_SYMBOLS``.

        Returns
        -------
        SessionSummary
            End-of-session summary with regime history, rankings, and
            alert breakdown.
        """
        symbols = symbols or list(ALL_SYMBOLS)

        # Initialize historical baselines
        logger.info("=== Replay session: %s ===", self.session_date)
        self.engine.initialize()

        bar_count = 0
        bars_since_update = 0

        for sym, bar in self.provider.stream_bars(symbols):
            self.engine.ingest_bar(sym, bar)
            bar_count += 1
            bars_since_update += 1

            # After ingesting a full round of symbols, maybe run an update
            if bars_since_update >= len(symbols) * self.update_every:
                bars_since_update = 0
                now = _bar_timestamp(bar)
                snapshot = self.engine.update(now)
                if snapshot is not None:
                    self.snapshots.append(snapshot)
                    if self.on_snapshot:
                        self.on_snapshot(snapshot)

            if max_bars is not None and bar_count >= max_bars * len(symbols):
                logger.info("Reached max_bars=%d, stopping replay", max_bars)
                break

        # Final update to capture end-of-session state
        final = self.engine.update()
        if final is not None:
            self.snapshots.append(final)
            if self.on_snapshot:
                self.on_snapshot(final)

        summary = self.engine.get_session_summary()
        logger.info(
            "=== Replay complete: %d updates, %d alerts, final regime=%s ===",
            summary.total_updates,
            summary.total_alerts,
            summary.final_regime.label if summary.final_regime else "N/A",
        )
        return summary


def _bar_timestamp(bar: pd.Series) -> datetime:
    """Extract a UTC-aware timestamp from a bar Series."""
    if hasattr(bar, "name") and bar.name is not None:
        ts = pd.Timestamp(bar.name)
        if ts.tzinfo is None:
            return ts.to_pydatetime().replace(tzinfo=timezone.utc)
        return ts.to_pydatetime()
    return datetime.now(timezone.utc)
