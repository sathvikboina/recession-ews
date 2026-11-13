#!/usr/bin/env python3
"""Invariants for data/scope.csv (the collection shortlist).

``data/scope.csv`` is a tracked build artefact, so its absence is a failure,
not a reason to skip.
Runs under pytest or standalone:
    python tests/test_scope.py
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parents[1]
SCOPE_CSV = PROJECT / "data" / "scope.csv"
CATALOGUE = PROJECT / "series_catalogue.csv"
KEY = re.compile(r"^(?:[A-Z]{3}|GLOBAL)\.[A-Z0-9_]+\.[DWMQA]\.[A-Z0-9_]+$")

REQUIRED = {
    "series_key", "country_iso3", "indicator_id", "priority_class",
    "beai_eligible", "preferred_source", "id_status", "inclusion_status",
}


def _rows() -> list[dict]:
    assert SCOPE_CSV.exists(), "data/scope.csv is tracked; regenerate it with `make scope`"
    with SCOPE_CSV.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_scope_exists_and_nonempty() -> None:
    rows = _rows()
    assert rows


def test_columns_present() -> None:
    rows = _rows()
    assert rows
    assert REQUIRED <= set(rows[0].keys())


def test_keys_unique_and_well_formed() -> None:
    rows = _rows()
    assert rows
    keys = [r["series_key"] for r in rows]
    assert len(keys) == len(set(keys)), "duplicate series_key in scope"
    bad = [k for k in keys if not KEY.match(k)]
    assert not bad, f"malformed keys: {bad[:3]}"


def test_every_key_is_in_the_catalogue() -> None:
    rows = _rows()
    assert rows
    assert CATALOGUE.exists(), "series_catalogue.csv is tracked and must be present"
    with CATALOGUE.open(newline="", encoding="utf-8") as fh:
        known = {r["series_key"] for r in csv.DictReader(fh)}
    missing = [r["series_key"] for r in rows if r["series_key"] not in known]
    assert not missing, f"keys not in catalogue: {missing[:3]}"


def test_scope_respects_config() -> None:
    rows = _rows()
    assert rows
    with (PROJECT / "config" / "scope.yaml").open(encoding="utf-8") as fh:
        scope = yaml.safe_load(fh)
    with (PROJECT / "config" / "indicators.yaml").open(encoding="utf-8") as fh:
        indicators = {x["id"]: x for x in yaml.safe_load(fh)["indicators"]}

    allowed = set(scope["countries"]["enabled"]) | {"GLOBAL"}
    assert {r["country_iso3"] for r in rows} <= allowed
    assert {r["priority_class"] for r in rows} <= set(scope["indicators"]["priorities"])

    core = set(scope["indicators"]["core"])
    for r in rows:
        if r["beai_eligible"] == "Y":
            assert r["indicator_id"] in core, f"{r['series_key']} breaks the firewall"
        assert indicators[r["indicator_id"]]["priority"] in scope["indicators"]["priorities"]


def test_scope_excludes_decision_rows() -> None:
    rows = _rows()
    assert rows
    assert not [r for r in rows if r["inclusion_status"] in {"EXCLUDED_BY_DECISION", "NOT_APPLICABLE"}]


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  ok    {name}")
            except AssertionError as exc:
                failures += 1
                print(f"  FAIL  {name}: {exc}")
    print(f"\n{'FAILED' if failures else 'passed'}")
    sys.exit(1 if failures else 0)
