#!/usr/bin/env python3
"""Harmonise verified series into a quarterly panel (Pipeline A & B inputs).

Rules implemented here are the frozen ones in docs/BUILD_CONTRACT.md:

  C-06  monthly -> quarterly mean, but a quarter is missing unless every
        constituent month is present (no partial-quarter imputation).
        daily -> monthly mean -> quarterly mean, same completeness rule.
  C-02  growth for the label is dlog(level)*100, with the sign flipped so that
        + always means stronger activity (a rise in an indicator whose risk
        sign is POSITIVE lowers activity).
  C-03  no interpolation, no forward fill: missing stays missing.

Outputs
-------
data/clean/<ISO3>_levels.parquet    one column per scope key, levels, quarterly
data/clean/<ISO3>_growth.parquet    label-ready activity growth (BEAI core only)
data/clean/<ISO3>_panel.csv         same panel as CSV for eyeballing / git diff
data/clean/<ISO3>_growth.csv        activity growth CSV
data/clean/coverage_<ISO3>.csv      quarters present per series in the window
data/clean/coverage.csv             (for USA only: preserved for backwards compatibility)
data/clean/USA_validation.parquet   (for USA only: external validation series)

Run:
    python scripts/harmonize.py --country USA
    python scripts/harmonize.py --country JPN
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from ews.runtime import estimation_start, study_window  # noqa: E402

RAW = PROJECT / "data" / "raw"
CLEAN = PROJECT / "data" / "clean"
MANIFEST = PROJECT / "data" / "manifest.csv"

# Standard USA core indicators mapping (frozen in USA milestone)
CORE_USA = {
    "ACT_GDP_REAL": "USA.ACT_GDP_REAL.Q.NA",
    "ACT_IP": "USA.ACT_IP.M.STD",
    "ACT_EMP": "USA.ACT_EMP.Q.NA",
    "ACT_HOURS": "USA.ACT_HOURS.Q.STD",
    "ACT_RINC": "USA.ACT_RINC.Q.STD",
    "ACT_CONS": "USA.ACT_CONS.Q.NA",
    "ACT_RETAIL": "USA.ACT_RETAIL.M.STD",
    "ACT_INV": "USA.ACT_INV.Q.STD",
}


def load_registry() -> dict:
    with (PROJECT / "config" / "indicators.yaml").open(encoding="utf-8") as fh:
        ind = {x["id"]: x for x in yaml.safe_load(fh)["indicators"]}
    return ind


def load_scope_config() -> dict:
    with (PROJECT / "config" / "scope.yaml").open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def get_country_core_keys(country: str, scope_cfg: dict) -> dict[str, str]:
    """Map each 8 core indicators to the country's scope series_key."""
    if country == "USA":
        return dict(CORE_USA)

    core_indicators = scope_cfg.get("indicators", {}).get("core", list(CORE_USA.keys()))
    scope_file = PROJECT / "data" / "scope.csv"
    source_map_file = PROJECT / "data" / f"source_map_{country}.csv"

    mapping: dict[str, str] = {}
    candidates: list[dict[str, Any]] = []

    if source_map_file.exists():
        with source_map_file.open(newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                scope_key = r.get("scope_key", "")
                if scope_key.startswith(f"{country}."):
                    parts = scope_key.split(".")
                    if len(parts) >= 2:
                        candidates.append({"series_key": scope_key, "indicator_id": parts[1]})

    if scope_file.exists():
        with scope_file.open(newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if r["country_iso3"] == country and r["beai_eligible"] == "Y":
                    candidates.append({"series_key": r["series_key"], "indicator_id": r["indicator_id"]})

    for ind in core_indicators:
        matching = [c["series_key"] for c in candidates if c["indicator_id"] == ind]
        if matching:
            q_na = [m for m in matching if ".Q.NA" in m]
            q_std = [m for m in matching if ".Q." in m]
            if q_na:
                mapping[ind] = q_na[0]
            elif q_std:
                mapping[ind] = q_std[0]
            else:
                mapping[ind] = matching[0]
        else:
            mapping[ind] = f"{country}.{ind}.Q.STD"

    return mapping


def latest_raw(source_id: str) -> Path:
    """Locate latest raw download for a source id under data/raw/."""
    hits = sorted(RAW.glob(f"*/*/{source_id}.csv"))
    if not hits:
        hits = sorted(RAW.glob(f"*/{source_id}.csv"))
    if not hits:
        raise FileNotFoundError(f"no raw download for {source_id}")
    return hits[-1]


def manifest_raw(source_id: str) -> Path:
    """Resolve the exact raw file recorded in the manifest and verify its hash."""
    if not MANIFEST.exists():
        return latest_raw(source_id)
    rows = pd.read_csv(MANIFEST)
    rows = rows[rows["source_id"].astype(str) == str(source_id)]
    if rows.empty:
        return latest_raw(source_id)
    row = rows.iloc[-1]
    retrieved = str(row["retrieved_at"])
    source_name = str(row.get("source", "")).lower()
    candidate_paths = [
        RAW / source_name / retrieved / f"{source_id}.csv",
        RAW / retrieved / f"{source_id}.csv",
        RAW / f"fred/{retrieved}/{source_id}.csv",
        RAW / f"esri/{retrieved}/{source_id}.csv",
    ]
    path = None
    for p in candidate_paths:
        if p.exists():
            path = p
            break
    if path is None:
        path = latest_raw(source_id)
    expected = str(row.get("sha256", ""))
    if expected and path.exists():
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError(f"raw SHA-256 mismatch for {source_id}: {path}")
    return path


def read_series(source_id: str) -> pd.Series:
    path = manifest_raw(source_id)
    df = pd.read_csv(path, parse_dates=["observation_date"])
    df = df.dropna(subset=["value"])
    if df.empty:
        return pd.Series(dtype=float)
    return pd.Series(df["value"].to_numpy(), index=pd.DatetimeIndex(df["observation_date"]))


def to_quarterly(s: pd.Series, freq: str) -> pd.Series:
    """Native frequency -> quarterly, complete quarters only."""
    if s.empty:
        return pd.Series(dtype=float)
    if freq == "Q":
        out = s.copy()
        out.index = s.index.to_period("Q")
        return out.groupby(level=0).last()
    if freq == "A":
        annual = s.copy()
        annual.index = s.index.to_period("Y")
        annual = annual.groupby(level=0).last()
        carried: dict[pd.Period, float] = {}
        for year, value in annual.items():
            if pd.isna(value):
                continue
            for quarter in pd.period_range(f"{year + 1}Q1", f"{year + 1}Q4", freq="Q"):
                carried[quarter] = float(value)
        return pd.Series(carried).sort_index()
    if freq == "M":
        m = s.copy()
        m.index = m.index.to_period("M")
        m = m.groupby(level=0).last()
        m.index = m.index.asfreq("Q")
        g = m.groupby(level=0).agg(["mean", "count"])
        return g.loc[g["count"] == 3, "mean"]
    if freq == "B":
        m = s.copy()
        m.index = m.index.to_period("M")
        m = m.groupby(level=0).last()
        m.index = m.index.asfreq("Q")
        g = m.groupby(level=0).agg(["mean", "count"])
        return g.loc[g["count"] >= 2, "mean"]
    if freq == "D":
        d = s.copy()
        d.index = d.index.to_period("D")
        m = d.groupby(level=0).mean()
        m.index = m.index.asfreq("M")
        m = m.groupby(level=0).mean()
        m.index = m.index.asfreq("Q")
        g = m.groupby(level=0).agg(["mean", "count"])
        return g.loc[g["count"] == 3, "mean"]
    raise ValueError(f"unsupported frequency {freq}")


def dlog(s: pd.Series) -> pd.Series:
    return 100.0 * np.log(s.where(s > 0)).diff()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--country", default="USA", help="ISO3 country code (default: USA)")
    parser.add_argument("--sample-start", default=None, help="Explicit sample start (e.g. 1994Q2)")
    args = parser.parse_args()

    country = args.country.upper()
    CLEAN.mkdir(parents=True, exist_ok=True)
    ind = load_registry()
    scope_cfg = load_scope_config()

    win_start_cfg, win_end_cfg = study_window()
    window = pd.period_range(win_start_cfg, win_end_cfg, freq="Q")

    res_path = PROJECT / "data" / "series_resolution.csv"
    map_path = PROJECT / "data" / f"source_map_{country}.csv"
    scope_rows: list[dict[str, str]] = []

    if country == "USA" and res_path.exists():
        with res_path.open(newline="", encoding="utf-8") as fh:
            scope_rows = [r for r in csv.DictReader(fh) if r["series_key"].startswith("USA.")]
    elif map_path.exists():
        with map_path.open(newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                scope_rows.append({
                    "series_key": r.get("scope_key", ""),
                    "source": r.get("source_domain", ""),
                    "source_id": r.get("series_id", ""),
                    "native_freq": r.get("native_freq", "Q"),
                    "status": r.get("status", "VERIFIED"),
                })
    elif res_path.exists():
        with res_path.open(newline="", encoding="utf-8") as fh:
            scope_rows = [r for r in csv.DictReader(fh) if r["series_key"].startswith(f"{country}.")]

    levels: dict[str, pd.Series] = {}
    validation: dict[str, pd.Series] = {}
    used: list[dict[str, str]] = []

    for r in scope_rows:
        if r.get("status") not in ("VERIFIED", "PROVISIONAL", "CANDIDATE"):
            continue
        sid = r.get("source_id", "")
        if not sid:
            continue
        try:
            s = read_series(sid)
        except Exception as exc:
            print(f"[{country}] warning: failed to read {sid} ({r.get('series_key')}): {exc}")
            continue

        q = to_quarterly(s, r.get("native_freq", "Q"))
        q = q[~q.index.duplicated(keep="last")].sort_index()

        skey = r["series_key"]
        if skey == "USA.NBER.Q":
            validation[skey] = q
        else:
            levels[skey] = q
        used.append(r)

    if not levels:
        print(f"ERROR: No series resolved for country {country}", file=sys.stderr)
        return 1

    raw_panel = pd.DataFrame(levels).sort_index()
    raw_panel.index.name = "quarter"
    validation_panel = pd.DataFrame(validation).sort_index() if validation else None
    if validation_panel is not None:
        validation_panel.index.name = "quarter"

    core_map = get_country_core_keys(country, scope_cfg)

    # ---- Q-02 handling for USA -------------------------------------------
    if country == "USA":
        inv_inputs = [
            "USA.ACT_INV_EQ.Q.STD",
            "USA.ACT_INV_STRUCT.Q.STD",
            "USA.ACT_INV_IPP.Q.STD",
            "USA.ACT_INV_DEFL.Q.STD",
        ]
        missing = [k for k in inv_inputs if k not in raw_panel.columns]
        if missing:
            raise RuntimeError(f"Q-02 component series missing from panel: {missing}")
        raw_panel["USA.ACT_INV.Q.STD"] = (
            raw_panel["USA.ACT_INV_EQ.Q.STD"]
            + raw_panel["USA.ACT_INV_STRUCT.Q.STD"]
            + raw_panel["USA.ACT_INV_IPP.Q.STD"]
        ) / (raw_panel["USA.ACT_INV_DEFL.Q.STD"] / 100.0)

    # ---- label matrix: core series, dlog, sign-aligned -------------------
    core_cols: dict[str, pd.Series] = {}
    for ind_id, key in core_map.items():
        if key not in raw_panel.columns:
            continue
        meta = ind.get(ind_id, {})
        src = raw_panel[key]
        if meta.get("form") == "rate":
            g = src.diff()
        else:
            g = dlog(src)
        direction = 1.0 if meta.get("sign_1q_2q") == "NEGATIVE" else -1.0 if meta.get("sign_1q_2q") == "POSITIVE" else 1.0
        core_cols[ind_id] = direction * g

    raw_growth = pd.DataFrame(core_cols)

    # ---- derive SAMPLE_START from config or data availability ------------
    sample_start_cfg = scope_cfg.get("window", {}).get("sample_start", {}).get(country)
    if args.sample_start:
        sample_start = args.sample_start
    elif sample_start_cfg:
        sample_start = sample_start_cfg
    elif country == "USA":
        sample_start = estimation_start()
    else:
        n_avail = raw_growth.notna().sum(axis=1)
        eligible_qs = n_avail[n_avail >= 4].index
        if len(eligible_qs):
            sample_start = str(eligible_qs[0])
        else:
            sample_start = win_start_cfg

    sample_range = pd.period_range(sample_start, win_end_cfg, freq="Q")
    panel = raw_panel.reindex(sample_range)
    panel.index.name = "quarter"
    growth = raw_growth.reindex(sample_range)
    growth.index.name = "quarter"

    panel.to_parquet(CLEAN / f"{country}_levels.parquet")
    growth.to_parquet(CLEAN / f"{country}_growth.parquet")
    panel.to_csv(CLEAN / f"{country}_panel.csv", float_format="%.6f")
    growth.to_csv(CLEAN / f"{country}_growth.csv", float_format="%.6f")

    if country == "USA" and validation_panel is not None:
        validation_panel.reindex(sample_range).to_parquet(CLEAN / "USA_validation.parquet")

    # ---- coverage reporting ----------------------------------------------
    key_to_core = {v: k for k, v in core_map.items()}
    cov = []
    for key in raw_panel.columns:
        raw_cnt = int(raw_panel[key].reindex(window).notna().sum())
        raw_pct = round(raw_cnt / len(window), 4)
        ind_id = key_to_core.get(key)
        if ind_id and ind_id in growth.columns:
            sample_cnt = int(growth[ind_id].reindex(window).notna().sum())
            sample_pct = round(sample_cnt / len(window), 4)
        else:
            sample_cnt = int(panel[key].reindex(window).notna().sum()) if key in panel.columns else 0
            sample_pct = round(sample_cnt / len(window), 4)
        cov.append({
            "series_key": key,
            "raw_window_coverage": raw_cnt,
            "raw_window_coverage_pct": raw_pct,
            "estimator_sample_coverage": sample_cnt,
            "estimator_sample_coverage_pct": sample_pct,
            "quarters": raw_cnt,
            "window": len(window),
            "coverage_pct": raw_pct,
        })
    for ind_id in growth.columns:
        sample_cnt = int(growth[ind_id].reindex(window).notna().sum())
        sample_pct = round(sample_cnt / len(window), 4)
        src_key = core_map.get(ind_id)
        raw_cnt = int(raw_panel[src_key].reindex(window).notna().sum()) if src_key and src_key in raw_panel.columns else sample_cnt
        raw_pct = round(raw_cnt / len(window), 4)
        cov.append({
            "series_key": f"LABEL:{ind_id}",
            "raw_window_coverage": raw_cnt,
            "raw_window_coverage_pct": raw_pct,
            "estimator_sample_coverage": sample_cnt,
            "estimator_sample_coverage_pct": sample_pct,
            "quarters": raw_cnt,
            "window": len(window),
            "coverage_pct": raw_pct,
        })
    cov_df = pd.DataFrame(cov)
    cov_df.to_csv(CLEAN / f"coverage_{country}.csv", index=False)
    if country == "USA":
        cov_df.to_csv(CLEAN / "coverage.csv", index=False)

    print(f"[{country}] panel   : {panel.shape[0]} quarters x {panel.shape[1]} series")
    print(f"[{country}] sample  : {sample_range[0]} .. {sample_range[-1]} (window: {window[0]} .. {window[-1]})")
    print(f"\n[{country}] label coverage (BEAI core):")
    for row in cov:
        if row["series_key"].startswith("LABEL:"):
            print(f"  {row['series_key'][6:]:14s} raw={row['raw_window_coverage']:3d}/{row['window']} ({row['raw_window_coverage_pct']:6.1%})  sample={row['estimator_sample_coverage']:3d}/{row['window']} ({row['estimator_sample_coverage_pct']:6.1%})")

    first_q_4 = growth.notna().sum(axis=1).ge(4)
    if first_q_4.any():
        print(f"\n[{country}] first quarter with >=4 core indicators: {first_q_4.idxmax()}")
    print(f"[{country}] written : {CLEAN}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
