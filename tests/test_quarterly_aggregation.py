
import pandas as pd
import pytest
from ews.models.quarterly_aggregation import available_daily_quarterly_mean
from ews.models.quarterly_aggregation import available_quarterly_values

from ews.models.quarterly_aggregation import (
    available_monthly_quarterly_mean,
)


def test_complete_monthly_quarter():
    data = pd.DataFrame({
        "observation_date": [
            "2026-01-01",
            "2026-02-01",
            "2026-03-01",
        ],
        "value": [100.0, 110.0, 120.0],
    })

    result = available_monthly_quarterly_mean(
        data, "MONTHLY", "2026Q1"
    )

    assert result.loc["2026Q1"] == pytest.approx(110.0)


def test_incomplete_quarter_is_missing():
    data = pd.DataFrame({
        "observation_date": [
            "2026-01-01",
            "2026-03-01",
        ],
        "value": [100.0, 120.0],
    })

    result = available_monthly_quarterly_mean(
        data, "MONTHLY", "2026Q1"
    )

    assert pd.isna(result.loc["2026Q1"])


def test_unpublished_month_is_excluded():
    data = pd.DataFrame({
        "observation_date": [
            "2026-01-01",
            "2026-02-01",
            "2026-03-01",
        ],
        "value": [100.0, 110.0, 120.0],
    })

    result = available_monthly_quarterly_mean(
        data, "NA", "2026Q1"
    )

    # The quarter may exist with NaN because
    # its monthly observations are not fully published.
    quarter = pd.Period("2026Q1", freq="Q")

    if quarter in result.index:
        assert pd.isna(result.loc[quarter])
    else:
        assert result.empty


def test_duplicate_month_rejected():
    data = pd.DataFrame({
        "observation_date": [
            "2026-01-01",
            "2026-01-15",
            "2026-02-01",
            "2026-03-01",
        ],
        "value": [100.0, 105.0, 110.0, 120.0],
    })

    with pytest.raises(ValueError):
        available_monthly_quarterly_mean(
            data, "MONTHLY", "2026Q1"
        )


def test_quarterly_gdp_lag():
    data = pd.DataFrame({
        "observation_date": [
            "2025-10-01",
            "2026-01-01",
        ],
        "value": [100.0, 110.0],
    })

    result = available_quarterly_values(
        data, "NA", "2026Q1"
    )

    assert result.loc["2025Q4"] == 100.0
    assert pd.Period("2026Q1", freq="Q") not in result.index


def test_quarterly_non_na_lag():
    data = pd.DataFrame({
        "observation_date": [
            "2025-10-01",
            "2026-01-01",
        ],
        "value": [50.0, 60.0],
    })

    result = available_quarterly_values(
        data, "NA_ASSUMED", "2026Q1"
    )

    assert result.loc["2025Q4"] == 50.0
    assert pd.Period("2026Q1", freq="Q") not in result.index


def test_duplicate_quarter_rejected():
    data = pd.DataFrame({
        "observation_date": [
            "2026-01-01",
            "2026-02-01",
        ],
        "value": [100.0, 105.0],
    })

    with pytest.raises(ValueError):
        available_quarterly_values(
            data, "MARKET", "2026Q1"
        )


def test_daily_market_quarterly_mean():
    data = pd.DataFrame({
        "observation_date": [
            "2026-01-05",
            "2026-01-06",
            "2026-02-05",
            "2026-02-06",
            "2026-03-05",
            "2026-03-06",
        ],
        "value": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
    })

    result = available_daily_quarterly_mean(
        data, "MARKET", "2026Q1"
    )

    # Monthly means: 15, 35, 55
    # Quarterly mean: 35
    assert result.loc["2026Q1"] == pytest.approx(35.0)


def test_daily_market_incomplete_quarter():
    data = pd.DataFrame({
        "observation_date": [
            "2026-01-05",
            "2026-03-05",
        ],
        "value": [10.0, 30.0],
    })

    result = available_daily_quarterly_mean(
        data, "MARKET", "2026Q1"
    )

    assert pd.isna(result.loc["2026Q1"])


def test_daily_market_future_observations_excluded():
    data = pd.DataFrame({
        "observation_date": [
            "2026-01-05",
            "2026-02-05",
            "2026-03-05",
            "2026-04-05",
        ],
        "value": [10.0, 20.0, 30.0, 999.0],
    })

    result = available_daily_quarterly_mean(
        data, "MARKET", "2026Q1"
    )

    assert result.loc["2026Q1"] == pytest.approx(20.0)


def test_duplicate_daily_observations_rejected():
    data = pd.DataFrame({
        "observation_date": [
            "2026-01-05",
            "2026-01-05",
            "2026-02-05",
            "2026-03-05",
        ],
        "value": [10.0, 11.0, 20.0, 30.0],
    })

    with pytest.raises(ValueError):
        available_daily_quarterly_mean(
            data, "MARKET", "2026Q1"
        )

