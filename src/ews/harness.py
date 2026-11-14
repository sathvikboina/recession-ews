"""Walk-forward harness: fold export and contract checks (Lane 2B).

The generator lives in :mod:`ews.models.folds`; this module serialises its
output, validates the harness contract and writes ``folds.json``. It does not
reimplement fold generation and it does not read model scores.

Status: the exported file is **draft** until the initial training window is
approved (docs/DECISIONS.md).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from ews.models.folds import (
    Fold,
    generate_inner_folds,
    generate_outer_folds,
    quarter_index,
)

HORIZONS = (1, 2, 4)
PRIMARY_HORIZON = 2
STEP_QUARTERS = 1


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _outer_to_dict(fold: Fold) -> dict:
    return {
        "train_start": fold.train_start,
        "train_end": fold.train_end,
        "test_start": fold.test_start,
        "test_end": fold.test_end,
        "purge_quarters": fold.purge_quarters,
        "train_quarters": (
            quarter_index(fold.train_end) - quarter_index(fold.train_start) + 1
        ),
    }


def build_horizon(
    start: str,
    last_scored: str,
    initial_train: int,
    inner_initial_train: int,
    horizon: int,
    step_quarters: int = STEP_QUARTERS,
) -> dict:
    outer = generate_outer_folds(
        start=start,
        last_scored=last_scored,
        initial_train_quarters=initial_train,
        horizon=horizon,
        step_quarters=step_quarters,
    )
    outer_records = []
    inner_records = []
    for fold in outer:
        inner = generate_inner_folds(
            outer_fold=fold,
            initial_train_quarters=inner_initial_train,
            horizon=horizon,
            step_quarters=step_quarters,
        )
        outer_records.append(_outer_to_dict(fold))
        inner_records.append(
            [[f.train_end, f.test_start, f.test_end] for f in inner]
        )
    return {"outer": outer_records, "inner": inner_records}


def build_payload(
    start: str,
    last_scored: str,
    initial_train: int,
    inner_initial_train: int,
    labels_path: Path,
    horizons: tuple[int, ...] = HORIZONS,
    step_quarters: int = STEP_QUARTERS,
) -> dict:
    payload = {
        "schema": {
            "outer": [
                "train_start",
                "train_end",
                "test_start",
                "test_end",
                "purge_quarters",
                "train_quarters",
            ],
            "inner": (
                "list parallel to outer; each item is a list of "
                "[train_end, test_start, test_end] triples. train_start is the "
                "parent outer train_start; purge equals the horizon."
            ),
        },
        "metadata": {
            "draft": True,
            "approved": False,
            "reason": (
                "initial training window is not yet approved "
                "(docs/DECISIONS.md, Lane 2 open decision)"
            ),
            "generated_from": "outputs/labels/USA_labels.csv",
            "labels_file": str(Path(labels_path)),
            "labels_sha256": sha256_file(labels_path),
            "start": start,
            "last_scored": last_scored,
            "horizons": list(horizons),
            "primary_horizon": PRIMARY_HORIZON,
            "step_quarters": step_quarters,
            "initial_train_quarters": initial_train,
            "inner_initial_train_quarters": inner_initial_train,
            "method": "expanding_window_time_ordered",
            "generator": "ews.models.folds",
        },
        "horizons": {
            str(h): build_horizon(
                start=start,
                last_scored=last_scored,
                initial_train=initial_train,
                inner_initial_train=inner_initial_train,
                horizon=h,
                step_quarters=step_quarters,
            )
            for h in horizons
        },
    }
    validate_payload(payload)
    return payload


def validate_payload(payload: dict) -> None:
    """Raise ValueError if a fold violates the harness contract."""
    for horizon_key, block in payload["horizons"].items():
        horizon = int(horizon_key)
        outer = block["outer"]
        inner = block["inner"]
        if len(outer) != len(inner):
            raise ValueError(f"horizon {horizon}: outer/inner length mismatch")
        for i, fold in enumerate(outer):
            train_end = quarter_index(fold["train_end"])
            test_start = quarter_index(fold["test_start"])
            if fold["purge_quarters"] != horizon:
                raise ValueError(f"horizon {horizon} fold {i}: wrong purge")
            if test_start - train_end - 1 != horizon:
                raise ValueError(
                    f"horizon {horizon} fold {i}: purge gap is "
                    f"{test_start - train_end - 1}, expected {horizon}"
                )
            if train_end >= test_start:
                raise ValueError(f"horizon {horizon} fold {i}: test row in train")
            for train_end_i, test_start_i, test_end_i in inner[i]:
                if quarter_index(test_end_i) > train_end:
                    raise ValueError(
                        f"horizon {horizon} fold {i}: inner validation escapes train"
                    )
                if quarter_index(train_end_i) >= quarter_index(test_start_i):
                    raise ValueError(
                        f"horizon {horizon} fold {i}: inner test row in inner train"
                    )
                if (
                    quarter_index(test_start_i) - quarter_index(train_end_i) - 1
                    != horizon
                ):
                    raise ValueError(
                        f"horizon {horizon} fold {i}: inner purge is not {horizon}"
                    )


def write_folds(payload: dict, output: Path) -> Path:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n")
    return output


def load_labels(path: Path) -> tuple[str, str]:
    labels = pd.read_csv(path)
    if "quarter" not in labels.columns:
        raise ValueError(f"{path} has no 'quarter' column")
    quarters = labels["quarter"].astype(str).tolist()
    if not quarters:
        raise ValueError(f"{path} has no rows")
    return quarters[0], quarters[-1]
