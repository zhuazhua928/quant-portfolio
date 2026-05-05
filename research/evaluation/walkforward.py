"""Purged walk-forward cross-validation with embargo (López de Prado).

Splits a time-ordered index into N expanding-train / fixed-test folds. Around
each test fold we apply a `embargo_days` window of training rows excluded
on both sides, preventing label leakage when forward-return targets cross
the train/test boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import numpy as np
import pandas as pd


@dataclass
class WalkForwardSplit:
    train_idx: pd.DatetimeIndex
    test_idx: pd.DatetimeIndex
    fold: int


def walk_forward_splits(
    index: pd.DatetimeIndex,
    n_splits: int = 6,
    embargo_days: int = 5,
) -> Iterator[WalkForwardSplit]:
    """Yield WalkForwardSplit objects.

    The index is divided into n_splits+1 chunks (the first is pure training,
    each subsequent chunk is a test fold). Train is everything earlier than
    the test fold, minus an embargo window immediately preceding it.
    """
    if not isinstance(index, pd.DatetimeIndex):
        index = pd.DatetimeIndex(index)
    index = index.sort_values().unique()

    n = len(index)
    if n_splits < 1 or n < (n_splits + 1) * 100:
        raise ValueError(f"index too short ({n} rows) for {n_splits} folds")

    # split rows into n_splits+1 contiguous chunks of equal size
    chunk_edges = np.linspace(0, n, n_splits + 2, dtype=int)
    embargo = pd.Timedelta(days=embargo_days)

    for k in range(n_splits):
        test_start = chunk_edges[k + 1]
        test_end = chunk_edges[k + 2]
        test_idx = pd.DatetimeIndex(index[test_start:test_end])

        train_cutoff = test_idx[0] - embargo
        train_idx = pd.DatetimeIndex(index[:test_start])
        train_idx = train_idx[train_idx < train_cutoff]

        if len(train_idx) == 0 or len(test_idx) == 0:
            continue
        yield WalkForwardSplit(train_idx=train_idx, test_idx=test_idx, fold=k)
