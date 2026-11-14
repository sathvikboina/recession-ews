
"""Forward-looking recession peak prediction targets.

Uses the approved reporting window and BEAI turning points.
Does not modify or overwrite frozen label artifacts.
"""

from __future__ import annotations

import pandas as pd


def build_peak_targets(
    quarters,
    turning_points,
    horizon=2,
    last_observed="2026Q3",
):
    """Label whether a peak occurs in the next H quarters."""

    if horizon <= 0:
        raise ValueError("horizon must be positive")

    periods = pd.PeriodIndex(
        quarters, freq="Q"
    )

    if periods.has_duplicates:
        raise ValueError("Duplicate quarters")

    if not periods.is_monotonic_increasing:
        raise ValueError("Quarters must be sorted")

    last = pd.Period(last_observed, freq="Q")

    peaks = turning_points.loc[
        turning_points["kind"] == "peak",
        "quarter",
    ]

    peak_periods = set(
        pd.PeriodIndex(peaks, freq="Q")
    )

    targets = []

    for quarter in periods:
        if quarter + horizon > last:
            targets.append(pd.NA)
            continue

        future = [
            quarter + step
            for step in range(1, horizon + 1)
        ]

        targets.append(
            int(any(p in peak_periods for p in future))
        )

    return pd.DataFrame(
        {
            "quarter": periods.astype(str),
            "y_true": pd.array(targets, dtype="Int64"),
        }
    )
