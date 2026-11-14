
from ews.models.folds import (
    generate_outer_folds,
    generate_inner_folds,
    quarter_index,
    quarter_label,
)

import pytest

from ews.models.folds import (
    generate_outer_folds,
    quarter_index,
    quarter_label,
)


def test_quarter_conversion():
    assert quarter_index("1990Q1") == 1990 * 4
    assert quarter_label(1990 * 4) == "1990Q1"


def test_invalid_quarter():
    with pytest.raises(ValueError):
        quarter_index("2026Q5")


def test_first_fold_boundaries():
    folds = generate_outer_folds(
        start="1990Q1",
        last_scored="2026Q1",
        initial_train_quarters=80,
        horizon=2,
    )

    first = folds[0]

    assert first.train_start == "1990Q1"
    assert first.train_end == "2009Q2"
    assert first.test_start == "2010Q1"
    assert first.purge_quarters == 2


def test_purge_gap_in_every_fold():
    folds = generate_outer_folds(
        start="1990Q1",
        last_scored="2026Q1",
        initial_train_quarters=80,
        horizon=2,
    )

    for fold in folds:
        gap = (
            quarter_index(fold.test_start)
            - quarter_index(fold.train_end)
            - 1
        )
        assert gap == 2


def test_last_scored_quarter():
    folds = generate_outer_folds(
        start="1990Q1",
        last_scored="2026Q1",
        initial_train_quarters=80,
        horizon=2,
    )

    assert folds[-1].test_end == "2026Q1"


def test_number_of_folds():
    folds = generate_outer_folds(
        start="1990Q1",
        last_scored="2026Q1",
        initial_train_quarters=80,
        horizon=2,
    )

    assert len(folds) == 65


def test_invalid_initial_size():
    with pytest.raises(ValueError):
        generate_outer_folds(
            "1990Q1",
            "2026Q1",
            initial_train_quarters=0,
        )




def test_inner_folds_stay_inside_outer_training():
    outer = generate_outer_folds(
        start="1990Q1",
        last_scored="2026Q1",
        initial_train_quarters=80,
        horizon=2,
    )[0]

    inner = generate_inner_folds(
        outer_fold=outer,
        initial_train_quarters=40,
        horizon=2,
    )

    assert len(inner) > 0

    for fold in inner:
        assert quarter_index(fold.train_start) >= quarter_index(
            outer.train_start
        )
        assert quarter_index(fold.test_end) <= quarter_index(
            outer.train_end
        )


def test_inner_folds_have_two_quarter_purge():
    outer = generate_outer_folds(
        start="1990Q1",
        last_scored="2026Q1",
        initial_train_quarters=80,
        horizon=2,
    )[0]

    inner = generate_inner_folds(
        outer_fold=outer,
        initial_train_quarters=40,
        horizon=2,
    )

    for fold in inner:
        gap = (
            quarter_index(fold.test_start)
            - quarter_index(fold.train_end)
            - 1
        )

        assert gap == 2


def test_inner_validation_is_chronological():
    outer = generate_outer_folds(
        start="1990Q1",
        last_scored="2026Q1",
        initial_train_quarters=80,
        horizon=2,
    )[0]

    inner = generate_inner_folds(
        outer_fold=outer,
        initial_train_quarters=40,
        horizon=2,
    )

    for fold in inner:
        assert quarter_index(fold.train_end) < quarter_index(
            fold.test_start
        )


def test_inner_folds_reject_insufficient_history():
    outer = generate_outer_folds(
        start="1990Q1",
        last_scored="2026Q1",
        initial_train_quarters=80,
        horizon=2,
    )[0]

    with pytest.raises(ValueError):
        generate_inner_folds(
            outer_fold=outer,
            initial_train_quarters=100,
            horizon=2,
        )
