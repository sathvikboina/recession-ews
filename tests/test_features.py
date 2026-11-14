#!/usr/bin/env python3
"""tests/test_features.py

Lane 2A Firewall Test Suite: Exactly the six required tests enforcing
Rule C-01, C-05, C-07 and C-08 invariants against the feature builder and dataset.
"""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

import importlib

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

features_mod = importlib.import_module("06_features")
build_features = features_mod.build_features
validate_table = features_mod.validate_table

DATA_DIR = PROJECT / "data"
CLEAN_DIR = DATA_DIR / "clean"
FEATURES_DIR = DATA_DIR / "features"


@pytest.fixture(scope="module")
def panel_data():
    panel_path = CLEAN_DIR / "USA_panel.csv"
    if not panel_path.exists():
        pytest.skip("data/clean/USA_panel.csv does not exist; run make harmonize first")
    return pd.read_csv(panel_path)


@pytest.fixture(scope="module")
def growth_data():
    growth_path = CLEAN_DIR / "USA_growth.parquet"
    if not growth_path.exists():
        pytest.skip("data/clean/USA_growth.parquet does not exist; run make harmonize first")
    return pd.read_parquet(growth_path)


@pytest.fixture(scope="module")
def feature_table(panel_data, growth_data):
    dataset_path = FEATURES_DIR / "dataset.parquet"
    if dataset_path.exists():
        return pd.read_parquet(dataset_path)
    return build_features(panel_data, growth_data)


def test_schema(feature_table):
    """Test 1: 147 rows, key 'quarter', contiguous 1990Q1-2026Q3, no duplicates."""
    df = feature_table
    assert len(df) == 147, f"Expected exactly 147 rows, got {len(df)}"

    assert "quarter" in df.columns, "Key 'quarter' must be present in feature table"
    quarters = df["quarter"].astype(str).tolist()

    expected_quarters = [str(q) for q in pd.period_range("1990Q1", "2026Q3", freq="Q")]
    assert quarters == expected_quarters, "Quarters must be contiguous 1990Q1-2026Q3"
    assert len(set(quarters)) == 147, "No duplicate quarter keys allowed"


def test_blacklist(feature_table):
    """Test 2: No forbidden column or prefix appears (case-insensitive scan)."""
    df = feature_table
    forbidden_exact = {
        "factor", "level", "r", "r_t", "rt", "recession", "n_available",
        "deterioration_share", "turning_point", "peak", "trough", "nber",
        "validation", "usa_validation", "country_id", "country", "iso3",
        "episode_id", "episode"
    }
    forbidden_substrings = [
        "factor", "deterioration_share", "turning_point", "n_available",
        "nber", "usa_validation", "episode_id"
    ]

    for col in df.columns:
        col_lower = str(col).strip().lower()
        assert col_lower not in forbidden_exact, f"Forbidden exact column name: '{col}'"
        for sub in forbidden_substrings:
            assert sub not in col_lower, f"Forbidden substring '{sub}' found in column '{col}'"
        assert col_lower != "r" and not col_lower.startswith("r_"), f"Recession label indicator found: '{col}'"
        assert not col_lower.startswith("peak") and not col_lower.startswith("trough"), f"Turning point column found: '{col}'"


def test_unscaled(feature_table, panel_data):
    """Test 3: No column standardized (mean~0, std~1) and at least one equals source series."""
    df = feature_table
    numeric_cols = [c for c in df.columns if c != "quarter"]

    for col in numeric_cols:
        s = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(s) > 1:
            m = abs(float(s.mean()))
            std = float(s.std(ddof=1))
            assert not (m < 1e-9 and abs(std - 1.0) < 1e-6), (
                f"Column '{col}' appears standardized (|mean|={m:.2e}, |std-1|={abs(std-1.0):.2e})"
            )

    # At least one column's values must equal the source series values directly
    panel_df = panel_data.copy()
    if "quarter" in panel_df.columns:
        panel_df = panel_df.set_index("quarter")

    df_aligned = df.set_index("quarter")

    # rate_long (GS10) in feature table should match source USA.FIN_LONG.M.STD exactly
    matched_source_count = 0
    if "rate_long" in df_aligned.columns and "USA.FIN_LONG.M.STD" in panel_df.columns:
        common_q = df_aligned.index.intersection(panel_df.index)
        diff = np.abs(df_aligned.loc[common_q, "rate_long"] - panel_df.loc[common_q, "USA.FIN_LONG.M.STD"])
        if np.nanmax(diff) < 1e-6:
            matched_source_count += 1

    if "unemp" in df_aligned.columns and "USA.LAB_UNEMP.M.STD" in panel_df.columns:
        common_q = df_aligned.index.intersection(panel_df.index)
        diff = np.abs(df_aligned.loc[common_q, "unemp"] - panel_df.loc[common_q, "USA.LAB_UNEMP.M.STD"])
        if np.nanmax(diff) < 1e-6:
            matched_source_count += 1

    assert matched_source_count >= 1, "At least one column must equal source series unscaled"


def test_no_future_leakage(panel_data, growth_data):
    """Test 4: For several cutoffs t, build_features(..., cutoff=t) equals full table at <= t."""
    full_table = build_features(panel_data, growth_data)
    full_df = full_table.set_index("quarter")

    test_cutoffs = ["2000Q4", "2010Q2", "2019Q4", "2024Q3"]

    for cutoff in test_cutoffs:
        truncated_table = build_features(panel_data, growth_data, cutoff=cutoff)
        trunc_df = truncated_table.set_index("quarter")

        cutoff_period = pd.Period(cutoff, freq="Q")
        history_quarters = [
            q for q in trunc_df.index
            if pd.Period(q, freq="Q") <= cutoff_period and pd.Period(q, freq="Q") >= pd.Period("1990Q1", freq="Q")
        ]

        for col in full_df.columns:
            s_full = full_df.loc[history_quarters, col]
            s_trunc = trunc_df.loc[history_quarters, col]

            # Both should match (accounting for NaNs)
            both_nan = s_full.isna() & s_trunc.isna()
            valid = ~both_nan
            if valid.any():
                diff = np.abs(s_full[valid].to_numpy() - s_trunc[valid].to_numpy())
                max_diff = np.max(diff)
                assert max_diff < 1e-9, (
                    f"Future leakage at cutoff {cutoff} in column '{col}': max diff={max_diff:.2e}"
                )


def test_independence(feature_table, growth_data):
    """Test 5: No Pipeline A objects; beai_copy_* reproducible from USA_growth.parquet alone; no scalers."""
    df = feature_table
    df_aligned = df.set_index("quarter")

    # 1. No factor/level/R/diffusion/turning-point/NBER column
    blacklisted = ["factor", "level", "r", "diffusion", "turning_point", "nber"]
    for col in df.columns:
        for b in blacklisted:
            assert b != col.lower(), f"Independence failure: Pipeline A object '{col}' found"

    # 2. Every beai_copy_* column is reproducible from USA_growth.parquet alone
    g_df = growth_data.copy()
    if not isinstance(g_df.index, pd.PeriodIndex):
        g_df.index = pd.PeriodIndex(g_df.index, freq="Q")

    beai_copies = {
        "beai_copy_act_gdp_real": ("ACT_GDP_REAL", 1),
        "beai_copy_act_ip": ("ACT_IP", 0),
        "beai_copy_act_emp": ("ACT_EMP", 1),
        "beai_copy_act_hours": ("ACT_HOURS", 1),
        "beai_copy_act_rinc": ("ACT_RINC", 1),
        "beai_copy_act_cons": ("ACT_CONS", 1),
        "beai_copy_act_retail": ("ACT_RETAIL", 0),
        "beai_copy_act_inv": ("ACT_INV", 1),
    }

    target_periods = pd.PeriodIndex(df_aligned.index, freq="Q")

    for feat_name, (src_col, lag_q) in beai_copies.items():
        assert feat_name in df_aligned.columns, f"Missing required copy: {feat_name}"
        reproduced = g_df[src_col].shift(lag_q).reindex(target_periods)

        actual = df_aligned[feat_name].to_numpy()
        expected = reproduced.to_numpy()

        both_nan = np.isnan(actual) & np.isnan(expected)
        valid = ~both_nan
        if valid.any():
            diff = np.abs(actual[valid] - expected[valid])
            assert np.max(diff) < 1e-6, f"{feat_name} not reproduced from USA_growth.parquet alone"

    # 3. No scaler object is written anywhere in data/features or feature pipeline
    for p in FEATURES_DIR.rglob("*"):
        if p.is_file():
            assert p.suffix.lower() not in (".pkl", ".joblib", ".pickle", ".scaler"), (
                f"Prohibited scaler object found: {p}"
            )


def test_mutation_fails_on_leak(panel_data, growth_data):
    """Test 6: Mutation test -- validate_table MUST raise on (a) R column and (b) future-shifted column."""
    clean_table = build_features(panel_data, growth_data)
    validate_table(clean_table)

    # Poison Variant (a): inject the R column
    poisoned_a = clean_table.copy()
    poisoned_a["R"] = 0
    with pytest.raises(ValueError, match="[Bb]lacklisted"):
        validate_table(poisoned_a, reference_df=clean_table)

    # Poison Variant (b): inject a column shifted one quarter from the future
    poisoned_b = clean_table.copy()
    # Shift an existing column one quarter into the future
    poisoned_b["rate_long"] = clean_table["rate_long"].shift(-1)
    with pytest.raises(ValueError, match="[Ff]uture leakage"):
        validate_table(poisoned_b, reference_df=clean_table)

    # Also test injecting a brand-new future-shifted column
    poisoned_b2 = clean_table.copy()
    poisoned_b2["future_leak_col"] = clean_table["rate_short"].shift(-1)
    with pytest.raises(ValueError, match="[Ff]uture leakage"):
        validate_table(poisoned_b2, reference_df=clean_table)
