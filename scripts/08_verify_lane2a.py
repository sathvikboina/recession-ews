#!/usr/bin/env python3
"""Self-verification for the integrated Lane 2A deliverables.

Runs the mandatory gates, prints one PASS/FAIL line per gate and writes
``outputs/results/lane2a_verification.json``. This script verifies the Lane 2B
artefacts (table, folds) plus the Lane 2A artefacts (firewall suite, baselines,
JPN window closeout). It does not run the official Lane 3 model.

Usage:
    python scripts/08_verify_lane2a.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ews.features import load_panel, validate_feature_table  # noqa: E402

PROJECT = ROOT
CLEAN_DIR = PROJECT / "data" / "clean"
RESULTS_DIR = PROJECT / "outputs" / "results"
LABELS_DIR = PROJECT / "outputs" / "labels"
FOLDS_PATH = PROJECT / "outputs" / "folds" / "folds.json"
DOCS_DIR = PROJECT / "docs"

EXPECTED_USA_LABEL = "2379fd53e4c9023538cafcd5668a4835bcdd7b45cfae9e3cbc3d4f306ed19daa"
EXPECTED_JPN_LABEL = "b20a9f23dec8516f12cf2047dfd87f2575a307ed0839c811d30b95f29cd6b6f5"
EXPECTED_JPN_METADATA = "3b74d3e63f4b6f19e15c372637c2f776e029903f710eba93c8a6cb395b99ed9a"
EXPECTED_FOLDS = "afd51bc5f885f74a84f2e5f29bd6732de78454945cb189f2fee1d8c426afc261"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_gate(name: str, fn):
    try:
        ok, message, details = fn()
    except Exception as exc:  # noqa: BLE001 - gates report any failure
        ok, message, details = False, f"exception: {exc}", {"error": str(exc)}
    print(f"{name}: {'PASS' if ok else 'FAIL'} - {message}")
    return {"status": "PASS" if ok else "FAIL", "passed": ok, "details": details}


def gate_labels():
    usa = sha256(LABELS_DIR / "USA_labels.csv")
    jpn = sha256(LABELS_DIR / "JPN" / "JPN_labels.csv")
    jpn_meta = sha256(LABELS_DIR / "JPN" / "labels-v1-JPN.json")
    ok = (
        usa == EXPECTED_USA_LABEL
        and jpn == EXPECTED_JPN_LABEL
        and jpn_meta == EXPECTED_JPN_METADATA
    )
    return ok, f"USA {usa[:12]}..., JPN {jpn[:12]}..., metadata {jpn_meta[:12]}...", {
        "usa": usa,
        "jpn": jpn,
        "jpn_metadata": jpn_meta,
    }


def gate_table():
    path = CLEAN_DIR / "dataset.parquet"
    if not path.exists():
        return False, "missing data/clean/dataset.parquet; run make features", {}
    frame = pd.read_parquet(path)
    table = frame.set_index(pd.PeriodIndex(frame["quarter"], freq="Q")).drop(
        columns=["quarter"]
    )
    table.index.name = "quarter"
    validate_feature_table(table)
    digest = sha256(path)
    ok = table.shape == (147, 149)
    return ok, f"{table.shape[0]} x {table.shape[1]}, sha256 {digest[:12]}...", {
        "rows": int(table.shape[0]),
        "features": int(table.shape[1]),
        "sha256": digest,
    }


def gate_panel():
    panel_path = CLEAN_DIR / "USA_panel.csv"
    if not panel_path.exists():
        return False, "missing data/clean/USA_panel.csv", {}
    panel = load_panel(panel_path)
    ok = str(panel.index[0]) == "1960Q1" and str(panel.index[-1]) == "2026Q3"
    return ok, f"{panel.shape[0]} rows, {panel.shape[1]} series, {panel.index[0]}..{panel.index[-1]}", {
        "rows": int(panel.shape[0]),
        "series": int(panel.shape[1]),
    }


def gate_folds():
    if not FOLDS_PATH.exists():
        return False, "missing outputs/folds/folds.json", {}
    payload = json.loads(FOLDS_PATH.read_text(encoding="utf-8"))
    metadata = payload.get("metadata", {})
    digest = sha256(FOLDS_PATH)
    approved = metadata.get("approved") is True and metadata.get("draft") is False
    ok = approved and digest == EXPECTED_FOLDS
    return ok, f"approved={approved}, sha256 {digest[:12]}...", {
        "approved": approved,
        "sha256": digest,
        "outer_2q": len(payload["horizons"]["2"]["outer"]),
    }


def _pytest(target: str):
    result = subprocess.run(
        [sys.executable, "-m", "pytest", target, "-q", "-p", "no:cacheprovider"],
        cwd=PROJECT,
        capture_output=True,
        text=True,
    )
    summary = [line for line in result.stdout.splitlines() if "passed" in line]
    return result.returncode == 0, summary[-1] if summary else result.stdout.strip(), result


def gate_firewall():
    ok, summary, _ = _pytest("tests/test_feature_firewall.py")
    return ok, summary, {"pytest": summary}


def gate_baselines():
    command = [sys.executable, str(PROJECT / "scripts" / "07_baselines.py")]
    first = subprocess.run(command, cwd=PROJECT, capture_output=True, text=True)
    if first.returncode != 0:
        return False, f"baseline run failed: {first.stderr.strip()}", {}
    csv_hash = sha256(RESULTS_DIR / "baselines.csv")
    md_hash = sha256(RESULTS_DIR / "baselines.md")
    second = subprocess.run(command, cwd=PROJECT, capture_output=True, text=True)
    if second.returncode != 0:
        return False, f"second baseline run failed: {second.stderr.strip()}", {}
    stable = csv_hash == sha256(RESULTS_DIR / "baselines.csv") and md_hash == sha256(
        RESULTS_DIR / "baselines.md"
    )
    frame = pd.read_csv(RESULTS_DIR / "baselines.csv")
    primary = frame[frame["is_primary"]]
    ok = stable and frame["pr_auc"].notna().all() and not primary.empty
    return ok, f"stable={stable}, csv {csv_hash[:12]}..., {len(primary)} primary rows", {
        "csv_sha256": csv_hash,
        "md_sha256": md_hash,
        "stable": stable,
        "primary": primary[["model", "pr_auc", "episode_recall"]].to_dict("records"),
    }


def gate_jpn_decision():
    decisions = (DOCS_DIR / "DECISIONS.md").read_text(encoding="utf-8")
    validation = (DOCS_DIR / "LABEL_VALIDATION_JPN.md").read_text(encoding="utf-8")
    metadata_hash = sha256(LABELS_DIR / "JPN" / "labels-v1-JPN.json")
    recorded = "D-R38" in decisions and "144" in decisions and "JPN" in decisions
    documented = "D-R38" in validation and metadata_hash in validation
    ok = recorded and documented and metadata_hash == EXPECTED_JPN_METADATA
    return ok, f"D-R38 recorded={recorded}, hash in note={documented}", {
        "recorded": recorded,
        "documented": documented,
        "metadata_sha256": metadata_hash,
    }


def gate_labels_clean():
    result = subprocess.run(
        ["git", "status", "--porcelain", "outputs/labels"],
        cwd=PROJECT,
        capture_output=True,
        text=True,
    )
    clean = result.stdout.strip() == ""
    return clean, "outputs/labels is untouched" if clean else result.stdout.strip(), {
        "status": result.stdout.strip()
    }


def main() -> int:
    print("=" * 70)
    print("LANE 2A INTEGRATION VERIFICATION")
    print("=" * 70)
    gates = {
        "G1 frozen label hashes": gate_labels,
        "G2 feature table (147 x 149, valid)": gate_table,
        "G3 harmonised panel window": gate_panel,
        "G4 frozen folds (D-R37)": gate_folds,
        "G5 firewall suite": gate_firewall,
        "G6 baselines reproducible": gate_baselines,
        "G7 JPN 144/147 closeout (D-R38)": gate_jpn_decision,
        "G8 labels untouched": gate_labels_clean,
    }
    results = {name: run_gate(name, fn) for name, fn in gates.items()}
    all_passed = all(item["passed"] for item in results.values())
    print("=" * 70)
    print("ALL GATES PASS" if all_passed else "GATES FAILED")
    print("=" * 70)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / "lane2a_verification.json"
    out.write_text(
        json.dumps({"all_passed": all_passed, "gates": results}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"report written to {out.relative_to(PROJECT)}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
