"""Fold-safe REWI coefficient and feature-selection stability exports.

Inputs must be from fitted training folds only. Never fit on test observations.
"""
from pathlib import Path
import numpy as np
import pandas as pd


def coefficient_table(feature_names, coefficients, fold_id, model='elastic_net'):
    """One coefficient per selected feature, excluding any intercept."""
    names = list(feature_names)
    coef = np.asarray(coefficients, dtype=float).ravel()
    if len(names) != len(coef):
        raise ValueError('Feature names and coefficient counts differ')
    if len(names) != len(set(names)) or any(str(x).lower() in ('intercept', 'const') for x in names):
        raise ValueError('Duplicate features or intercept in feature list')
    if not np.isfinite(coef).all():
        raise ValueError('Non-finite coefficient')
    return pd.DataFrame({'fold_id': str(fold_id), 'model': str(model),
                         'feature': names, 'coefficient': coef,
                         'abs_coefficient': np.abs(coef)})


def feature_stability(coefficient_tables, *, selection_tolerance=1e-12):
    """Selection frequency and coefficient statistics across training folds.

    Absent features count as unselected (coefficient 0). Each input is one fold.
    """
    tables = list(coefficient_tables)
    if not tables:
        raise ValueError('At least one training fold is required')
    for t in tables:
        if not {'feature', 'coefficient'}.issubset(t.columns):
            raise ValueError('Missing feature or coefficient column')
        if t['feature'].duplicated().any():
            raise ValueError('Duplicate feature within fold')
    features = sorted(set().union(*(set(t['feature']) for t in tables)))
    if not features:
        raise ValueError('No features to summarize')
    values = np.zeros((len(tables), len(features)), dtype=float)
    for i, t in enumerate(tables):
        values[i] = pd.Series(t['coefficient'].to_numpy(dtype=float), index=t['feature']).reindex(features, fill_value=0).to_numpy()
    if not np.isfinite(values).all():
        raise ValueError('Non-finite coefficient')
    return pd.DataFrame({'feature': features,
                         'fold_count': len(tables),
                         'selected_folds': (np.abs(values) > selection_tolerance).sum(axis=0),
                         'selection_frequency': (np.abs(values) > selection_tolerance).mean(axis=0),
                         'mean_coefficient': values.mean(axis=0),
                         'std_coefficient': values.std(axis=0),
                         'mean_abs_coefficient': np.abs(values).mean(axis=0)}).sort_values(
                             ['selection_frequency', 'mean_abs_coefficient'], ascending=False).reset_index(drop=True)


def export_rewi_reporting(coefficient_tables, output_dir):
    """Write fold coefficients and feature stability as auditable CSV files."""
    tables = list(coefficient_tables)
    stability = feature_stability(tables)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    pd.concat(tables, ignore_index=True).to_csv(out / 'rewi_fold_coefficients.csv', index=False)
    stability.to_csv(out / 'feature_stability.csv', index=False)
    return stability
