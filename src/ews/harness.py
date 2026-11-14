"""Walk-forward harness: fold export and contract checks (Lane 2B).

The generator lives in :mod:`ews.models.folds`; this module serialises its
output, validates the harness contract and writes ``folds.json``. It does not
reimplement fold generation and it does not read model scores.

Status: the exported file is **draft** unless generated with ``approved=True``.
``D-R37`` freezes the current definition (expanding, 80 outer / 40 inner
quarters, step 1, horizons 1/2/4, 2 primary).
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
    labels_file: str | None = None,
    horizons: tuple[int, ...] = HORIZONS,
    step_quarters: int = STEP_QUARTERS,
    approved: bool = False,
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
            "draft": not approved,
            "approved": approved,
            "reason": (
                "frozen under D-R37 on 2026-11-14 (expanding, 80 outer / 40 "
                "inner quarters, step 1, horizons 1/2/4, 2 primary)"
                if approved
                else (
                    "initial training window is not yet approved "
                    "(docs/DECISIONS.md, Lane 2 open decision)"
                )
            ),
            "decision": "D-R37" if approved else None,
            "generated_from": labels_file or str(Path(labels_path)),
            "labels_file": labels_file or str(Path(labels_path)),
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


# ---------------------------------------------------------------------------
# Adapter: fold quarter labels -> row positions for ews.models.nested_runner
# ---------------------------------------------------------------------------

def quarter_positions(index) -> dict[str, int]:
    """Map quarter labels to row positions.

    ``index`` is a PeriodIndex, a sequence of quarter strings, or a DataFrame
    with a ``quarter`` column. Duplicate quarters are rejected so a position
    cannot silently mean two rows.
    """
    if isinstance(index, pd.DataFrame):
        if "quarter" not in index.columns:
            raise ValueError("DataFrame index source has no 'quarter' column")
        values = index["quarter"].astype(str).tolist()
    else:
        values = [str(value) for value in index]

    positions: dict[str, int] = {}
    for position, quarter in enumerate(values):
        if quarter in positions:
            raise ValueError(f"duplicate quarter in index: {quarter}")
        positions[quarter] = position
    if not positions:
        raise ValueError("index is empty")
    return positions


def _span(positions: dict[str, int], start: str, end: str) -> list[int]:
    if start not in positions:
        raise KeyError(f"quarter {start} is not in the feature table")
    if end not in positions:
        raise KeyError(f"quarter {end} is not in the feature table")
    first = positions[start]
    last = positions[end]
    if first > last:
        raise ValueError(f"span {start}..{end} is reversed")
    return list(range(first, last + 1))


def fold_index_splits(
    payload: dict,
    index,
    *,
    horizon: int = PRIMARY_HORIZON,
    fold: int | None = None,
) -> list[dict] | dict:
    """Map fold quarter boundaries onto row positions.

    Returns one record per outer fold::

        {"fold": i, "outer_train": [...], "outer_test": [...],
         "inner_splits": [(train, validation), ...]}

    Positions index the rows of the feature table used to build ``X``/``y``.
    Every inner train/validation split lies inside the outer training block,
    and the purge gap before each test/validation block equals the horizon.
    """
    key = str(horizon)
    if key not in payload.get("horizons", {}):
        raise KeyError(f"horizon {horizon} is not in the fold payload")
    block = payload["horizons"][key]
    positions = quarter_positions(index)

    records = []
    for i, (outer, inner) in enumerate(zip(block["outer"], block["inner"])):
        if fold is not None and i != fold:
            continue

        outer_train = _span(positions, outer["train_start"], outer["train_end"])
        outer_test = _span(positions, outer["test_start"], outer["test_end"])
        if outer_train[-1] + horizon >= outer_test[0]:
            raise ValueError(
                f"horizon {horizon} fold {i}: purge gap shorter than {horizon}"
            )

        inner_splits = []
        for train_end_i, test_start_i, test_end_i in inner:
            train = _span(positions, outer["train_start"], train_end_i)
            validation = _span(positions, test_start_i, test_end_i)
            if train[-1] + horizon >= validation[0]:
                raise ValueError(
                    f"horizon {horizon} fold {i}: inner purge shorter than {horizon}"
                )
            if validation[-1] > outer_train[-1]:
                raise ValueError(
                    f"horizon {horizon} fold {i}: inner validation escapes outer train"
                )
            inner_splits.append((train, validation))

        records.append(
            {
                "fold": i,
                "outer_train": outer_train,
                "outer_test": outer_test,
                "inner_splits": inner_splits,
            }
        )

    if fold is not None:
        if not records:
            raise IndexError(f"fold {fold} is out of range for horizon {horizon}")
        return records[0]
    return records

