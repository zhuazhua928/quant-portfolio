"""Mock / placeholder provider for development and testing.

Generates synthetic 1-minute bars with random-walk prices so the engine
can be exercised without a live API connection.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta, timezone
from typing import Iterator

import numpy as np
import pandas as pd

from . import MarketDataProvider

logger = logging.getLogger(__name__)

# Rough starting prices and daily vol for synthetic data
_SEEDS: dict[str, tuple[float, float]] = {
    "TSLA": (400.0, 0.03),
    "NVDA": (185.0, 0.025),
    "PLTR": (150.0, 0.035),
    "MU": (408.0, 0.025),
    "HOOD": (79.0, 0.03),
    "AMD": (204.0, 0.025),
    "QQQ": (480.0, 0.012),
    "SPY": (570.0, 0.010),
}


def _generate_day(
    symbol: str,
    session_date: date,
    seed: int | None = None,
) -> pd.DataFrame:
    """Generate 390 synthetic 1-min bars (9:30–16:00 ET) for one symbol."""
    rng = np.random.default_rng(
        seed if seed is not None else hash((symbol, str(session_date))) & 0xFFFFFFFF
    )
    start_price, daily_vol = _SEEDS.get(symbol, (100.0, 0.02))
    minute_vol = daily_vol / np.sqrt(390)

    n_bars = 390
    log_returns = rng.normal(0, minute_vol, n_bars)
    # Add a slight drift for variety
    drift = rng.normal(0, 0.001)
    log_returns += drift / n_bars

    prices = start_price * np.exp(np.cumsum(log_returns))

    # Build timestamps (ET -> UTC)
    from datetime import timezone as tz

    et_offset = timedelta(hours=-5)  # simplified, no DST
    base = datetime.combine(session_date, time(9, 30), tzinfo=timezone(et_offset))
    timestamps = [base + timedelta(minutes=i) for i in range(n_bars)]
    utc_timestamps = [t.astimezone(timezone.utc) for t in timestamps]

    # Construct OHLCV
    noise = rng.uniform(0.0002, 0.001, n_bars)
    highs = prices * (1 + noise)
    lows = prices * (1 - noise)
    opens = np.roll(prices, 1)
    opens[0] = start_price
    volumes = rng.integers(500, 50000, n_bars).astype(float)

    df = pd.DataFrame(
        {
            "open": opens,
            "high": highs,
            "low": lows,
            "close": prices,
            "volume": volumes,
        },
        index=pd.DatetimeIndex(utc_timestamps, name="timestamp"),
    )
    return df


class MockProvider(MarketDataProvider):
    """Synthetic data provider for offline testing."""

    def __init__(
        self,
        symbols: list[str] | None = None,
        session_date: date | None = None,
        seed: int | None = None,
    ) -> None:
        self._symbols = symbols or list(_SEEDS.keys())
        self._session_date = session_date or date.today()
        self._seed = seed
        self._cache: dict[str, pd.DataFrame] = {}
        self._stream_index = 0

        # Pre-generate session data
        for sym in self._symbols:
            self._cache[sym] = _generate_day(sym, self._session_date, self._seed)

    def get_latest_bar(self, symbol: str) -> pd.Series | None:
        df = self._cache.get(symbol)
        if df is None or df.empty:
            return None
        idx = min(self._stream_index, len(df) - 1)
        return df.iloc[idx]

    def get_session_bars(
        self, symbol: str, session_date: date | None = None
    ) -> pd.DataFrame:
        df = self._cache.get(symbol, pd.DataFrame())
        if session_date and session_date != self._session_date:
            return _generate_day(symbol, session_date, self._seed)
        # Return bars up to current stream position
        end = min(self._stream_index + 1, len(df))
        return df.iloc[:end].copy()

    def get_historical_bars(
        self, symbol: str, start: date, end: date
    ) -> pd.DataFrame:
        """Generate multi-day history for volume baseline."""
        frames = []
        current = start
        while current <= end:
            if current.weekday() < 5:  # skip weekends
                frames.append(_generate_day(symbol, current, self._seed))
            current += timedelta(days=1)
        if not frames:
            return pd.DataFrame()
        return pd.concat(frames)

    def stream_bars(
        self, symbols: list[str]
    ) -> Iterator[tuple[str, pd.Series]]:
        """Yield bars one minute at a time across all symbols."""
        max_bars = max(len(self._cache.get(s, [])) for s in symbols)
        for i in range(max_bars):
            self._stream_index = i
            for sym in symbols:
                df = self._cache.get(sym)
                if df is not None and i < len(df):
                    yield (sym, df.iloc[i])
