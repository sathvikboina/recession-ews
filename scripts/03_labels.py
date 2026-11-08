#!/usr/bin/env python3
"""Build the USA BEAI label: DFM -> BBQ -> diffusion gate.

Writes
------
outputs/labels/USA_labels.csv      quarter-level factor, level, R, episode id
outputs/labels/USA_episodes.csv    every candidate episode, kept or rejected
outputs/labels/USA_turning_points.csv
outputs/labels/labels-v3.json      frozen parameter + hash record
outputs/figures/USA_factor.png     factor/level with labelled recessions

Run:
    python scripts/03_labels.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from ews.labels import build as build_label  # noqa: E402
from ews.labels.freeze import (  # noqa: E402
    canonical_frame_sha256,
    check_frozen_input,
    existing_created,
)
from ews.labels.ids import renumber_window_episodes  # noqa: E402
from ews.runtime import study_window  # noqa: E402

OUT = PROJECT / "outputs" / "labels"
FIG = PROJECT / "outputs" / "figures"

# labels-v1 and labels-v2 remain byte-identical under outputs/labels/archive/.
# v3 extends the reporting window to 2026Q3; the estimator, BBQ settings,
# diffusion gate and eight-indicator structure are unchanged from v2.
LABEL_VERSION = "labels-v3"
SUPERSEDES = "labels-v2"
CORE_KEYS = {
    "ACT_GDP_REAL": "USA.ACT_GDP_REAL.Q.NA",
    "ACT_IP": "USA.ACT_IP.M.STD",
    "ACT_EMP": "USA.ACT_EMP.Q.NA",
    "ACT_HOURS": "USA.ACT_HOURS.Q.STD",
    "ACT_RINC": "USA.ACT_RINC.Q.STD",
    "ACT_CONS": "USA.ACT_CONS.Q.NA",
    "ACT_RETAIL": "USA.ACT_RETAIL.M.STD",
    "ACT_INV": "USA.ACT_INV.Q.STD",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--allow-overwrite",
        action="store_true",
        help="replace an existing label version even if its input values differ",
    )
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)

    growth = pd.read_parquet(PROJECT / "data" / "clean" / "USA_growth.parquet")
    ok, message = check_frozen_input(
        growth,
        OUT / f"{LABEL_VERSION}.json",
        allow_overwrite=args.allow_overwrite,
    )
    if message:
        print(message, file=sys.stderr)
    if not ok:
        return 1
    result = build_label(growth, country="USA")

    window = pd.period_range(*study_window(), freq="Q")
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

    meta_path = OUT / f"{LABEL_VERSION}.json"
    created = existing_created(meta_path, date.today().isoformat())
    resolution = (
        pd.read_csv(PROJECT / "data" / "series_resolution.csv")
        .drop_duplicates("series_key", keep="last")
        .set_index("series_key")
    )
    source_ids = {
        ind: str(resolution.loc[key, "source_id"])
        for ind, key in CORE_KEYS.items()
        if key in resolution.index
    }
    record = {
        "label_version": LABEL_VERSION,
        "supersedes": SUPERSEDES,
        "country": "USA",
        "created": created,
        "window": {"start": str(frame.index[0]), "end": str(frame.index[-1]), "quarters": int(len(frame))},
        "window_note": "v3 extends the v2 reporting window by 2026Q1-2026Q3; estimator, BBQ and diffusion gates unchanged.",
        "decisions": {
            "Q-02": {
                "choice": "constructed real non-residential business fixed investment",
                "components": [
                    "Y033RC1Q027SBEA",
                    "B009RC1Q027SBEA",
                    "Y001RC1Q027SBEA",
                    "A008RD3Q086SBEA",
                ],
                "method": "(equipment + structures + intellectual property products) / (deflator/100)",
                "supersedes": "GPDIC1 (broad private investment, included residential and inventories)",
            },
            "Q-04": {
                "choice": "CE16OV LFS fallback, quarterly mean",
                "reason": "US national-accounts quarterly employment is not available in OECD QNA; PAYEMS is an establishment survey, not the Q-04 fallback.",
                "supersedes": "PAYEMS (establishment payrolls)",
            },
            "Q-05": {
                "choice": "keep HOANBS",
                "reason": "Only full-coverage quarterly total-hours series on FRED; nonfarm-business sector coverage is documented. No re-freeze driver.",
            },
        },
        "inputs": {
            "series": list(growth.columns),
            "source_ids": source_ids,
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
        "hashes": {
            "labels_csv_sha256": sha256(labels_path),
            "episodes_csv_sha256": sha256(OUT / "USA_episodes.csv"),
            "turning_points_csv_sha256": sha256(OUT / "USA_turning_points.csv"),
        },
    }
    prior_labels = OUT / "archive" / SUPERSEDES / "USA_labels.csv"
    if prior_labels.exists():
        record["hashes"]["superseded_labels_csv_sha256"] = sha256(prior_labels)
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
