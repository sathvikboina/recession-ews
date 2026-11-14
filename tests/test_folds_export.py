"""Contract tests for the Lane 2B fold export (`ews.harness`)."""
from __future__ import annotations

import pandas as pd

from ews.harness import (
    PRIMARY_HORIZON,
    build_payload,
    quarter_index,
    validate_payload,
)


def make_labels(tmp_path, start="1990Q1", end="2012Q3"):
    quarters = pd.period_range(start, end, freq="Q").astype(str).tolist()
    path = tmp_path / "labels.csv"
    pd.DataFrame(
        {"quarter": quarters, "R": [0] * len(quarters)}
    ).to_csv(path, index=False)
    return path


def build(tmp_path):
    labels = make_labels(tmp_path)
    return build_payload(
        start="1990Q1",
        last_scored="2012Q3",
        initial_train=40,
        inner_initial_train=16,
        labels_path=labels,
    )


def test_all_three_horizons_are_exported(tmp_path):
    payload = build(tmp_path)
    assert set(payload["horizons"]) == {"1", "2", "4"}
    for block in payload["horizons"].values():
        assert block["outer"], "no outer folds generated"


def test_primary_horizon_is_two(tmp_path):
    payload = build(tmp_path)
    assert payload["metadata"]["primary_horizon"] == PRIMARY_HORIZON == 2


def test_no_test_row_appears_in_training(tmp_path):
    payload = build(tmp_path)
    for block in payload["horizons"].values():
        for fold in block["outer"]:
            train = range(
                quarter_index(fold["train_start"]),
                quarter_index(fold["train_end"]) + 1,
            )
            test = range(
                quarter_index(fold["test_start"]),
                quarter_index(fold["test_end"]) + 1,
            )
            assert set(train).isdisjoint(test)


def test_purge_gap_equals_horizon(tmp_path):
    payload = build(tmp_path)
    for horizon_key, block in payload["horizons"].items():
        horizon = int(horizon_key)
        for fold in block["outer"]:
            gap = quarter_index(fold["test_start"]) - quarter_index(
                fold["train_end"]
            ) - 1
            assert gap == horizon
            assert fold["purge_quarters"] == horizon


def test_inner_folds_stay_inside_outer_training(tmp_path):
    payload = build(tmp_path)
    for horizon_key, block in payload["horizons"].items():
        horizon = int(horizon_key)
        for fold, inner in zip(block["outer"], block["inner"]):
            outer_end = quarter_index(fold["train_end"])
            for train_end, test_start, test_end in inner:
                assert quarter_index(test_end) <= outer_end
                assert quarter_index(train_end) < quarter_index(test_start)
                assert (
                    quarter_index(test_start) - quarter_index(train_end) - 1
                    == horizon
                )


def test_export_is_deterministic_in_folds(tmp_path):
    first = build(tmp_path)["horizons"]
    second = build(tmp_path)["horizons"]
    assert first == second


def test_marking_draft_and_unapproved(tmp_path):
    payload = build(tmp_path)
    assert payload["metadata"]["draft"] is True
    assert payload["metadata"]["approved"] is False
    assert payload["metadata"]["reason"]


def test_validation_rejects_a_leaking_fold(tmp_path):
    payload = build(tmp_path)
    block = payload["horizons"]["2"]
    block["outer"][0]["train_end"] = block["outer"][0]["test_start"]
    block["outer"][0]["purge_quarters"] = 0
    try:
        validate_payload(payload)
    except ValueError:
        return
    raise AssertionError("validate_payload accepted a leaking fold")
