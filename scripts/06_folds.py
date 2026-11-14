#!/usr/bin/env python3
"""scripts/06_folds.py

Deterministic expanding-window folds generator for horizons 1Q, 2Q (primary), and 4Q.
Initial train 60 quarters (15 years); test blocks of 4 quarters; gap/embargo equal
to the horizon so no test row can appear in training.
Outputs data/features/folds.json and prints its SHA-256 checksum.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
FEATURES_DIR = PROJECT / "data" / "features"
FOLDS_FILE = FEATURES_DIR / "folds.json"

WINDOW_START = "1990Q1"
WINDOW_END = "2026Q3"
INITIAL_TRAIN_QUARTERS = 60
TEST_BLOCK_QUARTERS = 4
HORIZONS = [1, 2, 4]
PRIMARY_HORIZON = 2


def quarter_index(label: str) -> int:
    """Convert YYYYQn into a chronological integer."""
    year = int(label[:4])
    quarter = int(label[5])
    return year * 4 + quarter - 1


def quarter_label(index: int) -> str:
    """Convert a chronological integer into YYYYQn."""
    year, offset = divmod(index, 4)
    return f"{year:04d}Q{offset + 1}"


def generate_folds_for_horizon(
    start: str = WINDOW_START,
    end: str = WINDOW_END,
    initial_train: int = INITIAL_TRAIN_QUARTERS,
    test_block: int = TEST_BLOCK_QUARTERS,
    horizon: int = 2,
) -> list[dict[str, Any]]:
    """Generate expanding-window folds for a given horizon."""
    first_idx = quarter_index(start)
    last_idx = quarter_index(end)

    first_test_idx = first_idx + initial_train
    folds = []

    fold_idx = 0
    for test_start_idx in range(first_test_idx, last_idx + 1, test_block):
        test_end_idx = min(test_start_idx + test_block - 1, last_idx)
        # Gap / embargo equals horizon quarters
        train_end_idx = test_start_idx - horizon - 1

        if train_end_idx < first_idx:
            raise ValueError(f"Insufficient training history for horizon {horizon}")

        # Verify no test row can appear in training
        assert train_end_idx < test_start_idx, "Train end must strictly precede test start"
        assert (test_start_idx - train_end_idx - 1) == horizon, "Purge gap must equal horizon"

        # Generate inner validation folds for time-ordered hyperparameter tuning
        # Uses expanding window within train set, 4-quarter test blocks
        inner_folds = []
        inner_min_train = max(20, initial_train // 2)
        inner_first_test = first_idx + inner_min_train
        inner_idx = 0
        for in_test_start in range(inner_first_test, train_end_idx + 1, test_block):
            in_test_end = min(in_test_start + test_block - 1, train_end_idx)
            in_train_end = in_test_start - horizon - 1
            if in_train_end >= first_idx:
                inner_folds.append({
                    "inner_fold_id": f"inner_{inner_idx:02d}",
                    "train_start": start,
                    "train_end": quarter_label(in_train_end),
                    "val_start": quarter_label(in_test_start),
                    "val_end": quarter_label(in_test_end),
                    "purge_quarters": horizon,
                })
                inner_idx += 1

        folds.append({
            "fold_id": f"fold_{fold_idx:02d}",
            "train_start": start,
            "train_end": quarter_label(train_end_idx),
            "test_start": quarter_label(test_start_idx),
            "test_end": quarter_label(test_end_idx),
            "purge_quarters": horizon,
            "n_train_quarters": train_end_idx - first_idx + 1,
            "n_test_quarters": test_end_idx - test_start_idx + 1,
            "inner_folds": inner_folds,
        })
        fold_idx += 1

    return folds


def build_folds_payload() -> dict[str, Any]:
    """Construct full folds payload for all horizons."""
    payload: dict[str, Any] = {
        "metadata": {
            "window_start": WINDOW_START,
            "window_end": WINDOW_END,
            "initial_train_quarters": INITIAL_TRAIN_QUARTERS,
            "test_block_quarters": TEST_BLOCK_QUARTERS,
            "primary_horizon": PRIMARY_HORIZON,
            "horizons": HORIZONS,
        },
        "folds": {}
    }

    for h in HORIZONS:
        payload["folds"][f"{h}Q"] = generate_folds_for_horizon(
            start=WINDOW_START,
            end=WINDOW_END,
            initial_train=INITIAL_TRAIN_QUARTERS,
            test_block=TEST_BLOCK_QUARTERS,
            horizon=h,
        )

    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic expanding folds")
    parser.add_argument("--out", type=Path, default=FOLDS_FILE)
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)

    payload = build_folds_payload()
    json_bytes = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")

    with open(args.out, "wb") as fh:
        fh.write(json_bytes)

    digest = hashlib.sha256(json_bytes).hexdigest()
    print(f"Folds written: {args.out}")
    print(f"SHA-256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
