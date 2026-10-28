#!/usr/bin/env python3
"""Export runtime configuration from the Phase 2 specification.

spec.py stays the documentation source of truth (it regenerates the workbook).
This script freezes the machine-readable subset that the modelling pipeline reads:
  config/indicators.yaml
  config/countries.yaml
  config/sources.yaml

Run:
    python scripts/export_spec.py

The output is deterministic. Re-run only when spec.py changes on purpose, and
commit the diff so a change of indicator semantics is visible in review.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

import spec  # noqa: E402  (documentation source; imported only here and in build.py)

CONFIG = PROJECT / "config"
HEADER = (
    "# GENERATED FILE - do not edit by hand.\n"
    "# Source: spec.py via scripts/export_spec.py.\n"
    "# Change spec.py, re-run the exporter, then commit the diff.\n"
)


def variant_rows(ind: dict) -> list[dict]:
    rows = []
    for v in ind["variants"]:
        applies = v["app"] if v["app"] is not None else ind["app"]
        rows.append(
            {
                "freq": v["freq"],
                "tag": v["tag"],
                "description": v["desc"] or "Default variant",
                "applies_to": applies,
                "us_fred_id": v["us"],
                "lag_class": v["lagc"] or ind["lagc"],
                "kind": v["kind"] or ind["kind"],
            }
        )
    return rows


def export_indicators() -> list[dict]:
    out = []
    for x in spec.IND:
        out.append(
            {
                "id": x["id"],
                "name": x["name"],
                "category": x["cat"],
                "subcategory": x["sub"],
                "intended_role": x["role"],
                "beai_eligible": x["beai"],
                "beai_exclusion_reason": x["beai_why"] or None,
                "form": x["form"],
                "lag_class": x["lagc"],
                "kind": x["kind"],
                "sign_1q_2q": x["s1"],
                "sign_4q": x["s4"],
                "priority": x["prio"],
                "redundancy_group": x["red"] or None,
                "ablation_tier1": x["abl1"] or None,
                "ablation_tier2": x["abl2"] or None,
                "proposal_ref": x["sec"],
                "variants": variant_rows(x),
                "notes": x["notes"] or None,
            }
        )
    return out


def export_countries() -> list[dict]:
    out = []
    for iso, name, group in spec.COUNTRIES:
        chain = spec.CHAIN.get(iso, spec.DEFAULT_CHAIN)
        out.append(
            {
                "iso3": iso,
                "name": name,
                "group": group,
                "chain_keys": chain,
                "source_chain": [spec.SRC[c] for c in chain],
            }
        )
    out.append(
        {
            "iso3": "GLOBAL",
            "name": "Global / panel-level",
            "group": "GLOBAL",
            "chain_keys": ["FRED", "IMF"],
            "source_chain": ["FRED (USA chain assumed; Q-18)", "IMF/World Bank supplement"],
        }
    )
    return out


def export_sources() -> list[dict]:
    out = []
    for row in spec.SOURCE_REGISTRY:
        sid, name, role, url, access, url_status, verified, caveats = row
        out.append(
            {
                "id": sid,
                "name": name,
                "role": role,
                "portal_url": url,
                "access_method": access,
                "url_status": url_status,
                "verified_2026_10_24": verified,
                "caveats": caveats,
            }
        )
    return out


def dump(path: Path, payload: dict) -> None:
    text = HEADER
    text += yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, width=120)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    CONFIG.mkdir(parents=True, exist_ok=True)
    indicators = export_indicators()
    countries = export_countries()
    sources = export_sources()

    dump(
        CONFIG / "indicators.yaml",
        {
            "version": 1,
            "n_indicators": len(indicators),
            "indicators": indicators,
        },
    )
    dump(
        CONFIG / "countries.yaml",
        {
            "version": 1,
            "n_countries": len(countries) - 1,
            "countries": countries,
        },
    )
    dump(
        CONFIG / "sources.yaml",
        {
            "version": 1,
            "n_sources": len(sources),
            "sources": sources,
        },
    )

    beai = [x["id"] for x in indicators if x["beai_eligible"] == "Y"]
    by_prio = {}
    for x in indicators:
        by_prio[x["priority"]] = by_prio.get(x["priority"], 0) + 1

    print(f"indicators : {len(indicators)}  by priority {by_prio}")
    print(f"beai = Y   : {len(beai)}  {beai}")
    print(f"countries  : {len(countries) - 1} + GLOBAL")
    print(f"sources    : {len(sources)}")
    print(f"written    : {CONFIG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
