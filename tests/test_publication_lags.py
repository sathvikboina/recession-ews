
from datetime import date, timedelta

import pytest

from ews.models.publication_lags import (
    availability_date,
    prediction_origin,
    quarter_end,
    is_available,
)


def test_quarter_end():
    assert quarter_end(2026, 1) == date(2026, 3, 31)


def test_prediction_origin():
    assert prediction_origin(2026, 1) == (
        date(2026, 3, 31) + timedelta(weeks=6)
    )


def test_monthly_six_week_lag():
    assert availability_date(
        date(2026, 3, 31), "MONTHLY"
    ) == date(2026, 5, 12)


def test_survey_four_week_lag():
    assert availability_date(
        date(2026, 3, 31), "SURVEY"
    ) == date(2026, 4, 28)


def test_market_zero_lag():
    assert availability_date(
        date(2026, 3, 31), "MARKET"
    ) == date(2026, 3, 31)


def test_national_accounts_quarter_lag():
    assert availability_date(
        date(2026, 3, 31), "NA"
    ) == date(2026, 6, 30)


def test_annual_one_year_lag():
    assert availability_date(
        date(2025, 12, 31), "ANNUAL"
    ) == date(2026, 12, 31)


def test_future_observation_rejected():
    assert not is_available(
        date(2026, 4, 15),
        "MARKET",
        prediction_origin(2026, 1),
        quarter_end(2026, 1),
    )


def test_unpublished_observation_rejected():
    assert not is_available(
        date(2026, 3, 31),
        "NA",
        prediction_origin(2026, 1),
        quarter_end(2026, 1),
    )


def test_available_monthly_observation():
    assert is_available(
        date(2026, 2, 28),
        "MONTHLY",
        prediction_origin(2026, 1),
        quarter_end(2026, 1),
    )


def test_unknown_lag_class_rejected():
    with pytest.raises(ValueError):
        availability_date(date(2026, 3, 31), "DERIVED")

def test_quarterly_non_na_lag():
    assert availability_date(
        date(2026, 3, 31),
        "NA_ASSUMED",
    ) == date(2026, 6, 30)
