"""Smoke test: run a single scan and print results."""

import logging
import sys
from datetime import date, timedelta

import pandas as pd

from monitor.watchlist.pipeline import scan_watchlist
from monitor.watchlist.snapshot import save_json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

# Use last weekday as the test date
today = date.today()
offset = max(1, today.weekday() - 4 + 1) if today.weekday() > 4 else 1
test_date = today - timedelta(days=offset)

print(f"=== Watchlist scan for {test_date} ===\n")

output = scan_watchlist(target_date=test_date)
regime = output["regime"]
results = output["symbols"]
ranking = output["ranking"]

if not results:
    print("No results — check date / credentials.")
    sys.exit(1)

# --- Regime ---
print("=" * 60)
print("MARKET REGIME")
print("=" * 60)
if regime:
    print(f"  Label:       {regime.label}")
    print(f"  Confidence:  {regime.confidence:.1%}")
    print(f"  Explanation: {regime.explanation}")
    print()
    for bench in ["QQQ", "SPY"]:
        if bench in regime.details:
            print(f"  {bench} signals:")
            for sig, info in regime.details[bench].items():
                print(f"    {sig:20s}  score={info['score']:+.3f}  {info['detail']}")
            print(f"    {'composite':20s}  score={regime.details[f'{bench}_composite']:+.3f}")

# --- Rankings ---
print()
print("=" * 60)
print("RANKINGS")
print("=" * 60)
print(ranking.summary())

# --- Factor breakdown ---
print()
print("=" * 60)
print("FACTOR SCORES (regime-adjusted)")
print("=" * 60)
factor_rows = []
for r in ranking.ranked:
    row = {"symbol": r.symbol, "composite": r.composite_score}
    row.update(r.factor_scores)
    factor_rows.append(row)
factor_df = pd.DataFrame(factor_rows).set_index("symbol")
print(factor_df.to_string())

# --- Symbol features ---
print()
print("=" * 60)
print("RAW FEATURES")
print("=" * 60)
df = pd.DataFrame(results).set_index("symbol")
cols_to_show = [
    "last_price", "ret_5m", "ret_15m", "ret_dtd",
    "rsi", "vwap", "rvol",
    "orb_status",
    "ret_dtd_xs_qqq", "ret_dtd_xs_spy",
]
available = [c for c in cols_to_show if c in df.columns]
print(df[available].to_string())

# Save snapshot
path = save_json(results)
print(f"\nSaved to {path}")
