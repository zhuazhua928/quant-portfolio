"""Regime-aware watchlist ranking engine.

Scores each watchlist symbol across multiple factors, then ranks them
according to the current market regime:

- bullish  → rank by strength and trend quality (buy the leaders)
- bearish  → rank by weakness and trend quality (short the laggards)
- mixed    → rank by stability and breakout potential
"""

from dataclasses import dataclass, field
from typing import Any

from .features.regime import RegimeResult


# ---------------------------------------------------------------------------
# Output types
# ---------------------------------------------------------------------------

@dataclass
class RankedSymbol:
    symbol: str
    rank: int
    composite_score: float
    factor_scores: dict[str, float]
    explanation: str


@dataclass
class RankingResult:
    regime: RegimeResult
    ranked: list[RankedSymbol]
    top_bullish: list[RankedSymbol]
    top_bearish: list[RankedSymbol]

    def summary(self) -> str:
        lines = [
            f"Regime: {self.regime.label} ({self.regime.confidence:.0%})",
            "",
            "Full ranking:",
        ]
        for r in self.ranked:
            lines.append(f"  #{r.rank} {r.symbol:5s}  score={r.composite_score:+.3f}  {r.explanation}")

        lines.append("")
        lines.append("Top 3 bullish candidates (strongest momentum + trend):")
        for r in self.top_bullish:
            lines.append(f"  #{r.rank} {r.symbol:5s}  score={r.composite_score:+.3f}  {r.explanation}")

        lines.append("")
        lines.append("Top 3 bearish candidates (weakest momentum + trend):")
        for r in self.top_bearish:
            lines.append(f"  #{r.rank} {r.symbol:5s}  score={r.composite_score:+.3f}  {r.explanation}")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Factor scoring — each returns [-1, +1], positive = bullish
# ---------------------------------------------------------------------------

def _safe(val: Any, default: float = 0.0) -> float:
    if val is None:
        return default
    return float(val)


def _clamp(val: float, scale: float = 1.0) -> float:
    """Clamp val/scale into [-1, +1]."""
    return max(-1.0, min(1.0, val / scale))


def _score_excess_return(feat: dict) -> tuple[float, str]:
    """Average excess return vs QQQ and SPY across all windows."""
    xs_keys = [k for k in feat if k.startswith("ret_") and "_xs_" in k]
    vals = [_safe(feat[k]) for k in xs_keys if feat.get(k) is not None]
    if not vals:
        return 0.0, "no excess return data"
    avg_xs = sum(vals) / len(vals)
    score = _clamp(avg_xs, 0.005)
    return score, f"avg excess {avg_xs*100:+.2f}%"


def _score_rsi(feat: dict) -> tuple[float, str]:
    """RSI mapped to a directional score.

    >70 strongly bullish, 50 neutral, <30 strongly bearish.
    For the *pullback* factor we note if RSI is in a constructive zone.
    """
    rsi = feat.get("rsi")
    if rsi is None:
        return 0.0, "RSI n/a"
    # Map 0-100 to [-1, +1] centered at 50
    score = _clamp(rsi - 50, 30)
    if rsi >= 60:
        desc = f"RSI {rsi:.0f} (strong)"
    elif rsi <= 40:
        desc = f"RSI {rsi:.0f} (weak)"
    else:
        desc = f"RSI {rsi:.0f} (neutral)"
    return score, desc


def _score_price_vs_vwap(feat: dict) -> tuple[float, str]:
    """Price relative to session VWAP."""
    price = feat.get("last_price")
    vwap = feat.get("vwap")
    if price is None or vwap is None or vwap == 0:
        return 0.0, "VWAP n/a"
    pct = (price - vwap) / vwap
    score = _clamp(pct, 0.005)
    side = "above" if pct > 0 else "below"
    return score, f"{side} VWAP {abs(pct)*100:.2f}%"


def _score_ma_alignment(feat: dict) -> tuple[float, str]:
    """Count bullish MA pairings: 5>10, 10>20, 20>60."""
    mas = [feat.get(f"ma_{p}") for p in [5, 10, 20, 60]]
    valid = [m for m in mas if m is not None]
    if len(valid) < 2:
        return 0.0, "MA data insufficient"

    pairs = list(zip(valid[:-1], valid[1:]))
    bullish = sum(1 for s, l in pairs if s > l)
    total = len(pairs)
    # Normalize to [-1, +1]
    score = (bullish / total - 0.5) * 2

    if bullish == total:
        desc = f"all {total} MA pairs bullish"
    elif bullish == 0:
        desc = f"all {total} MA pairs bearish"
    else:
        desc = f"{bullish}/{total} MA pairs bullish"
    return score, desc


def _score_relative_volume(feat: dict) -> tuple[float, str]:
    """Higher relative volume = more conviction (amplifies direction)."""
    rvol = feat.get("rvol")
    if rvol is None:
        return 0.0, "RVOL n/a"
    # 1.0 = average → 0 score, 2.0 → +1, 0.5 → -0.5
    score = _clamp(rvol - 1.0, 1.0)
    return score, f"RVOL {rvol:.2f}x"


def _score_cross_events(feat: dict) -> tuple[float, str]:
    """Golden cross = bullish boost, death cross = bearish boost."""
    golden = feat.get("golden_cross", False)
    death = feat.get("death_cross", False)
    if golden:
        return 1.0, "golden cross (MA10 > MA20)"
    if death:
        return -1.0, "death cross (MA10 < MA20)"
    return 0.0, "no cross event"


def _score_trend_quality(feat: dict) -> tuple[float, str]:
    """Trend quality: consistency of returns across windows.

    Good trend = all return windows agree in direction and are monotonic.
    """
    r5 = feat.get("ret_5m")
    r15 = feat.get("ret_15m")
    r30 = feat.get("ret_30m")
    rdtd = feat.get("ret_dtd")

    vals = [v for v in [r5, r15, r30, rdtd] if v is not None]
    if len(vals) < 2:
        return 0.0, "insufficient return data"

    # Directional consistency: fraction of returns with same sign
    positive = sum(1 for v in vals if v > 0)
    negative = sum(1 for v in vals if v < 0)
    dominant = max(positive, negative)
    consistency = dominant / len(vals)  # 0.5 to 1.0

    # Average magnitude
    avg_mag = sum(abs(v) for v in vals) / len(vals)

    # Monotonicity: are longer windows showing larger moves?
    monotonic = True
    for i in range(len(vals) - 1):
        if abs(vals[i + 1]) < abs(vals[i]) * 0.5:
            monotonic = False
            break

    # Direction of the dominant trend
    direction = 1.0 if positive >= negative else -1.0

    # Quality score: high consistency + monotonic = clean trend
    quality = consistency * (1.0 if monotonic else 0.6)
    # Scale by magnitude (cap at 1%)
    magnitude_boost = min(1.0, avg_mag / 0.01)

    score = direction * quality * magnitude_boost
    score = _clamp(score, 1.0)

    pct = f"{positive}/{len(vals)}"
    mono_tag = "monotonic" if monotonic else "choppy"
    return score, f"trend {pct} positive, {mono_tag}, avg |ret| {avg_mag*100:.2f}%"


def _score_orb(feat: dict) -> tuple[float, str]:
    """ORB breakout direction."""
    status = feat.get("orb_status", "undefined")
    if status == "above":
        return 1.0, "above opening range"
    elif status == "below":
        return -1.0, "below opening range"
    return 0.0, f"ORB {status}"


# ---------------------------------------------------------------------------
# Regime-specific weight profiles
# ---------------------------------------------------------------------------

# Weights per factor for each regime.
# bullish:  reward strength leaders
# bearish:  reward weakness leaders (scores get flipped)
# mixed:    reward stability, breakout potential, volume conviction

_WEIGHTS: dict[str, dict[str, float]] = {
    "bullish": {
        "excess_return": 0.22,
        "rsi": 0.10,
        "price_vs_vwap": 0.15,
        "ma_alignment": 0.15,
        "relative_volume": 0.08,
        "cross_events": 0.05,
        "trend_quality": 0.15,
        "orb": 0.10,
    },
    "bearish": {
        "excess_return": 0.22,
        "rsi": 0.10,
        "price_vs_vwap": 0.15,
        "ma_alignment": 0.15,
        "relative_volume": 0.08,
        "cross_events": 0.05,
        "trend_quality": 0.15,
        "orb": 0.10,
    },
    "mixed": {
        "excess_return": 0.12,
        "rsi": 0.08,
        "price_vs_vwap": 0.10,
        "ma_alignment": 0.10,
        "relative_volume": 0.15,
        "cross_events": 0.10,
        "trend_quality": 0.15,
        "orb": 0.20,
    },
}

_FACTOR_FNS = {
    "excess_return": _score_excess_return,
    "rsi": _score_rsi,
    "price_vs_vwap": _score_price_vs_vwap,
    "ma_alignment": _score_ma_alignment,
    "relative_volume": _score_relative_volume,
    "cross_events": _score_cross_events,
    "trend_quality": _score_trend_quality,
    "orb": _score_orb,
}


# ---------------------------------------------------------------------------
# Core ranking logic
# ---------------------------------------------------------------------------

def _score_symbol(feat: dict, regime_label: str) -> RankedSymbol:
    """Score one symbol under the given regime."""
    weights = _WEIGHTS[regime_label]
    factor_scores: dict[str, float] = {}
    explanations: list[str] = []

    for factor_name, fn in _FACTOR_FNS.items():
        raw_score, detail = fn(feat)

        # In bearish regime, flip scores: the most negative = best short
        if regime_label == "bearish":
            effective = -raw_score
        else:
            effective = raw_score

        factor_scores[factor_name] = round(effective, 3)
        explanations.append(detail)

    composite = sum(
        factor_scores[name] * weights[name]
        for name in factor_scores
    )

    # Build a concise explanation: top 2 factors by |contribution|
    contribs = sorted(
        [(name, factor_scores[name] * weights[name]) for name in factor_scores],
        key=lambda x: abs(x[1]),
        reverse=True,
    )
    top_factors = contribs[:2]
    expl_parts = []
    for name, contrib in top_factors:
        _, detail = _FACTOR_FNS[name](feat)
        expl_parts.append(detail)
    explanation = "; ".join(expl_parts)

    return RankedSymbol(
        symbol=feat["symbol"],
        rank=0,  # assigned after sorting
        composite_score=round(composite, 4),
        factor_scores=factor_scores,
        explanation=explanation,
    )


def rank_watchlist(
    regime: RegimeResult,
    symbol_features: list[dict],
) -> RankingResult:
    """Rank all watchlist symbols according to the current regime.

    Returns a RankingResult with:
    - full ranked list (descending by composite score)
    - top 3 bullish candidates (always ranked by raw bullish score)
    - top 3 bearish candidates (always ranked by raw bearish score, i.e. most negative)
    """
    label = regime.label

    # --- regime-aware ranking ---
    scored = [_score_symbol(feat, label) for feat in symbol_features]
    scored.sort(key=lambda s: s.composite_score, reverse=True)
    for i, s in enumerate(scored, 1):
        s.rank = i

    # --- always compute bullish and bearish lists (regime-independent) ---
    bullish_scored = [_score_symbol(feat, "bullish") for feat in symbol_features]
    bullish_scored.sort(key=lambda s: s.composite_score, reverse=True)
    for i, s in enumerate(bullish_scored, 1):
        s.rank = i
    top_bullish = bullish_scored[:3]

    bearish_scored = [_score_symbol(feat, "bearish") for feat in symbol_features]
    bearish_scored.sort(key=lambda s: s.composite_score, reverse=True)
    for i, s in enumerate(bearish_scored, 1):
        s.rank = i
    top_bearish = bearish_scored[:3]

    return RankingResult(
        regime=regime,
        ranked=scored,
        top_bullish=top_bullish,
        top_bearish=top_bearish,
    )
