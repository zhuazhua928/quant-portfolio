"""Symbols, EIA series IDs, and output paths."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "src" / "data" / "energy"

FRONT_MONTH_TICKER = "NG=F"
FORWARD_CONTRACT_MONTHS = 18

NYMEX_MONTH_CODES = {
    1: "F", 2: "G", 3: "H", 4: "J", 5: "K", 6: "M",
    7: "N", 8: "Q", 9: "U", 10: "V", 11: "X", 12: "Z",
}

EIA_API_BASE = "https://api.eia.gov/v2"
EIA_API_KEY = os.environ.get("EIA_API_KEY")

EIA_SERIES_HENRY_HUB_SPOT = "NG.RNGWHHD.D"
EIA_SERIES_LOWER48_STORAGE = "NG.NW2_EPG0_SWO_R48_BCF.W"

PRICE_HISTORY_YEARS = 5
STORAGE_HISTORY_YEARS = 6  # need 5 yrs for envelope + current year

VOL_WINDOWS = (10, 30)
TRADING_DAYS_PER_YEAR = 252
