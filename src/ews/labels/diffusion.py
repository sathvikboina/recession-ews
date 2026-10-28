"""Episode diffusion gate (BUILD_CONTRACT C-02 step 8, §15).

Diffusion is the share of available core indicators that are deteriorating at a
given quarter. The gate keeps a contraction only if the average diffusion across
the episode is at least 0.50. This stops the label from recording a one-indicator
dip as a recession.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def deterioration_share(growth: pd.DataFrame) -> pd.Series:
    """Share of available indicators with negative activity growth, per quarter."""
    negative = (growth < 0).where(growth.notna())
    available = growth.notna()
    n_neg = negative.sum(axis=1)
    n_avail = available.sum(axis=1)
    share = n_neg / n_avail.replace(0, np.nan)
    share.name = "deterioration_share"
    return share


def episode_diffusion(growth: pd.DataFrame, peak_index: int, trough_index: int) -> float:
    """Mean deterioration share over the quarters after the peak through the trough."""
    share = deterioration_share(growth)
    window = share.iloc[peak_index + 1 : trough_index + 1].dropna()
    return float(window.mean()) if len(window) else float("nan")
