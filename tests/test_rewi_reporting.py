import numpy as np
import pytest
from ews.models.rewi_reporting import coefficient_table, feature_stability, export_rewi_reporting


def test_stability_counts_missing_features_as_zero():
    a = coefficient_table(['gdp', 'spread'], [0.5, 0], 'fold-1')
    b = coefficient_table(['gdp', 'claims'], [-0.2, 0.8], 'fold-2')
    result = feature_stability([a, b]).set_index('feature')
    assert result.loc['gdp', 'selection_frequency'] == 1.0
    assert result.loc['spread', 'selection_frequency'] == 0.0
    assert result.loc['claims', 'selection_frequency'] == 0.5
    assert np.isclose(result.loc['gdp', 'mean_coefficient'], 0.15)


def test_intercept_rejected():
    with pytest.raises(ValueError, match='intercept'):
        coefficient_table(['gdp', 'intercept'], [0.3, 0.1], 'fold-1')


def test_feature_count_must_match():
    with pytest.raises(ValueError):
        coefficient_table(['gdp'], [0.2, 0.3], 'fold-1')


def test_exports(tmp_path):
    a = coefficient_table(['gdp'], [0.4], 'fold-1')
    result = export_rewi_reporting([a], tmp_path)
    assert len(result) == 1
    assert (tmp_path / 'rewi_fold_coefficients.csv').exists()
    assert (tmp_path / 'feature_stability.csv').exists()
