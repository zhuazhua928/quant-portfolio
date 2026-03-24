import json
import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .config import DATA_DIR, NON_TRADEABLE, SYMBOLS

logger = logging.getLogger(__name__)


def ensure_directories() -> None:
    for subdir in ["snapshots", "intraday", "features"]:
        (DATA_DIR / subdir).mkdir(parents=True, exist_ok=True)


def _atomic_write(path: Path, content: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    tmp_path = Path(tmp)
    try:
        tmp_path.write_text(content, encoding="utf-8")
        tmp_path.replace(path)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise


def _build_summary(symbol_features: list[dict[str, Any]], now: datetime) -> dict:
    from .utils import is_us_market_open

    market_open = is_us_market_open()
    symbols = []
    for feat in symbol_features:
        name = feat["name"]
        symbols.append(
            {
                "name": name,
                "ticker": SYMBOLS[name],
                "last_price": feat["last_price"],
                "is_tradeable": name not in NON_TRADEABLE,
                "market_open": market_open if name != "BTC" else True,
                "returns": feat["returns"],
                "rolling_volatility_1h": feat["rolling_volatility_1h"],
                "rolling_correlation_to_TSLA_1h": feat[
                    "rolling_correlation_to_TSLA_1h"
                ],
                "bar_count": feat["bar_count"],
                "data_as_of": feat["data_as_of"],
            }
        )
    return {"timestamp": now.isoformat(), "symbols": symbols}


def save_latest_json(symbol_features: list[dict[str, Any]]) -> None:
    now = datetime.now(timezone.utc)
    summary = _build_summary(symbol_features, now)
    path = DATA_DIR / "latest.json"
    _atomic_write(path, json.dumps(summary, indent=2))
    logger.info("Wrote %s", path)


def save_snapshot_json(symbol_features: list[dict[str, Any]]) -> None:
    now = datetime.now(timezone.utc)
    summary = _build_summary(symbol_features, now)
    ts = now.strftime("%Y%m%dT%H%M%SZ")
    path = DATA_DIR / "snapshots" / f"{ts}.json"
    _atomic_write(path, json.dumps(summary, indent=2))


def save_intraday_parquet(data: dict[str, pd.DataFrame]) -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for name, df in data.items():
        dir_path = DATA_DIR / "intraday" / name
        dir_path.mkdir(parents=True, exist_ok=True)
        path = dir_path / f"{today}.parquet"
        df.to_parquet(path)


def save_features_parquet(symbol_features: list[dict[str, Any]]) -> None:
    if not symbol_features:
        return
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    rows = []
    for feat in symbol_features:
        row = {
            "name": feat["name"],
            "last_price": feat["last_price"],
            "bar_count": feat["bar_count"],
            "data_as_of": feat["data_as_of"],
            "rolling_volatility_1h": feat["rolling_volatility_1h"],
            "rolling_correlation_to_TSLA_1h": feat["rolling_correlation_to_TSLA_1h"],
        }
        for k, v in feat["returns"].items():
            row[f"return_{k}"] = v
        rows.append(row)
    df = pd.DataFrame(rows)
    path = DATA_DIR / "features" / f"{today}.parquet"
    df.to_parquet(path, index=False)
