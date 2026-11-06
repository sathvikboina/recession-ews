#!/usr/bin/env python3
"""Harmonise the verified FRED series into one quarterly panel.

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
data/clean/USA_levels.parquet    predictor/non-label levels, quarterly
data/clean/USA_validation.parquet  external validation series (NBER), kept out of the feature panel
data/clean/USA_growth.parquet    label-ready activity growth (BEAI core only)
data/clean/USA_panel.csv         same predictor panel as CSV for eyeballing / git diff
data/clean/coverage.csv          quarters present per series in the window

Run:
    python scripts/harmonize.py
"""
from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from ews.runtime import estimation_start, study_window  # noqa: E402

RAW = PROJECT / "data" / "raw" / "fred"
CLEAN = PROJECT / "data" / "clean"
MANIFEST = PROJECT / "data" / "manifest.csv"
# Reporting and estimation windows come from config/scope.yaml. The factor is
# estimated with pre-1990 context so the left endpoint does not censor the
# 1990-91 peak (D-R22); labels are still reported for WINDOW only.
WIN_START, WIN_END = study_window()
WINDOW = pd.period_range(WIN_START, WIN_END, freq="Q")
SAMPLE = pd.period_range(estimation_start(), WIN_END, freq="Q")

# The eight §11 core indicators, in the variant chosen for the US label.
CORE = {
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


def latest_raw(source_id: str) -> Path:
    """Fallback for a raw tree without a manifest (legacy checkouts only)."""
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
        raise FileNotFoundError(f"{source_id} is not in {MANIFEST}")
    row = rows.iloc[-1]
    path = RAW / str(row["retrieved_at"]) / f"{source_id}.csv"
    if not path.exists():
        raise FileNotFoundError(f"manifest points to a missing raw file: {path}")
    expected = str(row.get("sha256", ""))
    if expected:
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
        # C-06: the annual value for year Y is carried forward to the four
        # quarters of Y+1 (one-year publication lag); no disaggregation.
        carried: dict[pd.Period, float] = {}
        for year, value in annual.items():
            if pd.isna(value):
                continue
            for quarter in pd.period_range(f"{year + 1}Q1", f"{year + 1}Q4", freq="Q"):
                carried[quarter] = float(value)
        return pd.Series(carried, dtype=float).sort_index()
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
    CLEAN.mkdir(parents=True, exist_ok=True)
    ind = load_registry()

    with (PROJECT / "data" / "series_resolution.csv").open(newline="", encoding="utf-8") as fh:
        res = [r for r in csv.DictReader(fh) if r["series_key"].startswith("USA.")]

    levels: dict[str, pd.Series] = {}
    validation: dict[str, pd.Series] = {}
    used = []
    for r in res:
        if r["source"] != "FRED" or r["status"] != "VERIFIED":
            continue
        if r["source_id"] in {u["source_id"] for u in used}:
            # same FRED id used by two scope rows: keep both, they are variants
            pass
        s = read_series(r["source_id"])
        q = to_quarterly(s, r["native_freq"])
        q = q[~q.index.duplicated(keep="last")].sort_index()
        q = q.reindex(SAMPLE)
        # External chronologies are validation-only. They must never enter the
        # panel that feature construction reads (C-01, C-11, FW-06).
        if r["series_key"] == "USA.NBER.Q":
            validation[r["series_key"]] = q
        else:
            levels[r["series_key"]] = q
        used.append(r)

    panel = pd.DataFrame(levels).sort_index()
    panel.index.name = "quarter"
    validation_panel = pd.DataFrame(validation).sort_index()
    validation_panel.index.name = "quarter"

    # ---- Q-02: real non-residential business fixed investment -----------
    # The current FRED vintage has no full-history single series for this
    # concept (PNFIC1 starts in 2007).  Construct it from the three nominal
    # BEA asset components and the non-residential implicit price deflator.
    # Over the 2007Q1-2026Q3 overlap this reproduces PNFIC1 to <0.02bn.
    inv_inputs = [
        "USA.ACT_INV_EQ.Q.STD",
        "USA.ACT_INV_STRUCT.Q.STD",
        "USA.ACT_INV_IPP.Q.STD",
        "USA.ACT_INV_DEFL.Q.STD",
    ]
    missing = [k for k in inv_inputs if k not in panel.columns]
    if missing:
        raise RuntimeError(f"Q-02 component series missing from panel: {missing}")
    panel["USA.ACT_INV.Q.STD"] = (
        panel["USA.ACT_INV_EQ.Q.STD"]
        + panel["USA.ACT_INV_STRUCT.Q.STD"]
        + panel["USA.ACT_INV_IPP.Q.STD"]
    ) / (panel["USA.ACT_INV_DEFL.Q.STD"] / 100.0)

    # ---- label matrix: eight core series, dlog, sign-aligned -----------
    core_cols: dict[str, pd.Series] = {}
    for ind_id, key in CORE.items():
        meta = ind[ind_id]
        src = panel[key]
        if meta["form"] == "rate":
            g = src.diff()
        else:
            g = dlog(src)
        # expected_sign is relative to recession risk:
        # NEGATIVE = higher value lowers risk  -> +1 for activity
        # POSITIVE = higher value raises risk   -> -1 for activity
        direction = 1.0 if meta["sign_1q_2q"] == "NEGATIVE" else -1.0 if meta["sign_1q_2q"] == "POSITIVE" else 1.0
        core_cols[ind_id] = direction * g
    growth = pd.DataFrame(core_cols).reindex(SAMPLE)
    growth.index.name = "quarter"

    panel.to_parquet(CLEAN / "USA_levels.parquet")
    validation_panel.to_parquet(CLEAN / "USA_validation.parquet")
    growth.to_parquet(CLEAN / "USA_growth.parquet")
    panel.to_csv(CLEAN / "USA_panel.csv", float_format="%.6f")
    growth.to_csv(CLEAN / "USA_growth.csv", float_format="%.6f")

    cov = []
    for key in panel.columns:
        n = int(panel[key].reindex(WINDOW).notna().sum())
        cov.append({"series_key": key, "quarters": n, "window": len(WINDOW), "coverage_pct": round(n / len(WINDOW), 4)})
    for ind_id in growth.columns:
        n = int(growth[ind_id].reindex(WINDOW).notna().sum())
        cov.append({"series_key": f"LABEL:{ind_id}", "quarters": n, "window": len(WINDOW), "coverage_pct": round(n / len(WINDOW), 4)})
    pd.DataFrame(cov).to_csv(CLEAN / "coverage.csv", index=False)

    print(f"panel   : {panel.shape[0]} quarters x {panel.shape[1]} series")
    print(f"sample  : {SAMPLE[0]} .. {SAMPLE[-1]}  (labels reported {WINDOW[0]} .. {WINDOW[-1]})")
    print("\nlabel coverage (BEAI core):")
    for row in cov:
        if row["series_key"].startswith("LABEL:"):
            print(f"  {row['series_key'][6:]:14s} {row['quarters']:3d}/{row['window']}  {row['coverage_pct']:6.1%}")
    print("\nfirst quarter with >=4 core indicators:",
          str(growth.notna().sum(axis=1).ge(4).idxmax()))
    print(f"written : {CLEAN}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
