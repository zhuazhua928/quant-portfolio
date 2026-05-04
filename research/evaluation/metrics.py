"""Evaluation metrics for the two-stage forecaster."""

from __future__ import annotations

import numpy as np
import pandas as pd


def directional_accuracy(y_true: pd.Series, y_pred: pd.Series) -> float:
    """Sign-match rate excluding y_true == 0."""
    a = pd.concat([y_true.rename("t"), y_pred.rename("p")], axis=1).dropna()
    a = a[a["t"] != 0]
    if a.empty:
        return float("nan")
    return float((np.sign(a["t"]) == np.sign(a["p"])).mean())


def brier_score(y_true: pd.Series, p_up: pd.Series) -> float:
    """Brier on the binary up/down outcome."""
    a = pd.concat([y_true.rename("t"), p_up.rename("p")], axis=1).dropna()
    if a.empty:
        return float("nan")
    y = (a["t"] > 0).astype(float)
    return float(((a["p"] - y) ** 2).mean())


def log_loss_binary(y_true: pd.Series, p_up: pd.Series, eps: float = 1e-9) -> float:
    a = pd.concat([y_true.rename("t"), p_up.rename("p")], axis=1).dropna()
    if a.empty:
        return float("nan")
    y = (a["t"] > 0).astype(float)
    p = a["p"].clip(eps, 1 - eps)
    return float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean())


def mae(y_true: pd.Series, y_pred: pd.Series) -> float:
    a = pd.concat([y_true.rename("t"), y_pred.rename("p")], axis=1).dropna()
    if a.empty:
        return float("nan")
    return float((a["t"] - a["p"]).abs().mean())


def information_coefficient(y_true: pd.Series, y_pred: pd.Series) -> float:
    """Spearman rank correlation between prediction and realized return."""
    a = pd.concat([y_true.rename("t"), y_pred.rename("p")], axis=1).dropna()
    if len(a) < 30:
        return float("nan")
    return float(a["t"].rank().corr(a["p"].rank()))


def summarize(y_true: pd.Series, y_pred_reg: pd.Series, p_up: pd.Series) -> dict:
    return {
        "n": int(min(len(y_true.dropna()), len(y_pred_reg.dropna()))),
        "directional_accuracy": directional_accuracy(y_true, y_pred_reg),
        "brier": brier_score(y_true, p_up),
        "log_loss": log_loss_binary(y_true, p_up),
        "mae_bps": mae(y_true, y_pred_reg) * 1e4,
        "ic": information_coefficient(y_true, y_pred_reg),
    }
