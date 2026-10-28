#!/usr/bin/env python3
"""Reduce the 1,883-row Phase 2 catalogue to the rows this build will actually collect.

Inputs : series_catalogue.csv, config/scope.yaml, config/indicators.yaml
Outputs: data/scope.csv            one row per series to collect / derive
         data/scope_coverage.csv   country x indicator availability view
         data/scope_summary.txt    human-readable counts (also printed)

Run:
    python scripts/scope_catalog.py
"""
from __future__ import annotations

import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parents[1]
SERIES_KEY = re.compile(r"^(?:[A-Z]{3}|GLOBAL)\.[A-Z0-9_]+\.[DWMQA]\.[A-Z0-9_]+$")

PRIO_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
EXCLUDED_STATUS = {"EXCLUDED_BY_DECISION", "NOT_APPLICABLE"}

SCOPE_COLS = [
    "collection_rank",
    "series_key",
    "country_iso3",
    "country_group",
    "indicator_id",
    "indicator_name",
    "category",
    "intended_role",
    "beai_eligible",
    "priority_class",
    "collection_batch",
    "preferred_source",
    "preferred_source_series_id",
    "id_status",
    "inclusion_status",
    "collection_method",
    "availability_risk",
    "open_questions",
]


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def main() -> int:
    scope = load_yaml(PROJECT / "config" / "scope.yaml")
    indicators = load_yaml(PROJECT / "config" / "indicators.yaml")["indicators"]
    ind_prio = {x["id"]: x["priority"] for x in indicators}
    ind_name = {x["id"]: x["name"] for x in indicators}

    enabled = set(scope["countries"]["enabled"])
    include_global = bool(scope["countries"].get("include_global", False))
    allowed_countries = enabled | ({"GLOBAL"} if include_global else set())
    priorities = set(scope["indicators"]["priorities"])
    only = set(scope["indicators"].get("only") or [])
    exclude = set(scope["indicators"].get("exclude") or [])
    COUNTRY_ORDER = {iso: i for i, iso in enumerate(scope["countries"]["enabled"])}
    if include_global:
        COUNTRY_ORDER["GLOBAL"] = len(COUNTRY_ORDER)

    catalogue_path = PROJECT / scope["paths"]["catalogue"]
    with catalogue_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    selected, dropped = [], Counter()
    for r in rows:
        iso = r["country_iso3"]
        iid = r["indicator_id"]
        prio = r["priority_class"]
        status = r["inclusion_status"]
        if iso not in allowed_countries:
            dropped["country_not_enabled"] += 1
            continue
        if prio not in priorities or ind_prio.get(iid) not in priorities:
            dropped["priority"] += 1
            continue
        if status in EXCLUDED_STATUS:
            dropped["excluded_status"] += 1
            continue
        if only and iid not in only:
            dropped["not_in_only"] += 1
            continue
        if iid in exclude:
            dropped["excluded_indicator"] += 1
            continue
        if not SERIES_KEY.match(r["series_key"]):
            dropped["bad_series_key"] += 1
            continue
        selected.append(r)

    selected.sort(
        key=lambda r: (
            COUNTRY_ORDER.get(r["country_iso3"], 99),
            PRIO_ORDER.get(r["priority_class"], 9),
            r["indicator_id"],
            r["series_key"],
        )
    )

    out_path = PROJECT / scope["paths"]["scope_out"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=SCOPE_COLS, extrasaction="ignore")
        w.writeheader()
        for rank, r in enumerate(selected, 1):
            r = dict(r)
            r["collection_rank"] = rank
            w.writerow(r)

    # coverage view: country x indicator
    cov: dict[tuple[str, str], dict] = {}
    for r in selected:
        key = (r["country_iso3"], r["indicator_id"])
        c = cov.setdefault(
            key,
            {
                "country_iso3": key[0],
                "country_group": r["country_group"],
                "indicator_id": key[1],
                "indicator_name": ind_name.get(key[1], r["indicator_name"]),
                "priority_class": r["priority_class"],
                "beai_eligible": r["beai_eligible"],
                "n_variants": 0,
                "id_statuses": set(),
                "collection_batches": set(),
            },
        )
        c["n_variants"] += 1
        c["id_statuses"].add(r["id_status"])
        c["collection_batches"].add(r["collection_batch"])

    cov_rows = []
    for c in cov.values():
        c["id_statuses"] = "; ".join(sorted(c["id_statuses"]))
        c["collection_batches"] = "; ".join(sorted(c["collection_batches"]))
        cov_rows.append(c)
    cov_rows.sort(
        key=lambda c: (
            COUNTRY_ORDER.get(c["country_iso3"], 99),
            PRIO_ORDER.get(c["priority_class"], 9),
            c["indicator_id"],
        )
    )
    cov_path = PROJECT / scope["paths"]["coverage_out"]
    with cov_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(cov_rows[0].keys()))
        w.writeheader()
        w.writerows(cov_rows)

    # summary
    by_country = Counter(r["country_iso3"] for r in selected)
    by_prio = Counter(r["priority_class"] for r in selected)
    by_batch = Counter(r["collection_batch"] for r in selected)
    by_id = Counter(r["id_status"] for r in selected)
    beai_rows = sum(1 for r in selected if r["beai_eligible"] == "Y")
    core = set(scope["indicators"]["core"])
    seen_core = {
        (r["country_iso3"], r["indicator_id"])
        for r in selected
        if r["indicator_id"] in core
    }
    core_by_country = defaultdict(set)
    for iso, iid in seen_core:
        core_by_country[iso].add(iid)

    lines = [
        f"catalogue rows          : {len(rows)}",
        f"selected rows           : {len(selected)}",
        f"dropped                 : {dict(dropped)}",
        f"countries               : {len(by_country)}  {dict(by_country)}",
        f"priority                : {dict(by_prio)}",
        f"batch                   : {dict(by_batch)}",
        f"id_status               : {dict(by_id)}",
        f"beai_eligible = Y rows  : {beai_rows}",
        f"core indicators present : {dict((k, len(v)) for k, v in sorted(core_by_country.items()))}",
        "",
        "gate reminder: a country needs >=6 of the 8 core indicators at >=70% coverage",
        "of the target window before its BEAI label can be built (spec §19).",
    ]
    summary = "\n".join(lines)
    (PROJECT / "data" / "scope_summary.txt").write_text(summary + "\n", encoding="utf-8")
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
