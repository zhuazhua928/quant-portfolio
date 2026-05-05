"""Alpaca historical bars client with monthly batching and parquet cache.

Uses the modern alpaca-py SDK. Reads credentials from .env (project root).
Writes parquet files to research_data/bars/{SYMBOL}/{YYYY-MM}.parquet so a
re-run is incremental and resumable.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from research.config import BARS_DIR, ensure_dirs

logger = logging.getLogger(__name__)

_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_ENV_PATH)


# ---------------------------------------------------------------------------
# Lazy SDK import: keeps module importable even if alpaca-py is not installed
# ---------------------------------------------------------------------------

def _get_sdk():
    from alpaca.data.enums import Adjustment, DataFeed
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

    return {
        "StockHistoricalDataClient": StockHistoricalDataClient,
        "StockBarsRequest": StockBarsRequest,
        "TimeFrame": TimeFrame,
        "TimeFrameUnit": TimeFrameUnit,
        "DataFeed": DataFeed,
        "Adjustment": Adjustment,
    }


def check_credentials() -> tuple[str, str]:
    key = os.environ.get("APCA_API_KEY_ID")
    secret = os.environ.get("APCA_API_SECRET_KEY")
    if not key or not secret:
        raise EnvironmentError(
            "Alpaca credentials not found.\n"
            f"  Set APCA_API_KEY_ID and APCA_API_SECRET_KEY in {_ENV_PATH}\n"
            f"  or export them before running."
        )
    return key, secret


@dataclass
class AlpacaBarsClient:
    """Thin wrapper over alpaca-py StockHistoricalDataClient.

    feed: 'iex' (free tier, default) or 'sip' (paid Algo Trader Plus).
    """

    feed: str = "iex"

    def __post_init__(self) -> None:
        sdk = _get_sdk()
        key, secret = check_credentials()
        self._client = sdk["StockHistoricalDataClient"](key, secret)
        self._sdk = sdk

    # -- single-symbol fetch ------------------------------------------------

    def fetch_bars(self, symbol: str, start: datetime, end: datetime) -> pd.DataFrame:
        """Fetch 1-min bars for [start, end). Returns UTC-indexed DataFrame.

        SDK paginates internally; we just request the full range.
        """
        sdk = self._sdk
        feed_enum = sdk["DataFeed"].SIP if self.feed.lower() == "sip" else sdk["DataFeed"].IEX
        req = sdk["StockBarsRequest"](
            symbol_or_symbols=symbol,
            timeframe=sdk["TimeFrame"](1, sdk["TimeFrameUnit"].Minute),
            start=start,
            end=end,
            feed=feed_enum,
            adjustment=sdk["Adjustment"].SPLIT,
            limit=10000,
        )
        try:
            bars = self._client.get_stock_bars(req)
        except Exception as exc:  # network / rate limit
            logger.warning("alpaca fetch failed for %s [%s, %s): %s", symbol, start, end, exc)
            raise

        df = bars.df
        if df is None or df.empty:
            return pd.DataFrame()

        # alpaca-py returns a MultiIndex (symbol, timestamp); drop symbol level.
        if isinstance(df.index, pd.MultiIndex):
            df = df.xs(symbol, level=0)

        df.index = df.index.tz_convert("UTC") if df.index.tz else df.index.tz_localize("UTC")
        df = df[~df.index.duplicated(keep="first")].sort_index()
        # standardize columns
        keep = [c for c in ("open", "high", "low", "close", "volume", "trade_count", "vwap") if c in df.columns]
        return df[keep].astype("float64")


# ---------------------------------------------------------------------------
# Cache layer
# ---------------------------------------------------------------------------

def _month_iter(start: date, end: date):
    """Yield (year, month, month_start, month_end) covering [start, end]."""
    cur = date(start.year, start.month, 1)
    last = date(end.year, end.month, 1)
    while cur <= last:
        if cur.month == 12:
            nxt = date(cur.year + 1, 1, 1)
        else:
            nxt = date(cur.year, cur.month + 1, 1)
        m_start = max(cur, start)
        m_end = min(nxt - timedelta(days=1), end)
        yield cur.year, cur.month, m_start, m_end
        cur = nxt


def _bar_path(symbol: str, year: int, month: int) -> Path:
    return BARS_DIR / symbol / f"{year:04d}-{month:02d}.parquet"


def fetch_symbol_cached(
    symbol: str,
    start: date,
    end: date,
    client: AlpacaBarsClient | None = None,
    force: bool = False,
    rate_limit_sleep: float = 0.35,  # ~170 req/min, safely under free 200 cap
) -> int:
    """Pull all months in [start, end] for *symbol*, caching to parquet.

    Returns number of new monthly parquet files written.
    """
    ensure_dirs()
    if client is None:
        client = AlpacaBarsClient()

    written = 0
    for year, month, m_start, m_end in _month_iter(start, end):
        out_path = _bar_path(symbol, year, month)
        if out_path.exists() and not force:
            continue
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Alpaca treats 'end' as exclusive at the second; pad by one day.
        start_dt = datetime.combine(m_start, datetime.min.time(), tzinfo=timezone.utc)
        end_dt = datetime.combine(m_end + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
        try:
            df = client.fetch_bars(symbol, start_dt, end_dt)
        except Exception as exc:
            logger.error("skip %s %04d-%02d: %s", symbol, year, month, exc)
            time.sleep(2.0)
            continue

        if df.empty:
            logger.info("%s %04d-%02d: no bars", symbol, year, month)
            # write an empty marker so we don't refetch every run
            df.to_parquet(out_path)
        else:
            df.to_parquet(out_path)
            logger.info("%s %04d-%02d: %d bars -> %s", symbol, year, month, len(df), out_path)
            written += 1
        time.sleep(rate_limit_sleep)
    return written


def load_symbol(symbol: str, start: date | None = None, end: date | None = None) -> pd.DataFrame:
    """Load all cached parquet files for *symbol*, optionally clipped to [start, end]."""
    sym_dir = BARS_DIR / symbol
    if not sym_dir.exists():
        return pd.DataFrame()
    parts: list[pd.DataFrame] = []
    for p in sorted(sym_dir.glob("*.parquet")):
        df = pd.read_parquet(p)
        if not df.empty:
            parts.append(df)
    if not parts:
        return pd.DataFrame()
    out = pd.concat(parts).sort_index()
    out = out[~out.index.duplicated(keep="first")]
    if start is not None:
        out = out.loc[out.index >= pd.Timestamp(start, tz="UTC")]
    if end is not None:
        out = out.loc[out.index <= pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)]
    return out
