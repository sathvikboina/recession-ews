#!/usr/bin/env python3
"""Build the USA BEAI label: DFM -> BBQ -> diffusion gate.

Writes
------
outputs/labels/USA_labels.csv      quarter-level factor, level, R, episode id
outputs/labels/USA_episodes.csv    every candidate episode, kept or rejected
outputs/labels/USA_turning_points.csv
outputs/labels/labels-v1.json      frozen parameter + hash record
outputs/figures/USA_factor.png     factor/level with labelled recessions

Run:
    python scripts/03_labels.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from ews.labels import build as build_label  # noqa: E402
from ews.labels.freeze import canonical_frame_sha256, existing_created  # noqa: E402
from ews.labels.ids import renumber_window_episodes  # noqa: E402

OUT = PROJECT / "outputs" / "labels"
FIG = PROJECT / "outputs" / "figures"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)

    growth = pd.read_parquet(PROJECT / "data" / "clean" / "USA_growth.parquet")
    result = build_label(growth, country="USA")

    window = pd.period_range("1990Q1", "2025Q4", freq="Q")
    frame = result.frame.reindex(window).copy()
    # renumber episode ids inside the reporting window (the estimation sample
    # starts in 1960 and carries earlier episodes that are not reported)
    frame, eps = renumber_window_episodes(frame, result.episodes, window)
    result.diagnostics["n_kept_episodes"] = int(eps["kept"].sum()) if len(eps) else 0
    frame.index = frame.index.astype(str)
    frame.index.name = "quarter"
    frame = frame.round(6)
    labels_path = OUT / "USA_labels.csv"
    frame.to_csv(labels_path, float_format="%.6f")

    if len(eps):
        eps = eps.round(6)
    eps.to_csv(OUT / "USA_episodes.csv", index=False)

    tps = result.turning_points.copy()
    if len(tps):
        tps["in_window"] = tps["quarter"].isin([str(q) for q in window]).astype(bool)
        tps = tps.round(6)
    tps.to_csv(OUT / "USA_turning_points.csv", index=False)

    # ---- figure ---------------------------------------------------------
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(10, 4.5))
        ax.plot(pd.PeriodIndex(frame.index, freq="Q").to_timestamp(), frame["level"], lw=1.6, color="#1f4e79")
        for _, row in eps[eps["kept"]].iterrows():
            ax.axvspan(
                pd.Period(row["peak"], freq="Q").to_timestamp(),
                pd.Period(row["trough"], freq="Q").to_timestamp(),
                color="#c00000", alpha=0.18,
            )
        ax.set_title("USA BEAI activity factor (level), shaded = retained contractions")
        ax.set_ylabel("cumulated factor (growth units)")
        ax.grid(alpha=0.25)
        fig.tight_layout()
        fig.savefig(FIG / "USA_factor.png", dpi=150)
        plt.close(fig)
    except Exception as exc:  # pragma: no cover
        print(f"figure skipped: {exc}")

    meta_path = OUT / "labels-v1.json"
    created = existing_created(meta_path, date.today().isoformat())
    record = {
        "label_version": "labels-v1",
        "country": "USA",
        "created": created,
        "window": {"start": str(frame.index[0]), "end": str(frame.index[-1]), "quarters": int(len(frame))},
        "inputs": {
            "series": list(growth.columns),
            "coverage_window": {c: int(growth[c].reindex(window).notna().sum()) for c in growth.columns},
            "source": "FRED, revised historical data (not real-time vintages)",
            "growth_file_sha256": sha256(PROJECT / "data" / "clean" / "USA_growth.parquet"),
            "growth_values_sha256": canonical_frame_sha256(growth),
        },
        "method": {
            "estimator": result.diagnostics["method"],
            "converged": result.diagnostics["converged"],
            "loglik": result.diagnostics["loglik"],
            "factor_notes": result.diagnostics["factor_notes"],
            "params": result.diagnostics["params"],
            "loadings": result.diagnostics["loadings"],
        },
        "episodes": {
            "candidates_in_window": int(len(eps)),
            "kept": result.diagnostics["n_kept_episodes"],
            "dates": eps.loc[eps["kept"], ["peak", "trough", "duration", "depth_sd", "diffusion"]].to_dict("records")
            if len(eps)
            else [],
        },
        "hashes": {"labels_csv_sha256": sha256(labels_path)},
    }
    meta_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

    print(f"estimator        : {result.diagnostics['method']} (converged={result.diagnostics['converged']})")
    print(f"quarters         : {len(frame)}  {frame.index[0]} .. {frame.index[-1]}")
    print(f"candidate episodes: {result.diagnostics['n_candidate_episodes']}")
    print(f"kept episodes    : {result.diagnostics['n_kept_episodes']}")
    if len(eps):
        print("\nepisodes")
        print(eps[["peak", "trough", "duration", "depth_sd", "diffusion", "kept", "review_flag"]].to_string(index=False))
    print(f"\nwritten: {labels_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
