
"""Time-ordered validation helpers for recession models.

Development utilities only. Production fold boundaries
must come from the approved fold artifact.
"""

from __future__ import annotations

import numpy as np


def expanding_window_splits(
    n_samples: int,
    initial_train_size: int,
    test_size: int = 1,
    gap: int = 0,
):
    """Generate expanding-window train/test index pairs.

    Parameters
    ----------
    n_samples:
        Number of time-ordered observations.
    initial_train_size:
        Number of observations in the first training block.
    test_size:
        Number of observations in each test block.
    gap:
        Number of observations excluded between training
        and testing.

    Yields
    ------
    train_idx, test_idx:
        NumPy arrays containing chronological row indices.
    """

    if n_samples <= 0:
        raise ValueError("n_samples must be positive")

    if initial_train_size <= 0:
        raise ValueError("initial_train_size must be positive")

    if test_size <= 0:
        raise ValueError("test_size must be positive")

    if gap < 0:
        raise ValueError("gap cannot be negative")

    test_start = initial_train_size + gap

    while test_start + test_size <= n_samples:
        train_end = test_start - gap

        train_idx = np.arange(0, train_end)
        test_idx = np.arange(
            test_start,
            test_start + test_size,
        )

        yield train_idx, test_idx

        test_start += test_size

from sklearn.preprocessing import StandardScaler


def scale_train_test(X_train, X_test):
    """Fit scaling on training data only.

    The test data is transformed using the
    training data's mean and standard deviation.
    """

    scaler = StandardScaler()

    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    return X_train_scaled, X_test_scaled, scaler


from sklearn.linear_model import LogisticRegression


def select_features(
    X_train,
    y_train,
    X_test,
    C=1.0,
    l1_ratio=0.5,
):
    """Select features using training-only Elastic Net.

    C and l1_ratio must eventually be chosen through
    time-ordered inner-fold tuning.
    """

    selector = LogisticRegression(
        penalty="elasticnet",
        solver="saga",
        C=C,
        l1_ratio=l1_ratio,
        class_weight="balanced",
        max_iter=5000,
        random_state=42,
    )

    selector.fit(X_train, y_train)

    selected_mask = selector.coef_[0] != 0

    if not selected_mask.any():
        raise ValueError(
            "Elastic Net selected no features. "
            "Handle this through the approved tuning policy."
        )

    X_train_selected = X_train[:, selected_mask]
    X_test_selected = X_test[:, selected_mask]

    return (
        X_train_selected,
        X_test_selected,
        selected_mask,
        selector,
    )
