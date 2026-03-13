"""Opening Range Breakout detection."""

from datetime import time
from typing import Any

import pandas as pd

from ..config import ORB_MINUTES


def compute_orb(df: pd.DataFrame, orb_minutes: int = ORB_MINUTES) -> dict[str, Any]:
    """Identify opening range and current breakout status.

    Opening range = high/low of bars between 9:30 and 9:30+orb_minutes ET.
    """
    result: dict[str, Any] = {
        "orb_high": None,
        "orb_low": None,
        "orb_status": "undefined",
    }
    if df.empty:
        return result

    idx_et = df.index.tz_convert("America/New_York")
    df_et = df.copy()
    df_et.index = idx_et

    market_open = time(9, 30)
    orb_end_hour = 9 + (30 + orb_minutes) // 60
    orb_end_min = (30 + orb_minutes) % 60
    orb_end = time(orb_end_hour, orb_end_min)

    orb_mask = (df_et.index.time >= market_open) & (df_et.index.time < orb_end)
    orb_bars = df_et.loc[orb_mask]

    if orb_bars.empty:
        return result

    orb_high = float(orb_bars["high"].max())
    orb_low = float(orb_bars["low"].min())
    result["orb_high"] = orb_high
    result["orb_low"] = orb_low

    last_close = float(df["close"].iloc[-1])
    if last_close > orb_high:
        result["orb_status"] = "above"
    elif last_close < orb_low:
        result["orb_status"] = "below"
    else:
        result["orb_status"] = "inside"

    return result
