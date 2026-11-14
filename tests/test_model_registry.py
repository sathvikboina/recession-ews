
import numpy as np
import pytest

from ews.models.registry import MODEL_NAMES, create_model


@pytest.mark.parametrize("model_name", MODEL_NAMES)
def test_model_probabilities(model_name):
    """Check each model can fit and return probabilities."""

    rng = np.random.default_rng(42)

    # Synthetic data, not real recession data
    X = rng.normal(size=(80, 5))
    y = np.array([0, 1] * 40)

    model = create_model(model_name)

    model.fit(X[:60], y[:60])
    probabilities = model.predict_proba(X[60:])

    assert probabilities.shape == (20, 2)
    assert np.isfinite(probabilities).all()
    assert np.all(probabilities >= 0)
    assert np.all(probabilities <= 1)
    assert np.allclose(probabilities.sum(axis=1), 1)
