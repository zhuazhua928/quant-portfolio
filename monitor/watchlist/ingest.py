"""Data ingestion via Alpaca market data."""

import logging
from datetime import date, timedelta

import pandas as pd

from monitor.alpaca_bars import _get_client, fetch_bars
from .config import ALL_SYMBOLS

logger = logging.getLogger(__name__)


def fetch_today(
    symbols: list[str] | None = None,
) -> dict[str, pd.DataFrame]:
    """Fetch today's 1-min bars for all symbols."""
    symbols = symbols or ALL_SYMBOLS
    client = _get_client()
    today = date.today()
    results: dict[str, pd.DataFrame] = {}
    for sym in symbols:
        df = fetch_bars(sym, today, today, client=client)
        if not df.empty:
            results[sym] = df
    return results


def fetch_range(
    start: date,
    end: date,
    symbols: list[str] | None = None,
) -> dict[str, pd.DataFrame]:
    """Fetch 1-min bars for a date range."""
    symbols = symbols or ALL_SYMBOLS
    client = _get_client()
    results: dict[str, pd.DataFrame] = {}
    for sym in symbols:
        df = fetch_bars(sym, start, end, client=client)
        if not df.empty:
            results[sym] = df
    return results


def fetch_recent_days(
    n_days: int = 5,
    symbols: list[str] | None = None,
) -> dict[str, pd.DataFrame]:
    """Fetch the last *n_days* calendar-adjusted trading days (request 2x to cover weekends)."""
    symbols = symbols or ALL_SYMBOLS
    today = date.today()
    start = today - timedelta(days=n_days * 2)  # overshoot to cover weekends/holidays
    end = today - timedelta(days=1)
    return fetch_range(start, end, symbols)
