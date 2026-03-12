"""Market regime classifier based on QQQ and SPY intraday signals.

Classifies the session as bullish / bearish / mixed using a weighted
scoring system across five signal dimensions.
"""

from dataclasses import dataclass
from datetime import time
from typing import Any

import pandas as pd

from .moving_averages import compute_moving_averages
from .vwap import compute_vwap
from .orb import compute_orb
from .returns import compute_returns


@dataclass
class RegimeResult:
    label: str          # "bullish" | "bearish" | "mixed"
    confidence: float   # 0.0 – 1.0
    explanation: str
    details: dict[str, Any]


# ---------------------------------------------------------------------------
# Individual signal scorers — each returns a float in [-1, +1]
# positive = bullish, negative = bearish
# ---------------------------------------------------------------------------

def _score_price_vs_vwap(df: pd.DataFrame) -> tuple[float, str]:
    """Last price relative to session VWAP."""
    vwap = compute_vwap(df)
    if vwap is None or vwap == 0:
        return 0.0, "vwap n/a"

    last = float(df["close"].iloc[-1])
    pct = (last - vwap) / vwap

    # Clamp to [-1, 1] — ±0.5% maps to full score
    score = max(-1.0, min(1.0, pct / 0.005))
    side = "above" if pct > 0 else "below"
    return score, f"price {side} VWAP by {abs(pct)*100:.2f}%"


def _score_ma_alignment(close: pd.Series) -> tuple[float, str]:
    """Short-term MAs vs long-term MAs alignment."""
    mas = compute_moving_averages(close, periods=[5, 10, 20, 60])
    ma5, ma10, ma20, ma60 = mas.get("ma_5"), mas.get("ma_10"), mas.get("ma_20"), mas.get("ma_60")

    if any(v is None for v in [ma5, ma10, ma20, ma60]):
        available = {k: v for k, v in mas.items() if v is not None}
        if not available:
            return 0.0, "MAs insufficient data"
        vals = list(available.values())
        if len(vals) < 2:
            return 0.0, "MAs insufficient data"
        # Fallback: compare shortest vs longest available
        score = 1.0 if vals[0] > vals[-1] else -1.0
        return score * 0.5, "partial MA alignment"

    # Count bullish pairings: (5>10), (10>20), (20>60)
    pairs = [(ma5, ma10), (ma10, ma20), (ma20, ma60)]
    bullish = sum(1 for s, l in pairs if s > l)
    # 3 bullish = +1, 0 bullish = -1
    score = (bullish - 1.5) / 1.5

    if bullish == 3:
        desc = "all MAs aligned bullish (5>10>20>60)"
    elif bullish == 0:
        desc = "all MAs aligned bearish (5<10<20<60)"
    else:
        desc = f"{bullish}/3 MA pairs bullish"
    return score, desc


def _score_early_session_direction(df: pd.DataFrame) -> tuple[float, str]:
    """Directional persistence in the first 15m and 30m of RTH."""
    idx_et = df.index.tz_convert("America/New_York")
    df_et = df.copy()
    df_et.index = idx_et

    open_time = time(9, 30)
    t15 = time(9, 45)
    t30 = time(10, 0)

    rth = df_et[(df_et.index.time >= open_time)]
    if rth.empty:
        return 0.0, "no RTH data"

    open_price = float(rth["close"].iloc[0])
    scores = []
    descs = []

    # 15-min direction
    first15 = rth[rth.index.time <= t15]
    if len(first15) >= 2:
        ret15 = float(first15["close"].iloc[-1] / open_price - 1)
        # ±0.3% maps to full score
        s15 = max(-1.0, min(1.0, ret15 / 0.003))
        scores.append(s15)
        descs.append(f"first 15m {ret15*100:+.2f}%")

    # 30-min direction
    first30 = rth[rth.index.time <= t30]
    if len(first30) >= 2:
        ret30 = float(first30["close"].iloc[-1] / open_price - 1)
        s30 = max(-1.0, min(1.0, ret30 / 0.003))
        scores.append(s30)
        descs.append(f"first 30m {ret30*100:+.2f}%")

    if not scores:
        return 0.0, "early session data insufficient"

    return sum(scores) / len(scores), "; ".join(descs)


def _score_intraday_momentum(close: pd.Series) -> tuple[float, str]:
    """DTD return and recent 30m trend."""
    rets = compute_returns(close)
    dtd = rets.get("ret_dtd")
    r30 = rets.get("ret_30m")

    if dtd is None:
        return 0.0, "momentum n/a"

    # DTD: ±0.5% → full score
    s_dtd = max(-1.0, min(1.0, dtd / 0.005))

    if r30 is not None:
        s_r30 = max(-1.0, min(1.0, r30 / 0.003))
        score = 0.6 * s_dtd + 0.4 * s_r30
        desc = f"DTD {dtd*100:+.2f}%, last 30m {r30*100:+.2f}%"
    else:
        score = s_dtd
        desc = f"DTD {dtd*100:+.2f}%"

    return score, desc


def _score_orb_behavior(df: pd.DataFrame) -> tuple[float, str]:
    """Opening range breakout direction."""
    orb = compute_orb(df)
    status = orb["orb_status"]

    if status == "above":
        return 1.0, "price above opening range"
    elif status == "below":
        return -1.0, "price below opening range"
    elif status == "inside":
        return 0.0, "price inside opening range"
    else:
        return 0.0, "opening range not defined"


# ---------------------------------------------------------------------------
# Aggregate classifier
# ---------------------------------------------------------------------------

_SIGNAL_WEIGHTS = {
    "price_vs_vwap": 0.25,
    "ma_alignment": 0.20,
    "early_direction": 0.20,
    "momentum": 0.20,
    "orb": 0.15,
}


def classify_regime(
    qqq_df: pd.DataFrame,
    spy_df: pd.DataFrame,
) -> RegimeResult:
    """Classify market regime from QQQ and SPY intraday bars.

    Scores each benchmark independently, then averages.
    """
    bench_scores: dict[str, dict[str, tuple[float, str]]] = {}

    for name, df in [("QQQ", qqq_df), ("SPY", spy_df)]:
        if df.empty:
            continue
        close = df["close"]
        bench_scores[name] = {
            "price_vs_vwap": _score_price_vs_vwap(df),
            "ma_alignment": _score_ma_alignment(close),
            "early_direction": _score_early_session_direction(df),
            "momentum": _score_intraday_momentum(close),
            "orb": _score_orb_behavior(df),
        }

    if not bench_scores:
        return RegimeResult(
            label="mixed",
            confidence=0.0,
            explanation="No benchmark data available",
            details={},
        )

    # Weighted composite per benchmark, then average
    composites = []
    all_details: dict[str, Any] = {}

    for name, signals in bench_scores.items():
        weighted = sum(
            score * _SIGNAL_WEIGHTS[sig_name]
            for sig_name, (score, _) in signals.items()
        )
        composites.append(weighted)
        all_details[name] = {
            sig_name: {"score": round(score, 3), "detail": detail}
            for sig_name, (score, detail) in signals.items()
        }
        all_details[f"{name}_composite"] = round(weighted, 3)

    avg_composite = sum(composites) / len(composites)
    all_details["composite"] = round(avg_composite, 3)

    # Classify
    if avg_composite > 0.2:
        label = "bullish"
    elif avg_composite < -0.2:
        label = "bearish"
    else:
        label = "mixed"

    confidence = min(1.0, abs(avg_composite))

    # Build explanation from the strongest signals
    explanations = []
    for name, signals in bench_scores.items():
        strongest = max(signals.items(), key=lambda x: abs(x[1][0]))
        sig_name, (score, detail) = strongest
        explanations.append(f"{name}: {detail}")

    explanation = f"{label} (score {avg_composite:+.2f}) — " + "; ".join(explanations)

    return RegimeResult(
        label=label,
        confidence=round(confidence, 3),
        explanation=explanation,
        details=all_details,
    )
