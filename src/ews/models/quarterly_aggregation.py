
"""C-06 quarterly aggregation of availability-filtered observations."""

import pandas as pd

from ews.models.raw_availability import filter_available_observations


def available_monthly_quarterly_mean(
    observations,
    lag_class,
    target_quarter,
):
    """Compute quarterly means using only published complete months.

    Returns a Series indexed by quarter. Incomplete quarters are NaN.
    """

    target = pd.Period(target_quarter, freq="Q")

    eligible = filter_available_observations(
        observations,
        frequency="M",
        lag_class=lag_class,
        target_quarter=target,
    )

    if eligible.empty:
        return pd.Series(dtype=float)

    data = eligible.copy()
    dates = pd.to_datetime(data["observation_date"])
    data["quarter"] = dates.dt.to_period("Q")
    data["month"] = dates.dt.to_period("M")
    data["value"] = pd.to_numeric(data["value"], errors="coerce")

    # Reject duplicate monthly observations rather than
    # silently counting them as separate months.
    if data["month"].duplicated().any():
        raise ValueError("Duplicate monthly observations")

    grouped = data.groupby("quarter")

    means = grouped["value"].mean()
    counts = grouped["value"].count()
    months = grouped["month"].nunique()

    complete = (counts == 3) & (months == 3)

    return means.where(complete)


def available_quarterly_values(
    observations,
    lag_class,
    target_quarter,
):
    """Return quarterly values available by the prediction origin."""

    target = pd.Period(target_quarter, freq="Q")

    eligible = filter_available_observations(
        observations,
        frequency="Q",
        lag_class=lag_class,
        target_quarter=target,
    )

    if eligible.empty:
        return pd.Series(dtype=float)

    data = eligible.copy()

    dates = pd.to_datetime(data["observation_date"])
    data["quarter"] = dates.dt.to_period("Q")
    data["value"] = pd.to_numeric(
        data["value"], errors="coerce"
    )

    if data["quarter"].duplicated().any():
        raise ValueError("Duplicate quarterly observations")

    return data.set_index("quarter")["value"].sort_index()



def available_daily_quarterly_mean(
    observations,
    lag_class,
    target_quarter,
):
    """Aggregate available daily data to quarterly means.

    Daily -> monthly mean -> quarterly mean.
    Requires observations in all three calendar months.
    """

    eligible = filter_available_observations(
        observations,
        frequency="D",
        lag_class=lag_class,
        target_quarter=target_quarter,
    )

    if eligible.empty:
        return pd.Series(dtype=float)

    data = eligible.copy()
    dates = pd.to_datetime(data["observation_date"])

    data["month"] = dates.dt.to_period("M")
    data["quarter"] = dates.dt.to_period("Q")
    data["value"] = pd.to_numeric(
        data["value"], errors="coerce"
    )

    if dates.duplicated().any():
        raise ValueError("Duplicate daily observations")

    monthly = data.groupby(["quarter", "month"])["value"].mean()

    quarterly = monthly.groupby(level="quarter").mean()
    month_counts = monthly.groupby(level="quarter").count()

    return quarterly.where(month_counts == 3)
