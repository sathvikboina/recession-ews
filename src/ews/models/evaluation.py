"""Out-of-sample evaluation helpers for the USA recession early-warning project.

Only evaluate predictions produced on untouched outer test quarters.
Undefined metrics remain NaN, never silently replaced with zero.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (average_precision_score, roc_auc_score, brier_score_loss,
                             precision_score, recall_score, f1_score, accuracy_score,
                             confusion_matrix)


def pooled_metrics(y_true, probability, threshold=0.5):
    y = np.asarray(y_true)
    p = np.asarray(probability, dtype=float)
    if y.ndim != 1 or p.ndim != 1 or len(y) != len(p):
        raise ValueError('Targets and probabilities must be equal-length vectors')
    valid = pd.notna(y) & np.isfinite(p)
    y = np.asarray(y[valid], dtype=int)
    p = p[valid]
    if len(y) == 0:
        raise ValueError('No scorable observations')
    if not np.isin(y, [0, 1]).all():
        raise ValueError('Targets must be binary')
    if not np.all((p >= 0) & (p <= 1)):
        raise ValueError('Probabilities must lie in [0,1]')
    pred = (p >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    both = len(np.unique(y)) == 2
    return {
        'n': int(len(y)), 'n_positive': int(y.sum()),
        'pr_auc': float(average_precision_score(y, p)) if both else float('nan'),
        'roc_auc': float(roc_auc_score(y, p)) if both else float('nan'),
        'precision': float(precision_score(y, pred, zero_division=0)),
        'recall': float(recall_score(y, pred, zero_division=0)) if y.sum() else float('nan'),
        'f1': float(f1_score(y, pred, zero_division=0)),
        'accuracy': float(accuracy_score(y, pred)),
        'brier': float(brier_score_loss(y, p)),
        'tn': int(tn), 'fp': int(fp), 'fn': int(fn), 'tp': int(tp),
    }


def choose_threshold_inner(y_true, probability):
    """Maximize F1 on INNER validation predictions only; tie -> lowest threshold."""
    y = np.asarray(y_true, dtype=int)
    p = np.asarray(probability, dtype=float)
    if len(y) != len(p) or not len(y) or not np.isfinite(p).all():
        raise ValueError('Invalid inner-validation predictions')
    candidates = np.unique(np.r_[0.0, p, 1.0])
    scores = np.array([f1_score(y, p >= t, zero_division=0) for t in candidates])
    return float(candidates[np.argmax(scores)])


def equal_weight_top_three(probabilities, inner_scores):
    """Average OUTER predictions of three configurations ranked by INNER PR-AUC.

    probabilities: mapping config_id -> array of untouched outer-test probabilities.
    inner_scores: mapping config_id -> pooled inner-validation PR-AUC.
    This function does not fit models or select on outer scores.
    """
    if len(inner_scores) < 3:
        raise ValueError('At least three candidate configurations are required')
    if not set(inner_scores).issubset(probabilities):
        raise ValueError('Missing outer predictions for an inner-ranked configuration')
    if any(not np.isfinite(score) for score in inner_scores.values()):
        raise ValueError('All candidate inner scores must be finite')
    ranked = sorted(inner_scores, key=lambda name: (-inner_scores[name], name))[:3]
    arrays = [np.asarray(probabilities[name], dtype=float) for name in ranked]
    if len({len(a) for a in arrays}) != 1 or not all(np.isfinite(a).all() for a in arrays):
        raise ValueError('Outer prediction vectors must be finite and equally sized')
    return np.mean(np.stack(arrays), axis=0), ranked


def episode_detection(peaks, predicted_warning_quarters, horizon=2):
    """Episode-level detection against peak quarters using warnings in preceding H quarters.

    Returns one row per peak. False-warning episodes require a separate
    definition of warning clustering and should not be inferred from this table.
    """
    if horizon <= 0:
        raise ValueError('horizon must be positive')
    warnings = set(pd.PeriodIndex(list(predicted_warning_quarters), freq='Q'))
    rows = []
    for peak in pd.PeriodIndex(list(peaks), freq='Q'):
        matched = sorted((q for q in warnings if 1 <= (peak.ordinal - q.ordinal) <= horizon))
        rows.append({'peak': str(peak), 'detected': bool(matched),
                     'first_warning': str(matched[0]) if matched else None,
                     'lead_quarters': int(peak.ordinal - matched[0].ordinal) if matched else None})
    return pd.DataFrame(rows, columns=['peak', 'detected', 'first_warning', 'lead_quarters'])
