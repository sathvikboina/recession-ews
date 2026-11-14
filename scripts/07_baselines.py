#!/usr/bin/env python3
"""Lane 2A baselines on the frozen walk-forward folds.

Three deliberately simple baselines, evaluated on untouched outer test blocks:

1. ``majority`` — the training-block positive prevalence, used as a constant score.
2. ``term_spread`` — univariate logistic on the yield-curve slope
   (``FIN_SLOPE__level``, the 10-year minus 3-month spread).
3. ``plain_logistic`` — multivariate logistic on all 149 predictors.

Imputation and scaling are fitted inside each outer training block only. There is
no feature selection on the test block and no threshold search on the test block:
the threshold is fixed at 0.50 for every baseline. Seed is 42.

Inputs are the Lane 2B artefacts:
``data/clean/dataset.parquet`` and the frozen ``outputs/folds/folds.json`` (D-R37),
mapped onto table rows with :func:`ews.harness.fold_index_splits`.

Outputs: ``outputs/results/baselines.csv`` and ``outputs/results/baselines.md``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ews.harness import fold_index_splits  # noqa: E402
from ews.models.evaluation import episode_detection, pooled_metrics  # noqa: E402
from ews.models.targets import build_peak_targets  # noqa: E402

PROJECT = ROOT
DEFAULT_FEATURES = PROJECT / "data" / "clean" / "dataset.parquet"
DEFAULT_FOLDS = PROJECT / "outputs" / "folds" / "folds.json"
DEFAULT_TURNING_POINTS = PROJECT / "outputs" / "labels" / "USA_turning_points.csv"
RESULTS_DIR = PROJECT / "outputs" / "results"

SEED = 42
THRESHOLD = 0.5
HORIZONS = (("1Q", 1), ("2Q", 2), ("4Q", 4))
PRIMARY_HORIZON = 2
TERM_SPREAD_COLUMN = "FIN_SLOPE__level"


def load_features(path: Path) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    if "quarter" not in frame.columns:
        raise ValueError(f"{path} has no 'quarter' column")
    index = pd.PeriodIndex(frame["quarter"].astype(str), freq="Q")
    table = frame.drop(columns=["quarter"]).astype(float)
    table.index = index
    table.index.name = "quarter"
    return table


def _eligible(index: pd.Index, targets: pd.Series) -> tuple[pd.Index, np.ndarray]:
    keep = targets.reindex(index).notna()
    return index[keep], targets.reindex(index)[keep].astype(int).to_numpy()


def run_baselines(
    features_path: Path = DEFAULT_FEATURES,
    folds_path: Path = DEFAULT_FOLDS,
    turning_points_path: Path = DEFAULT_TURNING_POINTS,
    seed: int = SEED,
) -> tuple[pd.DataFrame, str]:
    table = load_features(features_path)
    turning_points = pd.read_csv(turning_points_path)

    payload = json.loads(folds_path.read_text(encoding="utf-8"))
    if not payload.get("metadata", {}).get("approved"):
        raise ValueError("folds.json is not approved; run make folds first")

    predictor_columns = list(table.columns)
    if TERM_SPREAD_COLUMN not in predictor_columns:
        raise KeyError(f"{TERM_SPREAD_COLUMN} is missing from the feature table")

    peaks = turning_points.loc[
        (turning_points["kind"] == "peak") & (turning_points["in_window"]), "quarter"
    ].astype(str).tolist()

    rows: list[dict] = []
    markdown = [
        "# Baseline Results on the Frozen Folds",
        "",
        f"- Seed: `{seed}`",
        "- Decision threshold: `0.50` (fixed; no threshold search on test)",
        f"- Term-spread predictor: `{TERM_SPREAD_COLUMN}` (10Y minus 3M)",
        "- Imputation and scaling: fitted inside each outer training block only",
        "- Folds: `outputs/folds/folds.json` (D-R37), via `ews.harness.fold_index_splits`",
        "",
        "| Horizon | Baseline | Pooled PR-AUC | ROC-AUC | Episode recall | Accuracy | Brier | N test |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]

    entries = {label: horizon for label, horizon in HORIZONS}
    for horizon_label, horizon in HORIZONS:
        targets_frame = build_peak_targets(
            table.index.astype(str), turning_points, horizon=horizon
        )
        targets = targets_frame.set_index(
            pd.PeriodIndex(targets_frame["quarter"], freq="Q")
        )["y_true"]

        splits = fold_index_splits(payload, table.index, horizon=horizon)

        y_pooled: list[int] = []
        q_pooled: list[str] = []
        predictions = {"majority": [], "term_spread": [], "plain_logistic": []}

        for split in splits:
            train_index = table.index[split["outer_train"]]
            test_index = table.index[split["outer_test"]]

            train_index, y_train = _eligible(train_index, targets)
            test_index, y_test = _eligible(test_index, targets)
            if len(train_index) == 0 or len(test_index) == 0:
                continue
            if len(np.unique(y_train)) < 2:
                continue

            x_train = table.loc[train_index, predictor_columns]
            x_test = table.loc[test_index, predictor_columns]

            prevalence = float(np.mean(y_train))
            predictions["majority"].extend([prevalence] * len(y_test))

            with np.errstate(all="ignore"):
                spread_model = LogisticRegression(random_state=seed, solver="lbfgs")
                spread_model.fit(x_train[[TERM_SPREAD_COLUMN]], y_train)
                predictions["term_spread"].extend(
                    spread_model.predict_proba(x_test[[TERM_SPREAD_COLUMN]])[:, 1]
                )

                imputer = SimpleImputer(strategy="median", keep_empty_features=True)
                x_train_imp = imputer.fit_transform(x_train)
                x_test_imp = imputer.transform(x_test)
                scaler = StandardScaler()
                x_train_scaled = scaler.fit_transform(x_train_imp)
                x_test_scaled = scaler.transform(x_test_imp)

                logistic = LogisticRegression(
                    random_state=seed, solver="lbfgs", max_iter=5000
                )
                logistic.fit(x_train_scaled, y_train)
                predictions["plain_logistic"].extend(
                    logistic.predict_proba(x_test_scaled)[:, 1]
                )

            y_pooled.extend(y_test.tolist())
            q_pooled.extend(test_index.astype(str).tolist())

        y_array = np.asarray(y_pooled, dtype=int)
        # Peak strings and test quarters share the same YYYYQn format.
        test_quarters = set(q_pooled)
        test_peaks = [peak for peak in peaks if peak in test_quarters or peak > min(test_quarters)]

        for model_name, scores in predictions.items():
            score_array = np.asarray(scores, dtype=float)
            if len(score_array) != len(y_array):
                raise RuntimeError(f"{model_name}: prediction/target length mismatch")
            metrics = pooled_metrics(y_array, score_array, threshold=THRESHOLD)
            warnings = [
                q_pooled[i]
                for i in range(len(score_array))
                if score_array[i] >= THRESHOLD
            ]
            detection = episode_detection(test_peaks, warnings, horizon=horizon)
            episode_recall = (
                float(detection["detected"].mean()) if len(detection) else float("nan")
            )

            row = {
                "horizon": horizon_label,
                "horizon_quarters": horizon,
                "is_primary": horizon == PRIMARY_HORIZON,
                "model": model_name,
                "seed": seed,
                "threshold": THRESHOLD,
                "pr_auc": round(float(metrics["pr_auc"]), 6),
                "roc_auc": round(float(metrics["roc_auc"]), 6),
                "episode_recall": round(episode_recall, 6),
                "precision": round(float(metrics["precision"]), 6),
                "recall": round(float(metrics["recall"]), 6),
                "f1": round(float(metrics["f1"]), 6),
                "accuracy": round(float(metrics["accuracy"]), 6),
                "brier": round(float(metrics["brier"]), 6),
                "n_test_obs": metrics["n"],
                "n_positives": metrics["n_positive"],
            }
            rows.append(row)
            star = " **(primary)**" if row["is_primary"] else ""
            markdown.append(
                f"| {horizon_label}{star} | `{model_name}` | {row['pr_auc']:.4f} | "
                f"{row['roc_auc']:.4f} | {row['episode_recall']:.4f} | "
                f"{row['accuracy']:.4f} | {row['brier']:.4f} | {row['n_test_obs']} |"
            )

    if not rows:
        raise RuntimeError("no scorable baseline folds were produced")

    markdown.extend(
        [
            "",
            "Episode recall counts in-window peaks detected by a warning in the "
            "preceding `H` quarters. It is a baseline diagnostic, not the official "
            "C-13 episode-recall guardrail.",
            "",
            "These are baselines only. The official model comparison and the C-13 "
            "ensemble verdict belong to Lane 3.",
            "",
        ]
    )
    return pd.DataFrame(rows), "\n".join(markdown)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features", type=Path, default=DEFAULT_FEATURES)
    parser.add_argument("--folds", type=Path, default=DEFAULT_FOLDS)
    parser.add_argument("--turning-points", type=Path, default=DEFAULT_TURNING_POINTS)
    parser.add_argument("--out-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    results, markdown = run_baselines(
        features_path=args.features,
        folds_path=args.folds,
        turning_points_path=args.turning_points,
        seed=args.seed,
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.out_dir / "baselines.csv"
    md_path = args.out_dir / "baselines.md"
    results.to_csv(csv_path, index=False, float_format="%.6f")
    md_path.write_text(markdown, encoding="utf-8")

    for path in (csv_path, md_path):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        print(f"{path.relative_to(PROJECT)}  sha256 {digest}")

    primary = results[results["is_primary"]]
    print("\nPrimary horizon (2Q), pooled out-of-sample:")
    for _, row in primary.iterrows():
        print(
            f"  {row['model']:15s} PR-AUC {row['pr_auc']:.4f}  "
            f"episode recall {row['episode_recall']:.4f}  n={row['n_test_obs']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
