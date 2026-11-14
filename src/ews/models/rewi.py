
"""Recession Early Warning Index (REWI).

Uses training-fold coefficients and statistics only.
"""

import numpy as np


def build_rewi(X_train, X_test, coefficients):
    """Build and normalize REWI without test leakage.

    X_train and X_test must already be scaled and
    feature-selected using training-fold information.
    """

    X_train = np.asarray(X_train, dtype=float)
    X_test = np.asarray(X_test, dtype=float)
    coefficients = np.asarray(coefficients, dtype=float).ravel()

    if X_train.ndim != 2 or X_test.ndim != 2:
        raise ValueError("Feature arrays must be 2D")

    if X_train.shape[1] != X_test.shape[1]:
        raise ValueError("Train/test feature counts differ")

    if X_train.shape[1] != len(coefficients):
        raise ValueError("Coefficient count does not match features")

    # Linear index: coefficients only, no intercept.
    train_raw = X_train @ coefficients
    test_raw = X_test @ coefficients

    # Normalize using training-fold statistics only.
    mean = float(np.mean(train_raw))
    std = float(np.std(train_raw))

    if not np.isfinite(std) or std == 0:
        raise ValueError("REWI has zero or invalid training variance")

    train_rewi = (train_raw - mean) / std
    test_rewi = (test_raw - mean) / std

    return train_rewi, test_rewi, {
        "mean": mean,
        "std": std,
        "coefficients": coefficients.tolist(),
    }
