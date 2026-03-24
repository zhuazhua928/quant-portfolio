"""Watchlist universe and feature parameters."""

from pathlib import Path

WATCHLIST = ["TSLA", "NVDA", "PLTR", "MU", "HOOD", "AMD"]
BENCHMARKS = ["QQQ", "SPY"]
ALL_SYMBOLS = WATCHLIST + BENCHMARKS

MA_PERIODS = [5, 10, 20, 60]
RSI_PERIOD = 14
RETURN_WINDOWS = {"5m": 5, "15m": 15, "30m": 30}
ORB_MINUTES = 30  # first 30 min define the opening range
RVOL_LOOKBACK_DAYS = 5  # trading days for avg volume baseline

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "monitor_data" / "watchlist"
