
import pandas as pd
import pytest

from ews.models.availability_snapshot import (
    latest_available_quarter,
)


def test_latest_available_quarter():
    data = pd.Series(
        [100.0, 110.0],
        index=pd.period_range("2025Q3", "2025Q4", freq="Q"),
    )

    quarter, value = latest_available_quarter(
        data, "2026Q1"
    )

    assert quarter == pd.Period("2025Q4", freq="Q")
    assert value == pytest.approx(110.0)


def test_missing_latest_quarter_skipped():
    data = pd.Series(
        [100.0, float("nan")],
        index=pd.period_range("2025Q3", "2025Q4", freq="Q"),
    )

    quarter, value = latest_available_quarter(
        data, "2026Q1"
    )

    assert quarter == pd.Period("2025Q3", freq="Q")
    assert value == pytest.approx(100.0)


def test_future_quarter_excluded():
    data = pd.Series(
        [100.0, 999.0],
        index=pd.period_range("2026Q1", "2026Q2", freq="Q"),
    )

    quarter, value = latest_available_quarter(
        data, "2026Q1"
    )

    assert quarter == pd.Period("2026Q1", freq="Q")
    assert value == pytest.approx(100.0)


def test_no_available_quarter():
    data = pd.Series(
        [float("nan")],
        index=pd.period_range("2026Q1", "2026Q1", freq="Q"),
    )

    quarter, value = latest_available_quarter(
        data, "2026Q1"
    )

    assert quarter is None
    assert pd.isna(value)


def test_duplicate_quarters_rejected():
    data = pd.Series(
        [100.0, 110.0],
        index=pd.PeriodIndex(
            ["2025Q4", "2025Q4"], freq="Q"
        ),
    )

    with pytest.raises(ValueError):
        latest_available_quarter(
            data, "2026Q1"
        )
