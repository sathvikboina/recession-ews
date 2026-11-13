#!/usr/bin/env python3
"""Regression tests for the raw-to-quarterly harmoniser.

These cover two leakage findings from the review:

* annual predictors must use the C-06 one-year publication lag instead of the
  observation year;
* the harmoniser must read the raw file named in the manifest and verify its
  SHA-256, not just pick the newest filename on disk.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import harmonize  # noqa: E402


def test_annual_values_carry_to_the_following_year() -> None:
    series = pd.Series(
        [1.0, 2.0],
        index=pd.to_datetime(["2000-12-31", "2001-12-31"]),
    )
    quarterly = harmonize.to_quarterly(series, "A")

    assert len(quarterly) == 8
    assert quarterly.loc["2001Q1"] == 1.0
    assert quarterly.loc["2001Q4"] == 1.0
    assert quarterly.loc["2002Q1"] == 2.0
    assert quarterly.loc["2002Q4"] == 2.0
    assert "2000Q4" not in quarterly.index, "the observation year must not be used"


def test_manifest_raw_verifies_the_recorded_hash(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    raw = tmp_path / "raw"
    run = raw / "run-1"
    run.mkdir(parents=True)
    path = run / "SERIES.csv"
    path.write_text("observation_date,value\n2000-01-01,1.0\n", encoding="utf-8")

    manifest = tmp_path / "manifest.csv"
    pd.DataFrame(
        [
            {
                "source_id": "SERIES",
                "retrieved_at": "run-1",
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        ]
    ).to_csv(manifest, index=False)

    monkeypatch.setattr(harmonize, "RAW", raw)
    monkeypatch.setattr(harmonize, "MANIFEST", manifest)
    assert harmonize.manifest_raw("SERIES") == path

    path.write_text("observation_date,value\n2000-01-01,999.0\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="SHA-256 mismatch"):
        harmonize.manifest_raw("SERIES")


def test_clean_panel_excludes_validation_series() -> None:
    path = PROJECT / "data" / "clean" / "USA_levels.parquet"
    if not path.exists():
        pytest.skip("data/clean is git-ignored; run `make harmonize` first")
    panel = pd.read_parquet(path)
    assert "USA.NBER.Q" not in panel.columns
    assert "NBER" not in "".join(panel.columns)
