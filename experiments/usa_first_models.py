#!/usr/bin/env python3
"""Exploratory USA-first model run.

This is NOT the pre-registered official result. It exists because the shared
feature table, fold file and model code were not delivered. It builds a
contract-shaped walk-forward run from the frozen label and the existing clean
panel, using numpy/scipy reference implementations of the six model families
(scikit-learn and xgboost could not be installed in this environment).

Outputs go to outputs/exploratory/usa_first/ and must not be copied into
outputs/results/ensemble/ without the official frozen folds.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "exploratory" / "usa_first"
OUT.mkdir(parents=True, exist_ok=True)

HORIZON = 2
WINDOW_START = pd.Period("1990Q1", freq="Q")
WINDOW_END = pd.Period("2026Q1", freq="Q")  # last quarter with a known H=2 target
SEED = 42


# --------------------------------------------------------------------------- data
def load_data():
    panel = pd.read_csv(ROOT / "data" / "clean" / "USA_panel.csv")
    panel["quarter"] = pd.PeriodIndex(panel["quarter"], freq="Q")
    panel = panel.set_index("quarter").sort_index()

    labels = pd.read_csv(ROOT / "outputs" / "labels" / "USA_labels.csv")
    labels["quarter"] = pd.PeriodIndex(labels["quarter"], freq="Q")
    labels = labels.set_index("quarter").sort_index()

    episodes = pd.read_csv(ROOT / "outputs" / "labels" / "USA_episodes.csv")
    peaks = [pd.Period(p, freq="Q") for p in episodes["peak"]]
    return panel, labels, peaks


def publication_lag(col: str) -> int:
    """C-05 availability lag in quarters at a quarter-end + 6 week origin."""
    quarterly_na = (
        "ACT_GDP_REAL",
        "ACT_EMP.Q",
        "ACT_HOURS",
        "ACT_RINC.Q",
        "ACT_CONS",
        "ACT_INV",
        "FIN_CREDIT_GDP",
        "FIN_HOUSEPRICE.Q",
    )
    return 1 if any(k in col for k in quarterly_na) else 0


def base_transform(level: pd.Series, col: str) -> tuple[str, pd.Series]:
    """Return (form, base series) following the C-07 spirit."""
    if any(k in col for k in ("FIN_EQUITY", "FIN_HOUSEPRICE", "PRC_CPI")):
        return "price", np.log(level.where(level > 0)).diff() * 100.0
    if "ACT_" in col:
        return "growth", np.log(level.where(level > 0)).diff() * 100.0
    return "level", level.astype(float)


def build_features(panel: pd.DataFrame) -> pd.DataFrame:
    feats: dict[str, pd.Series] = {}
    for col in panel.columns:
        lag = publication_lag(col)
        raw = panel[col].shift(lag)
        form, base = base_transform(raw, col)
        short = col.replace("USA.", "")
        feats[f"{short}__base"] = base
        if form == "price":
            feats[f"{short}__yoy"] = np.log(raw.where(raw > 0)).diff(4) * 100.0
        feats[f"{short}__lag1"] = base.shift(1)
        feats[f"{short}__lag2"] = base.shift(2)
        feats[f"{short}__lag4"] = base.shift(4)
        feats[f"{short}__ma4"] = base.rolling(4, min_periods=3).mean()
        feats[f"{short}__sd4"] = base.rolling(4, min_periods=3).std()
        feats[f"{short}__chg4"] = base.diff(4)
    X = pd.DataFrame(feats, index=panel.index)
    return X.replace([np.inf, -np.inf], np.nan)


def build_target(labels: pd.DataFrame, peaks: list[pd.Period]) -> pd.Series:
    y = pd.Series(0, index=labels.index, dtype=int)
    for peak in peaks:
        for k in range(1, HORIZON + 1):
            t = peak - k
            if t in y.index:
                y.loc[t] = 1
    return y


# --------------------------------------------------------------- math utilities
def sigmoid(z):
    z = np.clip(z, -35.0, 35.0)
    return 1.0 / (1.0 + np.exp(-z))


def soft_threshold(v, t):
    return np.sign(v) * np.maximum(np.abs(v) - t, 0.0)


def balanced_weights(y):
    y = np.asarray(y)
    n = len(y)
    pos = max(int(y.sum()), 1)
    neg = max(n - pos, 1)
    w = np.where(y == 1, n / (2.0 * pos), n / (2.0 * neg))
    return w


def average_precision(y, p):
    y = np.asarray(y, dtype=int)
    p = np.asarray(p, dtype=float)
    if y.sum() == 0:
        return float("nan")
    order = np.argsort(-p, kind="mergesort")
    y = y[order]
    tp = np.cumsum(y)
    precision = tp / np.arange(1, len(y) + 1)
    recall = tp / y.sum()
    ap = 0.0
    prev = 0.0
    for r, pr in zip(recall, precision):
        ap += (r - prev) * pr
        prev = r
    return float(ap)


def roc_auc(y, p):
    y = np.asarray(y, dtype=int)
    p = np.asarray(p, dtype=float)
    pos = y == 1
    neg = y == 0
    if pos.sum() == 0 or neg.sum() == 0:
        return float("nan")
    # Mann-Whitney with average ranks for ties.
    order = np.argsort(p, kind="mergesort")
    ranks = np.empty(len(p), dtype=float)
    sp = p[order]
    i = 0
    while i < len(p):
        j = i
        while j + 1 < len(p) and sp[j + 1] == sp[i]:
            j += 1
        ranks[order[i : j + 1]] = 0.5 * (i + j) + 1.0
        i = j + 1
    return float((ranks[pos].sum() - pos.sum() * (pos.sum() + 1) / 2.0) / (pos.sum() * neg.sum()))


def best_threshold(y, p):
    y = np.asarray(y, dtype=int)
    p = np.asarray(p, dtype=float)
    if len(np.unique(y)) < 2:
        return 0.5
    cand = np.unique(np.round(np.concatenate(([0.0, 0.5, 1.0], p)), 6))
    best_t, best_f1 = 0.5, -1.0
    for t in cand:
        pred = p >= t
        tp = int((pred & (y == 1)).sum())
        fp = int((pred & (y == 0)).sum())
        fn = int(((~pred) & (y == 1)).sum())
        if tp == 0:
            f1 = 0.0
        else:
            prec = tp / (tp + fp)
            rec = tp / (tp + fn)
            f1 = 2 * prec * rec / (prec + rec)
        if f1 > best_f1 + 1e-12:
            best_f1, best_t = f1, float(t)
    return best_t


# ------------------------------------------------------------------ logistic L2
def fit_logistic_l2(X, y, C=1.0, sample_weight=None):
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    n, p = X.shape
    sw = balanced_weights(y) if sample_weight is None else np.asarray(sample_weight, float)
    sw = sw / sw.mean()
    lam = 1.0 / max(C, 1e-9)

    def obj(w):
        z = X @ w[1:] + w[0]
        pr = sigmoid(z)
        loss = -np.sum(sw * (y * np.log(pr + 1e-12) + (1 - y) * np.log(1 - pr + 1e-12))) / n
        loss += 0.5 * lam * np.dot(w[1:], w[1:])
        grad = np.empty(p + 1)
        grad[0] = np.sum(sw * (pr - y)) / n
        grad[1:] = X.T @ (sw * (pr - y)) / n + lam * w[1:]
        return loss, grad

    res = minimize(obj, np.zeros(p + 1), jac=True, method="L-BFGS-B",
                   options={"maxiter": 500, "ftol": 1e-10})
    return res.x


def predict_logistic(w, X):
    return sigmoid(np.asarray(X, float) @ w[1:] + w[0])


# --------------------------------------------------------- elastic-net logistic
def fit_enet_logit(X, y, alpha=0.01, l1_ratio=0.5, max_iter=1500):
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    n, p = X.shape
    sw = balanced_weights(y)
    sw = sw / sw.mean()
    L = 0.25 * np.linalg.norm(X, ord=2) ** 2 / n + alpha * (1 - l1_ratio)
    step = 1.0 / max(L, 1e-9)
    w = np.zeros(p + 1)
    for _ in range(max_iter):
        pr = sigmoid(X @ w[1:] + w[0])
        grad = np.empty(p + 1)
        grad[0] = np.sum(sw * (pr - y)) / n
        grad[1:] = X.T @ (sw * (pr - y)) / n
        v = w - step * grad
        w[0] = v[0]
        w[1:] = soft_threshold(v[1:], step * alpha * l1_ratio)
        w[1:] /= 1.0 + step * alpha * (1.0 - l1_ratio)
    return w


# ------------------------------------------------------------------------- trees
class TreeNode:
    __slots__ = ("feature", "threshold", "left", "right", "value")

    def __init__(self):
        self.feature = -1
        self.threshold = 0.0
        self.left = None
        self.right = None
        self.value = 0.0


class Tree:
    def __init__(self, max_depth=3, min_samples_leaf=5, max_features=None, criterion="gini", rng=None):
        self.max_depth = max_depth
        self.min_samples_leaf = min_samples_leaf
        self.max_features = max_features
        self.criterion = criterion
        self.rng = rng if rng is not None else np.random.default_rng(0)
        self.root = None

    def fit(self, X, y, sample_weight=None):
        X = np.asarray(X, float)
        y = np.asarray(y, float)
        sw = np.ones(len(y)) if sample_weight is None else np.asarray(sample_weight, float)
        self.root = self._grow(X, y, sw, depth=0)
        return self

    def _grow(self, X, y, sw, depth):
        node = TreeNode()
        node.value = float(np.average(y, weights=sw))
        if depth >= self.max_depth or len(y) < 2 * self.min_samples_leaf:
            return node
        p = X.shape[1]
        n_try = p if self.max_features is None else min(p, self.max_features)
        feats = self.rng.choice(p, size=n_try, replace=False)
        best = None
        for f in feats:
            vals = X[:, f]
            qs = np.unique(np.quantile(vals, np.linspace(0.1, 0.9, 9)))
            for th in qs:
                left = vals <= th
                nl, nr = int(left.sum()), int((~left).sum())
                if nl < self.min_samples_leaf or nr < self.min_samples_leaf:
                    continue
                score = self._score(y, sw, left)
                if best is None or score < best[0]:
                    best = (score, f, float(th), left)
        if best is None:
            return node
        _, f, th, left = best
        node.feature, node.threshold = f, th
        node.left = self._grow(X[left], y[left], sw[left], depth + 1)
        node.right = self._grow(X[~left], y[~left], sw[~left], depth + 1)
        return node

    def _score(self, y, sw, left):
        def impurity(mask):
            w = sw[mask]
            if w.sum() <= 0:
                return 0.0
            if self.criterion == "gini":
                p = np.average(y[mask], weights=w)
                return w.sum() * 2 * p * (1 - p)
            mu = np.average(y[mask], weights=w)
            return w.sum() * np.average((y[mask] - mu) ** 2, weights=w)
        return impurity(left) + impurity(~left)

    def predict(self, X):
        X = np.asarray(X, float)
        out = np.empty(len(X))
        for i, row in enumerate(X):
            node = self.root
            while node.feature >= 0:
                node = node.left if row[node.feature] <= node.threshold else node.right
            out[i] = node.value
        return out


class RandomForest:
    def __init__(self, n_estimators=200, max_depth=3, min_samples_leaf=5, max_features="sqrt", seed=SEED):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_leaf = min_samples_leaf
        self.max_features = max_features
        self.rng = np.random.default_rng(seed)
        self.trees = []

    def fit(self, X, y):
        X = np.asarray(X, float)
        y = np.asarray(y, int)
        n, p = X.shape
        k = max(1, int(math.sqrt(p))) if self.max_features == "sqrt" else p
        w = balanced_weights(y)
        prob = w / w.sum()
        self.trees = []
        for _ in range(self.n_estimators):
            idx = self.rng.choice(n, size=n, replace=True, p=prob)
            t = Tree(self.max_depth, self.min_samples_leaf, k, "gini", self.rng)
            t.fit(X[idx], y[idx])
            self.trees.append(t)
        return self

    def predict_proba(self, X):
        preds = np.mean([t.predict(X) for t in self.trees], axis=0)
        return np.clip(preds, 1e-6, 1 - 1e-6)


class GradientBoosting:
    def __init__(self, n_estimators=150, learning_rate=0.03, max_depth=2,
                 min_samples_leaf=5, seed=SEED):
        self.n_estimators = n_estimators
        self.lr = learning_rate
        self.max_depth = max_depth
        self.min_samples_leaf = min_samples_leaf
        self.rng = np.random.default_rng(seed)
        self.trees = []
        self.f0 = 0.0

    def fit(self, X, y):
        X = np.asarray(X, float)
        y = np.asarray(y, float)
        sw = balanced_weights(y)
        p0 = np.average(y, weights=sw)
        self.f0 = math.log(max(p0, 1e-6) / max(1 - p0, 1e-6))
        F = np.full(len(y), self.f0)
        self.trees = []
        for _ in range(self.n_estimators):
            pr = sigmoid(F)
            resid = y - pr
            t = Tree(self.max_depth, self.min_samples_leaf, None, "mse", self.rng)
            t.fit(X, resid, sample_weight=sw * np.maximum(pr * (1 - pr), 1e-6))
            leaf = t.predict(X)
            # Newton update at the leaf values.
            denom = max(np.sum(sw * pr * (1 - pr)), 1e-9)
            step = float(np.sum(sw * resid) / denom)
            F += self.lr * np.clip(leaf * step / max(np.std(leaf), 1e-6), -4, 4)
            self.trees.append(t)
        return self

    def predict_proba(self, X):
        X = np.asarray(X, float)
        F = np.full(len(X), self.f0)
        for t in self.trees:
            leaf = t.predict(X)
            F += self.lr * np.clip(leaf, -4, 4)
        return np.clip(sigmoid(F), 1e-6, 1 - 1e-6)


class LinearSVM:
    def __init__(self, C=0.1):
        self.C = C
        self.w = None
        self.platt = None

    def fit(self, X, y):
        X = np.asarray(X, float)
        y = np.asarray(y, float)
        n, p = X.shape
        sw = balanced_weights(y)
        sw = sw / sw.mean()
        yy = np.where(y == 1, 1.0, -1.0)

        def obj(w):
            z = X @ w[1:] + w[0]
            margin = 1.0 - yy * z
            hinge = np.maximum(margin, 0.0)
            loss = 0.5 * np.dot(w[1:], w[1:]) + self.C * np.sum(sw * hinge ** 2)
            grad = np.empty(p + 1)
            grad[0] = -2.0 * self.C * np.sum(sw * yy * hinge * (margin > 0))
            grad[1:] = w[1:] - 2.0 * self.C * (X.T @ (sw * yy * hinge * (margin > 0)))
            return loss, grad

        res = minimize(obj, np.zeros(p + 1), jac=True, method="L-BFGS-B",
                       options={"maxiter": 500})
        self.w = res.x
        return self

    def decision(self, X):
        return np.asarray(X, float) @ self.w[1:] + self.w[0]

    def calibrate(self, X, y):
        z = self.decision(X).reshape(-1, 1)
        self.platt = fit_logistic_l2(z, y, C=1.0)

    def predict_proba(self, X):
        z = self.decision(X).reshape(-1, 1)
        if self.platt is None:
            return sigmoid(z).ravel()
        return predict_logistic(self.platt, z)


class MLP:
    def __init__(self, hidden=8, alpha=0.001, epochs=300, lr=0.01, seed=0):
        self.hidden = hidden
        self.alpha = alpha
        self.epochs = epochs
        self.lr = lr
        self.rng = np.random.default_rng(seed)
        self.W1 = self.b1 = self.W2 = self.b2 = None

    def fit(self, X, y):
        X = np.asarray(X, float)
        y = np.asarray(y, float).reshape(-1, 1)
        n, p = X.shape
        h = self.hidden
        self.W1 = self.rng.normal(0, 1 / math.sqrt(p), (p, h))
        self.b1 = np.zeros((1, h))
        self.W2 = self.rng.normal(0, 1 / math.sqrt(h), (h, 1))
        self.b2 = np.zeros((1, 1))
        sw = balanced_weights(y.ravel()).reshape(-1, 1)
        sw = sw / sw.mean()
        m = {k: np.zeros_like(v) for k, v in
             (("W1", self.W1), ("b1", self.b1), ("W2", self.W2), ("b2", self.b2))}
        v = {k: np.zeros_like(val) for k, val in m.items()}
        b1, b2 = 0.9, 0.999
        for it in range(1, self.epochs + 1):
            H = np.tanh(X @ self.W1 + self.b1)
            out = sigmoid(H @ self.W2 + self.b2)
            dout = (out - y) * sw / n
            dW2 = H.T @ dout + self.alpha * self.W2
            db2 = dout.sum(axis=0, keepdims=True)
            dH = (dout @ self.W2.T) * (1 - H ** 2)
            dW1 = X.T @ dH + self.alpha * self.W1
            db1 = dH.sum(axis=0, keepdims=True)
            grads = {"W1": dW1, "b1": db1, "W2": dW2, "b2": db2}
            for k in grads:
                m[k] = b1 * m[k] + (1 - b1) * grads[k]
                v[k] = b2 * v[k] + (1 - b2) * grads[k] ** 2
                mhat = m[k] / (1 - b1 ** it)
                vhat = v[k] / (1 - b2 ** it)
                param = getattr(self, k)
                param -= self.lr * mhat / (np.sqrt(vhat) + 1e-8)
                setattr(self, k, param)
        return self

    def predict_proba(self, X):
        X = np.asarray(X, float)
        H = np.tanh(X @ self.W1 + self.b1)
        return np.clip(sigmoid(H @ self.W2 + self.b2).ravel(), 1e-6, 1 - 1e-6)


# ------------------------------------------------------------------ fold helper
@dataclass
class Fold:
    name: str
    train_start: pd.Period
    train_end: pd.Period
    test_start: pd.Period
    test_end: pd.Period


FOLDS = [
    Fold("F1", pd.Period("1990Q1", "Q"), pd.Period("2000Q2", "Q"), pd.Period("2000Q3", "Q"), pd.Period("2005Q4", "Q")),
    Fold("F2", pd.Period("1990Q1", "Q"), pd.Period("2005Q4", "Q"), pd.Period("2006Q1", "Q"), pd.Period("2010Q4", "Q")),
    Fold("F3", pd.Period("1990Q1", "Q"), pd.Period("2014Q4", "Q"), pd.Period("2015Q1", "Q"), pd.Period("2020Q4", "Q")),
    Fold("F4", pd.Period("1990Q1", "Q"), pd.Period("2020Q4", "Q"), pd.Period("2021Q1", "Q"), pd.Period("2026Q1", "Q")),
]


def inner_split(idx: pd.PeriodIndex, y: pd.Series):
    """Time-ordered inner train/validation, with at least one positive if possible."""
    n = len(idx)
    val_n = max(8, int(math.ceil(0.2 * n)))
    val_n = min(val_n, n - 12)
    max_val = min(n - 12, 40)
    while val_n < max_val:
        val_idx = idx[-val_n:]
        if int(y.loc[val_idx].sum()) > 0:
            break
        val_n += 4
    return idx[:-val_n], idx[-val_n:]


def prepare_matrix(train_idx, test_idx, X, y, medians=None):
    cols = [c for c in X.columns if X.loc[train_idx, c].notna().mean() >= 0.70]
    cols = [c for c in cols if X.loc[train_idx, c].std(skipna=True) > 1e-8]
    if medians is None:
        medians = X.loc[train_idx, cols].median()
    Xtr = X.loc[train_idx, cols].fillna(medians).to_numpy(float)
    Xte = X.loc[test_idx, cols].fillna(medians).to_numpy(float)
    mu = Xtr.mean(axis=0)
    sd = Xtr.std(axis=0)
    sd[sd < 1e-8] = 1.0
    return (Xtr - mu) / sd, (Xte - mu) / sd, cols, medians, mu, sd


# ------------------------------------------------------------------ model zoo
def model_candidates():
    return {
        "logistic": [{"C": c} for c in (0.01, 0.1, 1.0, 10.0)],
        "elastic_net": [{"alpha": a, "l1_ratio": r}
                        for a in (0.001, 0.005, 0.02)
                        for r in (0.2, 0.6, 0.9)],
        "random_forest": [{"max_depth": d, "min_samples_leaf": m}
                          for d in (2, 3) for m in (5, 10)],
        "xgboost_like": [{"max_depth": d, "min_samples_leaf": m}
                         for d in (1, 2) for m in (5, 10)],
        "svm": [{"C": c} for c in (0.01, 0.1, 1.0)],
        "mlp": [{"hidden": h, "alpha": a} for h in (4, 8) for a in (0.001, 0.01)],
    }


def fit_model(name, params, X, y):
    if name == "logistic":
        return ("logistic", fit_logistic_l2(X, y, C=params["C"]))
    if name == "elastic_net":
        return ("enet", fit_enet_logit(X, y, alpha=params["alpha"], l1_ratio=params["l1_ratio"]))
    if name == "random_forest":
        return ("rf", RandomForest(max_depth=params["max_depth"],
                                   min_samples_leaf=params["min_samples_leaf"]).fit(X, y))
    if name == "xgboost_like":
        return ("gb", GradientBoosting(max_depth=params["max_depth"],
                                       min_samples_leaf=params["min_samples_leaf"]).fit(X, y))
    if name == "svm":
        return ("svm", LinearSVM(C=params["C"]).fit(X, y))
    if name == "mlp":
        return ("mlp", MLP(hidden=params["hidden"], alpha=params["alpha"]).fit(X, y))
    raise ValueError(name)


def predict_model(kind, obj, X):
    if kind == "logistic":
        return predict_logistic(obj, X)
    if kind == "enet":
        return predict_logistic(obj, X)
    return obj.predict_proba(X)


def fit_predict_fold(fold, X, y):
    train_idx = X.loc[fold.train_start:fold.train_end].index
    test_idx = X.loc[fold.test_start:fold.test_end].index
    ytr, yte = y.loc[train_idx], y.loc[test_idx]

    inner_tr, inner_val = inner_split(train_idx, y)
    Xtr, Xval, cols, medians, mu, sd = prepare_matrix(inner_tr, inner_val, X, y)
    ytr_in, yval = y.loc[inner_tr].to_numpy(), y.loc[inner_val].to_numpy()

    # 1. Tune the Elastic Net selector on the inner validation block.
    selector_grid = [{"alpha": a, "l1_ratio": r}
                     for a in (0.001, 0.005, 0.02, 0.05)
                     for r in (0.2, 0.5, 0.8, 0.95)]
    best_sel, best_ap = None, -1.0
    for p in selector_grid:
        w = fit_enet_logit(Xtr, ytr_in, alpha=p["alpha"], l1_ratio=p["l1_ratio"])
        ap = average_precision(yval, predict_logistic(w, Xval))
        if np.isfinite(ap) and ap > best_ap:
            best_ap, best_sel = ap, p
    if best_sel is None:
        best_sel = {"alpha": 0.01, "l1_ratio": 0.5}
    w_inner = fit_enet_logit(Xtr, ytr_in, alpha=best_sel["alpha"], l1_ratio=best_sel["l1_ratio"])
    selected = [c for c, coef in zip(cols, w_inner[1:]) if abs(coef) > 1e-10]
    if len(selected) < 3:
        order = np.argsort(-np.abs(w_inner[1:]))
        selected = [cols[i] for i in order[:15]]
    if not selected:
        selected = cols[:]
    sel_idx = [cols.index(c) for c in selected]
    Xtr_s, Xval_s = Xtr[:, sel_idx], Xval[:, sel_idx]

    # 2. Tune and evaluate every model on the inner validation block.
    inner_scores, tuned = {}, {}
    for name, grid in model_candidates().items():
        best = None
        for p in grid:
            kind, obj = fit_model(name, p, Xtr_s, ytr_in)
            prob = predict_model(kind, obj, Xval_s)
            ap = average_precision(yval, prob)
            brier = float(np.mean((prob - yval) ** 2))
            key = (ap if np.isfinite(ap) else -1.0, -brier)
            if best is None or key > best[0]:
                best = (key, p, kind, obj, prob)
        _, p, kind, obj, prob = best
        tuned[name] = (p, kind, obj)
        inner_scores[name] = {
            "pr_auc": average_precision(yval, prob),
            "brier": float(np.mean((prob - yval) ** 2)),
            "threshold": best_threshold(yval, prob),
            "prob": prob,
        }

    # 3. Refit on the full outer training block with the selected features.
    Xfull, Xtest, _, _, mu2, sd2 = prepare_matrix(train_idx, test_idx, X, y)
    Xfull_s, Xtest_s = Xfull[:, sel_idx], Xtest[:, sel_idx]
    outer = {}
    for name, (p, kind, _) in tuned.items():
        kind2, obj2 = fit_model(name, p, Xfull_s, ytr.to_numpy())
        outer[name] = predict_model(kind2, obj2, Xtest_s)

    # 4. Locked thresholds from the inner validation block.
    thresholds = {k: v["threshold"] for k, v in inner_scores.items()}
    ranking = sorted(inner_scores, key=lambda k: (
        inner_scores[k]["pr_auc"] if np.isfinite(inner_scores[k]["pr_auc"]) else -1,
        -inner_scores[k]["brier"],
    ), reverse=True)
    top3 = ranking[:3]
    ens_inner = np.mean([inner_scores[m]["prob"] for m in top3], axis=0)
    ens_thr = best_threshold(yval, ens_inner)
    ens_test = np.mean([outer[m] for m in top3], axis=0)

    return {
        "fold": fold.name,
        "train_idx": train_idx,
        "test_idx": test_idx,
        "y_train": ytr,
        "y_test": yte,
        "selected": selected,
        "selector": best_sel,
        "inner_scores": {k: {kk: vv for kk, vv in v.items() if kk != "prob"} for k, v in inner_scores.items()},
        "ranking": ranking,
        "top3": top3,
        "thresholds": thresholds,
        "outer": outer,
        "ensemble": ens_test,
        "ensemble_threshold": ens_thr,
        "best_single": ranking[0],
    }


def bootstrap_delta(y, p_ens, p_single, n_boot=1000, seed=SEED):
    rng = np.random.default_rng(seed)
    y = np.asarray(y, int)
    deltas = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(y), len(y))
        if y[idx].sum() == 0 or y[idx].sum() == len(idx):
            continue
        deltas.append(average_precision(y[idx], p_ens[idx]) -
                      average_precision(y[idx], p_single[idx]))
    if not deltas:
        return float("nan"), float("nan")
    return float(np.quantile(deltas, 0.025)), float(np.quantile(deltas, 0.975))


def episode_report(test_idx, yhat, peaks):
    rows = []
    for peak in peaks:
        window = [peak - 2, peak - 1]
        window = [t for t in window if t in test_idx]
        if not window:
            continue
        flags = [t for t in window if yhat.get(t, 0) == 1]
        rows.append({
            "peak": str(peak),
            "detected": int(bool(flags)),
            "lead_quarters": (peak - min(flags)).n if flags else None,
        })
    return rows


def main():
    panel, labels, peaks = load_data()
    X = build_features(panel)
    y = build_target(labels, peaks)
    y = y.loc[WINDOW_START:WINDOW_END]
    X = X.loc[WINDOW_START:WINDOW_END]

    print(f"features: {X.shape[1]}, quarters: {len(X)}, positives: {int(y.sum())}")
    print("positive quarters:", [str(t) for t in y[y == 1].index])

    pred_rows, fold_rows, selection_rows = [], [], []
    all_y, all_ens, all_best = [], [], []
    fold_results = []

    for fold in FOLDS:
        res = fit_predict_fold(fold, X, y)
        fold_results.append(res)
        test_idx = res["test_idx"]
        yte = res["y_test"]
        all_y.extend(yte.tolist())
        all_ens.extend(res["ensemble"].tolist())
        all_best.extend(res["outer"][res["best_single"]].tolist())

        for model in list(res["outer"]) + ["ensemble"]:
            prob = res["ensemble"] if model == "ensemble" else res["outer"][model]
            thr = res["ensemble_threshold"] if model == "ensemble" else res["thresholds"][model]
            yhat = (prob >= thr).astype(int)
            for t, p, yy, hh in zip(test_idx, prob, yte, yhat):
                pred_rows.append({
                    "country": "USA", "horizon": HORIZON, "outer_fold": fold.name,
                    "quarter": str(t), "split": "test", "model": model,
                    "prob": float(p), "threshold": float(thr),
                    "y_true": int(yy), "y_hat": int(hh),
                })
            fold_rows.append({
                "country": "USA", "horizon": HORIZON, "outer_fold": fold.name,
                "model": model, "train_start": str(fold.train_start),
                "train_end": str(fold.train_end), "test_start": str(fold.test_start),
                "test_end": str(fold.test_end), "n_train": len(res["train_idx"]),
                "n_test": len(test_idx), "n_pos_train": int(res["y_train"].sum()),
                "n_pos_test": int(yte.sum()), "n_features": len(res["selected"]),
                "threshold": float(thr), "pr_auc": average_precision(yte, prob),
                "roc_auc": roc_auc(yte, prob),
                "brier": float(np.mean((prob - yte.to_numpy()) ** 2)),
            })
        for rank, model in enumerate(res["ranking"], 1):
            selection_rows.append({
                "outer_fold": fold.name, "rank": rank, "model": model,
                "inner_pr_auc": res["inner_scores"][model]["pr_auc"],
                "inner_brier": res["inner_scores"][model]["brier"],
                "selected_count": len(res["selected"]),
                "top3": int(model in res["top3"]),
            })

    pred = pd.DataFrame(pred_rows)
    foldm = pd.DataFrame(fold_rows)
    sel = pd.DataFrame(selection_rows)
    pred.to_csv(OUT / "predictions.csv", index=False)
    foldm.to_csv(OUT / "fold_metrics.csv", index=False)
    sel.to_csv(OUT / "model_selection.csv", index=False)

    # Pooled metrics use each fold's locked threshold, not one global threshold.
    def metrics_for(model):
        sub = pred[pred["model"] == model].copy()
        sub["quarter"] = pd.PeriodIndex(sub["quarter"], freq="Q")
        ytrue = sub["y_true"].to_numpy()
        prob = sub["prob"].to_numpy()
        yhat = sub["y_hat"].to_numpy()
        tp = int(((yhat == 1) & (ytrue == 1)).sum())
        fp = int(((yhat == 1) & (ytrue == 0)).sum())
        fn = int(((yhat == 0) & (ytrue == 1)).sum())
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        ep = episode_report(sub.set_index("quarter").index,
                            sub.set_index("quarter")["y_hat"], peaks)
        ep_rec = float(np.mean([e["detected"] for e in ep])) if ep else float("nan")
        return {
            "model": model,
            "pooled_pr_auc": average_precision(ytrue, prob),
            "pooled_roc_auc": roc_auc(ytrue, prob),
            "recall": rec, "precision": prec, "f1": f1,
            "brier": float(np.mean((prob - ytrue) ** 2)),
            "episode_recall": ep_rec,
            "false_positive_quarters": fp,
        }

    pooled = pd.DataFrame([metrics_for(m) for m in
                           ["logistic", "elastic_net", "random_forest",
                            "xgboost_like", "svm", "mlp", "ensemble"]])
    pooled.to_csv(OUT / "pooled_metrics.csv", index=False)

    ens = pooled[pooled["model"] == "ensemble"].iloc[0]
    best_single_models = {res["best_single"] for res in fold_results}
    best_single_label = "+".join(sorted(best_single_models))
    best_row = pooled[pooled["model"].isin(best_single_models)].iloc[0]
    # The per-fold best-single comparator is the model each fold chose; for the
    # headline delta use the stronger of those pooled rows.
    best_row = pooled[pooled["model"].isin(best_single_models)].sort_values(
        "pooled_pr_auc", ascending=False).iloc[0]

    y_all = pred[pred["model"] == "ensemble"]["y_true"].to_numpy()
    p_ens = pred[pred["model"] == "ensemble"]["prob"].to_numpy()
    p_best = pred[pred["model"] == best_row["model"]]["prob"].to_numpy()
    ap_ens, ap_best = ens["pooled_pr_auc"], best_row["pooled_pr_auc"]
    ci_lo, ci_hi = bootstrap_delta(y_all, p_ens, p_best)
    ens_yhat = pred[pred["model"] == "ensemble"]["y_hat"].to_numpy()
    ep = episode_report(pd.PeriodIndex(pred[pred["model"] == "ensemble"]["quarter"], freq="Q"),
                        pd.Series(ens_yhat, index=pd.PeriodIndex(
                            pred[pred["model"] == "ensemble"]["quarter"], freq="Q")), peaks)
    ep_df = pd.DataFrame(ep)
    ep_df.to_csv(OUT / "episodes.csv", index=False)
    rec = ens["episode_recall"]

    rule_met = (
        (ap_ens - ap_best) >= 0.01
        and np.isfinite(ci_lo) and ci_lo > 0
        and np.isfinite(ens["episode_recall"]) and np.isfinite(best_row["episode_recall"])
        and ens["episode_recall"] >= best_row["episode_recall"]
    )
    headline = pd.DataFrame([{
        "country": "USA", "horizon": HORIZON, "model": "ensemble_top3",
        "best_single_model": best_row["model"],
        "best_single_models_by_fold": best_single_label,
        "pooled_pr_auc": ap_ens, "best_single_pr_auc": ap_best,
        "delta_vs_best_single": ap_ens - ap_best, "ci_low": ci_lo,
        "ci_high": ci_hi, "episode_recall": ens["episode_recall"],
        "best_single_episode_recall": best_row["episode_recall"],
        "false_positive_quarters": int(ens["false_positive_quarters"]),
        "decision": "ensemble_primary_exploratory" if rule_met else
                    "single_primary_negative_ensemble_exploratory",
    }])
    headline.to_csv(OUT / "headline.csv", index=False)

    boot_rows = []
    rng = np.random.default_rng(SEED)
    for i in range(1000):
        idx = rng.integers(0, len(y_all), len(y_all))
        if y_all[idx].sum() == 0 or y_all[idx].sum() == len(idx):
            continue
        boot_rows.append({"country": "USA", "horizon": HORIZON, "resample": i,
                          "delta_pr_auc": average_precision(y_all[idx], p_ens[idx]) -
                          average_precision(y_all[idx], p_best[idx])})
    pd.DataFrame(boot_rows).to_csv(OUT / "ensemble_bootstrap.csv", index=False)

    # Simple markdown report.
    def block(df):
        return "```text\n" + df.to_string(index=False) + "\n```"

    lines = [
        "# Exploratory USA-first model run",
        "",
        "**Status:** exploratory only. Not the official pre-registered result.",
        "",
        f"- Window: {WINDOW_START}–{WINDOW_END}; features: {X.shape[1]}; positives: {int(y.sum())}",
        f"- Outer folds: {', '.join(f.name for f in FOLDS)}",
        f"- Pooled PR-AUC, ensemble: {ap_ens:.4f}",
        f"- Pooled PR-AUC, inner-selected best single: {ap_best:.4f}",
        f"- Delta: {ap_ens - ap_best:+.4f} (95% bootstrap {ci_lo:+.4f} to {ci_hi:+.4f})",
        f"- Episode recall: {rec:.3f}" if np.isfinite(rec) else "- Episode recall: n/a",
        f"- False-positive quarters: {int(ens['false_positive_quarters'])}",
        "",
        "## Fold metrics",
        "",
        block(foldm),
        "",
        "## Inner-fold ranking",
        "",
        block(sel),
        "",
        "## Episodes",
        "",
        block(ep_df) if len(ep_df) else "No test episodes.",
        "",
        "## Caveat",
        "",
        "The official run requires Arshiya's frozen feature table and folds and Palchhin's",
        "model code. This run uses a locally built feature table, four expanding folds and",
        "numpy/scipy reference implementations because scikit-learn and xgboost were not",
        "installable in this environment. Do not report it as the pre-registered result.",
    ]
    (OUT / "headline.md").write_text("\n".join(lines), encoding="utf-8")

    meta = {
        "status": "exploratory_only",
        "country": "USA",
        "horizon": HORIZON,
        "window": [str(WINDOW_START), str(WINDOW_END)],
        "features": int(X.shape[1]),
        "positives": int(y.sum()),
        "folds": [f.__dict__ | {"train_start": str(f.train_start), "train_end": str(f.train_end),
                                "test_start": str(f.test_start), "test_end": str(f.test_end)} for f in FOLDS],
        "seed": SEED,
        "models": ["logistic", "elastic_net", "random_forest", "xgboost_like", "svm", "mlp"],
        "ensemble": "equal-weight top-3 by inner PR-AUC",
        "data": "data/clean/USA_panel.csv",
        "label": "outputs/labels/USA_labels.csv (labels-v3)",
        "note": "Reference numpy/scipy implementations; not the pre-registered official run.",
    }
    (OUT / "run_metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print("\nheadline")
    print(headline.to_string(index=False))
    print("\nfold metrics")
    print(foldm.to_string(index=False))
    print("\nepisodes")
    print(ep_df.to_string(index=False) if len(ep_df) else "none")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
