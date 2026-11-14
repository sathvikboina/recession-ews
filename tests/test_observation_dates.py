
from datetime import date

import pytest

from ews.models.observation_dates import observation_period_end


def test_monthly_period_end():
    assert observation_period_end(
        "2026-03-01", "M"
    ) == date(2026, 3, 31)


def test_quarterly_period_end():
    assert observation_period_end(
        "2026-01-01", "Q"
    ) == date(2026, 3, 31)


def test_daily_period_end():
    assert observation_period_end(
        "2026-03-27", "D"
    ) == date(2026, 3, 27)


def test_annual_period_end():
    assert observation_period_end(
        "2025-01-01", "A"
    ) == date(2025, 12, 31)


def test_unknown_frequency_rejected():
    with pytest.raises(ValueError):
        observation_period_end(
            "2026-03-01", "UNKNOWN"
        )


def test_weekly_requires_verified_convention():
    with pytest.raises(ValueError):
        observation_period_end(
            "2026-03-01", "W"
        )
