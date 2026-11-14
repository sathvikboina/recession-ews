
"""Convert FRED observation dates to observation-period end dates."""

import calendar
from datetime import date

import pandas as pd


def observation_period_end(observation_date, frequency):
    """Return the end of the period represented by an observation."""

    day = pd.Timestamp(observation_date).date()

    if frequency == "D":
        return day

    if frequency == "W":
        # Weekly series require an explicitly verified
        # week-ending convention.
        raise ValueError(
            "Weekly observation-date convention must be verified"
        )

    if frequency == "M":
        last_day = calendar.monthrange(day.year, day.month)[1]
        return date(day.year, day.month, last_day)

    if frequency == "Q":
        quarter = (day.month - 1) // 3 + 1
        end_month = quarter * 3
        last_day = calendar.monthrange(day.year, end_month)[1]
        return date(day.year, end_month, last_day)

    if frequency == "A":
        return date(day.year, 12, 31)

    raise ValueError(f"Unsupported frequency: {frequency}")
