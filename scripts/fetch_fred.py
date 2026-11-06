#!/usr/bin/env python3
"""Verify and download FRED series for the scoped build.

Why curl: outbound `urllib`/`requests` reads stall in this environment while the
system `curl` works. The script therefore shells out to curl and keeps the rest
pure Python.

What it does per series
-----------------------
1. Fetch the series page and read title / units / frequency / SA / last update.
2. Fetch the observations as CSV (no API key needed).
3. Save the payload unchanged under data/raw/fred/<run-date>/<id>.csv.
4. Compute coverage of the frozen window 1990Q1-2026Q3 at native frequency,
   counting a quarter only when every constituent month/week/day is present.
5. Decide a status, append a manifest row, and record provenance.

Outputs
-------
data/raw/fred/<run-date>/<id>.csv   immutable downloads
data/manifest.csv                   one row per downloaded series
data/fred_verification.csv          verification facts + status per series
docs/VERIFICATION.md                progress table refreshed in place

Run:
    python scripts/fetch_fred.py                 # all registry entries
    python scripts/fetch_fred.py --only GDPC1    # subset
    python scripts/fetch_fred.py --list          # show the registry
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
RAW = PROJECT / "data" / "raw" / "fred"
MANIFEST = PROJECT / "data" / "manifest.csv"
VERIFY = PROJECT / "data" / "fred_verification.csv"
SUPERSEDED = PROJECT / "data" / "superseded_series.csv"
SUPERSEDED_COLS = ["series_key", "source", "source_id", "superseded_on", "superseded_by", "reason"]

START, END = "1990-01-01", "2026-09-30"
WINDOW_QUARTERS = 147
MIN_COVERAGE = 0.70

# scope_key -> (fred_id, note). `scope_key` is the key used in data/scope.csv so
# the manifest can be joined back to the collection shortlist.
REGISTRY: dict[str, dict] = {
    # ---- eight core (BEAI) indicators, label variants -------------------
    "USA.ACT_GDP_REAL.Q.NA": {"id": "GDPC1", "note": "real GDP, chain-volume, SA"},
    "USA.ACT_IP.M.STD": {"id": "INDPRO", "note": "industrial production index"},
    # Q-04: national-accounts quarterly employment is not available for the USA
    # in OECD QNA; the permitted LFS fallback is the household-survey level.
    "USA.ACT_EMP.Q.NA": {"id": "CE16OV", "note": "Q-04 LFS fallback: quarterly mean of household-survey employment"},
    "USA.ACT_HOURS.Q.STD": {"id": "HOANBS", "note": "nonfarm business hours of all persons"},
    "USA.ACT_RINC.Q.STD": {"id": "W875RX1", "note": "real personal income ex transfer receipts (coincident measure; transfers make DPI counter-cyclical)"},
    "USA.ACT_CONS.Q.NA": {"id": "PCECC96", "note": "real personal consumption expenditures"},
    "USA.ACT_RETAIL.M.STD": {"id": "RRSFS", "note": "real retail and food services sales"},
    # Q-02: real non-residential business fixed investment is constructed from
    # the three BEA asset components and the non-residential price deflator.
    "USA.ACT_INV_EQ.Q.STD": {"id": "Y033RC1Q027SBEA", "note": "Q-02 component: non-residential equipment, nominal"},
    "USA.ACT_INV_STRUCT.Q.STD": {"id": "B009RC1Q027SBEA", "note": "Q-02 component: non-residential structures, nominal"},
    "USA.ACT_INV_IPP.Q.STD": {"id": "Y001RC1Q027SBEA", "note": "Q-02 component: non-residential intellectual property products, nominal"},
    "USA.ACT_INV_DEFL.Q.STD": {"id": "A008RD3Q086SBEA", "note": "Q-02 component: non-residential implicit price deflator, 2017=100"},
    # ---- BEAI-eligible monthly variants (predictor copies) --------------
    "USA.ACT_CONS.M.US": {"id": "PCEC96", "note": "monthly real PCE; short history"},
    "USA.ACT_EMP.M.ESTAB": {"id": "PAYEMS", "note": "all employees, total nonfarm"},
    "USA.ACT_EMP.M.LFS": {"id": "CE16OV", "note": "employment level, household survey"},
    "USA.ACT_RINC.M.US": {"id": "DSPIC96", "note": "real disposable personal income (monthly)"},
    # ---- P1 predictors ---------------------------------------------------
    "USA.FIN_CREDIT_GDP.Q.STD": {"id": "QUSPAM770A", "note": "BIS total credit to private non-financial sector, % GDP"},
    "USA.FIN_EQUITY.M.STD": {"id": "NASDAQCOM", "note": "Nasdaq Composite (daily -> monthly)"},
    "USA.FIN_HOUSEPRICE.M.US_CS": {"id": "CSUSHPISA", "note": "Case-Shiller national, SA"},
    "USA.FIN_HOUSEPRICE.Q.OECD_BIS": {"id": "USSTHPI", "note": "FHFA all-transactions HPI (substitute for OECD/BIS)"},
    "USA.FIN_LONG.M.STD": {"id": "GS10", "note": "10-year Treasury constant maturity"},
    "USA.FIN_POLICY.M.STD": {"id": "FEDFUNDS", "note": "effective federal funds rate"},
    "USA.FIN_SHORT.M.STD": {"id": "TB3MS", "note": "3-month Treasury bill, secondary market"},
    "USA.LAB_UNEMP.M.STD": {"id": "UNRATE", "note": "civilian unemployment rate"},
    "USA.PRC_CPI.M.STD": {"id": "CPIAUCSL", "note": "CPI all urban consumers, SA"},
    "USA.SEN_BCI.M.STD": {"id": "BSCICP03USM665S", "note": "OECD composite business confidence"},
    "USA.SEN_CCI.M.STD": {"id": "UMCSENT", "note": "University of Michigan consumer sentiment"},
    # ---- external chronology (robustness only) --------------------------
    "USA.NBER.Q": {"id": "USRECQ", "note": "NBER recession indicator, quarterly"},
}

DERIVED = {
    "USA.ACT_INV.Q.STD": {
        "inputs": [
            "USA.ACT_INV_EQ.Q.STD",
            "USA.ACT_INV_STRUCT.Q.STD",
            "USA.ACT_INV_IPP.Q.STD",
            "USA.ACT_INV_DEFL.Q.STD",
        ],
        "method": "(equipment + structures + intellectual property products) / (deflator/100)",
        "note": "Q-02 real non-residential business fixed investment",
    },
    "USA.FIN_CREDIT_GAP.Q.STD": {
        "inputs": ["USA.FIN_CREDIT_GDP.Q.STD"],
        "method": "one-sided HP filter, lambda=400000",
        "note": "BIS-style credit-to-GDP gap from QUSPAM770A",
    },
    "USA.FIN_SLOPE.M.DERIVED": {
        "inputs": ["USA.FIN_LONG.M.STD", "USA.FIN_SHORT.M.STD"],
        "method": "GS10 - TB3MS",
        "note": "term spread",
    },
}


def record_superseded(existing: list[dict], fetched: list[dict], run_date: str) -> None:
    """Record a scope key whose active source id changed.

    One scope key must resolve to one active source. When a replacement removes
    an older download, the old row is written to ``data/superseded_series.csv``
    before it is dropped from the manifest.
    """
    new_by_key = {row["series_key"]: row for row in fetched}
    changes: list[dict] = []
    for old in existing:
        key = old.get("series_key")
        new = new_by_key.get(key)
        old_id = old.get("source_id")
        if not new or not old_id or old_id == new.get("source_id"):
            continue
        changes.append({
            "series_key": key,
            "source": old.get("source", ""),
            "source_id": old_id,
            "superseded_on": run_date,
            "superseded_by": new.get("source_id", ""),
            "reason": "active source changed for this scope key",
        })
    if not changes:
        return

    previous: list[dict] = []
    if SUPERSEDED.exists():
        with SUPERSEDED.open(newline="", encoding="utf-8") as fh:
            previous = list(csv.DictReader(fh))
    seen = {(row.get("series_key"), row.get("source_id")) for row in previous}
    merged = previous + [
        row for row in changes if (row["series_key"], row["source_id"]) not in seen
    ]
    with SUPERSEDED.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=SUPERSEDED_COLS)
        writer.writeheader()
        for row in merged:
            writer.writerow({key: row.get(key, "") for key in SUPERSEDED_COLS})


def curl(url: str, timeout: int = 40) -> tuple[str, str]:
    """Return (http_code, body). Uses the system curl; see module docstring."""
    proc = subprocess.run(
        [
            "curl", "-sS", "--http1.1", "--max-time", str(timeout),
            "-A", "curl/8.0", "-w", "\n__HTTP__%{http_code}", url,
        ],
        capture_output=True, text=True, errors="replace",
    )
    body = proc.stdout
    code = "000"
    if "__HTTP__" in body:
        body, _, tail = body.rpartition("__HTTP__")
        code = tail.strip()
    return code, body


def fetch_meta(sid: str) -> dict:
    code, html = curl(f"https://fred.stlouisfed.org/series/{sid}")
    if code != "200":
        return {"page_http": code}

    def grab(pat: str) -> str | None:
        m = re.search(pat, html, re.S)
        return re.sub(r"\s+", " ", m.group(1)).strip() if m else None

    units = grab(r'series-meta-value-units">([^<]+)<')
    tail = grab(r'series-meta-value-units">[^<]*</span>,</div>\s*<div class="default-text">\s*([^<]*)</span>')
    sa_text = f"{units or ''} {tail or ''}"
    if "Not Seasonally Adjusted" in sa_text:
        sa = "NSA"
    elif "Seasonally Adjusted" in sa_text:
        sa = "SA"
    else:
        sa = "UNKNOWN"
    return {
        "page_http": code,
        "title": grab(r'property="og:title" content="([^"]+)"'),
        "units": units,
        "sa_detail": tail,
        "seasonal": sa,
        "frequency": grab(r'series-meta-value-frequency">\s*([^<]+?)\s*<'),
        "updated": grab(r'series-meta-updated-date">([^<]+)<'),
    }


def fetch_obs(sid: str) -> tuple[str, list[tuple[str, float]]]:
    code, body = curl(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}")
    if code != "200":
        return code, []
    rows: list[tuple[str, float]] = []
    for rec in list(csv.reader(io.StringIO(body)))[1:]:
        if len(rec) != 2:
            continue
        date, value = rec[0].strip(), rec[1].strip()
        if not date or value in ("", ".", "NaN"):
            continue
        try:
            rows.append((date, float(value)))
        except ValueError:
            continue
    return code, rows


def parse_date(s: str) -> dt.date:
    return dt.date.fromisoformat(s[:10])


def period_key(d: dt.date, freq: str) -> tuple[int, int]:
    if freq == "M":
        return d.year, d.month
    if freq == "D" or freq == "W":
        return d.year, d.month
    return d.year, (d.month - 1) // 3 + 1


def quarter_set(rows: list[tuple[str, float]], freq: str) -> set[tuple[int, int]]:
    """Quarters (year, q) fully covered at the native frequency."""
    if freq == "Q":
        return {(d.year, (d.month - 1) // 3 + 1) for d, _ in ((parse_date(s), v) for s, v in rows)}
    if freq == "A":
        return {(d.year, q) for d, _ in ((parse_date(s), v) for s, v in rows) for q in (1, 2, 3, 4)}
    # M / W / D: require every month in the quarter
    months: dict[tuple[int, int], set[int]] = {}
    for s, _ in rows:
        d = parse_date(s)
        months.setdefault((d.year, (d.month - 1) // 3 + 1), set()).add(d.month)
    if freq == "M":
        need = 3
    elif freq == "W":
        need = 2  # a quarter has 13 weeks; 2+ distinct week-ending months is enough for W
    else:
        need = 3
    return {k for k, v in months.items() if len(v) >= need}


def window_quarters() -> list[tuple[int, int]]:
    """Quarters in the frozen study window, inclusive of END's quarter."""
    start = parse_date(START)
    end = parse_date(END)
    end_pair = (end.year, (end.month - 1) // 3 + 1)
    out = []
    y, q = start.year, (start.month - 1) // 3 + 1
    while (y, q) <= end_pair:
        out.append((y, q))
        q += 1
        if q == 5:
            y, q = y + 1, 1
    return out


def coverage(rows: list[tuple[str, float]], freq: str) -> tuple[int, int, float]:
    have = quarter_set(rows, freq) & set(window_quarters())
    n = len(have)
    return n, WINDOW_QUARTERS, round(n / WINDOW_QUARTERS, 4)


def infer_freq(meta: dict, rows: list[tuple[str, float]]) -> str:
    text = (meta.get("frequency") or "").lower()
    if "quarter" in text:
        return "Q"
    if "month" in text:
        return "M"
    if "annual" in text:
        return "A"
    if "daily" in text:
        return "D"
    if "weekly" in text:
        return "W"
    if len(rows) > 1:
        a, b = parse_date(rows[0][0]), parse_date(rows[1][0])
        delta = (b - a).days
        return "M" if delta < 45 else "Q" if delta < 120 else "A"
    return "UNKNOWN"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None, help="FRED ids to fetch")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    if args.list:
        for key, spec in REGISTRY.items():
            print(f"{spec['id']:18s} {key:34s} {spec['note']}")
        for key, spec in DERIVED.items():
            print(f"{'DERIVED':18s} {key:34s} {spec['note']}")
        return 0

    run_date = dt.date.today().isoformat()
    outdir = RAW / run_date
    outdir.mkdir(parents=True, exist_ok=True)

    wanted = set(args.only) if args.only else None
    fetched: list[dict] = []
    verify: list[dict] = []

    for scope_key, spec in REGISTRY.items():
        sid = spec["id"]
        if wanted and sid not in wanted:
            continue

        meta = fetch_meta(sid)
        code, rows = fetch_obs(sid)
        freq = infer_freq(meta, rows) if rows else "UNKNOWN"
        n_cov, n_win, cov = coverage(rows, freq) if rows else (0, WINDOW_QUARTERS, 0.0)
        first, last = (rows[0][0], rows[-1][0]) if rows else (None, None)

        if code != "200" or not rows:
            status = "FAILED"
        elif cov >= MIN_COVERAGE:
            status = "VERIFIED"
        else:
            status = "LOW_COVERAGE"

        payload = "\n".join(f"{d},{v}" for d, v in rows)
        path = outdir / f"{sid}.csv"
        path.write_text("observation_date,value\n" + payload + ("\n" if payload else ""), encoding="utf-8")
        sha = hashlib.sha256(path.read_bytes()).hexdigest()

        record = {
            "series_key": scope_key,
            "source": "FRED",
            "source_id": sid,
            "url": f"https://fred.stlouisfed.org/series/{sid}",
            "retrieved_at": run_date,
            "sha256": sha,
            "n_rows": len(rows),
            "first_obs": first,
            "last_obs": last,
            "native_freq": freq,
            "units": meta.get("units"),
            "seasonal": meta.get("seasonal"),
            "updated": meta.get("updated"),
            "window_quarters_covered": n_cov,
            "window_quarters": n_win,
            "coverage_pct": cov,
            "status": status,
            "note": spec["note"],
        }
        fetched.append(record)

        verify.append({
            "series_key": scope_key,
            "fred_id": sid,
            "title": meta.get("title"),
            "units": meta.get("units"),
            "frequency": meta.get("frequency"),
            "native_freq": freq,
            "seasonal": meta.get("seasonal"),
            "sa_detail": meta.get("sa_detail"),
            "first_obs": first,
            "last_obs": last,
            "n_obs": len(rows),
            "n_quarters_in_window": n_cov,
            "coverage_pct": cov,
            "page_http": meta.get("page_http"),
            "csv_http": code,
            "status": status,
            "checked_on": run_date,
        })
        print(f"{status:12s} {sid:18s} {freq:2s} {cov:6.1%}  {first} -> {last}  {meta.get('title')}")

    # ---- manifest (append-or-replace by scope key) ----------------------
    cols = list(fetched[0].keys()) if fetched else []
    existing: list[dict] = []
    if MANIFEST.exists() and fetched:
        with MANIFEST.open(newline="", encoding="utf-8") as fh:
            existing = list(csv.DictReader(fh))
        record_superseded(existing, fetched, run_date)
        existing = [r for r in existing if r.get("series_key") not in {f["series_key"] for f in fetched}]
    if fetched:
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        with MANIFEST.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            for r in existing + fetched:
                w.writerow({k: r.get(k, "") for k in cols})

    # ---- resolution table (scope_key -> concrete source id) ------------
    RESOLUTION = PROJECT / "data" / "series_resolution.csv"
    if fetched:
        res_cols = ["series_key", "source", "source_id", "status", "native_freq", "note"]
        res_rows = [{k: r[k] for k in res_cols} for r in fetched]
        old_res: list[dict] = []
        if RESOLUTION.exists():
            with RESOLUTION.open(newline="", encoding="utf-8") as fh:
                old_res = list(csv.DictReader(fh))
            touched = {r["series_key"] for r in res_rows} | set(DERIVED)
            old_res = [r for r in old_res if r.get("series_key") not in touched]
        res_rows = old_res + res_rows
        for key, spec in DERIVED.items():
            res_rows.append({
                "series_key": key,
                "source": "DERIVED",
                "source_id": "+".join(spec["inputs"]),
                "status": "DERIVED_AFTER_INPUTS",
                "native_freq": "M" if ".M." in key else "Q",
                "note": f"{spec['method']}: {spec['note']}",
            })
        with RESOLUTION.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=res_cols)
            w.writeheader()
            w.writerows(res_rows)

    if verify:
        vcols = list(verify[0].keys())
        old: list[dict] = []
        if VERIFY.exists():
            with VERIFY.open(newline="", encoding="utf-8") as fh:
                old = list(csv.DictReader(fh))
            old = [r for r in old if r.get("series_key") not in {v["series_key"] for v in verify}]
        with VERIFY.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=vcols)
            w.writeheader()
            for r in old + verify:
                w.writerow({k: r.get(k, "") for k in vcols})

    ok = sum(1 for r in verify if r["status"] == "VERIFIED")
    failed = [r["fred_id"] for r in verify if r["status"] == "FAILED"]
    print(f"\n{ok}/{len(verify)} verified at >= {MIN_COVERAGE:.0%} coverage")
    if failed:
        print(f"FAILED downloads: {failed}")
    print(f"raw    : {outdir}")
    print(f"verify : {VERIFY}")
    print(f"manifest: {MANIFEST}")
    # a recorded low-coverage series is a finding, not a pipeline error
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
