"""Bry-Boschan quarterly (BBQ) turning-point dating.

Reference: Harding & Pagan (2002), "Dissecting the cycle: a methodological
investigation", Journal of Monetary Economics 49(2). Quarterly variant.

Frozen parameters (BUILD_CONTRACT C-02):
    min_phase = 2 quarters
    min_cycle = 5 quarters (peak-to-peak and trough-to-trough)
    censor    = 2 quarters (no turning point this close to either endpoint)

The implementation works on a level series (never on growth). It returns
turning points and contraction episodes. No smoothing is applied: the DFM
factor that feeds this module is already a smooth common component.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class TurningPoint:
    quarter: str
    index: int
    kind: str          # "peak" | "trough"
    value: float

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Episode:
    peak: str
    trough: str
    peak_index: int
    trough_index: int
    duration: int          # quarters from peak to trough (trough - peak)
    depth: float           # level drop, peak -> trough
    depth_sd: float        # drop in standard deviations of the level

    def as_dict(self) -> dict:
        return asdict(self)


def _local_extrema(y: np.ndarray, k: int) -> list[tuple[int, str]]:
    """Local maxima/minima using a +/-k window."""
    n = len(y)
    out: list[tuple[int, str]] = []
    for i in range(k, n - k):
        window = y[i - k : i + k + 1]
        if not np.all(np.isfinite(window)):
            continue
        if y[i] > np.max(np.delete(window, k)):
            out.append((i, "peak"))
        elif y[i] < np.min(np.delete(window, k)):
            out.append((i, "trough"))
    return out


def _alternate(y: np.ndarray, tps: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """Collapse consecutive same-type points, keeping the more extreme one."""
    if not tps:
        return []
    out = [tps[0]]
    for idx, kind in tps[1:]:
        if kind != out[-1][1]:
            out.append((idx, kind))
            continue
        prev_idx, prev_kind = out[-1]
        keep_new = (kind == "peak" and y[idx] >= y[prev_idx]) or (kind == "trough" and y[idx] <= y[prev_idx])
        if keep_new:
            out[-1] = (idx, kind)
    return out


def _prominence(y: np.ndarray, tps: list[tuple[int, str]], i: int) -> float:
    """How much a turning point stands out relative to its direct neighbours."""
    idx, kind = tps[i]
    left = tps[i - 1][0] if i > 0 else None
    right = tps[i + 1][0] if i + 1 < len(tps) else None
    if kind == "peak":
        ref = min(y[j] for j in (left, right) if j is not None)
        return float(y[idx] - ref)
    ref = max(y[j] for j in (left, right) if j is not None)
    return float(ref - y[idx])


def _prune(
    y: np.ndarray,
    tps: list[tuple[int, str]],
    min_phase: int,
    min_cycle: int,
) -> list[tuple[int, str]]:
    """Enforce minimum phase and cycle length by dropping the weaker point."""
    tps = list(tps)
    guard = 0
    while len(tps) >= 2 and guard < 10_000:
        guard += 1
        changed = False

        # minimum phase: adjacent peak/trough legs
        for i in range(len(tps) - 1):
            if tps[i + 1][0] - tps[i][0] < min_phase:
                a = _prominence(y, tps, i) if 0 < i < len(tps) - 1 else np.inf
                b = _prominence(y, tps, i + 1) if 0 < i + 1 < len(tps) - 1 else np.inf
                drop = i if a < b else i + 1
                tps.pop(drop)
                tps = _alternate(y, tps)
                changed = True
                break

        if changed:
            continue

        # minimum cycle: same-type points two apart
        for i in range(len(tps) - 2):
            if tps[i][0] == tps[i + 2][0]:
                continue
            if tps[i + 2][0] - tps[i][0] < min_cycle:
                a = _prominence(y, tps, i)
                b = _prominence(y, tps, i + 2)
                drop = i if a < b else i + 2
                tps.pop(drop)
                tps = _alternate(y, tps)
                changed = True
                break

        if not changed:
            break
    return tps


def find_turning_points(
    level: pd.Series,
    min_phase: int = 2,
    min_cycle: int = 5,
    censor: int = 2,
    window: int = 2,
) -> list[TurningPoint]:
    """Date peaks and troughs on a quarterly level series."""
    y = level.to_numpy(dtype=float)
    n = len(y)
    tps = _local_extrema(y, window)
    tps = _alternate(y, tps)
    # inside the censored endpoints a turning point cannot be confirmed
    tps = [(i, k) for i, k in tps if censor <= i < n - censor]
    tps = _prune(y, tps, min_phase, min_cycle)
    out = []
    for i, kind in tps:
        out.append(TurningPoint(str(level.index[i]), i, kind, float(y[i])))
    return out


def contraction_episodes(
    level: pd.Series,
    tps: list[TurningPoint],
    min_phase: int = 2,
) -> list[Episode]:
    """Pair each peak with the next trough; the pair is a contraction."""
    # Depth is measured against the volatility of quarterly level changes, so it
    # reads as "how many typical quarterly moves deep is the contraction".
    sd = float(np.nanstd(level.diff().to_numpy(dtype=float)))
    out: list[Episode] = []
    for a, b in zip(tps, tps[1:]):
        if a.kind != "peak" or b.kind != "trough":
            continue
        if b.index - a.index < min_phase:
            continue
        depth = float(level.iloc[a.index] - level.iloc[b.index])
        out.append(
            Episode(
                peak=a.quarter,
                trough=b.quarter,
                peak_index=a.index,
                trough_index=b.index,
                duration=b.index - a.index,
                depth=depth,
                depth_sd=depth / sd if sd > 0 else np.nan,
            )
        )
    return out


def recession_flag(index: pd.Index, episodes: list[Episode]) -> pd.Series:
    """R_t = 1 from the quarter after the peak through the trough (NBER style)."""
    flag = pd.Series(0, index=index, dtype=int)
    for ep in episodes:
        flag.iloc[ep.peak_index + 1 : ep.trough_index + 1] = 1
    return flag


def as_frame(tps: list[TurningPoint]) -> pd.DataFrame:
    return pd.DataFrame([t.as_dict() for t in tps])


def episodes_frame(episodes: list[Episode]) -> pd.DataFrame:
    return pd.DataFrame([e.as_dict() for e in episodes])
