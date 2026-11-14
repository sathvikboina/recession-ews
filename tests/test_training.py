
import numpy as np
import pytest

from ews.models.training import expanding_window_splits


def test_expanding_window_order():
    folds = list(
        expanding_window_splits(
            n_samples=100,
            initial_train_size=80,
            test_size=1,
        )
    )

    assert len(folds) == 20

    for train_idx, test_idx in folds:
        assert train_idx[-1] < test_idx[0]
        assert train_idx[0] == 0


def test_expanding_window_expands():
    folds = list(
        expanding_window_splits(
            n_samples=90,
            initial_train_size=80,
            test_size=1,
        )
    )

    assert len(folds[0][0]) == 80
    assert len(folds[1][0]) == 81
    assert len(folds[-1][0]) == 89


def test_expanding_window_gap():
    folds = list(
        expanding_window_splits(
            n_samples=90,
            initial_train_size=80,
            test_size=1,
            gap=2,
        )
    )

    assert len(folds) == 8

    for train_idx, test_idx in folds:
        assert test_idx[0] - train_idx[-1] == 3


@pytest.mark.parametrize(
    "kwargs",
    [
        {"n_samples": 0, "initial_train_size": 80},
        {"n_samples": 100, "initial_train_size": 0},
        {"n_samples": 100, "initial_train_size": 80,
         "test_size": 0},
        {"n_samples": 100, "initial_train_size": 80,
         "gap": -1},
    ],
)
def test_invalid_split_settings(kwargs):
    with pytest.raises(ValueError):
        list(expanding_window_splits(**kwargs))

from ews.models.training import scale_train_test


def test_scaler_uses_training_data_only():
    X_train = np.array([
        [1.0, 10.0],
        [2.0, 20.0],
        [3.0, 30.0],
    ])

    X_test = np.array([
        [100.0, 1000.0],
    ])

    train_scaled, test_scaled, scaler = (
        scale_train_test(X_train, X_test)
    )

    # Scaler statistics must come from training only.
    np.testing.assert_allclose(
        scaler.mean_,
        [2.0, 20.0],
    )

    # Training features should have mean zero.
    np.testing.assert_allclose(
        train_scaled.mean(axis=0),
        [0.0, 0.0],
        atol=1e-10,
    )

    # Extreme test values must not alter training stats.
    assert test_scaled[0, 0] > 10
    assert test_scaled[0, 1] > 10



from ews.models.training import select_features


def test_feature_selection_uses_training_only():
    rng = np.random.default_rng(42)

    X_train = rng.normal(size=(100, 6))

    y_train = (
        X_train[:, 0] + X_train[:, 1] > 0
    ).astype(int)

    X_test = rng.normal(size=(20, 6))

    result1 = select_features(
        X_train, y_train, X_test
    )

    # Deliberately change only the test observations.
    X_test_changed = X_test * 1000

    result2 = select_features(
        X_train, y_train, X_test_changed
    )

    mask1 = result1[2]
    mask2 = result2[2]

    # Test observations cannot change feature selection.
    np.testing.assert_array_equal(mask1, mask2)

    assert mask1.sum() >= 1
    assert result1[0].shape[1] == mask1.sum()



def test_expanding_window_with_horizon_gap():
    from ews.models.training import expanding_window_splits

    splits = list(
        expanding_window_splits(
            n_samples=100,
            initial_train_size=80,
            test_size=1,
            gap=2,
        )
    )

    assert len(splits) == 18

    first_train, first_test = splits[0]

    assert len(first_train) == 80
    assert first_test.tolist() == [82]

    # No training label may extend into
    # the first test observation.
    assert first_train.max() + 2 < first_test.min()

    for train_idx, test_idx in splits:
        assert train_idx.max() + 2 < test_idx.min()
        assert len(test_idx) == 1

