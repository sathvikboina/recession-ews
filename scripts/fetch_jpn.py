#!/usr/bin/env python3
"""Fetch Japanese economic series for Lane 1 (Japan BEAI label).

Sources:
1. Cabinet Office (ESRI) SNA quarterly tables:
   - gaku-jk2622.csv: Real GDP (Col 1), Real Private Consumption (Col 2),
                      Real Business Fixed Investment / Private Non-Residential (Col 6).
   - kshotoku-q2622.csv: Real Compensation of Employees / Income (Col 11).
2. FRED (OECD MEI & MIC Labour Force Survey):
   - JPNPROINDMISMEI: Industrial Production Index (Mining & Manufacturing), SA.
   - LFEMTTTTJPM647S: Employment level (Total persons, MIC LFS), SA.

Outputs:
data/raw/esri/<YYYY-MM-DD>/gaku-jk2622.csv        immutable raw SNA tables
data/raw/esri/<YYYY-MM-DD>/kshotoku-q2622.csv
data/raw/esri/<YYYY-MM-DD>/JPN_ACT_GDP_REAL.csv   observation_date,value
data/raw/esri/<YYYY-MM-DD>/JPN_ACT_CONS.csv
data/raw/esri/<YYYY-MM-DD>/JPN_ACT_INV.csv
data/raw/esri/<YYYY-MM-DD>/JPN_ACT_RINC.csv
data/raw/fred/<YYYY-MM-DD>/JPNPROINDMISMEI.csv
data/raw/fred/<YYYY-MM-DD>/LFEMTTTTJPM647S.csv
data/manifest.csv                                updated with Japan active entries
data/series_resolution.csv                       updated with Japan active entries
data/source_map_JPN.csv                          updated with digests & status

Usage:
    python scripts/fetch_jpn.py
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
RAW_ESRI = PROJECT / "data" / "raw" / "esri"
RAW_FRED = PROJECT / "data" / "raw" / "fred"
MANIFEST = PROJECT / "data" / "manifest.csv"
SERIES_RES = PROJECT / "data" / "series_resolution.csv"
SOURCE_MAP = PROJECT / "data" / "source_map_JPN.csv"

WINDOW_START = "1990-01-01"
WINDOW_END = "2025-12-31"
WINDOW_QUARTERS = 144
MIN_COVERAGE = 0.70

ESRI_GAKU_URL = "https://www.esri.cao.go.jp/jp/sna/data/data_list/sokuhou/files/2026/qe262_2/tables/gaku-jk2622.csv"
ESRI_KSHOTOKU_URL = "https://www.esri.cao.go.jp/jp/sna/data/data_list/sokuhou/files/2026/qe262_2/tables/kshotoku-q2622.csv"


def curl_bytes(url: str, timeout: int = 40) -> bytes:
    proc = subprocess.run(
        ["curl.exe", "-sS", "--max-time", str(timeout), url],
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"curl failed for {url}: {proc.stderr.decode('utf-8', errors='ignore')}")
    return proc.stdout


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


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def parse_esri_table(csv_bytes: bytes, col_indices: dict[str, int], start_row: int) -> dict[str, list[tuple[str, float]]]:
    lines = csv_bytes.decode("cp932", errors="ignore").splitlines()
    data: dict[str, list[tuple[str, float]]] = {k: [] for k in col_indices}
    curr_year: str | None = None

    for l in lines[start_row:]:
        parts = next(csv.reader([l]), [])
        if not parts or not parts[0].strip():
            continue
        d = parts[0].strip()
        if "/" in d:
            curr_year, q_part = d.split("/")
            curr_year = curr_year.strip()
        else:
            q_part = d

        if "1- 3" in q_part or "1-3" in q_part:
            md = "01-01"
        elif "4- 6" in q_part or "4-6" in q_part:
            md = "04-01"
        elif "7- 9" in q_part or "7-9" in q_part:
            md = "07-01"
        elif "10-12" in q_part or "10- 12" in q_part:
            md = "10-01"
        else:
            continue

        if not curr_year:
            continue
        obs_date = f"{curr_year}-{md}"

        for name, col_idx in col_indices.items():
            if col_idx < len(parts):
                val_str = parts[col_idx].replace(",", "").strip()
                try:
                    val = float(val_str)
                    data[name].append((obs_date, val))
                except ValueError:
                    pass
    return data


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
    esri_outdir = RAW_ESRI / run_date
    fred_outdir = RAW_FRED / run_date
    esri_outdir.mkdir(parents=True, exist_ok=True)
    fred_outdir.mkdir(parents=True, exist_ok=True)

    print(f"=== Downloading Japan Data ({run_date}) ===")

    # 1. Download raw ESRI tables
    print(f"Fetching ESRI gaku-jk2622.csv from {ESRI_GAKU_URL}...")
    gaku_bytes = curl_bytes(ESRI_GAKU_URL)
    gaku_raw_path = esri_outdir / "gaku-jk2622.csv"
    gaku_raw_path.write_bytes(gaku_bytes)
    print(f"  Saved {gaku_raw_path} ({len(gaku_bytes)} bytes, sha256={sha256_bytes(gaku_bytes)[:12]}...)")

    print(f"Fetching ESRI kshotoku-q2622.csv from {ESRI_KSHOTOKU_URL}...")
    kshotoku_bytes = curl_bytes(ESRI_KSHOTOKU_URL)
    kshotoku_raw_path = esri_outdir / "kshotoku-q2622.csv"
    kshotoku_raw_path.write_bytes(kshotoku_bytes)
    print(f"  Saved {kshotoku_raw_path} ({len(kshotoku_bytes)} bytes, sha256={sha256_bytes(kshotoku_bytes)[:12]}...)")

    # Parse ESRI series
    gaku_series = parse_esri_table(
        gaku_bytes,
        col_indices={"JPN_ACT_GDP_REAL": 1, "JPN_ACT_CONS": 2, "JPN_ACT_INV": 6},
        start_row=7,
    )
    kshotoku_series = parse_esri_table(
        kshotoku_bytes,
        col_indices={"JPN_ACT_RINC": 11},
        start_row=8,
    )

    # 2. Download FRED series
    fred_series: dict[str, list[tuple[str, float]]] = {}
    fred_ids = {
        "JPNPROINDMISMEI": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=JPNPROINDMISMEI",
        "LFEMTTTTJPM647S": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=LFEMTTTTJPM647S",
    }
    for sid, url in fred_ids.items():
        print(f"Fetching FRED {sid} from {url}...")
        csv_text = curl_text(url)
        rows = parse_fred_csv(csv_text)
        fred_series[sid] = rows
        raw_fred_path = fred_outdir / f"{sid}.csv"
        save_series_csv(raw_fred_path, rows)
        print(f"  Saved {raw_fred_path} ({len(rows)} obs, sha256={sha256_file(raw_fred_path)[:12]}...)")

    # Save extracted ESRI individual series CSVs
    all_series_rows: dict[str, list[tuple[str, float]]] = {}
    for name, rows in {**gaku_series, **kshotoku_series}.items():
        p = esri_outdir / f"{name}.csv"
        save_series_csv(p, rows)
        all_series_rows[name] = rows
        print(f"  Saved {p} ({len(rows)} obs, sha256={sha256_file(p)[:12]}...)")
    for sid, rows in fred_series.items():
        all_series_rows[sid] = rows

    # Metadata map for Japan core indicators
    meta_specs = [
        {
            "series_key": "JPN.ACT_GDP_REAL.Q.NA",
            "source": "ESRI",
            "source_id": "JPN_ACT_GDP_REAL",
            "file_path": esri_outdir / "JPN_ACT_GDP_REAL.csv",
            "url": ESRI_GAKU_URL,
            "freq": "Q",
            "units": "Billion Yen, Chained (2020)",
            "seasonal": "SA",
            "note": "real GDP, expenditure approach, chained 2020 volume, SA",
        },
        {
            "series_key": "JPN.ACT_CONS.Q.NA",
            "source": "ESRI",
            "source_id": "JPN_ACT_CONS",
            "file_path": esri_outdir / "JPN_ACT_CONS.csv",
            "url": ESRI_GAKU_URL,
            "freq": "Q",
            "units": "Billion Yen, Chained (2020)",
            "seasonal": "SA",
            "note": "real private consumption expenditure, chained 2020 volume, SA",
        },
        {
            "series_key": "JPN.ACT_INV.Q.STD",
            "source": "ESRI",
            "source_id": "JPN_ACT_INV",
            "file_path": esri_outdir / "JPN_ACT_INV.csv",
            "url": ESRI_GAKU_URL,
            "freq": "Q",
            "units": "Billion Yen, Chained (2020)",
            "seasonal": "SA",
            "note": "real private non-residential business fixed investment, chained 2020 volume, SA",
        },
        {
            "series_key": "JPN.ACT_RINC.Q.STD",
            "source": "ESRI",
            "source_id": "JPN_ACT_RINC",
            "file_path": esri_outdir / "JPN_ACT_RINC.csv",
            "url": ESRI_KSHOTOKU_URL,
            "freq": "Q",
            "units": "Billion Yen, Chained (2020)",
            "seasonal": "SA",
            "note": "real compensation of employees (consumption deflated), chained 2020 volume, SA",
        },
        {
            "series_key": "JPN.ACT_IP.M.STD",
            "source": "FRED",
            "source_id": "JPNPROINDMISMEI",
            "file_path": fred_outdir / "JPNPROINDMISMEI.csv",
            "url": "https://fred.stlouisfed.org/series/JPNPROINDMISMEI",
            "freq": "M",
            "units": "Index 2015=100",
            "seasonal": "SA",
            "note": "industrial production index, mining and manufacturing (METI / OECD MEI), SA",
        },
        {
            "series_key": "JPN.ACT_EMP.M.LFS",
            "source": "FRED",
            "source_id": "LFEMTTTTJPM647S",
            "file_path": fred_outdir / "LFEMTTTTJPM647S.csv",
            "url": "https://fred.stlouisfed.org/series/LFEMTTTTJPM647S",
            "freq": "M",
            "units": "Persons",
            "seasonal": "SA",
            "note": "employment level, total persons (MIC Labour Force Survey), SA",
        },
        {
            "series_key": "JPN.ACT_EMP.Q.NA",
            "source": "FRED",
            "source_id": "LFEMTTTTJPM647S",
            "file_path": fred_outdir / "LFEMTTTTJPM647S.csv",
            "url": "https://fred.stlouisfed.org/series/LFEMTTTTJPM647S",
            "freq": "M",
            "units": "Persons",
            "seasonal": "SA",
            "note": "Q-04 LFS fallback: quarterly mean of household-survey employment",
        },
    ]

    # Compute coverage and build manifest records
    manifest_rows: list[dict] = []
    series_res_rows: list[dict] = []

    print("\n=== Japan Indicator Verification & Coverage ===")
    print(f"{'Indicator':<26} {'Source ID':<18} {'Freq':<4} {'Covered':<10} {'Coverage %':<10} {'Pass >=70%?'}")
    print("-" * 75)

    for item in meta_specs:
        sid = item["source_id"]
        rows = all_series_rows[sid]
        n_cov, n_win, cov_pct = compute_quarterly_coverage(rows, item["freq"])
        passed = cov_pct >= MIN_COVERAGE
        status = "VERIFIED" if passed else "LOW_COVERAGE"
        sha = sha256_file(item["file_path"])

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

    # Keep non-JPN rows, append or replace JPN rows
    jpn_keys = {m["series_key"] for m in manifest_rows}
    kept_manifest = [r for r in existing_manifest if r["series_key"] not in jpn_keys]
    merged_manifest = kept_manifest + manifest_rows

    manifest_fieldnames = list(merged_manifest[0].keys())
    with MANIFEST.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=manifest_fieldnames)
        writer.writeheader()
        writer.writerows(merged_manifest)
    print(f"\nUpdated {MANIFEST} with {len(manifest_rows)} Japan rows (total: {len(merged_manifest)} rows).")

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
    print(f"Updated {SERIES_RES} with {len(series_res_rows)} Japan rows (total: {len(merged_res)} rows).")

    # Update data/source_map_JPN.csv
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
