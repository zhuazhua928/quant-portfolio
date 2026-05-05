"""Naive baselines — paper's two reference strategies.

naive-DA: Y_t = 0 always, sells in day-ahead. Profit by definition is zero
          relative to the DA benchmark.
naive-RT: Y_t = 1 always, sells in real-time. Profit relative to DA is the
          realized spread minus cost.
"""

from __future__ import annotations

import pandas as pd


def naive_da_decisions(index: pd.Index) -> pd.Series:
    return pd.Series(0, index=index, name="y_hat")


def naive_rt_decisions(index: pd.Index) -> pd.Series:
    return pd.Series(1, index=index, name="y_hat")
