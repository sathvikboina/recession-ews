
import numpy as np
import pandas as pd
import pytest

from ews.models.asof_features import (
    features_at_origin,
)


def test_gdp_growth_uses_source_quarters():
    history = pd.Series(
        [100.0, 110.0, 121.0],
        index=pd.period_range(
            "2025Q2", periods=3, freq="Q"
        ),
    )

    features, source = features_at_origin(
        history, "growth", "2026Q1"
    )

    assert source == pd.Period("2025Q4", freq="Q")
    assert features["qoq_growth"] == pytest.approx(
        100 * np.log(121.0 / 110.0)
    )


def test_missing_quarter_not_compressed():
    history = pd.Series(
        [100.0, 121.0],
        index=pd.PeriodIndex(
            ["2025Q2", "2025Q4"], freq="Q"
        ),
    )

    features, source = features_at_origin(
        history, "growth", "2026Q1"
    )

    assert source == pd.Period("2025Q4", freq="Q")
    assert pd.isna(features["qoq_growth"])


def test_future_source_excluded():
    history = pd.Series(
        [100.0, 110.0, 999.0],
        index=pd.PeriodIndex(
            ["2025Q3", "2025Q4", "2026Q2"],
            freq="Q",
        ),
    )

    features, source = features_at_origin(
        history, "growth", "2026Q1"
    )

    assert source == pd.Period("2025Q4", freq="Q")
    assert features["qoq_growth"] == pytest.approx(
        100 * np.log(110.0 / 100.0)
    )


def test_empty_history():
    history = pd.Series(
        dtype=float,
        index=pd.PeriodIndex([], freq="Q"),
    )

    features, source = features_at_origin(
        history, "growth", "2026Q1"
    )

    assert features == {}
    assert source is None
