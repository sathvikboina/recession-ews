
import numpy as np
import pandas as pd
import pytest

from ews.models.feature_transforms import (
    transform_quarterly_series,
)


def make_series(values, start="2020Q1"):
    index = pd.period_range(
        start, periods=len(values), freq="Q"
    )
    return pd.Series(values, index=index)


def test_growth_features():
    series = make_series(
        [100, 110, 121, 133.1, 146.41]
    )

    result = transform_quarterly_series(
        series, "growth"
    )

    assert result.loc[
        "2020Q2", "qoq_growth"
    ] == pytest.approx(100 * np.log(1.1))

    assert result.loc[
        "2021Q1", "yoy_growth"
    ] == pytest.approx(100 * np.log(146.41 / 100))


def test_missing_quarter_not_compressed():
    series = pd.Series(
        [100.0, 121.0],
        index=pd.PeriodIndex(
            ["2020Q1", "2020Q3"], freq="Q"
        ),
    )

    result = transform_quarterly_series(
        series, "growth"
    )

    assert pd.isna(
        result.loc["2020Q3", "qoq_growth"]
    )


def test_rate_change():
    series = make_series(
        [2.0, 2.5, 3.0, 3.5, 4.0]
    )

    result = transform_quarterly_series(
        series, "rate"
    )

    assert result.loc[
        "2021Q1", "change_4q"
    ] == pytest.approx(2.0)


def test_ratio_change_8q():
    series = make_series(list(range(10)))

    result = transform_quarterly_series(
        series, "ratio"
    )

    assert result.loc[
        "2022Q1", "change_8q"
    ] == pytest.approx(8.0)


def test_reject_duplicate_quarters():
    series = pd.Series(
        [100.0, 110.0],
        index=pd.PeriodIndex(
            ["2020Q1", "2020Q1"], freq="Q"
        ),
    )

    with pytest.raises(ValueError):
        transform_quarterly_series(
            series, "growth"
        )


def test_reject_unknown_form():
    series = make_series([100.0, 110.0])

    with pytest.raises(ValueError):
        transform_quarterly_series(
            series, "unknown"
        )
