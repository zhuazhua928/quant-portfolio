"""Real-time session engine.

Maintains per-session state and drives the update cycle by reusing the
existing feature, regime, and ranking logic from monitor.watchlist.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any

import pandas as pd

from monitor.watchlist.config import WATCHLIST, BENCHMARKS, ALL_SYMBOLS
from monitor.watchlist.features import compute_all
from monitor.watchlist.features.returns import compute_returns
from monitor.watchlist.features.regime import classify_regime, RegimeResult
from monitor.watchlist.ranker import rank_watchlist, RankingResult

from ..models import (
    AlertEvent,
    RankedSymbolSnapshot,
    RegimeSnapshot,
    SessionSummary,
    WatchlistSnapshot,
)
from ..alerts import AlertManager
from ..providers import MarketDataProvider

logger = logging.getLogger(__name__)

# Scheduled snapshot minutes after open (9:30 ET)
SNAPSHOT_MINUTES = [5, 10, 15, 20, 30]


def _split_by_day(df: pd.DataFrame) -> list[pd.DataFrame]:
    if df.empty:
        return []
    return [g for _, g in df.groupby(df.index.date)]


def _regime_to_snapshot(r: RegimeResult, now: datetime) -> RegimeSnapshot:
    return RegimeSnapshot(
        timestamp=now,
        label=r.label,
        confidence=r.confidence,
        explanation=r.explanation,
        composite_score=r.details.get("composite", 0.0),
        details=r.details,
    )


def _ranked_to_snapshot(r: Any, feat: dict | None = None) -> RankedSymbolSnapshot:
    return RankedSymbolSnapshot(
        symbol=r.symbol,
        rank=r.rank,
        composite_score=r.composite_score,
        factor_scores=r.factor_scores,
        explanation=r.explanation,
        features=feat or {},
    )


class SessionEngine:
    """Drives one trading session, accepting bars incrementally."""

    def __init__(self, provider: MarketDataProvider, session_date: date | None = None) -> None:
        self.provider = provider
        self.session_date = session_date or date.today()

        # Per-symbol accumulated bars
        self._bars: dict[str, pd.DataFrame] = {s: pd.DataFrame() for s in ALL_SYMBOLS}

        # Historical volume baseline (fetched once)
        self._hist_volumes: dict[str, list[pd.DataFrame]] = {}

        # Latest outputs
        self.regime: RegimeSnapshot | None = None
        self.ranked: list[RankedSymbolSnapshot] = []
        self.top_bullish: list[RankedSymbolSnapshot] = []
        self.top_bearish: list[RankedSymbolSnapshot] = []
        self.features_by_symbol: dict[str, dict[str, Any]] = {}
        self.last_update: datetime | None = None
        self.update_count: int = 0

        # Transition tracking
        self._regime_history: list[RegimeSnapshot] = []
        self._regime_transitions: list[dict[str, Any]] = []

        # Scheduled snapshots
        self._snapshots_taken: set[int] = set()
        self._snapshots: list[WatchlistSnapshot] = []

        # Alert manager
        self.alerts = AlertManager()

        # State
        self._initialized = False

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Fetch historical volume baseline. Call once before streaming."""
        logger.info(
            "Initializing session for %s — %d symbols",
            self.session_date, len(ALL_SYMBOLS),
        )
        start = self.session_date - timedelta(days=10)
        end = self.session_date - timedelta(days=1)
        for sym in ALL_SYMBOLS:
            hist = self.provider.get_historical_bars(sym, start, end)
            if not hist.empty:
                self._hist_volumes[sym] = _split_by_day(hist)
            else:
                self._hist_volumes[sym] = []
        self._initialized = True
        logger.info("Session initialized — historical baselines loaded")

    # ------------------------------------------------------------------
    # Bar ingestion
    # ------------------------------------------------------------------

    def ingest_bar(self, symbol: str, bar: pd.Series) -> None:
        """Append a single 1-minute bar for *symbol*."""
        row = pd.DataFrame([bar], index=[bar.name] if hasattr(bar, "name") and bar.name is not None else None)
        if self._bars[symbol].empty:
            self._bars[symbol] = row
        else:
            self._bars[symbol] = pd.concat([self._bars[symbol], row])
            # Deduplicate
            self._bars[symbol] = self._bars[symbol][
                ~self._bars[symbol].index.duplicated(keep="last")
            ]

    def ingest_batch(self, symbol: str, df: pd.DataFrame) -> None:
        """Ingest a batch of bars (e.g. from replay)."""
        if self._bars[symbol].empty:
            self._bars[symbol] = df.copy()
        else:
            self._bars[symbol] = pd.concat([self._bars[symbol], df])
            self._bars[symbol] = self._bars[symbol][
                ~self._bars[symbol].index.duplicated(keep="last")
            ]

    # ------------------------------------------------------------------
    # Update cycle
    # ------------------------------------------------------------------

    def update(self, now: datetime | None = None) -> WatchlistSnapshot | None:
        """Run one full update cycle. Returns a snapshot of current state."""
        if now is None:
            now = datetime.now(timezone.utc)

        # Need at least some data
        data = {s: df for s, df in self._bars.items() if not df.empty}
        if not data:
            logger.debug("No data yet, skipping update")
            return None

        # --- Regime classification ---
        qqq_df = data.get("QQQ", pd.DataFrame())
        spy_df = data.get("SPY", pd.DataFrame())
        regime_result = classify_regime(qqq_df, spy_df)
        regime_snap = _regime_to_snapshot(regime_result, now)

        # Track regime transitions
        if self.regime and regime_snap.label != self.regime.label:
            self._regime_transitions.append({
                "from": self.regime.label,
                "to": regime_snap.label,
                "timestamp": now.isoformat(),
                "confidence": regime_snap.confidence,
            })
        self.regime = regime_snap
        self._regime_history.append(regime_snap)

        # --- Benchmark returns ---
        bench_returns: dict[str, dict[str, float | None]] = {}
        for bench in BENCHMARKS:
            if bench in data:
                bench_returns[bench] = compute_returns(data[bench]["close"])
            else:
                bench_returns[bench] = {}

        # --- Compute features per watchlist symbol ---
        results: list[dict[str, Any]] = []
        features_map: dict[str, dict[str, Any]] = {}
        for sym in WATCHLIST:
            if sym not in data:
                continue
            feat = compute_all(
                symbol=sym,
                df=data[sym],
                benchmark_returns=bench_returns,
                historical_volumes=self._hist_volumes.get(sym, []),
            )
            results.append(feat)
            features_map[sym] = feat

        self.features_by_symbol = features_map

        if not results:
            logger.debug("No watchlist data, skipping ranking")
            return None

        # --- Ranking ---
        ranking: RankingResult = rank_watchlist(regime_result, results)
        self.ranked = [_ranked_to_snapshot(r, features_map.get(r.symbol)) for r in ranking.ranked]
        self.top_bullish = [_ranked_to_snapshot(r, features_map.get(r.symbol)) for r in ranking.top_bullish]
        self.top_bearish = [_ranked_to_snapshot(r, features_map.get(r.symbol)) for r in ranking.top_bearish]

        # --- Alerts ---
        new_alerts = self.alerts.process_update(now, regime_snap, self.ranked, features_map)

        # --- Build snapshot ---
        snapshot = WatchlistSnapshot(
            timestamp=now,
            regime=regime_snap,
            ranked=self.ranked,
            top_bullish=self.top_bullish,
            top_bearish=self.top_bearish,
            alerts=new_alerts,
        )

        # Check scheduled snapshots
        self._check_scheduled_snapshot(now, snapshot)

        self.last_update = now
        self.update_count += 1

        # --- Log summary ---
        top_sym = self.ranked[0].symbol if self.ranked else "—"
        logger.info(
            "Update #%d @ %s | regime=%s (%.0f%%) | #1=%s | alerts=%d",
            self.update_count,
            now.strftime("%H:%M"),
            regime_snap.label,
            regime_snap.confidence * 100,
            top_sym,
            len(new_alerts),
        )

        return snapshot

    # ------------------------------------------------------------------
    # Scheduled snapshots
    # ------------------------------------------------------------------

    def _check_scheduled_snapshot(self, now: datetime, snapshot: WatchlistSnapshot) -> None:
        """Save snapshot at scheduled minutes after open."""
        # Convert to ET
        et_time = now.astimezone(timezone(timedelta(hours=-5)))
        minutes_since_open = (
            (et_time.hour - 9) * 60 + et_time.minute - 30
        )
        for m in SNAPSHOT_MINUTES:
            if m not in self._snapshots_taken and minutes_since_open >= m:
                self._snapshots_taken.add(m)
                self._snapshots.append(snapshot)
                provisional = " (provisional)" if m <= 15 else ""
                logger.info("SNAPSHOT @ +%dmin%s: regime=%s", m, provisional, snapshot.regime.label)

    # ------------------------------------------------------------------
    # Session summary
    # ------------------------------------------------------------------

    def get_session_summary(self) -> SessionSummary:
        alert_breakdown: dict[str, int] = {}
        for a in self.alerts.history:
            alert_breakdown[a.alert_type] = alert_breakdown.get(a.alert_type, 0) + 1

        return SessionSummary(
            session_date=str(self.session_date),
            total_updates=self.update_count,
            final_regime=self.regime,
            regime_transitions=self._regime_transitions,
            final_ranking=self.ranked,
            total_alerts=len(self.alerts.history),
            alert_breakdown=alert_breakdown,
        )

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def get_latest_snapshot(self) -> WatchlistSnapshot | None:
        if self.regime is None:
            return None
        return WatchlistSnapshot(
            timestamp=self.last_update or datetime.now(timezone.utc),
            regime=self.regime,
            ranked=self.ranked,
            top_bullish=self.top_bullish,
            top_bearish=self.top_bearish,
            alerts=self.alerts.active_alerts,
        )
