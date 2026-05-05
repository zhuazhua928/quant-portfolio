"""Session VWAP computed from intraday OHLCV bars."""

import pandas as pd


def compute_vwap(df: pd.DataFrame) -> float | None:
    if df.empty or "volume" not in df.columns:
        return None

    typical = (df["high"] + df["low"] + df["close"]) / 3
    cum_tp_vol = (typical * df["volume"]).cumsum()
    cum_vol = df["volume"].cumsum()

    last_vol = cum_vol.iloc[-1]
    if last_vol == 0:
        return None
    return float(cum_tp_vol.iloc[-1] / last_vol)
