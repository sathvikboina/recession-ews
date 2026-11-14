import numpy as np
import pytest
from ews.models.nested_runner import evaluate_nested_fold


def _data():
    rng = np.random.default_rng(42)
    x = rng.normal(size=(110, 4))
    y = (x[:, 0] + rng.normal(size=110) * .8 > 0).astype(int)
    return x, y


def test_nested_fold_runs_with_purge():
    x, y = _data()
    result = evaluate_nested_fold(
        x, y, np.arange(90), np.array([92]),
        [(np.arange(45), np.arange(47, 60)),
         (np.arange(60), np.arange(62, 75))], horizon=2)
    assert len(result['selected_models']) == 3
    assert len(result['outer_probabilities']) == 1
    assert 0 <= result['outer_probabilities'][0] <= 1
    assert result['inner_folds_used'] == 2


def test_rejects_inner_leakage():
    x, y = _data()
    with pytest.raises(ValueError, match='purge'):
        evaluate_nested_fold(x, y, np.arange(90), np.array([92]),
                             [(np.arange(45), np.arange(46, 60))])


def test_rejects_outer_leakage():
    x, y = _data()
    with pytest.raises(ValueError, match='purge'):
        evaluate_nested_fold(x, y, np.arange(90), np.array([90]),
                             [(np.arange(45), np.arange(47, 60))])
