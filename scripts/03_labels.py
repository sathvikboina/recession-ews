#!/usr/bin/env python3
"""Build country BEAI label: DFM -> BBQ -> diffusion gate.

Writes
------
outputs/labels/<ISO3>/<ISO3>_labels.csv      quarter-level factor, level, R, episode id
outputs/labels/<ISO3>/<ISO3>_episodes.csv    every candidate episode, kept or rejected
outputs/labels/<ISO3>/<ISO3>_turning_points.csv
outputs/labels/<ISO3>/labels-v1-<ISO3>.json  frozen parameter + hash record
outputs/figures/<ISO3>_factor.png            factor/level with labelled recessions

(For USA: writes directly under outputs/labels/ to preserve historical paths and tests).

Run:
    python scripts/03_labels.py --country USA
    python scripts/03_labels.py --country JPN --label-version labels-v1-JPN
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from ews.labels import build as build_label  # noqa: E402
from ews.labels.freeze import canonical_frame_sha256, existing_created  # noqa: E402
from ews.labels.ids import renumber_window_episodes  # noqa: E402

OUT = PROJECT / "outputs" / "labels"
FIG = PROJECT / "outputs" / "figures"
CLEAN = PROJECT / "data" / "clean"

# Core keys mapping for USA
CORE_KEYS_USA = {
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


def load_scope_config() -> dict:
    with (PROJECT / "config" / "scope.yaml").open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def get_source_ids(country: str) -> dict[str, str]:
    """Retrieve mapping of core indicator -> source_id."""
    if country == "JPN":
        return {
            "ACT_GDP_REAL": "ESRI:tables/gaku-jk2622.csv (Col 1 - 実質ＧＤＰ)",
            "ACT_CONS": "ESRI:tables/gaku-jk2622.csv (Col 2 - 民間最終消費支出)",
            "ACT_INV": "ESRI:tables/gaku-jk2622.csv (Col 6 - 民間企業設備)",
            "ACT_RINC": "ESRI:tables/kshotoku-q2622.csv (Col 11 - 雇用者報酬（実質・季節調整系列）)",
            "ACT_IP": "FRED:JPNPROINDMISMEI",
            "ACT_EMP": "FRED:LFEMTTTTJPM647S",
        }

    res_path = PROJECT / "data" / "series_resolution.csv"
    map_path = PROJECT / "data" / f"source_map_{country}.csv"
    source_ids: dict[str, str] = {}

    if res_path.exists():
        res = (
            pd.read_csv(res_path)
            .drop_duplicates("series_key", keep="last")
            .set_index("series_key")
        )
        if country == "USA":
            for ind, key in CORE_KEYS_USA.items():
                if key in res.index:
                    source_ids[ind] = str(res.loc[key, "source_id"])
            return source_ids

    if map_path.exists():
        m = pd.read_csv(map_path)
        for _, row in m.iterrows():
            scope_key = str(row.get("scope_key", ""))
            parts = scope_key.split(".")
            if len(parts) >= 2 and parts[1].startswith("ACT_"):
                source_ids[parts[1]] = str(row.get("series_id", ""))

    return source_ids


def get_raw_input_files_and_hashes(country: str) -> dict[str, str]:
    """Return dictionary of relative_path -> sha256 for all raw input files."""
    raw_files: dict[str, str] = {}
    if country == "JPN":
        esri_dir = PROJECT / "data" / "raw" / "esri" / "2026-11-13"
        fred_dir = PROJECT / "data" / "raw" / "fred" / "2026-11-13"
        target_files = [
            esri_dir / "gaku-jk2622.csv",
            esri_dir / "kshotoku-q2622.csv",
            esri_dir / "JPN_ACT_GDP_REAL.csv",
            esri_dir / "JPN_ACT_CONS.csv",
            esri_dir / "JPN_ACT_INV.csv",
            esri_dir / "JPN_ACT_RINC.csv",
            fred_dir / "JPNPROINDMISMEI.csv",
            fred_dir / "LFEMTTTTJPM647S.csv",
        ]
        for p in target_files:
            if p.exists():
                rel = str(p.relative_to(PROJECT)).replace("\\", "/")
                raw_files[rel] = sha256(p)
    return raw_files


def main() -> int:
    parser = argparse.ArgumentParser(description="Build country BEAI label.")
    parser.add_argument("--country", default="USA", help="ISO3 country code (default: USA)")
    parser.add_argument("--label-version", default=None, help="Label version string")
    parser.add_argument("--force", action="store_true", help="Force overwrite even if frozen")
    args = parser.parse_args()

    country = args.country.upper()
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)

    if country == "USA":
        out_dir = OUT
        label_version = args.label_version or "labels-v2"
        supersedes = "labels-v1"
    else:
        out_dir = OUT / country
        out_dir.mkdir(parents=True, exist_ok=True)
        label_version = args.label_version or f"labels-v1-{country}"
        supersedes = None

    scope_cfg = load_scope_config()
    win_start = scope_cfg.get("window", {}).get("start", "1990Q1")
    win_end = scope_cfg.get("window", {}).get("end", "2025Q4")
    window = pd.period_range(win_start, win_end, freq="Q")

    growth_path = PROJECT / "data" / "clean" / f"{country}_growth.parquet"
    if not growth_path.exists():
        raise FileNotFoundError(f"cleaned growth matrix missing: {growth_path}")
    growth = pd.read_parquet(growth_path)
    result = build_label(growth, country=country)

    frame = result.frame.reindex(window).copy()
    if "R" in frame.columns:
        frame["R"] = frame["R"].fillna(0).astype(int)
    if "n_available" in frame.columns:
        frame["n_available"] = frame["n_available"].fillna(0).astype(int)
    frame, eps = renumber_window_episodes(frame, result.episodes, window)
    result.diagnostics["n_kept_episodes"] = int(eps["kept"].sum()) if len(eps) else 0
    frame.index = frame.index.astype(str)
    frame.index.name = "quarter"
    frame = frame.round(6)

    labels_path = out_dir / f"{country}_labels.csv"
    episodes_path = out_dir / f"{country}_episodes.csv"
    turning_points_path = out_dir / f"{country}_turning_points.csv"
    meta_path = out_dir / f"{label_version}.json"

    # Freeze guard: check if label file already exists and is frozen
    frozen_guard_active = False
    if labels_path.exists() and not args.force:
        if country == "USA":
            # Baseline USA label must not move (no collateral change rule)
            frozen_guard_active = True
            print(f"freeze guard: {labels_path} is frozen. Preserving baseline label file.")
        elif meta_path.exists():
            # Check if canonical digest changed
            try:
                existing_meta = json.loads(meta_path.read_text(encoding="utf-8"))
                past_digest = existing_meta.get("inputs", {}).get("growth_values_sha256")
                curr_digest = canonical_frame_sha256(growth)
                if past_digest and past_digest != curr_digest:
                    frozen_guard_active = True
                    print(f"freeze guard: input growth digest changed from frozen {past_digest}. Refusing overwrite.")
            except Exception:
                pass

    if not frozen_guard_active:
        frame.to_csv(labels_path, float_format="%.6f", lineterminator="\n")
        if len(eps):
            eps = eps.round(6)
        eps.to_csv(episodes_path, index=False, lineterminator="\n")

        tps = result.turning_points.copy()
        if len(tps):
            tps["in_window"] = tps["quarter"].isin([str(q) for q in window]).astype(bool)
            tps = tps.round(6)
        tps.to_csv(turning_points_path, index=False, lineterminator="\n")

    # ---- figure ---------------------------------------------------------
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(10, 4.5))
        ax.plot(pd.PeriodIndex(frame.index, freq="Q").to_timestamp(), frame["level"], lw=1.6, color="#1f4e79")
        if len(eps):
            for _, row in eps[eps["kept"]].iterrows():
                ax.axvspan(
                    pd.Period(row["peak"], freq="Q").to_timestamp(),
                    pd.Period(row["trough"], freq="Q").to_timestamp(),
                    color="#c00000", alpha=0.18,
                )
        ax.set_title(f"{country} BEAI activity factor (level), shaded = retained contractions")
        ax.set_ylabel("cumulated factor (growth units)")
        ax.grid(alpha=0.25)
        fig.tight_layout()
        fig.savefig(FIG / f"{country}_factor.png", dpi=150)
        plt.close(fig)
    except Exception as exc:  # pragma: no cover
        print(f"figure skipped: {exc}")

    # ---- metadata -------------------------------------------------------
    created = existing_created(meta_path, date.today().isoformat())
    source_ids = get_source_ids(country)
    cfg = load_scope_config()
    sample_start_cfg = cfg.get("window", {}).get("sample_start", {}).get(country)
    if country == "USA":
        sample_start_provenance = "usa_baseline (D-R22 implementation baseline)"
    elif sample_start_cfg:
        sample_start_provenance = f"config_scope_yaml_{country}"
    else:
        sample_start_provenance = "dynamic_rule_c03_min4_indicators"

    cov_window: dict = {c: int(growth[c].reindex(window).notna().sum()) for c in growth.columns}
    if country != "USA":
        cov_csv = CLEAN / f"coverage_{country}.csv"
        raw_map = {}
        sample_map = {}
        if cov_csv.exists():
            cdf = pd.read_csv(cov_csv)
            for _, r in cdf.iterrows():
                sk = str(r.get("series_key", ""))
                if sk.startswith("LABEL:"):
                    cname = sk[6:]
                    raw_map[cname] = int(r.get("raw_window_coverage", 0))
                    sample_map[cname] = int(r.get("estimator_sample_coverage", 0))
        if raw_map:
            cov_window = {
                "raw_window_coverage": raw_map,
                "estimator_sample_coverage": sample_map,
            }

    record = {
        "label_version": label_version,
        "country": country,
        "created": created,
        "window": {"start": str(frame.index[0]), "end": str(frame.index[-1]), "quarters": int(len(frame))},
        "inputs": {
            "series": list(growth.columns),
            "source_ids": source_ids,
            "coverage_window": cov_window,
            "source": "FRED revised historical" if country == "USA" else f"Official statistics ({country})",
            "growth_file_sha256": sha256(growth_path),
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
            "episodes_csv_sha256": sha256(episodes_path),
            "turning_points_csv_sha256": sha256(turning_points_path),
        },
    }
    if country != "USA":
        record["sample_start"] = {
            "resolved": str(growth.index[0]),
            "provenance": sample_start_provenance,
        }
        record["inputs"]["raw_input_hashes"] = get_raw_input_files_and_hashes(country)
    if supersedes:
        record["supersedes"] = supersedes
        v1_labels = OUT / "archive" / supersedes / f"{country}_labels.csv"
        if v1_labels.exists():
            record["hashes"]["superseded_labels_csv_sha256"] = sha256(v1_labels)

    if not frozen_guard_active or not meta_path.exists():
        meta_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

    print(f"[{country}] estimator        : {result.diagnostics['method']} (converged={result.diagnostics['converged']})")
    print(f"[{country}] quarters         : {len(frame)}  {frame.index[0]} .. {frame.index[-1]}")
    print(f"[{country}] candidate episodes: {result.diagnostics['n_candidate_episodes']}")
    print(f"[{country}] kept episodes    : {result.diagnostics['n_kept_episodes']}")
    if len(eps):
        print(f"\n[{country}] episodes")
        print(eps[["peak", "trough", "duration", "depth_sd", "diffusion", "kept", "review_flag"]].to_string(index=False))
    print(f"\n[{country}] labels path    : {labels_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
