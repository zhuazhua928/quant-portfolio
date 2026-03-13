import math
from pathlib import Path

SYMBOLS = {
    "TSLA": "TSLA",
    "QQQ": "QQQ",
    "SPY": "SPY",
    "NVDA": "NVDA",
    "BTC": "BTC-USD",
    "Gold": "GC=F",
    "VIX": "^VIX",
}

BASE_SYMBOL = "TSLA"

RETURN_WINDOWS = {"5m": 5, "15m": 15, "1h": 60}

ROLLING_VOL_WINDOW = 60
ROLLING_CORR_WINDOW = 60

# Annualization factors for rolling vol (from 1-min bars)
# Equities: 390 trading minutes/day * 252 trading days/year
EQUITY_ANNUALIZATION = math.sqrt(390 * 252)
# BTC: 1440 minutes/day * 365 days/year
BTC_ANNUALIZATION = math.sqrt(1440 * 365)

NON_TRADEABLE = {"VIX"}

POLL_INTERVAL_SECONDS = 60
BACKOFF_INTERVAL_SECONDS = 300

DATA_DIR = Path(__file__).resolve().parent.parent / "monitor_data"
