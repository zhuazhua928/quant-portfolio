"""Real-time alert generation with transition detection.

Extends the existing alert logic with stream-friendly features:
stateful tracking, transition detection, and alert lifecycle management.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from ..models import AlertEvent, RegimeSnapshot, RankedSymbolSnapshot

logger = logging.getLogger(__name__)


class AlertManager:
    """Generates and manages the lifecycle of real-time alerts."""

    def __init__(self) -> None:
        self._active: dict[str, AlertEvent] = {}  # id -> alert
        self._history: list[AlertEvent] = []
        self._prev_regime: RegimeSnapshot | None = None
        self._prev_ranked: dict[str, RankedSymbolSnapshot] = {}  # symbol -> snapshot
        self._prev_features: dict[str, dict[str, Any]] = {}

    @property
    def active_alerts(self) -> list[AlertEvent]:
        return list(self._active.values())

    @property
    def history(self) -> list[AlertEvent]:
        return list(self._history)

    def _emit(self, alert: AlertEvent) -> AlertEvent:
        """Register an alert, deduplicating by type+symbol."""
        key = f"{alert.alert_type}:{alert.symbol}"
        existing = self._active.get(key)
        if existing and existing.status == "new":
            alert.status = "updated"
        self._active[key] = alert
        self._history.append(alert)
        logger.info("ALERT [%s] %s: %s", alert.severity.upper(), alert.symbol, alert.message)
        return alert

    def _resolve(self, key: str, now: datetime) -> None:
        if key in self._active:
            old = self._active.pop(key)
            resolved = AlertEvent(
                timestamp=now,
                symbol=old.symbol,
                alert_type=old.alert_type,
                severity=old.severity,
                message=f"Resolved: {old.message}",
                status="resolved",
            )
            self._history.append(resolved)

    def process_update(
        self,
        now: datetime,
        regime: RegimeSnapshot,
        ranked: list[RankedSymbolSnapshot],
        features_by_sym: dict[str, dict[str, Any]],
    ) -> list[AlertEvent]:
        """Process one update cycle. Returns new/updated alerts."""
        new_alerts: list[AlertEvent] = []

        # --- Regime transition ---
        new_alerts.extend(self._check_regime_transition(now, regime))

        # --- Per-symbol alerts ---
        ranked_map = {r.symbol: r for r in ranked}
        for sym, feat in features_by_sym.items():
            new_alerts.extend(self._check_symbol_alerts(now, sym, feat, ranked_map.get(sym)))
            new_alerts.extend(self._check_transitions(now, sym, feat, ranked_map.get(sym)))

        # Update previous state
        self._prev_regime = regime
        self._prev_ranked = ranked_map
        self._prev_features = dict(features_by_sym)

        return new_alerts

    # ---------------------------------------------------------------
    # Regime alerts
    # ---------------------------------------------------------------

    def _check_regime_transition(
        self, now: datetime, regime: RegimeSnapshot
    ) -> list[AlertEvent]:
        alerts = []
        if self._prev_regime is None:
            return alerts
        if regime.label != self._prev_regime.label:
            alerts.append(self._emit(AlertEvent(
                timestamp=now,
                symbol="MARKET",
                alert_type="regime_shift",
                severity="high",
                message=(
                    f"Regime shifted from {self._prev_regime.label} to {regime.label} "
                    f"(confidence {regime.confidence:.0%})"
                ),
            )))
        return alerts

    # ---------------------------------------------------------------
    # Per-symbol alerts (extends existing logic)
    # ---------------------------------------------------------------

    def _check_symbol_alerts(
        self, now: datetime, sym: str, feat: dict, ranked: RankedSymbolSnapshot | None
    ) -> list[AlertEvent]:
        alerts = []

        # Large move
        dtd = feat.get("ret_dtd")
        if dtd is not None and abs(dtd) > 0.02:
            direction = "up" if dtd > 0 else "down"
            alerts.append(self._emit(AlertEvent(
                timestamp=now, symbol=sym, alert_type="large_move", severity="high",
                message=f"{sym} large move {direction} ({dtd*100:+.1f}% DTD)",
            )))

        # ORB breakout
        orb = feat.get("orb_status")
        if orb == "above":
            alerts.append(self._emit(AlertEvent(
                timestamp=now, symbol=sym, alert_type="orb_breakout", severity="medium",
                message=f"{sym} broke above opening range",
            )))
        elif orb == "below":
            alerts.append(self._emit(AlertEvent(
                timestamp=now, symbol=sym, alert_type="orb_breakdown", severity="medium",
                message=f"{sym} broke below opening range",
            )))

        # Golden / death cross
        if feat.get("golden_cross"):
            alerts.append(self._emit(AlertEvent(
                timestamp=now, symbol=sym, alert_type="golden_cross", severity="high",
                message=f"{sym} golden cross (MA10 crossed above MA20)",
            )))
        if feat.get("death_cross"):
            alerts.append(self._emit(AlertEvent(
                timestamp=now, symbol=sym, alert_type="death_cross", severity="high",
                message=f"{sym} death cross (MA10 crossed below MA20)",
            )))

        # Extreme RSI
        rsi = feat.get("rsi")
        if rsi is not None:
            if rsi > 70:
                alerts.append(self._emit(AlertEvent(
                    timestamp=now, symbol=sym, alert_type="rsi_overbought", severity="medium",
                    message=f"{sym} RSI overbought ({rsi:.0f})",
                )))
            elif rsi < 30:
                alerts.append(self._emit(AlertEvent(
                    timestamp=now, symbol=sym, alert_type="rsi_oversold", severity="medium",
                    message=f"{sym} RSI oversold ({rsi:.0f})",
                )))

        # Elevated volume
        rvol = feat.get("rvol")
        if rvol is not None and rvol > 1.3:
            alerts.append(self._emit(AlertEvent(
                timestamp=now, symbol=sym, alert_type="high_volume", severity="low",
                message=f"{sym} elevated volume ({rvol:.1f}x average)",
            )))

        return alerts

    # ---------------------------------------------------------------
    # Transition alerts (strong→weak, weak→strong, etc.)
    # ---------------------------------------------------------------

    def _check_transitions(
        self, now: datetime, sym: str, feat: dict, ranked: RankedSymbolSnapshot | None
    ) -> list[AlertEvent]:
        alerts = []
        prev_feat = self._prev_features.get(sym)
        prev_rank = self._prev_ranked.get(sym)
        if prev_feat is None or prev_rank is None or ranked is None:
            return alerts

        prev_score = prev_rank.composite_score
        curr_score = ranked.composite_score
        score_delta = curr_score - prev_score

        # Strong getting stronger
        if prev_score > 0.3 and score_delta > 0.05:
            alerts.append(self._emit(AlertEvent(
                timestamp=now, symbol=sym, alert_type="strengthening", severity="medium",
                message=f"{sym} strong and getting stronger (score {prev_score:+.3f} -> {curr_score:+.3f})",
            )))

        # Weak getting weaker
        elif prev_score < -0.2 and score_delta < -0.05:
            alerts.append(self._emit(AlertEvent(
                timestamp=now, symbol=sym, alert_type="weakening", severity="medium",
                message=f"{sym} weak and getting weaker (score {prev_score:+.3f} -> {curr_score:+.3f})",
            )))

        # Strong to weak transition
        elif prev_score > 0.2 and curr_score < -0.1:
            alerts.append(self._emit(AlertEvent(
                timestamp=now, symbol=sym, alert_type="strong_to_weak", severity="high",
                message=f"{sym} transitioned from strong to weak (score {prev_score:+.3f} -> {curr_score:+.3f})",
            )))

        # Weak to strong transition
        elif prev_score < -0.1 and curr_score > 0.2:
            alerts.append(self._emit(AlertEvent(
                timestamp=now, symbol=sym, alert_type="weak_to_strong", severity="high",
                message=f"{sym} transitioned from weak to strong (score {prev_score:+.3f} -> {curr_score:+.3f})",
            )))

        # Pullback in bullish regime
        if self._prev_regime and self._prev_regime.label == "bullish":
            prev_rsi = prev_feat.get("rsi")
            curr_rsi = feat.get("rsi")
            if prev_rsi and curr_rsi and prev_rsi > 55 and curr_rsi < 45 and curr_score > 0:
                alerts.append(self._emit(AlertEvent(
                    timestamp=now, symbol=sym, alert_type="bullish_pullback", severity="medium",
                    message=f"{sym} quality pullback in bullish regime (RSI {prev_rsi:.0f} -> {curr_rsi:.0f}, score still positive)",
                )))

        # Failed rebound in bearish regime
        if self._prev_regime and self._prev_regime.label == "bearish":
            prev_rsi = prev_feat.get("rsi")
            curr_rsi = feat.get("rsi")
            if prev_rsi and curr_rsi and prev_rsi < 45 and curr_rsi > 55 and curr_score < 0:
                alerts.append(self._emit(AlertEvent(
                    timestamp=now, symbol=sym, alert_type="failed_rebound", severity="medium",
                    message=f"{sym} failed rebound in bearish regime (RSI {prev_rsi:.0f} -> {curr_rsi:.0f}, score still negative)",
                )))

        # Benchmark divergence
        xs_qqq = feat.get("ret_dtd_xs_qqq")
        prev_xs_qqq = prev_feat.get("ret_dtd_xs_qqq")
        if xs_qqq is not None and prev_xs_qqq is not None:
            if abs(xs_qqq) > 0.02 and abs(prev_xs_qqq) < 0.01:
                direction = "outperforming" if xs_qqq > 0 else "underperforming"
                alerts.append(self._emit(AlertEvent(
                    timestamp=now, symbol=sym, alert_type="benchmark_divergence", severity="medium",
                    message=f"{sym} diverging from QQQ ({direction}, excess {xs_qqq*100:+.1f}%)",
                )))

        return alerts
