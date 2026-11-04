#!/usr/bin/env python3
"""Regression tests for the frozen label artefacts and their provenance.

These protect three things the review found unguarded:

* the frozen chronology must stay byte-identical (D-R22..D-R25);
* episode ids in ``USA_labels.csv`` must join ``USA_episodes.csv``;
* one scope key must resolve to one active source.

Runs under pytest:
    python -m pytest tests/test_freeze.py
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from ews.labels.freeze import canonical_frame_sha256, existing_created  # noqa: E402

LABELS = PROJECT / "outputs" / "labels" / "USA_labels.csv"
EPISODES = PROJECT / "outputs" / "labels" / "USA_episodes.csv"
TURNING_POINTS = PROJECT / "outputs" / "labels" / "USA_turning_points.csv"
META = PROJECT / "outputs" / "labels" / "labels-v1.json"
VERIFY = PROJECT / "data" / "fred_verification.csv"
MANIFEST = PROJECT / "data" / "manifest.csv"
SUPERSEDED = PROJECT / "data" / "superseded_series.csv"

# Frozen 2026-10-29; do not change without a new label version.
LABELS_SHA256 = "1a1b1f6a566cb2cffe7181cbc59ec20bd07d8ef25e0300d4dd2d96ceb749e29a"

# (episode_id, peak, trough, duration)
FROZEN_EPISODES = [
    (1, "1990Q2", "1991Q1", 3),
    (2, "2001Q1", "2001Q4", 3),
    (3, "2007Q4", "2009Q3", 7),
    (4, "2019Q4", "2020Q2", 2),
]

# D-R25: scale = mean(sigma_j * |lambda_j|). These values are the visible
# consequence of that rule; a scaling regression would move them.
FROZEN_VALUES = {
    "1990Q1": (0.726289, 95.206884),
    "1990Q3": (-0.300903, 95.058250),
    "2009Q3": (-0.075538, 130.273647),
    "2020Q2": (-13.187955, 138.526571),
}


def test_frozen_label_hash_is_unchanged() -> None:
    digest = hashlib.sha256(LABELS.read_bytes()).hexdigest()
    assert digest == LABELS_SHA256, "the frozen label CSV changed"


def test_frozen_label_dates_and_factor_values() -> None:
    frame = pd.read_csv(LABELS, index_col=0)
    assert len(frame) == 144
    assert frame.index[0] == "1990Q1" and frame.index[-1] == "2025Q4"

    for quarter, (factor, level) in FROZEN_VALUES.items():
        row = frame.loc[quarter]
        assert abs(float(row["factor"]) - factor) < 1e-6, f"factor moved at {quarter}"
        assert abs(float(row["level"]) - level) < 1e-6, f"level moved at {quarter}"

    episodes = pd.read_csv(EPISODES)
    observed = [
        (int(row.episode_id), row.peak, row.trough, int(row.duration))
        for row in episodes[episodes["kept"]].itertuples()
    ]
    assert observed == FROZEN_EPISODES


def test_episode_ids_join_across_frozen_artefacts() -> None:
    labels = pd.read_csv(LABELS, index_col=0)
    episodes = pd.read_csv(EPISODES)
    index = pd.PeriodIndex(labels.index, freq="Q")

    kept = episodes[episodes["kept"]]
    assert kept["episode_id"].tolist() == list(range(1, len(kept) + 1))
    assert not kept["episode_id"].duplicated().any()

    for row in kept.itertuples():
        peak = pd.Period(row.peak, freq="Q")
        trough = pd.Period(row.trough, freq="Q")
        expected = [str(q) for q in pd.period_range(peak + 1, trough, freq="Q")]
        observed = [str(q) for q in index[labels["episode_id"].to_numpy() == row.episode_id]]
        assert observed == expected, f"episode {row.episode_id} does not join the label"

    # rejected candidates carry id 0, never a fake window id
    rejected = episodes[~episodes["kept"]]
    assert (rejected["episode_id"] == 0).all()


def test_turning_points_carry_in_window_flag() -> None:
    tps = pd.read_csv(TURNING_POINTS)
    assert "in_window" in tps.columns
    expected = (tps["quarter"] >= "1990Q1") & (tps["quarter"] <= "2025Q4")
    assert (tps["in_window"].astype(bool) == expected).all()


def test_one_active_source_per_scope_key() -> None:
    verification = pd.read_csv(VERIFY)
    manifest = pd.read_csv(MANIFEST)
    assert not verification["series_key"].duplicated().any(), "duplicate active verification row"
    assert not manifest["series_key"].duplicated().any(), "duplicate active manifest row"

    if SUPERSEDED.exists():
        superseded = pd.read_csv(SUPERSEDED)
        active = set(zip(verification["series_key"], verification["fred_id"]))
        retired = set(zip(superseded["series_key"], superseded["source_id"]))
        assert not (retired & active), "a superseded source is still active"


def test_created_date_is_preserved(tmp_path: Path) -> None:
    path = tmp_path / "labels-v1.json"
    assert existing_created(path, "2099-01-01") == "2099-01-01"

    path.write_text('{"created": "2026-10-29"}', encoding="utf-8")
    assert existing_created(path, "2099-01-01") == "2026-10-29"

    path.write_text("not json", encoding="utf-8")
    assert existing_created(path, "2099-01-01") == "2099-01-01"


def test_canonical_digest_tracks_values_not_parquet_bytes() -> None:
    first = pd.DataFrame({"a": [1.0, 2.0], "b": [3.0, 4.0]})
    second = first.copy()
    assert canonical_frame_sha256(first) == canonical_frame_sha256(second)
    second.loc[0, "a"] = 1.5
    assert canonical_frame_sha256(first) != canonical_frame_sha256(second)
