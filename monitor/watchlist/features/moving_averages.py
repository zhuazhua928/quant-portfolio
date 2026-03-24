"""Moving averages and cross detection."""

import pandas as pd

from ..config import MA_PERIODS


def compute_moving_averages(
    close: pd.Series, periods: list[int] | None = None
) -> dict[str, float | None]:
    periods = periods or MA_PERIODS
    result: dict[str, float | None] = {}
    for p in periods:
        ma = close.rolling(p).mean()
        result[f"ma_{p}"] = float(ma.iloc[-1]) if len(ma) >= p and pd.notna(ma.iloc[-1]) else None
    return result


def detect_crosses(close: pd.Series) -> dict[str, bool]:
    """Detect golden cross (MA10 crosses above MA20) and death cross at the latest bar."""
    if len(close) < 21:
        return {"golden_cross": False, "death_cross": False}

    ma_short = close.rolling(10).mean()
    ma_long = close.rolling(20).mean()

    prev_short, curr_short = ma_short.iloc[-2], ma_short.iloc[-1]
    prev_long, curr_long = ma_long.iloc[-2], ma_long.iloc[-1]

    if pd.isna(prev_short) or pd.isna(curr_long):
        return {"golden_cross": False, "death_cross": False}

    golden = prev_short <= prev_long and curr_short > curr_long
    death = prev_short >= prev_long and curr_short < curr_long
    return {"golden_cross": bool(golden), "death_cross": bool(death)}
