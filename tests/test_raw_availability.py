
import pandas as pd

from ews.models.raw_availability import (
    filter_available_observations,
)


def test_quarterly_gdp_excludes_current_quarter():
    data = pd.DataFrame({
        "observation_date": [
            "2025-10-01",
            "2026-01-01",
        ],
        "value": [100.0, 110.0],
    })

    result = filter_available_observations(
        data, "Q", "NA", "2026Q1"
    )

    assert result["value"].tolist() == [100.0]


def test_monthly_industrial_production():
    data = pd.DataFrame({
        "observation_date": [
            "2026-01-01",
            "2026-02-01",
            "2026-03-01",
        ],
        "value": [100.0, 101.0, 102.0],
    })

    result = filter_available_observations(
        data, "M", "MONTHLY", "2026Q1"
    )

    assert result["value"].tolist() == [
        100.0, 101.0, 102.0
    ]


def test_daily_market_excludes_post_quarter_data():
    data = pd.DataFrame({
        "observation_date": [
            "2026-03-31",
            "2026-04-01",
        ],
        "value": [200.0, 300.0],
    })

    result = filter_available_observations(
        data, "D", "MARKET", "2026Q1"
    )

    assert result["value"].tolist() == [200.0]


def test_monthly_data_not_yet_published():
    data = pd.DataFrame({
        "observation_date": [
            "2026-03-01",
        ],
        "value": [100.0],
    })

    result = filter_available_observations(
        data, "M", "NA", "2026Q1"
    )

    assert result.empty
