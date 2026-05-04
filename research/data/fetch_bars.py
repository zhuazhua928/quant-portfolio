"""CLI: backfill 1-minute bars from Alpaca for the configured universe.

Examples
--------
    # smoke test (1 symbol, 1 week)
    python -m research.data.fetch_bars --symbols TSLA --start 2022-01-03 --end 2022-01-07

    # full backfill (universe x 2022-01..2026-03), resumable
    python -m research.data.fetch_bars
"""

from __future__ import annotations

import argparse
import logging
from datetime import date, datetime

from research import config
from research.data.alpaca_client import AlpacaBarsClient, fetch_symbol_cached

logger = logging.getLogger(__name__)


def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Backfill Alpaca 1-min bars to parquet cache.")
    p.add_argument("--symbols", nargs="*", default=None,
                   help=f"Symbols to fetch (default: full UNIVERSE = {len(config.UNIVERSE)} names).")
    p.add_argument("--start", type=_parse_date, default=config.START)
    p.add_argument("--end", type=_parse_date, default=config.END)
    p.add_argument("--feed", choices=("iex", "sip"), default="iex")
    p.add_argument("--force", action="store_true", help="Re-fetch months even if parquet exists.")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    )

    symbols = args.symbols or config.UNIVERSE
    client = AlpacaBarsClient(feed=args.feed)

    total = 0
    for i, sym in enumerate(symbols, 1):
        logger.info("[%d/%d] %s", i, len(symbols), sym)
        try:
            total += fetch_symbol_cached(sym, args.start, args.end, client=client, force=args.force)
        except Exception as exc:  # keep going even if one symbol fails
            logger.error("fatal %s: %s", sym, exc)
    logger.info("done. wrote %d new monthly parquet files.", total)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
