import numpy as np
import pytest
from ews.models.runner import fit_one_fold


def test_fixture_logistic_and_rewi():
    rng = np.random.default_rng(1)
    X = rng.normal(size=(100, 5))
    y = (X[:, 0] + X[:, 1] > 0).astype(int)
    out = fit_one_fold(X, y, np.arange(70), np.arange(72, 80), model_names=("logistic",))
    assert len(out["predictions"]["logistic"]) == 8
    assert all(0 <= p <= 1 for p in out["predictions"]["logistic"])


def test_reject_overlap():
    rng = np.random.default_rng(1)
    X = rng.normal(size=(100, 3))
    y = np.arange(100) % 2
    with pytest.raises(ValueError):
        fit_one_fold(X, y, np.arange(70), np.arange(69, 75), model_names=("logistic",))
