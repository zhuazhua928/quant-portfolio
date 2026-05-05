"""Structured output models for the real-time engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


# ---------------------------------------------------------------------------
# Alert
# ---------------------------------------------------------------------------

@dataclass
class AlertEvent:
    timestamp: datetime
    symbol: str
    alert_type: str
    severity: str  # "high" | "medium" | "low"
    message: str
    status: str = "new"  # "new" | "updated" | "resolved"
    id: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            self.id = f"{self.alert_type}:{self.symbol}:{self.timestamp.isoformat()}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "message": self.message,
            "status": self.status,
        }


# ---------------------------------------------------------------------------
# Regime snapshot
# ---------------------------------------------------------------------------

@dataclass
class RegimeSnapshot:
    timestamp: datetime
    label: str  # "bullish" | "bearish" | "mixed"
    confidence: float
    explanation: str
    composite_score: float
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "label": self.label,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "composite_score": self.composite_score,
            "details": self.details,
        }


# ---------------------------------------------------------------------------
# Ranked symbol / watchlist snapshot
# ---------------------------------------------------------------------------

@dataclass
class RankedSymbolSnapshot:
    symbol: str
    rank: int
    composite_score: float
    factor_scores: dict[str, float]
    explanation: str
    features: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "rank": self.rank,
            "composite_score": self.composite_score,
            "factor_scores": self.factor_scores,
            "explanation": self.explanation,
            "features": self.features,
        }


@dataclass
class WatchlistSnapshot:
    timestamp: datetime
    regime: RegimeSnapshot
    ranked: list[RankedSymbolSnapshot]
    top_bullish: list[RankedSymbolSnapshot]
    top_bearish: list[RankedSymbolSnapshot]
    alerts: list[AlertEvent]

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "regime": self.regime.to_dict(),
            "ranked": [r.to_dict() for r in self.ranked],
            "top_bullish": [r.to_dict() for r in self.top_bullish],
            "top_bearish": [r.to_dict() for r in self.top_bearish],
            "alerts": [a.to_dict() for a in self.alerts],
        }


# ---------------------------------------------------------------------------
# Session summary (end of day)
# ---------------------------------------------------------------------------

@dataclass
class SessionSummary:
    session_date: str
    total_updates: int
    final_regime: RegimeSnapshot | None
    regime_transitions: list[dict[str, Any]]
    final_ranking: list[RankedSymbolSnapshot]
    total_alerts: int
    alert_breakdown: dict[str, int]  # alert_type -> count

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_date": self.session_date,
            "total_updates": self.total_updates,
            "final_regime": self.final_regime.to_dict() if self.final_regime else None,
            "regime_transitions": self.regime_transitions,
            "final_ranking": [r.to_dict() for r in self.final_ranking],
            "total_alerts": self.total_alerts,
            "alert_breakdown": self.alert_breakdown,
        }
