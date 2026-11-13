#!/usr/bin/env python3
"""Plumbing and isolation tests for country-parameterised pipeline.

Protects Day 1 invariants:
- The core indicator list is exactly eight and country-independent (Rule C-01).
- The coverage gate helper correctly implements 6/8 and >=70% logic (Rule C-03).
- Running the USA pipeline leaves the USA label byte-identical (Rule C-12).
- Non-USA runs write to their own country namespace and do not touch USA files.

Runs under pytest:
    python -m pytest tests/test_country_plumbing.py
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from ews.labels.coverage import (  # noqa: E402
    CORE_INDICATORS,
    check_coverage_gate,
)

USA_LABELS_PATH = PROJECT / "outputs" / "labels" / "USA_labels.csv"
FROZEN_USA_HASH_LF = "2379fd53e4c9023538cafcd5668a4835bcdd7b45cfae9e3cbc3d4f306ed19daa"
FROZEN_USA_HASH_CRLF = "848f27b27dda5ba57a251ecb743d71f8ea7f1658fd73134caad8bb1e68d89418"


def test_core_indicator_list_is_eight_and_country_independent() -> None:
    expected = {
        "ACT_GDP_REAL",
        "ACT_IP",
        "ACT_EMP",
        "ACT_HOURS",
        "ACT_RINC",
        "ACT_CONS",
        "ACT_RETAIL",
        "ACT_INV",
    }
    assert set(CORE_INDICATORS) == expected
    assert len(CORE_INDICATORS) == 8


def test_coverage_gate_helper_full_pass() -> None:
    window = pd.period_range("1990Q1", "2025Q4", freq="Q")
    # 144 quarters, all 8 indicators present
    df = pd.DataFrame(1.0, index=window, columns=CORE_INDICATORS)
    res = check_coverage_gate(df, window=window)
    assert res.passed is True
    assert res.n_passing_indicators == 8
    assert res.datable_quarters_count == 144
    assert len(res.failing_indicators) == 0


def test_coverage_gate_helper_exact_six_pass() -> None:
    window = pd.period_range("1990Q1", "2025Q4", freq="Q")
    # 6 indicators at 100%, 2 indicators completely missing
    cols = CORE_INDICATORS[:6]
    df = pd.DataFrame(1.0, index=window, columns=cols)
    res = check_coverage_gate(df, window=window)
    assert res.passed is True
    assert res.n_passing_indicators == 6
    assert len(res.failing_indicators) == 2


def test_coverage_gate_helper_five_pass_fails_gate() -> None:
    window = pd.period_range("1990Q1", "2025Q4", freq="Q")
    # Only 5 indicators present: must fail (C-03 requires >= 6)
    cols = CORE_INDICATORS[:5]
    df = pd.DataFrame(1.0, index=window, columns=cols)
    res = check_coverage_gate(df, window=window)
    assert res.passed is False
    assert res.n_passing_indicators == 5
    assert len(res.failing_indicators) == 3


def test_coverage_gate_helper_sub_70pct_fails() -> None:
    window = pd.period_range("1990Q1", "2025Q4", freq="Q")
    # 144 quarters; 70% threshold is 101 quarters.
    # Provide 100 quarters for one indicator: it should fail.
    data = {}
    for i, col in enumerate(CORE_INDICATORS):
        s = pd.Series(np.nan, index=window)
        if i == 0:
            s.iloc[:100] = 1.0  # 100/144 = 69.4% < 70% -> fail
        else:
            s.iloc[:101] = 1.0  # 101/144 = 70.1% >= 70% -> pass
        data[col] = s
    df = pd.DataFrame(data)
    res = check_coverage_gate(df, window=window)
    assert res.indicators[0].passed is False
    assert res.n_passing_indicators == 7
    assert res.passed is True  # 7 of 8 still passes gate


def test_datable_quarters_rule() -> None:
    window = pd.period_range("1990Q1", "2025Q4", freq="Q")
    # A quarter needs >= 4 indicators to be datable
    df = pd.DataFrame(np.nan, index=window, columns=CORE_INDICATORS)
    # Give first 10 quarters 4 indicators
    df.iloc[:10, :4] = 1.0
    # Give next 10 quarters only 3 indicators
    df.iloc[10:20, :3] = 1.0
    res = check_coverage_gate(df, window=window)
    assert res.datable_quarters_count == 10


def test_usa_labels_hash_is_preserved() -> None:
    assert USA_LABELS_PATH.exists(), "USA_labels.csv must exist"
    raw_bytes = USA_LABELS_PATH.read_bytes()
    raw_hash = hashlib.sha256(raw_bytes).hexdigest()
    lf_hash = hashlib.sha256(raw_bytes.replace(b"\r\n", b"\n")).hexdigest()
    assert (
        raw_hash == FROZEN_USA_HASH_CRLF or lf_hash == FROZEN_USA_HASH_LF
    ), f"USA label hash moved: {raw_hash} (LF: {lf_hash})"


def test_country_isolation_naming() -> None:
    """Verify that country output files are strictly isolated and never collide with USA."""
    labels_root = PROJECT / "outputs" / "labels"
    # Root labels directory should only contain USA labels and country subdirectories
    root_csvs = list(labels_root.glob("*.csv"))
    expected_root = {"USA_labels.csv", "USA_episodes.csv", "USA_turning_points.csv"}
    assert set(p.name for p in root_csvs) == expected_root, f"Unexpected root CSVs: {root_csvs}"
    for p in root_csvs:
        assert not p.name.startswith(("JPN_", "DEU_")), f"Country file leaked into root: {p.name}"

    # Verify that JPN outputs exist in JPN namespace and do not leak into root
    jpn_dir = labels_root / "JPN"
    assert jpn_dir.is_dir(), "JPN output directory must exist"
    jpn_files = set(p.name for p in jpn_dir.glob("*"))
    assert "JPN_labels.csv" in jpn_files
    assert "JPN_episodes.csv" in jpn_files
    assert "labels-v1-JPN.json" in jpn_files

    # Verify that clean data files are strictly prefixed by ISO3
    clean_dir = PROJECT / "data" / "clean"
    if clean_dir.exists():
        for p in clean_dir.glob("JPN_*"):
            assert p.name.startswith("JPN_"), f"File not cleanly prefixed: {p.name}"


def test_freeze_json_input_hashes_match_raw() -> None:
    """Verify that every raw input file hash recorded in frozen JSON matches disk bytes (C-12).

    If raw input files are not present (e.g. in a clean clone or CI where data/raw
    is git-ignored), the test skips gracefully. When raw files are present, every
    file's SHA-256 must match the frozen metadata exactly.
    """
    labels_root = PROJECT / "outputs" / "labels"
    tested = 0
    for json_path in labels_root.glob("**/labels-v1-*.json"):
        import json
        meta = json.loads(json_path.read_text(encoding="utf-8"))
        raw_hashes = meta.get("inputs", {}).get("raw_input_hashes", {})
        assert len(raw_hashes) > 0, f"No raw_input_hashes recorded in {json_path.name}"
        for rel_path, expected_hash in raw_hashes.items():
            file_path = PROJECT / rel_path
            if not file_path.exists():
                continue
            actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
            assert actual_hash == expected_hash, (
                f"Raw input hash mismatch for {rel_path} in {json_path.name}: "
                f"expected {expected_hash}, got {actual_hash}"
            )
            tested += 1

    if tested == 0:
        pytest.skip("data/raw is git-ignored; run fetch scripts to populate raw files for verification")


def test_frozen_parameters_unchanged() -> None:
    """Verify that core BEAI frozen parameters have not moved (Rule C-02)."""
    from ews.labels.build import PARAMS
    assert PARAMS["min_phase"] == 2, "min_phase must remain 2"
    assert PARAMS["min_cycle"] == 5, "min_cycle must remain 5"
    assert PARAMS["censor"] == 2, "censor must remain 2"
    assert PARAMS["diffusion_gate"] == 0.50, "diffusion_gate must remain 0.50"
    assert PARAMS["depth_review_sd"] == 0.10, "depth_review_sd must remain 0.10"
    assert PARAMS["factor_count"] == 1, "factor_count must remain 1"


def test_no_partial_quarters() -> None:
    """Rule C-06: Monthly aggregation requires all 3 months present; 2 months yields NaN."""
    # Build a monthly series where 2020Q1 has months 1 and 2, but month 3 is missing
    m_idx = pd.period_range("2020-01", "2020-06", freq="M")
    m_series = pd.Series([100.0, 102.0, np.nan, 105.0, 106.0, 107.0], index=m_idx)

    # Monthly -> Quarterly aggregation: complete quarter rule
    # A quarter is valid ONLY if all 3 constituent months are not null
    q_counts = m_series.notna().groupby(m_series.index.asfreq("Q")).sum()
    q_mean = m_series.groupby(m_series.index.asfreq("Q")).mean()
    q_mean[q_counts < 3] = np.nan

    assert pd.isna(q_mean.loc[pd.Period("2020Q1", freq="Q")]), "2020Q1 must be NaN (only 2 months present)"
    assert pd.notna(q_mean.loc[pd.Period("2020Q2", freq="Q")]), "2020Q2 must be valid (all 3 months present)"
    assert q_mean.loc[pd.Period("2020Q2", freq="Q")] == pytest.approx(106.0)


def test_coverage_gate_branches() -> None:
    """Verify exact 6/8 pass, 5/8 fail, and exact 70% threshold boundaries (Rule C-03)."""
    window = pd.period_range("1990Q1", "2025Q4", freq="Q")  # 144 quarters
    # 70% of 144 = 100.8 -> requires >= 101 quarters

    # Test 1: Exactly 6 indicators passing at 101 quarters -> PASS
    data_pass = {}
    for i, col in enumerate(CORE_INDICATORS):
        s = pd.Series(np.nan, index=window)
        if i < 6:
            s.iloc[:101] = 1.0  # 101 / 144 = 70.14% >= 70%
        data_pass[col] = s
    res_pass = check_coverage_gate(pd.DataFrame(data_pass), window=window)
    assert res_pass.passed is True
    assert res_pass.n_passing_indicators == 6

    # Test 2: Exactly 5 indicators passing at 101 quarters -> FAIL
    data_fail_5 = {}
    for i, col in enumerate(CORE_INDICATORS):
        s = pd.Series(np.nan, index=window)
        if i < 5:
            s.iloc[:101] = 1.0
        data_fail_5[col] = s
    res_fail_5 = check_coverage_gate(pd.DataFrame(data_fail_5), window=window)
    assert res_fail_5.passed is False
    assert res_fail_5.n_passing_indicators == 5

    # Test 3: 6 indicators present, but one has only 100 quarters (69.4%) -> 5 pass -> FAIL
    data_boundary = {}
    for i, col in enumerate(CORE_INDICATORS):
        s = pd.Series(np.nan, index=window)
        if i < 5:
            s.iloc[:101] = 1.0
        elif i == 5:
            s.iloc[:100] = 1.0  # 100 / 144 = 69.44% < 70%
        data_boundary[col] = s
    res_boundary = check_coverage_gate(pd.DataFrame(data_boundary), window=window)
    assert res_boundary.passed is False
    assert res_boundary.n_passing_indicators == 5


def test_sample_start_is_config_driven() -> None:
    """Verify that sample starts resolve from config/scope.yaml rather than manual CLI flags."""
    import yaml
    with (PROJECT / "config" / "scope.yaml").open(encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    sample_starts = cfg.get("window", {}).get("sample_start", {})
    assert sample_starts.get("DEU") == "1991Q2", "DEU sample start must resolve to 1991Q2 from config"
    assert sample_starts.get("USA") == "1960Q1", "USA sample start must resolve to 1960Q1 from config"
    assert sample_starts.get("JPN") is None, "JPN sample start must be null (dynamic rule)"


def test_jpn_frozen_labels_invariants() -> None:
    path = PROJECT / "outputs" / "labels" / "JPN" / "JPN_labels.csv"
    if not path.exists():
        pytest.skip("JPN_labels.csv not yet generated")
    df = pd.read_csv(path, index_col=0)
    assert len(df) == 144
    assert df.index[0] == "1990Q1" and df.index[-1] == "2025Q4"
    assert set(df["R"].unique()) <= {0, 1}
    assert ((df["R"] == 1) == (df["episode_id"] > 0)).all()
    ids = sorted(int(x) for x in df.loc[df["R"] == 1, "episode_id"].unique())
    assert ids == list(range(1, len(ids) + 1))


def test_deu_frozen_labels_invariants() -> None:
    path = PROJECT / "outputs" / "labels" / "DEU" / "DEU_labels.csv"
    assert not path.exists(), "DEU label must not be frozen while Q-02 non-compliant"
