"""Persist scan results to disk."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .config import DATA_DIR

logger = logging.getLogger(__name__)


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save_json(results: list[dict[str, Any]], path: Path | None = None) -> Path:
    _ensure_dir(DATA_DIR)
    if path is None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = DATA_DIR / f"scan_{ts}.json"
    path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    logger.info("Saved JSON: %s", path)
    return path


def save_parquet(results: list[dict[str, Any]], path: Path | None = None) -> Path:
    _ensure_dir(DATA_DIR)
    if path is None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = DATA_DIR / f"scan_{ts}.parquet"
    df = pd.DataFrame(results)
    df.to_parquet(path, index=False)
    logger.info("Saved Parquet: %s", path)
    return path
