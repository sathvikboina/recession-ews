"""Fixture-capable, leakage-aware model runner. NOT the frozen USA headline.

Requires chronological, binary-labelled training data and externally supplied fold
boundaries. Does not generate or replace the team's official folds.json.
"""
from __future__ import annotations
import warnings
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss
from sklearn.utils.class_weight import compute_sample_weight
from .registry import MODEL_NAMES, create_model
from .evaluation import pooled_metrics, choose_threshold_inner, equal_weight_top_three


def _prep(x_train, x_test):
    imputer = SimpleImputer(strategy="median", keep_empty_features=True)
    a = imputer.fit_transform(x_train)
    b = imputer.transform(x_test)
    scaler = StandardScaler()
    return scaler.fit_transform(a), scaler.transform(b)


def _selector(a, y, b, c=0.1, ratio=0.5):
    selector = LogisticRegression(penalty="elasticnet", solver="saga", C=c,
                                  l1_ratio=ratio, class_weight="balanced",
                                  max_iter=3000, random_state=42)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        selector.fit(a, y)
    mask = np.abs(selector.coef_[0]) > 1e-9
    # Contract requires a declared logistic fallback, not arbitrary forced features.
    if not mask.any():
        return a, b, mask, selector, True
    return a[:, mask], b[:, mask], mask, selector, False


def _fit_predict(name, a, y, b, seed=42):
    if name == "mlp":
        probabilities = []
        for s in (0, 1, 2):
            model = create_model(name, seed=s)
            model.set_params(max_iter=300, early_stopping=True, n_iter_no_change=10)
            weights = compute_sample_weight("balanced", y)
            # sklearn versions differ in MLP sample_weight support.
            try:
                model.fit(a, y, sample_weight=weights)
            except TypeError:
                raise RuntimeError("Installed sklearn MLP lacks sample_weight; cannot satisfy balanced MLP contract")
            probabilities.append(model.predict_proba(b)[:, 1])
        return np.mean(probabilities, axis=0)
    model = create_model(name, seed=seed)
    if name == "xgboost":
        pos = int(np.sum(y == 1)); neg = int(np.sum(y == 0))
        model.set_params(scale_pos_weight=neg / pos)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model.fit(a, y)
    return model.predict_proba(b)[:, 1]


def fit_one_fold(X, y, train_idx, test_idx, *, model_names=MODEL_NAMES, seed=42):
    """Train once on supplied outer indices; test labels never used in fitting.

    This is a fixture runner, not nested tuning. Threshold is not tuned here.
    """
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=int)
    train_idx = np.asarray(train_idx, dtype=int)
    test_idx = np.asarray(test_idx, dtype=int)
    if X.ndim != 2 or len(X) != len(y) or not len(train_idx) or not len(test_idx):
        raise ValueError("Invalid data or indices")
    if np.any(train_idx < 0) or np.any(test_idx >= len(y)) or np.any(train_idx >= len(y)):
        raise ValueError("Indices outside dataset")
    if train_idx.max() >= test_idx.min():
        raise ValueError("Fold must be strictly chronological")
    if len(np.unique(y[train_idx])) != 2:
        raise ValueError("Training fold needs both classes")
    a, b = _prep(X[train_idx], X[test_idx])
    selected_a, selected_b, mask, selector, fallback = _selector(a, y[train_idx], b)
    if fallback:
        selected_a, selected_b = a, b
    result = {"selected_features": np.flatnonzero(mask).tolist(), "fallback": fallback,
              "predictions": {}, "rewi": None}
    if not fallback:
        raw_rewi = selected_b @ selector.coef_[0, mask]
        result["rewi"] = {"raw": raw_rewi.tolist(),
                          "prob": selector.predict_proba(b)[:, 1].tolist(),
                          "intercept": float(selector.intercept_[0])}
    for name in model_names:
        result["predictions"][name] = _fit_predict(name, selected_a, y[train_idx], selected_b, seed).tolist()
    return result


def run_fixture(seed=42):
    """Synthetic smoke test only: no real recession forecast claims."""
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(140, 8))
    y = (X[:, 0] + 0.6 * X[:, 1] + rng.normal(size=140) * 0.8 > 0.2).astype(int)
    # 2-quarter purge: 0..99 train, 100..101 gap, 102..119 test.
    fold = fit_one_fold(X, y, np.arange(100), np.arange(102, 120))
    rows = []
    for name, probabilities in fold["predictions"].items():
        metrics = pooled_metrics(y[102:120], probabilities)
        rows.append({"model": name, **metrics})
    return pd.DataFrame(rows), fold
