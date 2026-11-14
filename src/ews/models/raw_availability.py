
"""Filter raw observations using C-05 publication rules."""

import pandas as pd

from ews.models.observation_dates import observation_period_end
from ews.models.publication_lags import (
    availability_date,
    prediction_origin,
    quarter_end,
)


def filter_available_observations(
    observations,
    frequency,
    lag_class,
    target_quarter,
):
    """Return observations available at a prediction origin.

    The observation period must end no later than the target
    quarter, and its assumed publication date must be no later
    than quarter-end plus six weeks.
    """

    target = pd.Period(target_quarter, freq="Q")

    cutoff = quarter_end(target.year, target.quarter)
    origin = prediction_origin(target.year, target.quarter)

    required = {"observation_date", "value"}

    if not required.issubset(observations.columns):
        raise ValueError(
            "Expected observation_date and value columns"
        )

    data = observations.copy()

    data["period_end"] = data["observation_date"].apply(
        lambda day: observation_period_end(day, frequency)
    )

    data["available_on"] = data["period_end"].apply(
        lambda day: availability_date(day, lag_class)
    )

    eligible = (
        (data["period_end"] <= cutoff)
        & (data["available_on"] <= origin)
    )

    return data.loc[eligible].copy()
