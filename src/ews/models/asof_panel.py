
"""Build a latest-known-value panel at each prediction origin.

Retains the original source quarter for every selected value.
Does not create or modify official folds or labels.
"""

import pandas as pd

from ews.models.fred_loader import (
    load_fred_manifest,
    load_fred_observations,
)
from ews.models.predictor_panel import (
    LAG_OVERRIDES,
    aggregate_available,
)
from ews.models.availability_snapshot import (
    latest_available_quarter,
)


def build_asof_panel(
    start="1990Q1",
    end="2026Q3",
    manifest_path="data/manifest.csv",
    raw_root="data/raw/fred",
):
    """Return latest-known values and their source quarters."""

    manifest = load_fred_manifest(manifest_path)
    quarters = pd.period_range(start, end, freq="Q")

    values = pd.DataFrame(index=quarters)
    source_quarters = pd.DataFrame(index=quarters)

    for series_key, lag_class in LAG_OVERRIDES.items():
        observations, frequency = load_fred_observations(
            series_key,
            manifest,
            raw_root=raw_root,
        )

        selected_values = []
        selected_quarters = []

        for target in quarters:
            available = aggregate_available(
                observations,
                frequency,
                lag_class,
                target,
            )

            source, value = latest_available_quarter(
                available,
                target,
            )

            selected_values.append(value)
            selected_quarters.append(
                str(source) if source is not None else None
            )

        values[series_key] = selected_values
        source_quarters[series_key] = selected_quarters

    values.index.name = "prediction_quarter"
    source_quarters.index.name = "prediction_quarter"

    return values, source_quarters
