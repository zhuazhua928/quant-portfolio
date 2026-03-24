"""Quick smoke test for alpaca_bars — requires valid credentials in env."""

import sys
from datetime import date, timedelta

from monitor.alpaca_bars import fetch_bars, fetch_all

# Use last trading weekday as test range
today = date.today()
offset = max(1, (today.weekday() - 4) + 1) if today.weekday() > 4 else 1
end = today - timedelta(days=offset)
start = end  # single day


def test_single():
    print(f"--- fetch_bars TSLA  {start} -> {end} ---")
    df = fetch_bars("TSLA", start, end)
    if df.empty:
        print("TSLA: empty (market may have been closed)")
    else:
        print(f"TSLA: {len(df)} bars, columns={list(df.columns)}")
        print(df.head(3))
        print(df.tail(3))
    return df


def test_all():
    print(f"\n--- fetch_all  {start} -> {end} ---")
    data = fetch_all(start, end)
    for sym, df in data.items():
        print(f"{sym}: {len(df)} bars  [{df.index.min()} .. {df.index.max()}]")
    if not data:
        print("No data returned for any symbol")
    return data


if __name__ == "__main__":
    df = test_single()
    data = test_all()
    if not data:
        print("\nNo data — check that the date was a trading day and creds are valid.")
        sys.exit(1)
    print("\nAll OK.")
