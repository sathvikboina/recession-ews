"""Nested, purged walk-forward model ranking; not an official USA headline.

Caller supplies approved outer and inner index splits. Inner validation alone
ranks candidate models and chooses the decision threshold.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score
from .runner import fit_one_fold
from .evaluation import pooled_metrics, choose_threshold_inner, equal_weight_top_three


def evaluate_nested_fold(X, y, outer_train, outer_test, inner_splits, *,
                         model_names=("logistic", "elastic_net", "random_forest"),
                         horizon=2, seed=42):
    """Fit candidates on purged inner folds, then untouched outer test data.

    Index arrays use positions in X/y, not relative positions. Every inner
    train and validation index must be within the outer training block.
    """
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=int)
    outer_train = np.asarray(outer_train, dtype=int)
    outer_test = np.asarray(outer_test, dtype=int)
    if horizon < 1 or len(outer_train) == 0 or len(outer_test) == 0:
        raise ValueError("Invalid horizon or empty outer split")
    if len(set(model_names)) < 3:
        raise ValueError("At least three distinct candidate models required")
    if outer_train.min() < 0 or outer_test.max() >= len(y) or outer_train.max() + horizon >= outer_test.min():
        raise ValueError("Outer split must have the required purge")
    if not np.all(np.diff(outer_train) > 0) or not np.all(np.diff(outer_test) > 0):
        raise ValueError("Outer indices must be sorted and unique")
    allowed = set(outer_train.tolist())
    validations = {name: [] for name in model_names}
    labels = []
    inner_count = 0
    for train, val in inner_splits:
        train = np.asarray(train, dtype=int)
        val = np.asarray(val, dtype=int)
        if len(train) == 0 or len(val) == 0:
            raise ValueError("Empty inner split")
        if not set(train.tolist()).issubset(allowed) or not set(val.tolist()).issubset(allowed):
            raise ValueError("Inner split outside outer training block")
        if not np.all(np.diff(train) > 0) or not np.all(np.diff(val) > 0):
            raise ValueError("Inner indices must be sorted and unique")
        if train.max() + horizon >= val.min():
            raise ValueError("Inner split lacks required purge")
        if len(np.unique(y[train])) < 2:
            continue  # Cannot fit a classifier to a single class
        fitted = fit_one_fold(X, y, train, val, model_names=model_names, seed=seed)
        labels.extend(y[val].tolist())
        for name in model_names:
            validations[name].extend(fitted["predictions"][name])
        inner_count += 1
    if not inner_count or len(set(labels)) < 2:
        raise ValueError("Inner validation needs both classes to rank PR-AUC")
    inner_scores = {name: float(average_precision_score(labels, predictions))
                    for name, predictions in validations.items()}
    selected = sorted(inner_scores, key=lambda name: (-inner_scores[name], name))[:3]
    inner_ensemble = np.mean(np.array([validations[name] for name in selected]), axis=0)
    threshold = choose_threshold_inner(labels, inner_ensemble)
    fitted_outer = fit_one_fold(X, y, outer_train, outer_test,
                                model_names=model_names, seed=seed)
    ensemble, ranked = equal_weight_top_three(fitted_outer["predictions"], inner_scores)
    return {
        "selected_models": ranked,
        "inner_pr_auc": inner_scores,
        "threshold": threshold,
        "outer_quarters": outer_test.tolist(),
        "outer_probabilities": ensemble.tolist(),
        "outer_metrics": pooled_metrics(y[outer_test], ensemble, threshold=threshold),
        "inner_folds_used": inner_count,
        "selected_features": fitted_outer["selected_features"],
        "feature_fallback": fitted_outer["fallback"],
    }
