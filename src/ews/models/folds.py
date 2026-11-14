
"""Draft walk-forward fold generator.

No official fold file is written here.
The 20-year initial training period requires team approval.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Fold:
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    purge_quarters: int


def quarter_index(label: str) -> int:
    """Convert YYYYQn into a chronological integer."""
    if (
        len(label) != 6
        or label[4] != "Q"
        or not label[:4].isdigit()
        or label[5] not in "1234"
    ):
        raise ValueError(f"Invalid quarter: {label}")

    year = int(label[:4])
    quarter = int(label[5])
    return year * 4 + quarter - 1


def quarter_label(index: int) -> str:
    """Convert a chronological integer into YYYYQn."""
    year, offset = divmod(index, 4)
    return f"{year:04d}Q{offset + 1}"


def generate_outer_folds(
    start: str,
    last_scored: str,
    initial_train_quarters: int,
    horizon: int = 2,
    step_quarters: int = 1,
) -> list[Fold]:
    """Generate draft expanding-window folds.

    The last `horizon` quarters before each test
    block are purged from training.
    """
    if initial_train_quarters <= 0:
        raise ValueError("Initial training size must be positive")

    if horizon <= 0:
        raise ValueError("Horizon must be positive")

    if step_quarters <= 0:
        raise ValueError("Step must be positive")

    first = quarter_index(start)
    last = quarter_index(last_scored)

    first_test = first + initial_train_quarters

    if first_test > last:
        raise ValueError("No test quarters available")

    folds = []

    for test_idx in range(
        first_test,
        last + 1,
        step_quarters,
    ):
        train_end_idx = test_idx - horizon - 1

        if train_end_idx < first:
            raise ValueError("Insufficient training history")

        folds.append(
            Fold(
                train_start=start,
                train_end=quarter_label(train_end_idx),
                test_start=quarter_label(test_idx),
                test_end=quarter_label(
                    min(test_idx + step_quarters - 1, last)
                ),
                purge_quarters=horizon,
            )
        )

    return folds


def generate_inner_folds(
    outer_fold: Fold,
    initial_train_quarters: int,
    horizon: int = 2,
    step_quarters: int = 1,
) -> list[Fold]:
    """Generate expanding inner folds inside outer training data.

    The inner validation blocks never extend beyond the
    outer fold's training end. A horizon-sized purge
    separates inner training and validation.
    """
    if initial_train_quarters <= 0:
        raise ValueError("Initial training size must be positive")

    if horizon <= 0:
        raise ValueError("Horizon must be positive")

    if step_quarters <= 0:
        raise ValueError("Step must be positive")

    outer_start = quarter_index(outer_fold.train_start)
    outer_end = quarter_index(outer_fold.train_end)

    if outer_end < outer_start:
        raise ValueError("Invalid outer training period")

    first_validation = outer_start + initial_train_quarters

    if first_validation > outer_end:
        raise ValueError("Insufficient data for inner folds")

    folds = generate_outer_folds(
        start=outer_fold.train_start,
        last_scored=outer_fold.train_end,
        initial_train_quarters=initial_train_quarters,
        horizon=horizon,
        step_quarters=step_quarters,
    )

    for fold in folds:
        if quarter_index(fold.test_end) > outer_end:
            raise ValueError("Inner validation exceeds outer training")

        if (
            quarter_index(fold.test_start)
            - quarter_index(fold.train_end)
            - 1
        ) != horizon:
            raise ValueError("Incorrect inner purge gap")

    return folds
