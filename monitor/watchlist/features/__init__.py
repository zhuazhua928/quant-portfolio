"""Aggregate all feature computations for a single symbol."""

from typing import Any

import pandas as pd

from .moving_averages import compute_moving_averages, detect_crosses
from .rsi import compute_rsi
from .vwap import compute_vwap
from .returns import compute_returns, compute_excess_returns
from .volume import compute_relative_volume
from .orb import compute_orb


def compute_all(
    symbol: str,
    df: pd.DataFrame,
    benchmark_returns: dict[str, dict[str, float | None]],
    historical_volumes: list[pd.DataFrame] | None = None,
) -> dict[str, Any]:
    """Compute every feature for one symbol. Returns a flat dict."""
    close = df["close"]

    # Moving averages + crosses
    feat: dict[str, Any] = {"symbol": symbol}
    feat["last_price"] = float(close.iloc[-1])
    feat["bar_count"] = len(df)
    feat["data_as_of"] = df.index[-1].isoformat()

    feat.update(compute_moving_averages(close))
    feat.update(detect_crosses(close))

    # RSI
    feat["rsi"] = compute_rsi(close)

    # Session VWAP
    feat["vwap"] = compute_vwap(df)

    # Returns + excess
    rets = compute_returns(close)
    feat.update(rets)
    feat.update(compute_excess_returns(rets, benchmark_returns))

    # Relative volume
    feat["rvol"] = compute_relative_volume(df, historical_volumes or [])

    # Opening range breakout
    feat.update(compute_orb(df))

    return feat
