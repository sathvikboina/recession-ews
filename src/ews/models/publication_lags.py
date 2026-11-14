
"""C-05 publication availability rules for Pipeline B.

Pipeline A (BEAI label construction) is not modified.
This module does not generate or freeze official folds.
"""

from datetime import date, datetime, timedelta
import calendar


LAG_CLASSES = {
    "NA": ("months", 3),
    "NA_ASSUMED": ("months", 3),
    "MONTHLY": ("weeks", 6),
    "MARKET": ("days", 0),
    "SURVEY": ("weeks", 4),
    "ANNUAL": ("months", 12),
}

def add_months(day: date, months: int) -> date:
    """Add calendar months, preserving a valid day."""
    month_index = day.year * 12 + day.month - 1 + months
    year, month_zero = divmod(month_index, 12)
    month = month_zero + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(day.day, last_day))


def availability_date(observation_date, lag_class):
    """Compute conservative availability from an observation date.

    Only explicitly mapped classes are accepted.
    """
    if isinstance(observation_date, datetime):
        observation_date = observation_date.date()

    if not isinstance(observation_date, date):
        raise TypeError("observation_date must be a date")

    if lag_class not in LAG_CLASSES:
        raise ValueError(
            f"Unresolved lag class: {lag_class}. "
            "Check the approved C-05 mapping."
        )

    unit, amount = LAG_CLASSES[lag_class]

    if unit == "months":
        return add_months(observation_date, amount)

    if unit == "weeks":
        return observation_date + timedelta(weeks=amount)

    return observation_date + timedelta(days=amount)


def quarter_end(year, quarter):
    """Return the last date of a calendar quarter."""
    if quarter not in (1, 2, 3, 4):
        raise ValueError("quarter must be 1, 2, 3 or 4")

    month = quarter * 3
    day = calendar.monthrange(year, month)[1]
    return date(year, month, day)


def prediction_origin(year, quarter):
    """C-05 prediction origin: quarter-end plus six weeks."""
    return quarter_end(year, quarter) + timedelta(weeks=6)


def is_available(
    observation_date,
    lag_class,
    origin,
    observation_cutoff,
):
    """Require both observation and availability cutoffs."""
    if isinstance(observation_date, datetime):
        observation_date = observation_date.date()

    if observation_date > observation_cutoff:
        return False

    return availability_date(observation_date, lag_class) <= origin
