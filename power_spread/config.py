"""Config for the ERCOT DA/RT spread replication."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "src" / "data" / "power-spread"
CACHE_DIR = PROJECT_ROOT / "power_spread" / "_cache"

# ---- Market scope ----
HUB = "HB_NORTH"  # ERCOT North Hub
TZ = "US/Central"

# ---- Time windows ----
START_DATE = "2022-01-01"
END_DATE = "2025-12-31"

# Calibration windows (paper Table 3): T in {30, 91, 182, 365} days
CALIBRATION_WINDOWS = (30, 91, 182, 365)

# OOS validation starts after the longest warm-up window
OOS_START = "2023-01-01"

# ---- Backtest economics ----
COST_PER_MWH = 0.50  # $/MWh per market-switch (Y_ht=1)
COST_SWEEP = (0.0, 0.25, 0.50, 1.00, 2.00)
THRESHOLD_SWEEP = (0.30, 0.40, 0.50)  # probit decision threshold mu
POSITION_MWH = 1.0  # 1 MWh per hour, $-denominated PnL

# Annualization for dollar-Sharpe (calendar days, electricity trades 24x365)
DAYS_PER_YEAR = 365

# ---- Lag set L (paper Sec. 3.1) ----
# L = [2, 7] is the best-performing for Polish ARX in Table 4. We replicate.
LAG_SET = (2, 7)

# ---- EIA-930 cross-check ----
EIA_API_BASE = "https://api.eia.gov/v2"
EIA_API_KEY = os.environ.get("EIA_API_KEY")
EIA_BA = "ERCO"  # ERCOT BA in EIA-930

# ---- Output JSON paths ----
JSON_FILES = (
    "pipeline",
    "summary",
    "models",
    "equity",
    "decisions",
    "sensitivity",
    "metadata",
)
