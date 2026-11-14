
"""Select the latest available complete quarterly observation."""

import pandas as pd


def latest_available_quarter(quarterly_series, target_quarter):
    """Return (source_quarter, value) for the latest valid quarter.

    Missing values are skipped, but their source dates are never
    replaced with the target quarter.
    """

    target = pd.Period(target_quarter, freq="Q")

    if not isinstance(quarterly_series.index, pd.PeriodIndex):
        raise TypeError("Expected a quarterly PeriodIndex")

    if quarterly_series.index.has_duplicates:
        raise ValueError("Duplicate quarters are not allowed")

    eligible = quarterly_series.loc[
        quarterly_series.index <= target
    ].dropna()

    if eligible.empty:
        return None, float("nan")

    source_quarter = eligible.index.max()
    value = float(eligible.loc[source_quarter])

    return source_quarter, value
