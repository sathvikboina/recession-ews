#!/usr/bin/env python3
"""scripts/07_baselines.py

Honest baselines on frozen folds for USA recession early-warning.
Seed: 42. Fixed threshold: 0.5. No tuning. No feature selection on test blocks.
Standardisation and imputation fitted inside each outer training fold only.

Baselines evaluated:
1. majority_class: training prevalence
2. term_spread: univariate logistic on term spread (T10Y3M / term_spread_10y_3m)
3. plain_logistic: multivariate logistic regression on all predictors

Outputs:
outputs/results/baselines.csv
outputs/results/baselines.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

PROJECT = Path(__file__).resolve().parents[1]
FEATURES_DIR = PROJECT / "data" / "features"
RESULTS_DIR = PROJECT / "outputs" / "results"
LABELS_DIR = PROJECT / "outputs" / "labels"

from ews.models.evaluation import pooled_metrics, episode_detection
from ews.models.targets import build_peak_targets

SEED = 42
HORIZONS = [("1Q", 1), ("2Q", 2), ("4Q", 4)]
PRIMARY_HORIZON = "2Q"


def find_term_spread_column(columns: list[str]) -> str:
    """Detect the term spread column by canonical names."""
    candidates = ["t10y3m", "t10y2y", "term", "term_spread", "term_spread_10y_3m"]
    col_map = {c.lower(): c for c in columns}
    for cand in candidates:
        if cand in col_map:
            return col_map[cand]
    # Check if GS10 and TB3MS exist to construct spread
    for c in columns:
        if "spread" in c.lower() or "t10y" in c.lower():
            return c
    raise ValueError(f"Could not detect term spread column among: {columns}")


def run_baselines(
    features_path: Path = FEATURES_DIR / "dataset.parquet",
    folds_path: Path = FEATURES_DIR / "folds.json",
    turning_points_path: Path = LABELS_DIR / "USA_turning_points.csv",
    seed: int = SEED,
) -> tuple[pd.DataFrame, str]:
    """Train and evaluate baselines across all horizons on frozen folds."""
    features_df = pd.read_parquet(features_path).set_index("quarter")
    tp_df = pd.read_csv(turning_points_path)

    with open(folds_path, "r", encoding="utf-8") as fh:
        folds_data = json.load(fh)["folds"]

    predictor_cols = [c for c in features_df.columns if c != "quarter"]
    spread_col = find_term_spread_column(predictor_cols)

    # In-window peaks
    all_peaks = tp_df.loc[(tp_df["kind"] == "peak") & (tp_df["in_window"]), "quarter"].tolist()

    results_rows = []
    markdown_lines = [
        "# Baseline Model Evaluation Results",
        "",
        f"- **Seed**: {seed}",
        "- **Evaluation**: Pooled out-of-sample predictions across untouched test blocks",
        "- **Decision Threshold**: 0.50 (fixed, no threshold tuning)",
        f"- **Term Spread Column**: `{spread_col}`",
        "- **Standardisation / Imputation**: Fitted strictly inside each training fold",
        "",
        "| Horizon | Baseline Model | Pooled PR-AUC | ROC-AUC | Episode Recall (Test) | Accuracy | Brier Score | N Test Obs |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]

    for h_label, h_int in HORIZONS:
        targets_df = build_peak_targets(features_df.index, tp_df, horizon=h_int).set_index("quarter")
        y_all = targets_df["y_true"]

        folds = folds_data[h_label]

        # Containers for out-of-sample pooled predictions
        y_test_all: list[int] = []
        q_test_all: list[str] = []

        preds_maj: list[float] = []
        preds_spread: list[float] = []
        preds_logistic: list[float] = []

        for fold in folds:
            tr_start, tr_end = fold["train_start"], fold["train_end"]
            te_start, te_end = fold["test_start"], fold["test_end"]

            tr_idx = features_df.loc[tr_start:tr_end].index
            te_idx = features_df.loc[te_start:te_end].index

            # Drop quarters where target is not observable (at endpoint horizon)
            y_tr_raw = y_all.loc[tr_idx]
            tr_valid = y_tr_raw.notna()
            tr_idx = tr_idx[tr_valid]
            y_tr = y_tr_raw.loc[tr_idx].astype(int)

            y_te_raw = y_all.loc[te_idx]
            te_valid = y_te_raw.notna()
            te_idx = te_idx[te_valid]
            y_te = y_te_raw.loc[te_idx].astype(int)

            if len(te_idx) == 0:
                continue

            X_tr = features_df.loc[tr_idx]
            X_te = features_df.loc[te_idx]

            # 1. Majority Class Baseline: empirical training positive prevalence
            p_maj = float(y_tr.mean())
            preds_maj.extend([p_maj] * len(y_te))

            # 2. Term Spread Logit Baseline
            if len(np.unique(y_tr)) == 2:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    model_sp = LogisticRegression(random_state=seed, solver="lbfgs")
                    model_sp.fit(X_tr[[spread_col]], y_tr)
                    p_sp = model_sp.predict_proba(X_te[[spread_col]])[:, 1]
            else:
                p_sp = np.array([p_maj] * len(y_te))
            preds_spread.extend(p_sp)

            # 3. Plain Logistic Regression on all predictors
            imp = SimpleImputer(strategy="median", keep_empty_features=True)
            X_tr_imp = imp.fit_transform(X_tr[predictor_cols])
            X_te_imp = imp.transform(X_te[predictor_cols])

            sc = StandardScaler()
            X_tr_sc = sc.fit_transform(X_tr_imp)
            X_te_sc = sc.transform(X_te_imp)

            if len(np.unique(y_tr)) == 2:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    model_lr = LogisticRegression(random_state=seed, solver="lbfgs", max_iter=2000)
                    model_lr.fit(X_tr_sc, y_tr)
                    p_lr = model_lr.predict_proba(X_te_sc)[:, 1]
            else:
                p_lr = np.array([p_maj] * len(y_te))
            preds_logistic.extend(p_lr)

            y_test_all.extend(y_te.tolist())
            q_test_all.extend(te_idx.astype(str).tolist())

        y_test_arr = np.array(y_test_all)
        first_test_q = folds[0]["test_start"]
        test_peaks = [p for p in all_peaks if p >= first_test_q]

        model_dict = {
            "majority": np.array(preds_maj),
            "term_spread": np.array(preds_spread),
            "plain_logistic": np.array(preds_logistic),
        }

        for m_name, p_arr in model_dict.items():
            metrics = pooled_metrics(y_test_arr, p_arr, threshold=0.5)

            # Episode recall: detection of peaks occurring within out-of-sample test sample
            warn_quarters = [q_test_all[i] for i in range(len(p_arr)) if p_arr[i] >= 0.5]
            det = episode_detection(test_peaks, warn_quarters, horizon=h_int)
            ep_recall = float(det["detected"].mean()) if len(det) else 0.0

            is_primary = (h_label == PRIMARY_HORIZON)

            row = {
                "horizon": h_label,
                "horizon_quarters": h_int,
                "is_primary": is_primary,
                "model": m_name,
                "seed": seed,
                "pr_auc": round(float(metrics["pr_auc"]), 6),
                "roc_auc": round(float(metrics["roc_auc"]), 6),
                "episode_recall": round(ep_recall, 6),
                "precision": round(float(metrics["precision"]), 6),
                "recall": round(float(metrics["recall"]), 6),
                "f1": round(float(metrics["f1"]), 6),
                "accuracy": round(float(metrics["accuracy"]), 6),
                "brier": round(float(metrics["brier"]), 6),
                "n_test_obs": metrics["n"],
                "n_positives": metrics["n_positive"],
            }
            results_rows.append(row)

            star = " (primary)" if is_primary else ""
            markdown_lines.append(
                f"| {h_label}{star} | `{m_name}` | {row['pr_auc']:.4f} | {row['roc_auc']:.4f} | "
                f"{row['episode_recall']:.4f} | {row['accuracy']:.4f} | {row['brier']:.4f} | {row['n_test_obs']} |"
            )

    df_results = pd.DataFrame(results_rows)
    md_content = "\n".join(markdown_lines) + "\n"
    return df_results, md_content


def main() -> int:
    parser = argparse.ArgumentParser(description="Run baseline models on frozen folds")
    parser.add_argument("--features", type=Path, default=FEATURES_DIR / "dataset.parquet")
    parser.add_argument("--folds", type=Path, default=FEATURES_DIR / "folds.json")
    parser.add_argument("--out-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    df_results, md_content = run_baselines(
        features_path=args.features,
        folds_path=args.folds,
        seed=args.seed,
    )

    csv_path = args.out_dir / "baselines.csv"
    md_path = args.out_dir / "baselines.md"

    df_results.to_csv(csv_path, index=False, float_format="%.6f")
    md_path.write_text(md_content, encoding="utf-8")

    csv_digest = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    md_digest = hashlib.sha256(md_path.read_bytes()).hexdigest()

    print(f"Baselines written to {csv_path} (SHA-256: {csv_digest})")
    print(f"Baselines note written to {md_path} (SHA-256: {md_digest})")
    print("\nSummary table (PR-AUC and Episode Recall):")
    for _, r in df_results.iterrows():
        print(f"  {r['horizon']:3s} {r['model']:15s} PR-AUC: {r['pr_auc']:.4f}  Episode Recall: {r['episode_recall']:.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
