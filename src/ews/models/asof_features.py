
"""Compute C-07 features using publication-available source histories."""

import pandas as pd

from ews.models.feature_transforms import (
    transform_quarterly_series,
)
from ews.models.availability_snapshot import (
    latest_available_quarter,
)


def features_at_origin(
    quarterly_history,
    form,
    target_quarter,
):
    """Compute features from a source-quarter-aligned history.

    quarterly_history must already be filtered for publication
    availability at the target prediction origin.

    Returns (feature_values, source_quarter).
    """

    target = pd.Period(target_quarter, freq="Q")

    if not isinstance(quarterly_history.index, pd.PeriodIndex):
        raise TypeError("Expected a quarterly PeriodIndex")

    # Prevent observations from future source quarters.
    history = quarterly_history.loc[
        quarterly_history.index <= target
    ].sort_index()

    source_quarter, _ = latest_available_quarter(
        history,
        target,
    )

    if source_quarter is None:
        return {}, None

    transformed = transform_quarterly_series(
        history,
        form,
    )

    # Select the latest available source quarter, not the
    # prediction quarter.
    features = transformed.loc[source_quarter].to_dict()

    return features, source_quarter

