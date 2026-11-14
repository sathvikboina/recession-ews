
import numpy as np

from ews.models.rewi import build_rewi


def test_rewi_training_normalization():
    X_train = np.array([
        [1.0, 2.0],
        [2.0, 3.0],
        [3.0, 4.0],
        [4.0, 5.0],
    ])

    X_test = np.array([[10.0, 20.0]])
    coefficients = np.array([0.6, -0.2])

    train_rewi, test_rewi, info = build_rewi(
        X_train, X_test, coefficients
    )

    assert np.isclose(train_rewi.mean(), 0.0)
    assert np.isclose(train_rewi.std(), 1.0)
    assert len(test_rewi) == 1
    assert len(info["coefficients"]) == 2


def test_rewi_does_not_use_test_statistics():
    X_train = np.array([
        [1.0, 2.0],
        [2.0, 3.0],
        [3.0, 4.0],
    ])

    coefficients = np.array([0.5, 0.3])

    result1 = build_rewi(
        X_train,
        np.array([[5.0, 6.0]]),
        coefficients,
    )

    result2 = build_rewi(
        X_train,
        np.array([[500.0, 600.0]]),
        coefficients,
    )

    # Changing test data must not change
    # the training index or normalization.
    np.testing.assert_allclose(result1[0], result2[0])

    assert result1[2]["mean"] == result2[2]["mean"]
    assert result1[2]["std"] == result2[2]["std"]
