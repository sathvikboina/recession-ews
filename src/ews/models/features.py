
"""Pipeline B: conservative quarterly availability-adjusted panel.

Does not modify Pipeline A labels or official folds.
"""

from datetime import timedelta

import pandas as pd

from ews.models.publication_lags import (
    availability_date,
    quarter_end,
    prediction_origin,
)


def build_available_panel(levels, lag_mapping):
    """Select the latest fully available quarterly observation.

    The input is a harmonised quarterly panel indexed by quarters.
    For each prediction quarter, use only observations from that
    quarter or earlier whose conservative publication date has
    passed.

    No interpolation, backfill, or future-value imputation.
    """
    if not isinstance(levels.index, pd.PeriodIndex):
        raise TypeError("levels must have a PeriodIndex")

    if not levels.index.is_unique:
        raise ValueError("Duplicate quarters are not allowed")

    if not levels.index.is_monotonic_increasing:
        raise ValueError("Quarters must be sorted")

    missing = set(levels.columns) - set(lag_mapping)
    if missing:
        raise ValueError(f"Missing lag mappings: {sorted(missing)}")

    available = pd.DataFrame(
        index=levels.index,
        columns=levels.columns,
        dtype=float,
    )

    for target_q in levels.index:
        cutoff = quarter_end(target_q.year, target_q.quarter)
        origin = prediction_origin(target_q.year, target_q.quarter)

        historical = levels.loc[levels.index <= target_q]

        for column in levels.columns:
            lag_class = lag_mapping[column]

            for source_q in reversed(historical.index):
                observation_end = quarter_end(
                    source_q.year, source_q.quarter
                )

                if observation_end > cutoff:
                    continue

                published = availability_date(
                    observation_end, lag_class
                )

                if published <= origin:
                    value = levels.at[source_q, column]

                    if pd.notna(value):
                        available.at[target_q, column] = value

                    break

    return available
