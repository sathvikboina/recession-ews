
import pandas as pd
import pytest

from ews.models.targets import build_peak_targets


def test_peak_within_two_quarters():
    quarters = ["2000Q3", "2000Q4", "2001Q1"]

    turning_points = pd.DataFrame({
        "quarter": ["2001Q1"],
        "kind": ["peak"],
    })

    result = build_peak_targets(
        quarters,
        turning_points,
        horizon=2,
        last_observed="2001Q3",
    )

    assert result["y_true"].tolist() == [1, 1, 0]


def test_final_quarters_are_missing():
    quarters = ["2026Q1", "2026Q2", "2026Q3"]

    turning_points = pd.DataFrame({
        "quarter": [],
        "kind": [],
    })

    result = build_peak_targets(
        quarters,
        turning_points,
        horizon=2,
        last_observed="2026Q3",
    )

    assert result.loc[0, "y_true"] == 0
    assert pd.isna(result.loc[1, "y_true"])
    assert pd.isna(result.loc[2, "y_true"])


def test_horizon_one():
    quarters = ["2000Q4", "2001Q1"]

    turning_points = pd.DataFrame({
        "quarter": ["2001Q1"],
        "kind": ["peak"],
    })

    result = build_peak_targets(
        quarters,
        turning_points,
        horizon=1,
        last_observed="2001Q2",
    )

    assert result["y_true"].tolist() == [1, 0]


def test_invalid_horizon():
    with pytest.raises(ValueError):
        build_peak_targets(
            ["2020Q1"],
            pd.DataFrame(columns=["quarter", "kind"]),
            horizon=0,
        )


def test_duplicate_quarters_rejected():
    with pytest.raises(ValueError):
        build_peak_targets(
            ["2020Q1", "2020Q1"],
            pd.DataFrame(columns=["quarter", "kind"]),
        )
