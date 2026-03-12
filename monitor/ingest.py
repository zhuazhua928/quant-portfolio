import logging
import time

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


def fetch_single(
    ticker: str, period: str = "1d", interval: str = "1m", retries: int = 2
) -> pd.DataFrame | None:
    for attempt in range(1, retries + 1):
        try:
            df = yf.download(
                ticker, period=period, interval=interval, progress=False
            )
            if df is None or df.empty:
                return None
            # Flatten MultiIndex columns if present
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            # Normalize to UTC
            if df.index.tz is not None:
                df.index = df.index.tz_convert("UTC")
            else:
                df.index = df.index.tz_localize("UTC")
            # Drop duplicate timestamps
            df = df[~df.index.duplicated(keep="first")]
            # Validate required columns
            if "Close" not in df.columns:
                logger.warning("%s: missing 'Close' column", ticker)
                return None
            return df
        except Exception:
            logger.warning(
                "%s: fetch attempt %d/%d failed", ticker, attempt, retries, exc_info=True
            )
            if attempt < retries:
                time.sleep(1)
    return None


def fetch_all_intraday(symbols: dict[str, str]) -> dict[str, pd.DataFrame]:
    results: dict[str, pd.DataFrame] = {}
    for name, ticker in symbols.items():
        df = fetch_single(ticker)
        if df is not None and not df.empty:
            results[name] = df
            logger.debug("%s: fetched %d bars", name, len(df))
        else:
            logger.info("%s: no data returned", name)
        time.sleep(0.3)
    return results
