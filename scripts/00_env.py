#!/usr/bin/env python3
"""Environment and configuration gate for the build.

Run before anything else and in CI:
    python scripts/00_env.py

Exits non-zero on any hard failure. Optional packages are reported as warnings
because they are only needed from the label/feature stages onward.
"""
from __future__ import annotations

import csv
import importlib
import re
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

FAIL: list[str] = []
WARN: list[str] = []
OK: list[str] = []


def check(cond: bool, msg: str, *, warn: bool = False) -> None:
    if cond:
        OK.append(msg)
    elif warn:
        WARN.append(msg)
    else:
        FAIL.append(msg)


def load_yaml(name: str):
    import yaml

    with (PROJECT / "config" / name).open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def main() -> int:
    # --- interpreter
    check(sys.version_info >= (3, 11), f"python >= 3.11 (found {sys.version.split()[0]})")
    for mod in ("yaml",):
        try:
            importlib.import_module(mod)
            check(True, f"required package: {mod}")
        except Exception:
            check(False, f"missing required package: {mod}")

    for mod in ("pandas", "numpy", "scipy", "statsmodels", "sklearn", "xgboost",
                "shap", "matplotlib", "pyarrow", "openpyxl", "pytest"):
        try:
            importlib.import_module(mod)
        except Exception:
            WARN.append(f"not installed yet (needed from later steps): {mod}")

    # --- files
    required = {
        "spec.py": PROJECT / "spec.py",
        "build.py": PROJECT / "build.py",
        "catalogue": PROJECT / "series_catalogue.csv",
        "scope.yaml": PROJECT / "config" / "scope.yaml",
        "indicators.yaml": PROJECT / "config" / "indicators.yaml",
        "countries.yaml": PROJECT / "config" / "countries.yaml",
        "sources.yaml": PROJECT / "config" / "sources.yaml",
    }
    for name, path in required.items():
        check(path.exists(), f"file present: {name}")

    if FAIL:
        report()
        return 1

    scope = load_yaml("scope.yaml")
    indicators = load_yaml("indicators.yaml")["indicators"]
    countries = load_yaml("countries.yaml")["countries"]
    sources = load_yaml("sources.yaml")["sources"]

    # --- indicator invariants
    ids = [x["id"] for x in indicators]
    check(len(ids) == len(set(ids)), "indicator ids are unique")
    beai = {x["id"] for x in indicators if x["beai_eligible"] == "Y"}
    core = set(scope["indicators"]["core"])
    check(beai == core, "beai_eligible=Y is exactly the 8 core indicators")
    check(len(beai) == 8, f"exactly 8 BEAI indicators (found {len(beai)})")
    unemp = next((x for x in indicators if x["id"] == "LAB_UNEMP"), None)
    check(unemp is not None and unemp["beai_eligible"] == "N",
          "LAB_UNEMP is predictor-only (Q-01)")
    check(scope["firewall"]["unemployment_in_beai"] is False,
          "scope.yaml agrees that unemployment is not a BEAI input")
    valid_freq = {"D", "W", "M", "Q", "A"}
    bad_freq = [f"{x['id']}:{v['freq']}" for x in indicators for v in x["variants"] if v["freq"] not in valid_freq]
    check(not bad_freq, f"all variant frequencies valid {bad_freq or ''}")
    valid_prio = {"P0", "P1", "P2", "P3"}
    check({x["priority"] for x in indicators} <= valid_prio, "indicator priorities valid")

    # --- country invariants
    iso = {c["iso3"] for c in countries}
    enabled = set(scope["countries"]["enabled"])
    check(enabled <= iso, "enabled countries exist in countries.yaml")
    check({"USA", "JPN"} <= enabled, "USA and JPN enabled for the first build")
    check(len(iso) == 41, f"40 countries + GLOBAL exported (found {len(iso)})")

    # --- scope rows
    scope_csv = PROJECT / scope["paths"]["scope_out"]
    if not scope_csv.exists():
        WARN.append("data/scope.csv missing - run: python scripts/scope_catalog.py")
    else:
        with scope_csv.open(newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        check(len(rows) > 0, f"scope rows present ({len(rows)})")
        keys = [r["series_key"] for r in rows]
        check(len(keys) == len(set(keys)), "scope series_key unique")
        pattern = re.compile(r"^(?:[A-Z]{3}|GLOBAL)\.[A-Z0-9_]+\.[DWMQA]\.[A-Z0-9_]+$")
        check(all(pattern.match(k) for k in keys), "scope series_key format valid")
        check({r["country_iso3"] for r in rows} <= (enabled | {"GLOBAL"}),
              "scope only contains enabled countries (+GLOBAL)")
        check({r["priority_class"] for r in rows} <= set(scope["indicators"]["priorities"]),
              "scope only contains configured priorities")
        with (PROJECT / scope["paths"]["catalogue"]).open(newline="", encoding="utf-8") as fh:
            catalogue_keys = {r["series_key"] for r in csv.DictReader(fh)}
        missing = [k for k in keys if k not in catalogue_keys]
        check(not missing, f"every scope key exists in the catalogue {missing[:3]}")

    check(len(sources) >= 8, f"source registry exported ({len(sources)})")

    report()
    return 1 if FAIL else 0


def report() -> None:
    for m in OK:
        print(f"  ok    {m}")
    for m in WARN:
        print(f"  warn  {m}")
    for m in FAIL:
        print(f"  FAIL  {m}")
    print(f"\n{len(OK)} ok, {len(WARN)} warnings, {len(FAIL)} failures")


if __name__ == "__main__":
    raise SystemExit(main())
