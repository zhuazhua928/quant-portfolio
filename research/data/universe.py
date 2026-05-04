"""Sanity-check the hardcoded HIGH_BETA list against rolling 60-day beta vs SPY.

Run after the backfill to print which names violate the beta>=1.3 screen at
the END of the sample period. Informational only — does not mutate UNIVERSE.
"""

from __future__ import annotations

import argparse
import logging

import numpy as np
import pandas as pd

from research import config
from research.data.alpaca_client import load_symbol

logger = logging.getLogger(__name__)


def daily_close(symbol: str) -> pd.Series:
    df = load_symbol(symbol)
    if df.empty:
        return pd.Series(dtype="float64")
    # Use last close per UTC date as a proxy daily close.
    daily = df["close"].groupby(df.index.date).last()
    daily.index = pd.to_datetime(daily.index)
    return daily.rename(symbol)


def rolling_beta(rs: pd.Series, rm: pd.Series, window: int = 60) -> pd.Series:
    aligned = pd.concat([rs.rename("s"), rm.rename("m")], axis=1).dropna()
    cov = aligned["s"].rolling(window).cov(aligned["m"])
    var = aligned["m"].rolling(window).var()
    return cov / var


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--threshold", type=float, default=1.3)
    p.add_argument("--window", type=int, default=60)
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    spy = daily_close("SPY")
    if spy.empty:
        logger.error("SPY data not cached. Run fetch_bars first.")
        return 1
    rm = np.log(spy).diff()

    rows = []
    for sym in config.HIGH_BETA:
        c = daily_close(sym)
        if c.empty:
            rows.append((sym, float("nan"), 0))
            continue
        rs = np.log(c).diff()
        b = rolling_beta(rs, rm, window=args.window)
        rows.append((sym, float(b.iloc[-1]) if not b.empty else float("nan"), int(c.notna().sum())))

    df = pd.DataFrame(rows, columns=["symbol", f"beta_{args.window}d", "n_obs"]).set_index("symbol")
    df = df.sort_values(f"beta_{args.window}d", ascending=False)
    logger.info("\n%s", df.to_string())
    below = df[df[f"beta_{args.window}d"] < args.threshold]
    if not below.empty:
        logger.info("\n%d names below threshold %.2f (informational only):\n%s",
                    len(below), args.threshold, below.index.tolist())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
