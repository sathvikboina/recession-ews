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

Run:
    python scripts/harmonize.py --country USA
    python scripts/harmonize.py --country JPN
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

PROJECT = Path(__file__).resolve().parents[1]
RAW = PROJECT / "data" / "raw"
CLEAN = PROJECT / "data" / "clean"

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
            # Prefer quarterly national accounts variant if available
            q_na = [m for m in matching if ".Q.NA" in m]
            q_std = [m for m in matching if ".Q." in m]
            if q_na:
                mapping[ind] = q_na[0]
            elif q_std:
                mapping[ind] = q_std[0]
            else:
                mapping[ind] = matching[0]
        else:
            # Fallback default key structure
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


def read_series(source_id: str) -> pd.Series:
    path = latest_raw(source_id)
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
        out = s.copy()
        out.index = s.index.to_period("Y")
        return out.groupby(level=0).last()
    if freq == "M":
        m = s.copy()
        m.index = s.index.to_period("M")
        m = m.groupby(level=0).mean()                 # one value per month
        m.index = m.index.asfreq("Q")
        g = m.groupby(level=0).agg(["mean", "count"])  # count = months in quarter
        return g.loc[g["count"] == 3, "mean"]
    if freq == "W":
        m = s.copy()
        m.index = s.index.to_period("M")
        m = m.groupby(level=0).mean()
        m.index = m.index.asfreq("Q")
        g = m.groupby(level=0).agg(["mean", "count"])
        return g.loc[g["count"] >= 2, "mean"]
    if freq == "D":
        d = s.copy()
        d.index = d.index.to_period("D")
        m = d.groupby(level=0).mean()
        m.index = m.index.asfreq("M")
        m = m.groupby(level=0).mean()                 # one value per month
        m.index = m.index.asfreq("Q")
        g = m.groupby(level=0).agg(["mean", "count"])
        return g.loc[g["count"] == 3, "mean"]
    raise ValueError(f"unsupported frequency {freq}")


def dlog(s: pd.Series) -> pd.Series:
    return 100.0 * np.log(s.where(s > 0)).diff()


def main() -> int:
    parser = argparse.ArgumentParser(description="Harmonise country data into quarterly panel.")
    parser.add_argument("--country", default="USA", help="ISO3 country code (default: USA)")
    parser.add_argument("--sample-start", default=None, help="Earliest estimation quarter, e.g. 1960Q1")
    parser.add_argument("--window-start", default=None, help="Reporting window start, e.g. 1990Q1")
    parser.add_argument("--window-end", default=None, help="Reporting window end, e.g. 2025Q4")
    args = parser.parse_args()

    country = args.country.upper()
    CLEAN.mkdir(parents=True, exist_ok=True)
    ind = load_registry()
    scope_cfg = load_scope_config()

    win_start_cfg = args.window_start or scope_cfg.get("window", {}).get("start", "1990Q1")
    win_end_cfg = args.window_end or scope_cfg.get("window", {}).get("end", "2025Q4")
    window = pd.period_range(win_start_cfg, win_end_cfg, freq="Q")

    with (PROJECT / "data" / "series_resolution.csv").open(newline="", encoding="utf-8") as fh:
        res = [r for r in csv.DictReader(fh) if r["series_key"].startswith(f"{country}.")]

    # If series_resolution has no rows for this country, try source_map_<country>.csv
    if not res:
        source_map_path = PROJECT / "data" / f"source_map_{country}.csv"
        if source_map_path.exists():
            with source_map_path.open(newline="", encoding="utf-8") as fh:
                res = [
                    {
                        "series_key": r.get("scope_key", ""),
                        "source": r.get("source", ""),
                        "source_id": r.get("series_id", ""),
                        "status": r.get("status", ""),
                        "native_freq": r.get("frequency", "Q"),
                        "note": r.get("note", ""),
                    }
                    for r in csv.DictReader(fh)
                    if r.get("status") in ("RESOLVED", "VERIFIED")
                ]

    core_map = get_country_core_keys(country, scope_cfg)

    levels: dict[str, pd.Series] = {}
    used = []
    for r in res:
        if r["status"] not in ("VERIFIED", "RESOLVED"):
            continue
        try:
            s = read_series(r["source_id"])
            q = to_quarterly(s, r["native_freq"])
            q = q[~q.index.duplicated(keep="last")].sort_index()
            levels[r["series_key"]] = q
            used.append(r)
        except FileNotFoundError:
            continue

    if not levels:
        # Check if clean parquet already exists
        existing_growth = CLEAN / f"{country}_growth.parquet"
        if existing_growth.exists():
            print(f"[{country}] using existing {existing_growth}")
            return 0
        raise RuntimeError(f"[{country}] no harmonisable series found in raw downloads")

    raw_panel = pd.DataFrame(levels).sort_index()
    raw_panel.index.name = "quarter"

    # ---- Q-02: real non-residential business fixed investment (USA only) -
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
        sample_start = "1960Q1"  # D-R22 implementation baseline
    else:
        # Earliest quarter with >= 4 core indicators available
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

    # Write files
    panel.to_parquet(CLEAN / f"{country}_levels.parquet")
    growth.to_parquet(CLEAN / f"{country}_growth.parquet")
    panel.to_csv(CLEAN / f"{country}_panel.csv", float_format="%.6f")
    growth.to_csv(CLEAN / f"{country}_growth.csv", float_format="%.6f")

    # ---- coverage reporting (Audit A5 / Step 3) ---------------------------
    # Report both raw_window_coverage and estimator_sample_coverage
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
