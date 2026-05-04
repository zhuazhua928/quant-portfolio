"""yfinance pulls for NG=F front-month and the dated forward curve."""

from __future__ import annotations

import logging
from datetime import date, timedelta

import pandas as pd
import yfinance as yf

from ..config import (
    FORWARD_CONTRACT_MONTHS,
    FRONT_MONTH_TICKER,
    NYMEX_MONTH_CODES,
    PRICE_HISTORY_YEARS,
)

logger = logging.getLogger(__name__)


def fetch_front_month(years: int = PRICE_HISTORY_YEARS) -> pd.DataFrame:
    """Daily NG=F closes for the last `years` years.

    Returns a DataFrame indexed by date with columns: open, high, low, close, volume.
    """
    end = date.today() + timedelta(days=1)
    start = end - timedelta(days=int(365.25 * years))
    raw = yf.download(
        FRONT_MONTH_TICKER,
        start=start.isoformat(),
        end=end.isoformat(),
        progress=False,
        auto_adjust=False,
    )
    if raw is None or raw.empty:
        logger.warning("yfinance returned no data for %s", FRONT_MONTH_TICKER)
        return pd.DataFrame()

    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.droplevel(1)
    df = raw[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.columns = ["open", "high", "low", "close", "volume"]
    df.index = pd.to_datetime(df.index).normalize()
    df.index.name = "date"
    return df.dropna(subset=["close"])


def _contract_symbol(year: int, month: int) -> str:
    """Build the NYMEX dated nat gas symbol expected by yfinance.

    yfinance accepts e.g. NGH26.NYM for March 2026 Henry Hub.
    """
    code = NYMEX_MONTH_CODES[month]
    yy = year % 100
    return f"NG{code}{yy:02d}.NYM"


def _next_n_contract_months(asof: date, n: int) -> list[tuple[int, int]]:
    """Return list of (year, month) for the next n delivery months starting
    from the month *after* `asof` (front month is M1 = next delivery month).
    """
    months: list[tuple[int, int]] = []
    y, m = asof.year, asof.month + 1
    if m > 12:
        m = 1
        y += 1
    for _ in range(n):
        months.append((y, m))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return months


def fetch_forward_curve(asof: date | None = None, n: int = FORWARD_CONTRACT_MONTHS) -> list[dict]:
    """Pull the most recent close for each dated NG contract over the next n months.

    Returns a list of `{symbol, year, month, expiry_label, close}` sorted by expiry.
    Skips contracts with no available data (yfinance returns empty for some
    far-dated tickers when liquidity is low).
    """
    if asof is None:
        asof = date.today()
    contracts = _next_n_contract_months(asof, n)
    rows: list[dict] = []
    for year, month in contracts:
        sym = _contract_symbol(year, month)
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="1mo", auto_adjust=False)
        except Exception as exc:  # noqa: BLE001
            logger.warning("fetch failed for %s: %s", sym, exc)
            continue
        if hist is None or hist.empty:
            logger.info("no data for %s — skipping", sym)
            continue
        last = hist.dropna(subset=["Close"]).tail(1)
        if last.empty:
            continue
        close = float(last["Close"].iloc[0])
        rows.append(
            {
                "symbol": sym,
                "year": year,
                "month": month,
                "expiry_label": f"{year}-{month:02d}",
                "close": round(close, 4),
            }
        )
    return rows
