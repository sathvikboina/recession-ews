#!/usr/bin/env python3
"""Regression tests for the frozen label artefacts and their provenance.

These protect the review invariants:

* ``labels-v1`` stays byte-identical in ``outputs/labels/archive/labels-v1``;
* the active ``labels-v2`` chronology matches its recorded dates and values;
* episode ids in ``USA_labels.csv`` join ``USA_episodes.csv``;
* one scope key resolves to one active source.

``labels-v2`` changes only two label inputs (Q-02 and Q-04).  The estimator,
BBQ settings and diffusion gate are unchanged from v1.

Runs under pytest:
    python -m pytest tests/test_freeze.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from ews.labels.freeze import canonical_frame_sha256, existing_created  # noqa: E402

LABELS = PROJECT / "outputs" / "labels" / "USA_labels.csv"
EPISODES = PROJECT / "outputs" / "labels" / "USA_episodes.csv"
TURNING_POINTS = PROJECT / "outputs" / "labels" / "USA_turning_points.csv"
META = PROJECT / "outputs" / "labels" / "labels-v2.json"

ARCHIVE = PROJECT / "outputs" / "labels" / "archive" / "labels-v1"
V1_LABELS = ARCHIVE / "USA_labels.csv"
V1_EPISODES = ARCHIVE / "USA_episodes.csv"
V1_TURNING_POINTS = ARCHIVE / "USA_turning_points.csv"
V1_META = ARCHIVE / "labels-v1.json"

VERIFY = PROJECT / "data" / "fred_verification.csv"
MANIFEST = PROJECT / "data" / "manifest.csv"
SUPERSEDED = PROJECT / "data" / "superseded_series.csv"

# Frozen 2026-10-29; do not change without a new label version.
V1_LABELS_SHA256 = "1a1b1f6a566cb2cffe7181cbc59ec20bd07d8ef25e0300d4dd2d96ceb749e29a"
V1_EPISODES_SHA256 = "f921ad38e6ccdde482700deaaba3e3ea3a6cda1fd09a78389abc7bcf8f40aa1d"
V1_TURNING_POINTS_SHA256 = "9f83438c4d57e7fea3ed2f13030379e112d4f24bc24a85a2cd4e4564ab80a1a1"
V1_META_SHA256 = "954565d2e2cd137109153b376389b1920c9d9d3598f6a027d574be7770991834"

# Active v2 chronology, frozen 2026-11-04 (Q-02 + Q-04 re-validation).
V2_LABELS_SHA256 = "f5ed42a6c4333aaecbae4fae1f5f6fcab3606ce46dd2b459791a6aa31816dc8e"

# (episode_id, peak, trough, duration)
FROZEN_EPISODES_V1 = [
    (1, "1990Q2", "1991Q1", 3),
    (2, "2001Q1", "2001Q4", 3),
    (3, "2007Q4", "2009Q3", 7),
    (4, "2019Q4", "2020Q2", 2),
]
FROZEN_EPISODES_V2 = [
    (1, "1990Q2", "1991Q1", 3),
    (2, "2001Q1", "2001Q4", 3),
    (3, "2007Q4", "2009Q2", 6),
    (4, "2019Q4", "2020Q2", 2),
]

# D-R25: scale = mean(sigma_j * |lambda_j|). These values are the visible
# consequence of that rule; a scaling regression would move them.
FROZEN_VALUES_V1 = {
    "1990Q1": (0.726289, 95.206884),
    "1990Q3": (-0.300903, 95.058250),
    "2009Q3": (-0.075538, 130.273647),
    "2020Q2": (-13.187955, 138.526571),
}
FROZEN_VALUES_V2 = {
    "1990Q1": (0.816971, 94.904461),
    "1990Q3": (-0.027610, 95.025593),
    "2009Q3": (0.074295, 133.262082),
    "2020Q2": (-10.651129, 144.753126),
}


def test_v1_archive_is_byte_identical() -> None:
    assert hashlib.sha256(V1_LABELS.read_bytes()).hexdigest() == V1_LABELS_SHA256
    assert hashlib.sha256(V1_EPISODES.read_bytes()).hexdigest() == V1_EPISODES_SHA256
    assert (
        hashlib.sha256(V1_TURNING_POINTS.read_bytes()).hexdigest()
        == V1_TURNING_POINTS_SHA256
    )
    assert hashlib.sha256(V1_META.read_bytes()).hexdigest() == V1_META_SHA256


def test_active_label_hash_is_v2() -> None:
    digest = hashlib.sha256(LABELS.read_bytes()).hexdigest()
    assert digest == V2_LABELS_SHA256, "the active v2 label CSV changed"


def test_v2_label_dates_and_factor_values() -> None:
    frame = pd.read_csv(LABELS, index_col=0)
    assert len(frame) == 144
    assert frame.index[0] == "1990Q1" and frame.index[-1] == "2025Q4"

    for quarter, (factor, level) in FROZEN_VALUES_V2.items():
        row = frame.loc[quarter]
        assert abs(float(row["factor"]) - factor) < 1e-6, f"factor moved at {quarter}"
        assert abs(float(row["level"]) - level) < 1e-6, f"level moved at {quarter}"

    episodes = pd.read_csv(EPISODES)
    observed = [
        (int(row.episode_id), row.peak, row.trough, int(row.duration))
        for row in episodes[episodes["kept"]].itertuples()
    ]
    assert observed == FROZEN_EPISODES_V2


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


def test_v2_metadata_records_the_input_decisions() -> None:
    meta = json.loads(META.read_text(encoding="utf-8"))
    assert meta["label_version"] == "labels-v2"
    assert meta["supersedes"] == "labels-v1"
    assert meta["hashes"]["superseded_labels_csv_sha256"] == V1_LABELS_SHA256
    assert meta["decisions"]["Q-02"]["choice"].startswith("constructed real non-residential")
    assert meta["decisions"]["Q-04"]["choice"].startswith("CE16OV")
    assert meta["decisions"]["Q-05"]["choice"] == "keep HOANBS"
    assert meta["inputs"]["source_ids"]["ACT_EMP"] == "CE16OV"
    assert "USA.ACT_INV_EQ.Q.STD" in meta["inputs"]["source_ids"]["ACT_INV"]


def test_created_date_is_preserved(tmp_path: Path) -> None:
    path = tmp_path / "labels-v2.json"
    assert existing_created(path, "2099-01-01") == "2099-01-01"

    path.write_text('{"created": "2026-11-04"}', encoding="utf-8")
    assert existing_created(path, "2099-01-01") == "2026-11-04"

    path.write_text("not json", encoding="utf-8")
    assert existing_created(path, "2099-01-01") == "2099-01-01"


def test_canonical_digest_tracks_values_not_parquet_bytes() -> None:
    first = pd.DataFrame({"a": [1.0, 2.0], "b": [3.0, 4.0]})
    second = first.copy()
    assert canonical_frame_sha256(first) == canonical_frame_sha256(second)
    second.loc[0, "a"] = 1.5
    assert canonical_frame_sha256(first) != canonical_frame_sha256(second)
