
import pandas as pd
import pytest

from ews.models.features import build_available_panel


def sample_panel():
    quarters = pd.period_range(
        "2025Q3", "2026Q2", freq="Q"
    )

    return pd.DataFrame(
        {
            "GDP": [100.0, 110.0, 120.0, 130.0],
            "MARKET": [10.0, 20.0, 30.0, 40.0],
        },
        index=quarters,
    )


def test_national_accounts_lag():
    panel = build_available_panel(
        sample_panel(),
        {"GDP": "NA", "MARKET": "MARKET"},
    )

    assert pd.isna(panel.loc["2025Q3", "GDP"])
    assert panel.loc["2026Q1", "GDP"] == 110.0


def test_market_current_quarter():
    panel = build_available_panel(
        sample_panel(),
        {"GDP": "NA", "MARKET": "MARKET"},
    )

    assert panel.loc["2026Q1", "MARKET"] == 30.0


def test_missing_mapping_rejected():
    with pytest.raises(ValueError):
        build_available_panel(
            sample_panel(),
            {"GDP": "NA"},
        )


def test_missing_value_not_backfilled():
    data = sample_panel()
    data.loc["2025Q4", "GDP"] = float("nan")

    panel = build_available_panel(
        data,
        {"GDP": "NA", "MARKET": "MARKET"},
    )

    assert pd.isna(panel.loc["2026Q1", "GDP"])
