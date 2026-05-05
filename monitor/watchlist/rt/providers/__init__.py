"""Market data provider abstraction.

The provider interface defines a clean boundary between the real-time engine
and whatever data source supplies 1-minute bars.  For now only a mock
provider is shipped; swapping in Alpaca or another feed requires implementing
the same interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Iterator

import pandas as pd


class MarketDataProvider(ABC):
    """Abstract interface for 1-minute bar data."""

    @abstractmethod
    def get_latest_bar(self, symbol: str) -> pd.Series | None:
        """Return the most recent 1-minute bar for *symbol*, or None."""
        ...

    @abstractmethod
    def get_session_bars(
        self, symbol: str, session_date: date | None = None
    ) -> pd.DataFrame:
        """Return all 1-minute bars for *symbol* on *session_date*.

        If *session_date* is None, return today's bars accumulated so far.
        Columns: open, high, low, close, volume (lowercase).
        Index: UTC-aware DatetimeIndex.
        """
        ...

    @abstractmethod
    def get_historical_bars(
        self, symbol: str, start: date, end: date
    ) -> pd.DataFrame:
        """Return historical bars for relative-volume baseline, etc."""
        ...

    @abstractmethod
    def stream_bars(
        self, symbols: list[str]
    ) -> Iterator[tuple[str, pd.Series]]:
        """Yield (symbol, bar) tuples as new bars arrive.

        This is the main real-time loop driver.  Each bar is a pd.Series
        with index [open, high, low, close, volume] and a `name` attribute
        set to the UTC timestamp of the bar.
        """
        ...
