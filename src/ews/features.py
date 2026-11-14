"""Pipeline B feature table for the USA (Lane 2B).

Builds the predictor-only table from the harmonised quarterly panel.

Design rules
------------
* The input is ``data/clean/USA_panel.csv`` (already harmonised, quarterly).
* C-05 availability lags are applied **before** any transform.
* C-07 transforms come from :mod:`ews.models.feature_transforms`; no scaling,
  interpolation, forward fill or full-sample fitting happens here.
* The eight BEAI-eligible core indicators appear only as separate, clearly
  named ``beai_copy_*`` predictor copies. They are transformed independently
  from Pipeline A and share no fitted object with it.
* No label output, NBER chronology, country identifier, country-size level or
  future observation is included.

The exact per-series form and lag live in :data:`FEATURE_SPEC`. This map is the
machine-readable version of the Lane 2A specification; when the written spec
changes, change this table and regenerate.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from ews.models.feature_transforms import transform_quarterly_series
from ews.models.features import build_available_panel

DEFAULT_START = "1990Q1"
DEFAULT_END = "2026Q3"

FORBIDDEN_COLUMNS = {
    "factor",
    "level",
    "R",
    "n_available",
    "deterioration_share",
    "episode_id",
    "USA.NBER.Q",
    "country",
    "country_iso3",
}


@dataclass(frozen=True)
class SeriesSpec:
    """One input series and how it becomes predictors."""

    column: str
    name: str
    form: str
    lag_class: str
    beai_copy: bool = False


# The eight BEAI-eligible core indicators, as separate predictor copies.
BEAI_COPY_SPECS = (
    SeriesSpec("USA.ACT_GDP_REAL.Q.NA", "ACT_GDP_REAL", "growth", "NA", True),
    SeriesSpec("USA.ACT_IP.M.STD", "ACT_IP", "growth", "MONTHLY", True),
    SeriesSpec("USA.ACT_EMP.Q.NA", "ACT_EMP", "growth", "NA", True),
    SeriesSpec("USA.ACT_HOURS.Q.STD", "ACT_HOURS", "growth", "NA", True),
    SeriesSpec("USA.ACT_RINC.Q.STD", "ACT_RINC", "growth", "NA", True),
    SeriesSpec("USA.ACT_CONS.Q.NA", "ACT_CONS", "growth", "NA", True),
    SeriesSpec("USA.ACT_RETAIL.M.STD", "ACT_RETAIL", "growth", "MONTHLY", True),
    SeriesSpec("USA.ACT_INV.Q.STD", "ACT_INV", "growth", "NA", True),
)

# Predictor-only series (beai_eligible = N in data/scope.csv).
PREDICTOR_SPECS = (
    SeriesSpec("USA.FIN_CREDIT_GDP.Q.STD", "FIN_CREDIT_GDP", "ratio", "NA"),
    SeriesSpec("USA.FIN_EQUITY.M.STD", "FIN_EQUITY", "price", "MARKET"),
    SeriesSpec("USA.FIN_HOUSEPRICE.M.US_CS", "FIN_HOUSEPRICE_CS", "price", "MONTHLY"),
    SeriesSpec("USA.FIN_HOUSEPRICE.Q.OECD_BIS", "FIN_HOUSEPRICE_BIS", "price", "NA"),
    SeriesSpec("USA.FIN_LONG.M.STD", "FIN_LONG", "rate", "MARKET"),
    SeriesSpec("USA.FIN_POLICY.M.STD", "FIN_POLICY", "rate", "MARKET"),
    SeriesSpec("USA.FIN_SHORT.M.STD", "FIN_SHORT", "rate", "MARKET"),
    SeriesSpec("USA.LAB_UNEMP.M.STD", "LAB_UNEMP", "rate", "MONTHLY"),
    SeriesSpec("USA.PRC_CPI.M.STD", "PRC_CPI", "price", "MONTHLY"),
    SeriesSpec("USA.SEN_BCI.M.STD", "SEN_BCI", "survey", "SURVEY"),
    SeriesSpec("USA.SEN_CCI.M.STD", "SEN_CCI", "survey", "SURVEY"),
)

FEATURE_SPEC = BEAI_COPY_SPECS + PREDICTOR_SPECS

# Derived series must be built before availability lags are applied.
DERIVED_SPECS = (
    SeriesSpec("USA.FIN_SLOPE.M.DERIVED", "FIN_SLOPE", "spread", "MARKET"),
)

# Documented exclusions. They stay out of the table on purpose.
EXCLUSIONS = {
    "USA.ACT_EMP.M.ESTAB": "BEAI-eligible variant, near-duplicate of ACT_EMP",
    "USA.ACT_EMP.M.LFS": "BEAI-eligible variant, raw source of ACT_EMP.Q.NA",
    "USA.ACT_RINC.M.US": "BEAI-eligible variant, near-duplicate of ACT_RINC",
    "USA.ACT_INV_EQ.Q.STD": "Q-02 supporting component, not a scope predictor",
    "USA.ACT_INV_STRUCT.Q.STD": "Q-02 supporting component, not a scope predictor",
    "USA.ACT_INV_IPP.Q.STD": "Q-02 supporting component, not a scope predictor",
    "USA.ACT_INV_DEFL.Q.STD": "Q-02 supporting component, not a scope predictor",
    "USA.FIN_CREDIT_GAP.Q.STD": "not in the harmonised panel; needs an HP gap",
}


def load_panel(path: Path) -> pd.DataFrame:
    """Load the quarterly panel and index it by calendar quarter."""
    panel = pd.read_csv(path)
    if "quarter" not in panel.columns:
        raise ValueError(f"{path} has no 'quarter' column")
    index = pd.PeriodIndex(panel["quarter"].astype(str), freq="Q")
    if index.has_duplicates:
        raise ValueError("Duplicate quarters in the panel")
    if not index.is_monotonic_increasing:
        raise ValueError("Panel quarters must be sorted")
    values = panel.drop(columns=["quarter"]).astype(float)
    values.index = index
    values.index.name = "quarter"
    return values


def _feature_frame(panel: pd.DataFrame, spec: SeriesSpec) -> pd.DataFrame:
    """Apply availability lag, then the C-07 transform, for one series."""
    if spec.column not in panel.columns:
        raise KeyError(f"{spec.column} is not in the panel")
    levels = panel[[spec.column]]
    available = build_available_panel(levels, {spec.column: spec.lag_class})
    transformed = transform_quarterly_series(
        available[spec.column], spec.form
    )
    prefix = "beai_copy_" if spec.beai_copy else ""
    transformed.columns = [
        f"{prefix}{spec.name}__{column}" for column in transformed.columns
    ]
    return transformed


def build_feature_table(
    panel: pd.DataFrame,
    *,
    start: str = DEFAULT_START,
    end: str = DEFAULT_END,
    spec: tuple[SeriesSpec, ...] = FEATURE_SPEC,
) -> pd.DataFrame:
    """Return one unscaled predictor row per quarter in ``start``..``end``."""
    working = panel.copy()
    if "USA.FIN_LONG.M.STD" in working.columns and "USA.FIN_SHORT.M.STD" in working.columns:
        working["USA.FIN_SLOPE.M.DERIVED"] = (
            working["USA.FIN_LONG.M.STD"] - working["USA.FIN_SHORT.M.STD"]
        )

    frames = [_feature_frame(working, item) for item in (*spec, *DERIVED_SPECS)]
    table = pd.concat(frames, axis=1).sort_index()

    window = pd.period_range(start, end, freq="Q")
    table = table.reindex(window)
    table.index.name = "quarter"

    validate_feature_table(table, start=start, end=end)
    return table


def validate_feature_table(
    table: pd.DataFrame,
    *,
    start: str = DEFAULT_START,
    end: str = DEFAULT_END,
) -> None:
    """Fail if the table breaks the Lane 2 contract."""
    expected = pd.period_range(start, end, freq="Q")
    if len(table) != len(expected):
        raise ValueError(
            f"expected {len(expected)} rows ({start}-{end}), got {len(table)}"
        )
    if not table.index.equals(expected):
        raise ValueError("table index is not the contiguous study window")

    forbidden = FORBIDDEN_COLUMNS.intersection(table.columns)
    if forbidden:
        raise ValueError(f"forbidden columns present: {sorted(forbidden)}")

    if table.columns.duplicated().any():
        duplicates = table.columns[table.columns.duplicated()].tolist()
        raise ValueError(f"duplicate feature columns: {duplicates}")

    if not all(pd.api.types.is_numeric_dtype(table[c]) for c in table.columns):
        raise ValueError("all feature columns must be numeric")

    # A size level would be monotone with the price level over decades. Every
    # activity/price column here is a growth or change, so no column may be a
    # near-perfect exponential trend. This is a cheap guard, not a proof.
    for column in table.columns:
        series = table[column].dropna()
        if len(series) > 20 and series.gt(0).all():
            if series.iloc[-1] > 5 * series.iloc[0]:
                raise ValueError(f"{column} looks like a raw level, not a change")


def to_frame(table: pd.DataFrame) -> pd.DataFrame:
    """Return the table with a string ``quarter`` key for Parquet/CSV."""
    out = table.copy()
    out.insert(0, "quarter", out.index.astype(str))
    out.index = pd.RangeIndex(len(out))
    return out
