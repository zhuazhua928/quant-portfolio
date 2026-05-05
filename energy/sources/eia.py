"""Thin EIA API v2 client for Henry Hub spot + Lower-48 weekly storage."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import requests

from ..config import (
    EIA_API_BASE,
    EIA_API_KEY,
    EIA_SERIES_HENRY_HUB_SPOT,
    EIA_SERIES_LOWER48_STORAGE,
)

logger = logging.getLogger(__name__)


class EIAKeyMissing(RuntimeError):
    pass


def _require_key() -> str:
    if not EIA_API_KEY:
        raise EIAKeyMissing(
            "EIA_API_KEY not set in .env — register a free key at "
            "https://www.eia.gov/opendata/register.php"
        )
    return EIA_API_KEY


def _fetch_series(series_id: str, length: int = 5000) -> list[dict[str, Any]]:
    key = _require_key()
    url = f"{EIA_API_BASE}/seriesid/{series_id}"
    params = {"api_key": key, "length": length}
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    response = payload.get("response", {})
    data = response.get("data") or []
    if not data:
        logger.warning("EIA series %s returned no rows", series_id)
    return data


def fetch_spot() -> pd.DataFrame:
    """Henry Hub daily spot price ($/MMBtu).

    Returns DataFrame with columns: date, value. Sorted ascending.
    """
    rows = _fetch_series(EIA_SERIES_HENRY_HUB_SPOT)
    if not rows:
        return pd.DataFrame(columns=["date", "value"])
    df = pd.DataFrame(rows)
    df = df.rename(columns={"period": "date", "value": "value"})
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df[["date", "value"]].dropna().sort_values("date").reset_index(drop=True)


def fetch_storage() -> pd.DataFrame:
    """Lower-48 weekly working gas in underground storage (Bcf).

    Returns DataFrame with columns: date, value. Sorted ascending.
    """
    rows = _fetch_series(EIA_SERIES_LOWER48_STORAGE)
    if not rows:
        return pd.DataFrame(columns=["date", "value"])
    df = pd.DataFrame(rows)
    df = df.rename(columns={"period": "date", "value": "value"})
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df[["date", "value"]].dropna().sort_values("date").reset_index(drop=True)
