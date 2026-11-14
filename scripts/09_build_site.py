#!/usr/bin/env python3
"""Build the static data bundle for the interactive project site.

Reads the frozen artefacts and writes ``site/assets/data.json``. The site itself is
plain HTML/CSS/JS and works offline. Nothing is fetched at runtime.

Usage:
    python scripts/09_build_site.py
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ews.features import load_panel  # noqa: E402

SITE_DATA = ROOT / "site" / "assets" / "data.json"
LABELS = ROOT / "outputs" / "labels"
FOLDS = ROOT / "outputs" / "folds" / "folds.json"
TABLE = ROOT / "data" / "clean" / "dataset.parquet"
BASELINES = ROOT / "outputs" / "results" / "baselines.csv"

NBER_EPISODES = [
    {"peak": "1990Q3", "trough": "1991Q1"},
    {"peak": "2001Q1", "trough": "2001Q4"},
    {"peak": "2007Q4", "trough": "2009Q2"},
    {"peak": "2019Q4", "trough": "2020Q2"},
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean_numbers(values: np.ndarray) -> list:
    out = []
    for value in values:
        if value is None or not math.isfinite(float(value)):
            out.append(None)
        else:
            out.append(round(float(value), 4))
    return out


def feature_groups(names: list[str]) -> dict[str, str]:
    groups = {}
    for name in names:
        series = name.split("__", 1)[0]
        if series.startswith("beai_copy_"):
            groups[name] = "BEAI copy · " + series[len("beai_copy_") :]
        else:
            groups[name] = series
    return groups


def main() -> int:
    labels = pd.read_csv(LABELS / "USA_labels.csv")
    episodes = pd.read_csv(LABELS / "USA_episodes.csv")
    turning_points = pd.read_csv(LABELS / "USA_turning_points.csv")
    table = pd.read_parquet(TABLE)
    folds = json.loads(FOLDS.read_text(encoding="utf-8"))
    baselines = pd.read_csv(BASELINES)

    names = [c for c in table.columns if c != "quarter"]
    values = table[names].to_numpy(dtype=float)
    feature_values = [clean_numbers(row) for row in values]

    kept = episodes[episodes["kept"] == True]  # noqa: E712
    label_episodes = [
        {
            "peak": str(row.peak),
            "trough": str(row.trough),
            "duration": int(row.duration),
            "depth_sd": round(float(row.depth_sd), 3),
            "diffusion": round(float(row.diffusion), 3),
            "episode_id": int(row.episode_id),
        }
        for row in kept.itertuples()
    ]

    fold_blocks = {}
    for horizon, block in folds["horizons"].items():
        fold_blocks[horizon] = [
            {
                "train_start": item["train_start"],
                "train_end": item["train_end"],
                "test_start": item["test_start"],
                "test_end": item["test_end"],
            }
            for item in block["outer"]
        ]

    baseline_rows = []
    for row in baselines.itertuples():
        baseline_rows.append(
            {
                "horizon": row.horizon,
                "horizon_quarters": int(row.horizon_quarters),
                "is_primary": bool(row.is_primary),
                "model": row.model,
                "seed": int(row.seed),
                "threshold": float(row.threshold),
                "pr_auc": None if pd.isna(row.pr_auc) else round(float(row.pr_auc), 4),
                "roc_auc": None if pd.isna(row.roc_auc) else round(float(row.roc_auc), 4),
                "episode_recall": None
                if pd.isna(row.episode_recall)
                else round(float(row.episode_recall), 4),
                "accuracy": round(float(row.accuracy), 4),
                "brier": round(float(row.brier), 4),
                "n_test_obs": int(row.n_test_obs),
                "n_positives": int(row.n_positives),
            }
        )

    payload = {
        "meta": {
            "generated": date.today().isoformat(),
            "project": "Cross-Country Recession Early Warning",
            "window": {"start": "1990Q1", "end": "2026Q3", "quarters": len(labels)},
            "status": "label, features, folds, firewall and baselines complete; official model run pending",
            "counts": {
                "label_quarters": int(len(labels)),
                "features": len(names),
                "beai_copy_columns": sum(n.startswith("beai_copy_") for n in names),
                "series": 20,
                "outer_folds_per_horizon": len(fold_blocks["2"]),
                "nber_episodes": len(NBER_EPISODES),
            },
            "hashes": {
                "USA_labels.csv": sha256(LABELS / "USA_labels.csv"),
                "JPN_labels.csv": sha256(LABELS / "JPN" / "JPN_labels.csv"),
                "dataset.parquet": sha256(TABLE),
                "folds.json": sha256(FOLDS),
            },
        },
        "label": {
            "quarters": labels["quarter"].astype(str).tolist(),
            "level": clean_numbers(labels["level"].to_numpy()),
            "factor": clean_numbers(labels["factor"].to_numpy()),
            "diffusion": clean_numbers(labels["deterioration_share"].to_numpy()),
            "n_available": labels["n_available"].astype(int).tolist(),
            "R": labels["R"].astype(int).tolist(),
            "episodes": label_episodes,
            "nber": NBER_EPISODES,
            "turning_points": [
                {"quarter": str(row.quarter), "kind": row.kind, "in_window": bool(row.in_window)}
                for row in turning_points.itertuples()
            ],
        },
        "features": {
            "names": names,
            "groups": feature_groups(names),
            "values": feature_values,
        },
        "folds": {
            "horizons": list(fold_blocks),
            "primary": 2,
            "blocks": fold_blocks,
            "metadata": folds["metadata"],
        },
        "baselines": baseline_rows,
        "jpn": {
            "window": "1990Q1–2025Q4",
            "quarters": 144,
            "episodes_matched": 5,
            "episodes_total": 5,
            "recall": 0.880,
            "precision": 0.629,
            "decision": "D-R38",
        },
        "ensemble_rule": {
            "members": 3,
            "weighting": "equal",
            "minimum_gain": 0.01,
            "bootstrap_resamples": 1000,
            "confidence": 0.95,
            "episode_guardrail": True,
        },
    }

    SITE_DATA.parent.mkdir(parents=True, exist_ok=True)
    SITE_DATA.write_text(
        json.dumps(payload, separators=(",", ":"), allow_nan=False),
        encoding="utf-8",
    )
    print(f"wrote {SITE_DATA.relative_to(ROOT)} ({SITE_DATA.stat().st_size / 1024:.0f} KB)")
    print(f"  {len(names)} features x {len(labels)} quarters, {len(label_episodes)} label episodes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
