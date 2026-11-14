import numpy as np
import pytest
from ews.models.evaluation import (pooled_metrics, choose_threshold_inner,
                                   equal_weight_top_three, episode_detection)


def test_pooled_metrics():
    result = pooled_metrics([0, 1, 0, 1], [0.1, 0.9, 0.2, 0.8])
    assert result['pr_auc'] == pytest.approx(1)
    assert result['tp'] == 2 and result['tn'] == 2


def test_single_class_auc_undefined():
    result = pooled_metrics([0, 0], [0.1, 0.2])
    assert np.isnan(result['pr_auc']) and np.isnan(result['roc_auc'])


def test_threshold():
    assert choose_threshold_inner([0, 1], [0.1, 0.9]) == pytest.approx(0.9)


def test_ensemble_uses_inner_scores():
    p, names = equal_weight_top_three({'a': [0.1], 'b': [0.2], 'c': [0.3], 'd': [0.9]},
                                      {'a': 0.8, 'b': 0.9, 'c': 0.7, 'd': 0.1})
    assert names == ['b', 'a', 'c']
    assert p[0] == pytest.approx(0.2)


def test_episode_lead():
    result = episode_detection(['2019Q4'], ['2019Q2'], horizon=2)
    assert bool(result.loc[0, 'detected'])
    assert result.loc[0, 'lead_quarters'] == 2
