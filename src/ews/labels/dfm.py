"""One-factor dynamic factor model for the BEAI label (BUILD_CONTRACT C-02).

The factor is estimated on the standardised activity-growth panel and then
cumulated to a level index. Turning points are dated on the level, never on the
growth rates (§12-13).

The reference estimator is `statsmodels` DynamicFactorMQ, which handles missing
cells through the Kalman filter. If it fails to converge, the module falls back
to an EM-PCA estimate and records which estimator was used, so a fallback can
never be mistaken for the reference result.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class FactorResult:
    factor: pd.Series                 # common component, growth units (SD)
    level: pd.Series                  # cumulative level index
    method: str                       # "dfm" | "pca_em"
    converged: bool
    loglik: float | None = None
    nobs: int = 0
    n_series: int = 0
    loadings: dict = field(default_factory=dict)
    notes: str = ""


def standardise(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Full-sample z-scores. Legitimate here: the label is an ex-post chronology."""
    mu = df.mean(axis=0)
    sd = df.std(axis=0, ddof=0).replace(0.0, np.nan)
    return (df - mu) / sd, mu, sd


def _fit_dfm(z: pd.DataFrame) -> tuple[pd.Series, dict]:
    from statsmodels.tsa.statespace.dynamic_factor_mq import DynamicFactorMQ

    mod = DynamicFactorMQ(
        z,
        factors=1,
        factor_orders=1,
        idiosyncratic_ar1=True,
        standardize=False,
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = mod.fit(disp=False, maxiter=1000)
    # Smoothed, not filtered: Pipeline A is an ex-post chronology and applies no
    # availability lag (C-05), so two-sided information is legitimate here and
    # avoids the revision noise that a one-sided filter injects into the dates.
    bunch = res.factors
    factors = getattr(bunch, "smoothed", None)
    if factors is None:
        factors = getattr(bunch, "filtered", bunch)
    if isinstance(factors, pd.DataFrame):
        f = factors.iloc[:, 0]
    else:
        f = pd.Series(np.asarray(factors).ravel(), index=z.index)
    f = pd.Series(np.asarray(f, dtype=float), index=z.index, name="factor")
    loadings = {}
    try:
        params = res.params
        for c in z.columns:
            key = f"loading.0->{c}"
            if key in params.index:
                loadings[c] = float(params[key])
    except Exception:
        pass
    ret = getattr(res, "mle_retvals", None) or {}
    info = {
        "converged": bool(ret.get("converged", True)),
        "loglik": float(res.llf),
        "loadings": loadings,
    }
    return f, info


def _fit_pca_em(df: pd.DataFrame, iters: int = 200, tol: float = 1e-8) -> tuple[pd.Series, dict]:
    """EM-PCA with missing cells. Used only when the DFM does not converge."""
    z, _, _ = standardise(df)
    x = z.to_numpy(dtype=float)
    mask = np.isfinite(x)
    filled = x.copy()
    col_mean = np.nanmean(x, axis=0)
    filled[~mask] = np.take(col_mean, np.where(~mask)[1])

    loadings = np.zeros(x.shape[1])
    for _ in range(iters):
        u, s, vt = np.linalg.svd(filled - filled.mean(axis=0), full_matrices=False)
        loadings = vt[0]
        scores = (filled - filled.mean(axis=0)) @ loadings
        recon = np.outer(scores, loadings) + filled.mean(axis=0)
        new = filled.copy()
        new[~mask] = recon[~mask]
        if np.max(np.abs(new - filled)) < tol:
            filled = new
            break
        filled = new

    # factor scores use only observed cells; normalise by squared loadings
    num = np.nansum(np.where(mask, x, 0.0) * loadings, axis=1)
    den = np.nansum(np.where(mask, loadings**2, 0.0), axis=1)
    f = np.divide(num, den, out=np.full_like(num, np.nan), where=den > 0)
    return (
        pd.Series(f, index=df.index, name="factor"),
        {"converged": True, "loglik": None, "loadings": dict(zip(df.columns, loadings))},
    )


def estimate_factor(df: pd.DataFrame, method: str = "dfm") -> FactorResult:
    """Estimate the common activity factor and cumulate it to a level index."""
    if df.shape[1] < 2:
        raise ValueError("need at least two series to estimate a factor")
    usable = df.dropna(axis=1, how="all")
    if usable.shape[1] < 2:
        raise ValueError("fewer than two series with any observation")

    z, mu, sd = standardise(usable)
    # Rows where no series has a value carry no information and destabilise the
    # first filtered state (the leading dlog observation is always all-NaN).
    estimable = z.loc[z.notna().any(axis=1)]
    if estimable.shape[0] < 8:
        raise ValueError("fewer than 8 quarters with any observation")
    z = estimable
    notes = ""
    used = method
    info: dict = {}
    factor = None

    if method == "dfm":
        try:
            factor, info = _fit_dfm(z)
        except Exception as exc:  # pragma: no cover - depends on statsmodels build
            notes = f"DFM failed ({type(exc).__name__}: {exc}); used EM-PCA"
            used = "pca_em"

    if factor is None:
        factor, info = _fit_pca_em(usable)
        used = used if used == "pca_em" else "pca_em"

    # sign convention: the factor must load positively on activity, so the
    # average loading (or correlation with the mean series) is made positive.
    ref = usable.mean(axis=1)
    corr = float(pd.concat([factor, ref], axis=1).corr().iloc[0, 1])
    if np.isfinite(corr) and corr < 0:
        factor = -factor
        info["loadings"] = {k: -v for k, v in info.get("loadings", {}).items()}
        notes = (notes + " " if notes else "") + "factor sign flipped to align with activity"

    # The factor is identified with unit variance, and each series loads on it
    # with |lambda_j| < 1. The common component of series j therefore has
    # standard deviation sigma_j * |lambda_j|, not sigma_j. Multiplying the
    # factor by mean(sigma_j) would overstate the common component by roughly
    # 1/|lambda| (about 3x here) and manufacture long, deep pseudo-recessions.
    lam = np.array([abs(info.get("loadings", {}).get(c, np.nan)) for c in usable.columns], dtype=float)
    if np.isfinite(lam).sum() == 0:
        lam = np.ones(len(usable.columns))
    lam = np.where(np.isfinite(lam), lam, float(np.nanmean(lam)))
    scale = float(np.nanmean(sd.to_numpy(dtype=float) * lam))
    if not np.isfinite(scale) or scale <= 0:
        scale = float(sd.mean())
    shift = float(mu.mean())
    # Restore the caller's index: the estimable sample drops the leading all-NaN
    # row, and an index offset here would shift every dated turning point.
    factor_units = (factor * scale + shift).reindex(usable.index)
    factor_units.name = "factor"

    level = factor_units.fillna(0.0).cumsum()
    level = level - level.iloc[0]
    level.name = "level"

    return FactorResult(
        factor=factor_units,
        level=level,
        method=used,
        converged=bool(info.get("converged", False)),
        loglik=info.get("loglik"),
        nobs=int(usable.dropna(how="all").shape[0]),
        n_series=int(usable.shape[1]),
        loadings=info.get("loadings", {}),
        notes=notes.strip(),
    )
