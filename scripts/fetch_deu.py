#!/usr/bin/env python3
"""Fetch German economic series for Lane 1 (Germany BEAI label & coverage evaluation).

Sources:
FRED (Destatis, Eurostat, OECD Main Economic Indicators):
- CLVMNACSCAB1GQDE: Real Gross Domestic Product for Germany (chained 2015 Euros, quarterly, SA).
- DEUPROINDMISMEI: Production of Total Industry in Germany (monthly, SA, Index 2015=100).
- LFEMTTTTDEQ647S: Employment Total: 15 Years or over for Germany (quarterly, SA, persons).
- NAEXKP02DEQ661S: Private Final Consumption Expenditure for Germany (quarterly, SA, chained 2015 Euros).
- NAEXKP04DEQ661S: Gross Fixed Capital Formation for Germany (quarterly, SA, chained 2015 Euros).
- DEUSARTMISMEI: Retail Trade Volume Index for Germany (monthly, SA, Index 2015=100).

Outputs:
data/raw/fred/<YYYY-MM-DD>/<id>.csv    immutable raw payload
data/manifest.csv                      updated with Germany active entries
data/series_resolution.csv             updated with Germany active entries
data/source_map_DEU.csv                updated with digests & status

Usage:
    python scripts/fetch_deu.py
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
from pathlib import Path
import subprocess
import sys

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
RAW_FRED = PROJECT / "data" / "raw" / "fred"
MANIFEST = PROJECT / "data" / "manifest.csv"
SERIES_RES = PROJECT / "data" / "series_resolution.csv"
SOURCE_MAP = PROJECT / "data" / "source_map_DEU.csv"

WINDOW_START = "1990-01-01"
WINDOW_END = "2025-12-31"
WINDOW_QUARTERS = 144
MIN_COVERAGE = 0.70

SERIES_SPECS = [
    {
        "series_key": "DEU.ACT_GDP_REAL.Q.NA",
        "source": "FRED",
        "source_id": "CLVMNACSCAB1GQDE",
        "url": "https://fred.stlouisfed.org/series/CLVMNACSCAB1GQDE",
        "freq": "Q",
        "units": "Millions of Chained 2015 Euros",
        "seasonal": "SA",
        "note": "real gross domestic product (Destatis / Eurostat), chained volume, SA",
    },
    {
        "series_key": "DEU.ACT_IP.M.STD",
        "source": "FRED",
        "source_id": "DEUPROINDMISMEI",
        "url": "https://fred.stlouisfed.org/series/DEUPROINDMISMEI",
        "freq": "M",
        "units": "Index 2015=100",
        "seasonal": "SA",
        "note": "industrial production index, total industry ex construction (OECD MEI), SA",
    },
    {
        "series_key": "DEU.ACT_EMP.Q.NA",
        "source": "FRED",
        "source_id": "LFEMTTTTDEQ647S",
        "url": "https://fred.stlouisfed.org/series/LFEMTTTTDEQ647S",
        "freq": "Q",
        "units": "Persons",
        "seasonal": "SA",
        "note": "total employment, all persons (OECD QNA / Destatis), SA",
    },
    {
        "series_key": "DEU.ACT_CONS.Q.NA",
        "source": "FRED",
        "source_id": "NAEXKP02DEQ661S",
        "url": "https://fred.stlouisfed.org/series/NAEXKP02DEQ661S",
        "freq": "Q",
        "units": "Millions of Chained 2015 Euros",
        "seasonal": "SA",
        "note": "real private final consumption expenditure (Destatis / Eurostat), chained volume, SA",
    },
    {
        "series_key": "DEU.ACT_INV.Q.STD",
        "source": "FRED",
        "source_id": "NAEXKP04DEQ661S",
        "url": "https://fred.stlouisfed.org/series/NAEXKP04DEQ661S",
        "freq": "Q",
        "units": "Millions of Chained 2015 Euros",
        "seasonal": "SA",
        "note": "real gross fixed capital formation (Destatis / Eurostat), chained volume, SA",
    },
    {
        "series_key": "DEU.ACT_RETAIL.M.STD",
        "source": "FRED",
        "source_id": "DEUSARTMISMEI",
        "url": "https://fred.stlouisfed.org/series/DEUSARTMISMEI",
        "freq": "M",
        "units": "Index 2015=100",
        "seasonal": "SA",
        "note": "retail trade volume index ex motor vehicles (Destatis / OECD MEI), SA",
    },
]


def curl_text(url: str, timeout: int = 40) -> str:
    proc = subprocess.run(
        ["curl.exe", "-sS", "--max-time", str(timeout), url],
        capture_output=True,
        text=True,
        errors="replace",
    )
    if proc.returncode != 0:
        raise RuntimeError(f"curl failed for {url}: {proc.stderr}")
    return proc.stdout


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def parse_fred_csv(csv_text: str) -> list[tuple[str, float]]:
    rows: list[tuple[str, float]] = []
    for rec in list(csv.reader(io.StringIO(csv_text)))[1:]:
        if len(rec) != 2:
            continue
        date, val = rec[0].strip(), rec[1].strip()
        if not date or val in ("", ".", "NaN"):
            continue
        try:
            rows.append((date, float(val)))
        except ValueError:
            continue
    return rows


def compute_quarterly_coverage(rows: list[tuple[str, float]], freq: str) -> tuple[int, int, float]:
    """Compute number of complete quarters in 1990Q1-2025Q4 window."""
    win = pd.period_range("1990Q1", "2025Q4", freq="Q")
    if not rows:
        return 0, len(win), 0.0

    df = pd.DataFrame(rows, columns=["date", "value"])
    df["dt"] = pd.to_datetime(df["date"])

    if freq == "Q":
        df["q"] = df["dt"].dt.to_period("Q")
        present = set(df["q"])
        covered = sum(1 for q in win if q in present)
    elif freq == "M":
        df["m"] = df["dt"].dt.to_period("M")
        m_counts = df.groupby(df["m"].dt.asfreq("Q"))["m"].nunique()
        complete_q = set(m_counts[m_counts == 3].index)
        covered = sum(1 for q in win if q in complete_q)
    else:
        covered = 0
    return covered, len(win), round(covered / len(win), 4)


def save_series_csv(path: Path, rows: list[tuple[str, float]]) -> None:
    lines = ["observation_date,value"]
    for d, v in rows:
        lines.append(f"{d},{v}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    run_date = dt.date.today().isoformat()
    fred_outdir = RAW_FRED / run_date
    fred_outdir.mkdir(parents=True, exist_ok=True)

    print(f"=== Downloading Germany Data ({run_date}) ===")

    manifest_rows: list[dict] = []
    series_res_rows: list[dict] = []

    print("\n=== Germany Indicator Verification & Coverage ===")
    print(f"{'Indicator':<26} {'Source ID':<18} {'Freq':<4} {'Covered':<10} {'Coverage %':<10} {'Pass >=70%?'}")
    print("-" * 75)

    for item in SERIES_SPECS:
        sid = item["source_id"]
        csv_url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
        print(f"Fetching {sid} from {csv_url}...")
        csv_text = curl_text(csv_url)
        rows = parse_fred_csv(csv_text)
        out_path = fred_outdir / f"{sid}.csv"
        save_series_csv(out_path, rows)

        n_cov, n_win, cov_pct = compute_quarterly_coverage(rows, item["freq"])
        passed = cov_pct >= MIN_COVERAGE
        status = "VERIFIED" if passed else "LOW_COVERAGE"
        sha = sha256_file(out_path)

        first_obs = rows[0][0] if rows else ""
        last_obs = rows[-1][0] if rows else ""

        print(f"{item['series_key']:<26} {sid:<18} {item['freq']:<4} {n_cov}/{n_win:<6} {cov_pct:>8.1%}  {str(passed):<6}")

        manifest_rows.append({
            "series_key": item["series_key"],
            "source": item["source"],
            "source_id": sid,
            "url": item["url"],
            "retrieved_at": run_date,
            "sha256": sha,
            "n_rows": len(rows),
            "first_obs": first_obs,
            "last_obs": last_obs,
            "native_freq": item["freq"],
            "units": item["units"],
            "seasonal": item["seasonal"],
            "updated": run_date,
            "window_quarters_covered": n_cov,
            "window_quarters": n_win,
            "coverage_pct": cov_pct,
            "status": status,
            "note": item["note"],
        })

        series_res_rows.append({
            "series_key": item["series_key"],
            "source": item["source"],
            "source_id": sid,
            "status": status,
            "native_freq": item["freq"],
            "note": item["note"],
        })

    # Update data/manifest.csv
    existing_manifest: list[dict] = []
    if MANIFEST.exists():
        with MANIFEST.open(newline="", encoding="utf-8") as fh:
            existing_manifest = list(csv.DictReader(fh))

    deu_keys = {m["series_key"] for m in manifest_rows}
    kept_manifest = [r for r in existing_manifest if r["series_key"] not in deu_keys]
    merged_manifest = kept_manifest + manifest_rows

    manifest_fieldnames = list(merged_manifest[0].keys())
    with MANIFEST.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=manifest_fieldnames)
        writer.writeheader()
        writer.writerows(merged_manifest)
    print(f"\nUpdated {MANIFEST} with {len(manifest_rows)} Germany rows (total: {len(merged_manifest)} rows).")

    # Update data/series_resolution.csv
    existing_res: list[dict] = []
    if SERIES_RES.exists():
        with SERIES_RES.open(newline="", encoding="utf-8") as fh:
            existing_res = list(csv.DictReader(fh))

    res_keys = {r["series_key"] for r in series_res_rows}
    kept_res = [r for r in existing_res if r["series_key"] not in res_keys]
    merged_res = kept_res + series_res_rows

    res_fieldnames = ["series_key", "source", "source_id", "status", "native_freq", "note"]
    with SERIES_RES.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=res_fieldnames)
        writer.writeheader()
        writer.writerows(merged_res)
    print(f"Updated {SERIES_RES} with {len(series_res_rows)} Germany rows (total: {len(merged_res)} rows).")

    # Update data/source_map_DEU.csv
    if SOURCE_MAP.exists():
        source_map_data: list[dict] = []
        with SOURCE_MAP.open(newline="", encoding="utf-8") as fh:
            source_map_data = list(csv.DictReader(fh))

        for row in source_map_data:
            skey = row["scope_key"]
            matching_m = [m for m in manifest_rows if m["series_key"] == skey]
            if matching_m:
                m = matching_m[0]
                row["first"] = m["first_obs"]
                row["last"] = m["last_obs"]
                row["coverage"] = f"{m['window_quarters_covered']}/{m['window_quarters']} ({m['coverage_pct']*100:.1f}%)"
                row["retrieved_date"] = run_date
                row["sha256"] = m["sha256"]
                row["status"] = m["status"]

        sm_fieldnames = list(source_map_data[0].keys())
        with SOURCE_MAP.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=sm_fieldnames)
            writer.writeheader()
            writer.writerows(source_map_data)
        print(f"Updated {SOURCE_MAP} with live hashes and coverage metrics.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
