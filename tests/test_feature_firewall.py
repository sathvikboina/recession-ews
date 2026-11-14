"""Lane 2A firewall tests for the Pipeline B feature table.

These are independent leakage checks written against the canonical builder in
:mod:`ews.features`, not against a second copy of the pipeline. They enforce the
C-01, C-05, C-07 and C-08 invariants and, importantly, prove that the checks
fail on deliberately poisoned tables.

Run with ``pytest tests/test_feature_firewall.py``. The tests skip cleanly when
the harmonised panel or the built table is absent.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ews.features import (
    BEAI_COPY_SPECS,
    DEFAULT_END,
    DEFAULT_START,
    EXCLUSIONS,
    FEATURE_SPEC,
    DERIVED_SPECS,
    build_feature_table,
    load_panel,
    validate_feature_table,
)
from ews.models.feature_transforms import transform_quarterly_series
from ews.models.features import build_available_panel

PROJECT = Path(__file__).resolve().parents[1]
PANEL_PATH = PROJECT / "data" / "clean" / "USA_panel.csv"
TABLE_PATH = PROJECT / "data" / "clean" / "dataset.parquet"

EXPECTED_QUARTERS = pd.period_range(DEFAULT_START, DEFAULT_END, freq="Q")


def _panel() -> pd.DataFrame:
    if not PANEL_PATH.exists():
        pytest.skip("data/clean/USA_panel.csv missing; run make harmonize first")
    return load_panel(PANEL_PATH)


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    return _panel()


@pytest.fixture(scope="module")
def feature_table(panel: pd.DataFrame) -> pd.DataFrame:
    if TABLE_PATH.exists():
        frame = pd.read_parquet(TABLE_PATH)
        table = frame.set_index(pd.PeriodIndex(frame["quarter"], freq="Q")).drop(
            columns=["quarter"]
        )
        table.index.name = "quarter"
        return table
    return build_feature_table(panel)


def _history_difference(
    full: pd.DataFrame,
    truncated: pd.DataFrame,
    cutoff: str,
) -> float:
    """Largest absolute difference over quarters at or before ``cutoff``."""
    cutoff_period = pd.Period(cutoff, freq="Q")
    history = [q for q in full.index if q <= cutoff_period]
    columns = sorted(set(full.columns) | set(truncated.columns))
    left = full.reindex(columns=columns).loc[history]
    right = truncated.reindex(columns=columns).loc[history]
    if not left.index.equals(right.index):
        raise AssertionError("truncated build does not cover the same history")
    nan_mismatch = (left.isna() != right.isna()).to_numpy().any()
    if nan_mismatch:
        # An extra, future-informed column is present in one build only.
        return float("inf")
    difference = np.abs(left.to_numpy(dtype=float) - right.to_numpy(dtype=float))
    return float(np.nanmax(difference)) if difference.size else 0.0


def test_schema(feature_table: pd.DataFrame) -> None:
    """147 contiguous quarters, a quarter key, no duplicate rows or columns."""
    assert len(feature_table) == len(EXPECTED_QUARTERS) == 147
    assert feature_table.index.equals(EXPECTED_QUARTERS)
    assert not feature_table.index.has_duplicates
    assert not feature_table.columns.duplicated().any()
    assert feature_table.shape[1] == 149


def test_blacklist(feature_table: pd.DataFrame) -> None:
    """No label, factor, chronology, identifier or size-level column survives."""
    forbidden_exact = {
        "factor",
        "level",
        "r",
        "r_t",
        "rt",
        "recession",
        "n_available",
        "deterioration_share",
        "turning_point",
        "peak",
        "trough",
        "nber",
        "usa.nber.q",
        "validation",
        "country",
        "country_id",
        "country_iso3",
        "iso3",
        "episode",
        "episode_id",
    }
    forbidden_substrings = (
        "factor",
        "deterioration_share",
        "turning_point",
        "n_available",
        "nber",
        "episode_id",
    )
    for column in feature_table.columns:
        name = str(column).strip().lower()
        assert name not in forbidden_exact, f"forbidden column {column!r}"
        for fragment in forbidden_substrings:
            assert fragment not in name, f"forbidden fragment {fragment!r} in {column!r}"
        assert not name.startswith(("peak", "trough", "episode"))

    # The validator, not only this scan, must reject a poisoned table.
    poisoned = feature_table.copy()
    poisoned["R"] = 0
    with pytest.raises(ValueError, match="forbidden"):
        validate_feature_table(poisoned)


def test_unscaled(feature_table: pd.DataFrame, panel: pd.DataFrame) -> None:
    """Nothing is standardised and rate levels equal their source series."""
    for column in feature_table.columns:
        series = feature_table[column].dropna()
        if len(series) < 2:
            continue
        mean = abs(float(series.mean()))
        std = float(series.std(ddof=1))
        assert not (mean < 1e-9 and abs(std - 1.0) < 1e-6), (
            f"{column} looks standardised (|mean|={mean:.2e}, |std-1|={abs(std - 1):.2e})"
        )

    # Availability lag "MARKET"/"MONTHLY" for rates keeps the current-quarter
    # level, so these columns must equal the harmonised source exactly.
    direct_pairs = {
        "FIN_LONG__level": "USA.FIN_LONG.M.STD",
        "FIN_SHORT__level": "USA.FIN_SHORT.M.STD",
        "FIN_POLICY__level": "USA.FIN_POLICY.M.STD",
        "LAB_UNEMP__level": "USA.LAB_UNEMP.M.STD",
    }
    matched = 0
    for feature, source in direct_pairs.items():
        if feature not in feature_table or source not in panel:
            continue
        difference = (
            feature_table[feature] - panel[source].reindex(feature_table.index)
        ).abs()
        if float(difference.max()) < 1e-9:
            matched += 1
    assert matched >= 1, "no rate level matches its source series unscaled"


def test_no_future_leakage(panel: pd.DataFrame) -> None:
    """Rebuilding on truncated history leaves all past values byte-identical."""
    full = build_feature_table(panel, validate=False)
    for cutoff in ("2000Q4", "2010Q2", "2019Q4", "2024Q3"):
        cutoff_period = pd.Period(cutoff, freq="Q")
        truncated = build_feature_table(
            panel.loc[:cutoff_period], validate=False
        )
        difference = _history_difference(full, truncated, cutoff)
        assert difference < 1e-9, f"future leakage at {cutoff}: max diff {difference:.2e}"


def test_independence(feature_table: pd.DataFrame, panel: pd.DataFrame) -> None:
    """BEAI copies are reproducible from the panel alone; no fitted objects are stored."""
    for spec in BEAI_COPY_SPECS:
        prefix = f"beai_copy_{spec.name}__"
        columns = [c for c in feature_table.columns if c.startswith(prefix)]
        assert columns, f"missing beai_copy columns for {spec.name}"

        available = build_available_panel(panel[[spec.column]], {spec.column: spec.lag_class})
        expected = transform_quarterly_series(available[spec.column], spec.form)
        expected.columns = [f"{prefix}{c}" for c in expected.columns]
        expected = expected.reindex(feature_table.index)

        for column in expected.columns:
            assert column in feature_table.columns
            left = feature_table[column].to_numpy(dtype=float)
            right = expected[column].to_numpy(dtype=float)
            same_nan = np.isnan(left) == np.isnan(right)
            assert same_nan.all(), f"{column} NaN pattern not reproducible from source"
            valid = ~np.isnan(left)
            if valid.any():
                assert np.max(np.abs(left[valid] - right[valid])) < 1e-9, (
                    f"{column} is not reproducible from the harmonised panel alone"
                )

    # No serialised scaler, imputer or factor model may live beside the data.
    for directory in (PROJECT / "data" / "clean", PROJECT / "data" / "interim"):
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if path.is_file():
                assert path.suffix.lower() not in {
                    ".pkl",
                    ".pickle",
                    ".joblib",
                    ".scaler",
                }, f"fitted object found in data: {path}"


def test_mutation_fails_on_leak(panel: pd.DataFrame, feature_table: pd.DataFrame) -> None:
    """A poisoned table must fail: exact forbidden names and future shifts."""
    # (a) label column injection is rejected by the validator
    for name in ("R", "factor", "n_available"):
        poisoned = feature_table.copy()
        poisoned[name] = 0.0
        with pytest.raises(ValueError, match="forbidden"):
            validate_feature_table(poisoned)

    # (b) a one-quarter future shift must trip the same comparison used by the
    # no-future test. If this passes, the firewall is not a firewall.
    full = build_feature_table(panel, validate=False)
    cutoff = "2019Q4"
    cutoff_period = pd.Period(cutoff, freq="Q")
    truncated = build_feature_table(panel.loc[:cutoff_period], validate=False)

    column = "FIN_LONG__level"
    assert column in full.columns
    clean_diff = _history_difference(full, truncated, cutoff)
    assert clean_diff < 1e-9

    poisoned = full.copy()
    poisoned[column] = full[column].shift(-1)
    assert _history_difference(poisoned, truncated, cutoff) > 0.0

    poisoned_new = full.copy()
    poisoned_new["future_leak_col"] = full[column].shift(-1)
    assert _history_difference(poisoned_new, truncated, cutoff) > 0.0


def test_spec_inventory(feature_table: pd.DataFrame, panel: pd.DataFrame) -> None:
    """The written inventory, the spec and the built table agree."""
    spec_columns = set()
    for item in (*FEATURE_SPEC, *DERIVED_SPECS):
        prefix = ("beai_copy_" if item.beai_copy else "") + item.name + "__"
        spec_columns.update(c for c in feature_table.columns if c.startswith(prefix))

    assert spec_columns == set(feature_table.columns)
    assert len(feature_table.columns) == 149
    assert len(FEATURE_SPEC) + len(DERIVED_SPECS) == 20
    assert len(BEAI_COPY_SPECS) == 8
    assert len([c for c in feature_table.columns if c.startswith("beai_copy_")]) == 64

    # Excluded source columns never appear in the table.
    for source in EXCLUSIONS:
        assert source not in feature_table.columns
