#!/usr/bin/env python3
"""Invariants for the generated runtime configuration.

Runs under pytest or standalone:
    python tests/test_config.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parents[1]
CFG = PROJECT / "config"
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

import spec  # noqa: E402
from ews.runtime import (  # noqa: E402
    estimation_start,
    quarter_count,
    study_window,
    window_bounds,
)

CORE = {
    "ACT_GDP_REAL", "ACT_IP", "ACT_EMP", "ACT_HOURS",
    "ACT_RINC", "ACT_CONS", "ACT_RETAIL", "ACT_INV",
}
LAG_CLASSES = {"NA", "MONTHLY", "MARKET", "SURVEY", "NA_ASSUMED", "ANNUAL", "DERIVED", "NONE"}
FORMS = {"growth", "rate", "ratio", "spread", "survey", "price", "support", "label"}


def _yaml(name: str) -> dict:
    with (CFG / name).open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def test_beai_set_is_exact() -> None:
    indicators = _yaml("indicators.yaml")["indicators"]
    beai = {x["id"] for x in indicators if x["beai_eligible"] == "Y"}
    assert beai == CORE, f"BEAI set drift: {beai ^ CORE}"
    assert len(beai) == 8


def test_unemployment_is_predictor_only() -> None:
    indicators = _yaml("indicators.yaml")["indicators"]
    unemp = next(x for x in indicators if x["id"] == "LAB_UNEMP")
    assert unemp["beai_eligible"] == "N"
    assert _yaml("scope.yaml")["firewall"]["unemployment_in_beai"] is False


def test_indicator_identifiers_unique() -> None:
    indicators = _yaml("indicators.yaml")["indicators"]
    ids = [x["id"] for x in indicators]
    assert len(ids) == len(set(ids))


def test_indicator_semantics_in_vocabulary() -> None:
    for x in _yaml("indicators.yaml")["indicators"]:
        assert x["form"] in FORMS, f"{x['id']} bad form {x['form']}"
        assert x["lag_class"] in LAG_CLASSES, f"{x['id']} bad lag class {x['lag_class']}"
        assert x["priority"] in {"P0", "P1", "P2", "P3"}
        for v in x["variants"]:
            assert v["freq"] in {"D", "W", "M", "Q", "A"}


def test_countries_and_scope() -> None:
    countries = _yaml("countries.yaml")["countries"]
    scope = _yaml("scope.yaml")
    iso = {c["iso3"] for c in countries}
    assert len(countries) == 41 and "GLOBAL" in iso
    assert set(scope["countries"]["enabled"]) <= iso
    assert scope["primary_horizon"] in scope["horizons"]
    assert scope["window"]["start"] < scope["window"]["end"]


def test_scope_priorities_are_valid() -> None:
    scope = _yaml("scope.yaml")
    assert set(scope["indicators"]["priorities"]) <= {"P0", "P1", "P2", "P3"}
    assert set(scope["indicators"]["core"]) == CORE


def test_window_has_one_source_of_truth() -> None:
    scope = _yaml("scope.yaml")
    start, end = study_window(scope)
    assert (start, end) == (spec.WIN_START, spec.WIN_END)
    assert estimation_start(scope) == "1960Q1"
    assert quarter_count(start, end) == 147
    assert window_bounds(start, end) == ("1990-01-01", "2026-09-30")
    assert scope["coverage"]["min_quarters_pct"] == 70
    assert scope["coverage"]["min_core_indicators"] == 6


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
