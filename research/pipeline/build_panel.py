"""Build the cross-sectional feature panel from cached parquet bars.

Reads research_data/bars/*, builds per-symbol features against SPY, applies
5-minute windowing, stacks into a (symbol, ts) panel, and writes parquet.
"""

from __future__ import annotations

import argparse
import logging
from datetime import date, datetime

import pandas as pd

from research import config
from research.data.alpaca_client import load_symbol
from research.features.intraday import build_features
from research.features.windowing import make_windows

logger = logging.getLogger(__name__)


def build_for_symbol(symbol: str, spy_bars: pd.DataFrame,
                     start: date | None = None, end: date | None = None) -> pd.DataFrame:
    bars = load_symbol(symbol, start=start, end=end)
    if bars.empty:
        logger.warning("no bars for %s", symbol)
        return pd.DataFrame()
    feats = build_features(bars, spy_bars=spy_bars)
    return make_windows(feats)


def build_panel(symbols: list[str] | None = None,
                start: date | None = None, end: date | None = None) -> pd.DataFrame:
    symbols = symbols or [s for s in config.UNIVERSE if s != "SPY"]
    spy = load_symbol("SPY", start=start, end=end)
    if spy.empty:
        raise RuntimeError("SPY bars missing — fetch SPY first via research.data.fetch_bars")

    parts: list[pd.DataFrame] = []
    for sym in symbols:
        w = build_for_symbol(sym, spy_bars=spy, start=start, end=end)
        if w.empty:
            continue
        w = w.copy()
        w["symbol"] = sym
        parts.append(w.reset_index().rename(columns={w.index.name or "index": "ts"}))
        logger.info("%s: %d windows", sym, len(w))

    if not parts:
        return pd.DataFrame()
    panel = pd.concat(parts, ignore_index=True)
    if "timestamp" in panel.columns and "ts" not in panel.columns:
        panel = panel.rename(columns={"timestamp": "ts"})
    return panel.set_index(["symbol", "ts"]).sort_index()


def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--symbols", nargs="*", default=None)
    p.add_argument("--start", type=_parse_date, default=None)
    p.add_argument("--end", type=_parse_date, default=None)
    p.add_argument("--out", default=str(config.WINDOWS_DIR / "panel.parquet"))
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s | %(message)s")
    config.ensure_dirs()

    panel = build_panel(args.symbols, args.start, args.end)
    if panel.empty:
        logger.error("empty panel")
        return 1
    panel.to_parquet(args.out)
    logger.info("wrote panel %s rows=%d cols=%d", args.out, len(panel), panel.shape[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
