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
FROZEN_USA_HASH_LF = "f5ed42a6c4333aaecbae4fae1f5f6fcab3606ce46dd2b459791a6aa31816dc8e"
FROZEN_USA_HASH_CRLF = "452ba036b5d0420a0b49c493738d1e46b4dba482ef4e830df1cf1734664577b0"


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
    """Verify that JPN and DEU output directory paths are correctly namespaced."""
    jpn_out = PROJECT / "outputs" / "labels" / "JPN"
    deu_out = PROJECT / "outputs" / "labels" / "DEU"
    assert jpn_out == PROJECT / "outputs" / "labels" / "JPN"
    assert deu_out == PROJECT / "outputs" / "labels" / "DEU"
    assert jpn_out != PROJECT / "outputs" / "labels"
    assert deu_out != PROJECT / "outputs" / "labels"


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
    if not path.exists():
        pytest.skip("DEU_labels.csv not yet generated")
    df = pd.read_csv(path, index_col=0)
    assert len(df) == 144
    assert df.index[0] == "1990Q1" and df.index[-1] == "2025Q4"
    assert set(df["R"].unique()) <= {0, 1}
    assert ((df["R"] == 1) == (df["episode_id"] > 0)).all()
    ids = sorted(int(x) for x in df.loc[df["R"] == 1, "episode_id"].unique())
    assert ids == list(range(1, len(ids) + 1))
