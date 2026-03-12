"""Fetch 1-minute historical bars from Alpaca Market Data."""

import logging
import os
from datetime import date
from pathlib import Path

import pandas as pd
from alpaca_trade_api.rest import REST, TimeFrame
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

SYMBOLS = ["TSLA", "QQQ", "SPY"]

# Load .env from project root (won't override existing env vars)
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)


def check_credentials() -> None:
    """Validate that Alpaca credentials are present. Call before any fetch."""
    key = os.environ.get("APCA_API_KEY_ID")
    secret = os.environ.get("APCA_API_SECRET_KEY")
    if not key or not secret:
        raise EnvironmentError(
            "Alpaca credentials not found.\n"
            f"  1. Set them in {_ENV_PATH}  OR\n"
            "  2. Export APCA_API_KEY_ID and APCA_API_SECRET_KEY before running."
        )
    logger.info("Alpaca credentials loaded (key=%s...)", key[:6])


def _get_client() -> REST:
    key = os.environ.get("APCA_API_KEY_ID")
    secret = os.environ.get("APCA_API_SECRET_KEY")
    base_url = os.environ.get("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")
    if not key or not secret:
        raise EnvironmentError(
            "Set APCA_API_KEY_ID and APCA_API_SECRET_KEY environment variables"
        )
    return REST(key_id=key, secret_key=secret, base_url=base_url)


def fetch_bars(
    symbol: str,
    start: date,
    end: date,
    client: REST | None = None,
) -> pd.DataFrame:
    """Fetch 1-minute bars for *symbol* between *start* and *end* (inclusive).

    Returns a timezone-aware (UTC) DataFrame with OHLCV columns,
    or an empty DataFrame if no data is available.
    """
    if client is None:
        client = _get_client()

    start_str = start.isoformat()
    end_str = end.isoformat()

    logger.info("Fetching %s bars %s -> %s", symbol, start_str, end_str)

    bars = client.get_bars(
        symbol,
        TimeFrame.Minute,
        start=start_str,
        end=end_str,
    )
    df = bars.df if hasattr(bars, "df") else pd.DataFrame(bars)

    if df is None or df.empty:
        logger.info("%s: no bars returned for %s -> %s", symbol, start_str, end_str)
        return pd.DataFrame()

    # Ensure UTC-aware index
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    else:
        df.index = df.index.tz_convert("UTC")

    df = df[~df.index.duplicated(keep="first")].sort_index()
    logger.info("%s: got %d bars", symbol, len(df))
    return df


def fetch_all(
    start: date,
    end: date,
    symbols: list[str] | None = None,
) -> dict[str, pd.DataFrame]:
    """Fetch 1-minute bars for all tracked symbols. Returns {symbol: DataFrame}."""
    symbols = symbols or SYMBOLS
    client = _get_client()
    results: dict[str, pd.DataFrame] = {}
    for sym in symbols:
        df = fetch_bars(sym, start, end, client=client)
        if not df.empty:
            results[sym] = df
    return results
