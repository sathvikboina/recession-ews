#!/usr/bin/env python3
"""Regression tests for the frozen label artefacts and their provenance.

These protect the review invariants:

* ``labels-v1`` and ``labels-v2`` stay byte-identical in their archives;
* the active ``labels-v3`` chronology matches its recorded dates and values;
* episode ids in ``USA_labels.csv`` join ``USA_episodes.csv``;
* one scope key resolves to one active source.

``labels-v3`` extends the reporting window to 2026Q3. The estimator, BBQ
settings, diffusion gate and eight-indicator structure are unchanged from v2.

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

from ews.labels.freeze import (  # noqa: E402
    canonical_frame_sha256,
    check_frozen_input,
    existing_created,
)

LABELS = PROJECT / "outputs" / "labels" / "USA_labels.csv"
EPISODES = PROJECT / "outputs" / "labels" / "USA_episodes.csv"
TURNING_POINTS = PROJECT / "outputs" / "labels" / "USA_turning_points.csv"
META = PROJECT / "outputs" / "labels" / "labels-v3.json"

ARCHIVE_V1 = PROJECT / "outputs" / "labels" / "archive" / "labels-v1"
V1_LABELS = ARCHIVE_V1 / "USA_labels.csv"
V1_EPISODES = ARCHIVE_V1 / "USA_episodes.csv"
V1_TURNING_POINTS = ARCHIVE_V1 / "USA_turning_points.csv"
V1_META = ARCHIVE_V1 / "labels-v1.json"

ARCHIVE_V2 = PROJECT / "outputs" / "labels" / "archive" / "labels-v2"
V2_LABELS = ARCHIVE_V2 / "USA_labels.csv"
V2_EPISODES = ARCHIVE_V2 / "USA_episodes.csv"
V2_TURNING_POINTS = ARCHIVE_V2 / "USA_turning_points.csv"
V2_META = ARCHIVE_V2 / "labels-v2.json"

VERIFY = PROJECT / "data" / "fred_verification.csv"
MANIFEST = PROJECT / "data" / "manifest.csv"
SUPERSEDED = PROJECT / "data" / "superseded_series.csv"

# Frozen 2026-10-29; do not change without a new label version.
V1_LABELS_SHA256 = "1a1b1f6a566cb2cffe7181cbc59ec20bd07d8ef25e0300d4dd2d96ceb749e29a"
V1_EPISODES_SHA256 = "f921ad38e6ccdde482700deaaba3e3ea3a6cda1fd09a78389abc7bcf8f40aa1d"
V1_TURNING_POINTS_SHA256 = "9f83438c4d57e7fea3ed2f13030379e112d4f24bc24a85a2cd4e4564ab80a1a1"
V1_META_SHA256 = "954565d2e2cd137109153b376389b1920c9d9d3598f6a027d574be7770991834"

# Archived v2 chronology, frozen 2026-11-04 (Q-02 + Q-04 re-validation).
V2_LABELS_SHA256 = "f5ed42a6c4333aaecbae4fae1f5f6fcab3606ce46dd2b459791a6aa31816dc8e"
V2_EPISODES_SHA256 = "45aca14077868d95639a69ac8d1c0666b059258635c05a70bf90bf5815a2d4f9"
V2_TURNING_POINTS_SHA256 = "26883399153f6bddb9a8ce6808faaedda96fe2bf35fc08f8d36d7371a45efecf"
V2_META_SHA256 = "1fb38a7691a0ecd5ba25921cf05b7357766aa9fb4ba350b5ebbdc032ca909e74"

# Active v3 chronology, frozen 2026-11-06 (2026Q3 window extension).
V3_LABELS_SHA256 = "2379fd53e4c9023538cafcd5668a4835bcdd7b45cfae9e3cbc3d4f306ed19daa"
V3_EPISODES_SHA256 = "421576904a9d9173dbe641a5a73f2b171d774600734919542c4abb6ebd569280"
V3_TURNING_POINTS_SHA256 = "c67725ce4ab3804f08f45a5efc4fbe81f30a47054c2f53416cf508f2e8a34d11"
V3_META_SHA256 = "6f1aa66598b1cdf823e3f97a25709c6cb5a7ed851ee8ab1c0a9b8e45402c0a50"

# (episode_id, peak, trough, duration)
FROZEN_EPISODES_V1 = [
    (1, "1990Q2", "1991Q1", 3),
    (2, "2001Q1", "2001Q4", 3),
    (3, "2007Q4", "2009Q3", 7),
    (4, "2019Q4", "2020Q2", 2),
]
FROZEN_EPISODES_V3 = [
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
FROZEN_VALUES_V3 = {
    "1990Q1": (0.820064, 95.271836),
    "1990Q3": (-0.024925, 95.399277),
    "2009Q3": (0.081718, 133.866186),
    "2020Q2": (-10.639094, 145.438580),
}


def test_v1_and_v2_archives_are_byte_identical() -> None:
    assert hashlib.sha256(V1_LABELS.read_bytes()).hexdigest() == V1_LABELS_SHA256
    assert hashlib.sha256(V1_EPISODES.read_bytes()).hexdigest() == V1_EPISODES_SHA256
    assert (
        hashlib.sha256(V1_TURNING_POINTS.read_bytes()).hexdigest()
        == V1_TURNING_POINTS_SHA256
    )
    assert hashlib.sha256(V1_META.read_bytes()).hexdigest() == V1_META_SHA256

    assert hashlib.sha256(V2_LABELS.read_bytes()).hexdigest() == V2_LABELS_SHA256
    assert hashlib.sha256(V2_EPISODES.read_bytes()).hexdigest() == V2_EPISODES_SHA256
    assert (
        hashlib.sha256(V2_TURNING_POINTS.read_bytes()).hexdigest()
        == V2_TURNING_POINTS_SHA256
    )
    assert hashlib.sha256(V2_META.read_bytes()).hexdigest() == V2_META_SHA256


def test_active_label_hash_is_v3() -> None:
    assert hashlib.sha256(LABELS.read_bytes()).hexdigest() == V3_LABELS_SHA256, (
        "the active v3 label CSV changed"
    )
    assert hashlib.sha256(EPISODES.read_bytes()).hexdigest() == V3_EPISODES_SHA256
    assert (
        hashlib.sha256(TURNING_POINTS.read_bytes()).hexdigest()
        == V3_TURNING_POINTS_SHA256
    )
    assert hashlib.sha256(META.read_bytes()).hexdigest() == V3_META_SHA256


def test_v3_label_dates_and_factor_values() -> None:
    frame = pd.read_csv(LABELS, index_col=0)
    assert len(frame) == 147
    assert frame.index[0] == "1990Q1" and frame.index[-1] == "2026Q3"

    for quarter, (factor, level) in FROZEN_VALUES_V3.items():
        row = frame.loc[quarter]
        assert abs(float(row["factor"]) - factor) < 1e-6, f"factor moved at {quarter}"
        assert abs(float(row["level"]) - level) < 1e-6, f"level moved at {quarter}"

    episodes = pd.read_csv(EPISODES)
    observed = [
        (int(row.episode_id), row.peak, row.trough, int(row.duration))
        for row in episodes[episodes["kept"]].itertuples()
    ]
    assert observed == FROZEN_EPISODES_V3


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
    expected = (tps["quarter"] >= "1990Q1") & (tps["quarter"] <= "2026Q3")
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


def test_v3_metadata_records_the_input_decisions() -> None:
    meta = json.loads(META.read_text(encoding="utf-8"))
    assert meta["label_version"] == "labels-v3"
    assert meta["supersedes"] == "labels-v2"
    assert meta["hashes"]["superseded_labels_csv_sha256"] == V2_LABELS_SHA256
    assert meta["window"]["end"] == "2026Q3"
    assert meta["decisions"]["Q-02"]["choice"].startswith("constructed real non-residential")
    assert meta["decisions"]["Q-04"]["choice"].startswith("CE16OV")
    assert meta["decisions"]["Q-05"]["choice"] == "keep HOANBS"
    assert meta["inputs"]["source_ids"]["ACT_EMP"] == "CE16OV"
    assert "USA.ACT_INV_EQ.Q.STD" in meta["inputs"]["source_ids"]["ACT_INV"]


def test_created_date_is_preserved(tmp_path: Path) -> None:
    path = tmp_path / "labels-v3.json"
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


def test_frozen_overwrite_guard_requires_an_explicit_opt_in(tmp_path: Path) -> None:
    growth = pd.DataFrame({"a": [1.0, 2.0]})
    meta = tmp_path / "labels-v3.json"
    meta.write_text(
        json.dumps({"inputs": {"growth_values_sha256": canonical_frame_sha256(growth)}}),
        encoding="utf-8",
    )
    ok, message = check_frozen_input(growth, meta)
    assert ok and not message

    changed = growth.copy()
    changed.loc[0, "a"] = 99.0
    ok, message = check_frozen_input(changed, meta)
    assert not ok and "refusing" in message

    ok, message = check_frozen_input(changed, meta, allow_overwrite=True)
    assert ok and "WARNING" in message
