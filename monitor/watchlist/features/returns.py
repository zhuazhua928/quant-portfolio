"""Period returns and excess returns versus benchmarks."""

import pandas as pd

from ..config import RETURN_WINDOWS


def compute_returns(close: pd.Series) -> dict[str, float | None]:
    result: dict[str, float | None] = {}
    for label, window in RETURN_WINDOWS.items():
        if len(close) > window:
            result[f"ret_{label}"] = float(close.iloc[-1] / close.iloc[-1 - window] - 1)
        else:
            result[f"ret_{label}"] = None

    # Day-to-date
    if len(close) >= 2:
        result["ret_dtd"] = float(close.iloc[-1] / close.iloc[0] - 1)
    else:
        result["ret_dtd"] = None
    return result


def compute_excess_returns(
    sym_returns: dict[str, float | None],
    benchmark_returns: dict[str, dict[str, float | None]],
) -> dict[str, float | None]:
    """Compute excess return vs each benchmark for every return window.

    benchmark_returns: {"QQQ": {"ret_5m": 0.001, ...}, "SPY": {...}}
    """
    result: dict[str, float | None] = {}
    for bench_name, bench_rets in benchmark_returns.items():
        suffix = bench_name.lower()
        for key in sym_returns:
            sym_val = sym_returns[key]
            bench_val = bench_rets.get(key)
            if sym_val is not None and bench_val is not None:
                result[f"{key}_xs_{suffix}"] = sym_val - bench_val
            else:
                result[f"{key}_xs_{suffix}"] = None
    return result
