
"""C-07 feature transformations.

Input must be a source-quarter-indexed quarterly series.
No scaling, interpolation, or forward filling is performed.
"""

import numpy as np
import pandas as pd


def transform_quarterly_series(series, form):
    """Create unscaled quarterly features for one indicator."""

    if not isinstance(series.index, pd.PeriodIndex):
        raise TypeError("Expected a quarterly PeriodIndex")

    if series.index.has_duplicates:
        raise ValueError("Duplicate quarters are not allowed")

    if not series.index.is_monotonic_increasing:
        raise ValueError("Quarters must be sorted")

    if series.index.freqstr != "Q-DEC":
        raise ValueError("Expected calendar quarters")

    values = pd.to_numeric(series, errors="coerce").astype(float)

    # Reindex to the full quarterly calendar so shifts always
    # represent actual calendar quarters.
    calendar = pd.period_range(
        values.index.min(),
        values.index.max(),
        freq="Q",
    )
    values = values.reindex(calendar)

    result = pd.DataFrame(index=calendar)

    if form == "growth":
        positive = values.where(values > 0)
        log_values = np.log(positive)

        base = 100 * log_values.diff(1)

        result["qoq_growth"] = base
        result["yoy_growth"] = 100 * log_values.diff(4)

    elif form == "price":
        positive = values.where(values > 0)
        log_values = np.log(positive)

        base = 100 * log_values.diff(1)

        result["qoq_log_change"] = base
        result["yoy_log_change"] = 100 * log_values.diff(4)

    elif form in {"rate", "spread", "survey"}:
        base = values

        result["level"] = values
        result["change_4q"] = values.diff(4)

    elif form == "ratio":
        base = values

        result["level"] = values
        result["change_4q"] = values.diff(4)
        result["change_8q"] = values.diff(8)

    else:
        raise ValueError(f"Unsupported form: {form}")

    for lag in (1, 2, 4):
        result[f"base_lag_{lag}"] = base.shift(lag)

    result["rolling_mean_4q"] = base.rolling(
        window=4, min_periods=4
    ).mean()

    result["rolling_volatility_4q"] = base.rolling(
        window=4, min_periods=4
    ).std()

    if form == "growth":
        result["trend_4q"] = base.rolling(
            window=4, min_periods=4
        ).apply(
            lambda x: np.polyfit(
                np.arange(4), x, 1
            )[0],
            raw=True,
        )

    return result
