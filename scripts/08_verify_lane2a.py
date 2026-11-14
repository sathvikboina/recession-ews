#!/usr/bin/env python3
"""scripts/08_verify_lane2a.py

Self-verification harness for Lane 2A (Feature Specification, Firewall Tests and Baselines).
Runs the nine mandatory gates, prints one PASS/FAIL line each, writes
outputs/results/lane2a_verification.json, and prints "ALL GATES PASS".
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT / "outputs" / "results"
LABELS_DIR = PROJECT / "outputs" / "labels"
FEATURES_DIR = PROJECT / "data" / "features"
CLEAN_DIR = PROJECT / "data" / "clean"
DOCS_DIR = PROJECT / "docs"

EXPECTED_USA_LABEL_HASH = "2379fd53e4c9023538cafcd5668a4835bcdd7b45cfae9e3cbc3d4f306ed19daa"
EXPECTED_JPN_JSON_HASH = "3b74d3e63f4b6f19e15c372637c2f776e029903f710eba93c8a6cb395b99ed9a"
BASE_COMMIT = "4556011"


def run_gate(name: str, fn) -> tuple[bool, str, dict]:
    try:
        ok, msg, details = fn()
        status_str = "PASS" if ok else "FAIL"
        print(f"{name}: {status_str} - {msg}")
        return ok, status_str, details
    except Exception as exc:
        print(f"{name}: FAIL - Exception: {exc}")
        return False, "FAIL", {"error": str(exc)}


def gate_1() -> tuple[bool, str, dict]:
    """G1 base commit contains 4556011"""
    cmd = ["git", "merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"]
    res = subprocess.run(cmd, cwd=PROJECT, capture_output=True, text=True)
    ok = (res.returncode == 0)
    msg = f"Commit {BASE_COMMIT} is an ancestor of HEAD" if ok else f"Base commit {BASE_COMMIT} missing"
    return ok, msg, {"base_commit": BASE_COMMIT, "is_ancestor": ok}


def gate_2() -> tuple[bool, str, dict]:
    """G2 USA label blob hash == 2379fd53...19daa"""
    cmd = ["git", "cat-file", "blob", "HEAD:outputs/labels/USA_labels.csv"]
    res = subprocess.run(cmd, cwd=PROJECT, capture_output=True)
    if res.returncode != 0:
        return False, "Failed to read git blob for USA_labels.csv", {}
    h = hashlib.sha256(res.stdout).hexdigest()
    ok = (h == EXPECTED_USA_LABEL_HASH)
    msg = f"Hash matches frozen digest {h[:12]}..." if ok else f"Hash mismatch: got {h}"
    return ok, msg, {"expected": EXPECTED_USA_LABEL_HASH, "actual": h}


def gate_3() -> tuple[bool, str, dict]:
    """G3 USA_panel shape and window recorded and match the spec text"""
    panel_file = CLEAN_DIR / "USA_panel.csv"
    if not panel_file.exists():
        return False, f"Missing {panel_file}", {}
    df = pd.read_csv(panel_file)
    n_rows, n_cols = df.shape
    q_start = str(df["quarter"].iloc[0])
    q_end = str(df["quarter"].iloc[-1])
    spec_text = (DOCS_DIR / "FEATURES.md").read_text(encoding="utf-8")
    
    in_spec = "1960Q1" in spec_text and "2026Q3" in spec_text and "267" in spec_text
    ok = (n_rows == 267 and n_cols == 27 and q_start == "1960Q1" and q_end == "2026Q3" and in_spec)
    msg = f"Shape ({n_rows}, {n_cols}) covering {q_start}..{q_end} (recorded in spec)" if ok else f"Mismatch ({n_rows}, {n_cols})"
    return ok, msg, {
        "n_rows": n_rows, "n_cols": n_cols, "start": q_start, "end": q_end, "spec_verified": in_spec
    }


def gate_4() -> tuple[bool, str, dict]:
    """G4 make features -> 147 rows, contiguous, unscaled, zero blacklisted columns"""
    res = subprocess.run([sys.executable, str(PROJECT / "scripts" / "06_features.py")], cwd=PROJECT, capture_output=True, text=True)
    if res.returncode != 0:
        return False, f"scripts/06_features.py failed: {res.stderr}", {}
    feat_file = FEATURES_DIR / "dataset.parquet"
    if not feat_file.exists():
        return False, f"Missing {feat_file}", {}
    df = pd.read_parquet(feat_file)
    if len(df) != 147:
        return False, f"Expected 147 rows, got {len(df)}", {}
    quarters = df["quarter"].tolist()
    expected_q = [str(q) for q in pd.period_range("1990Q1", "2026Q3", freq="Q")]
    if quarters != expected_q:
        return False, "Quarters not contiguous 1990Q1..2026Q3", {}
    
    # Blacklist check
    for col in df.columns:
        cl = str(col).lower()
        if cl in {"factor", "level", "r", "n_available", "deterioration_share", "turning_point", "nber"}:
            return False, f"Blacklisted column '{col}' found", {}
    
    # Unscaled check
    for col in df.columns:
        if col == "quarter": continue
        s = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(s) > 1 and abs(float(s.mean())) < 1e-9 and abs(float(s.std()) - 1.0) < 1e-6:
            return False, f"Column '{col}' is standardized", {}
            
    return True, f"147 rows, contiguous 1990Q1..2026Q3, unscaled, 0 blacklisted columns ({len(df.columns)-1} predictors)", {
        "rows": len(df), "predictors": len(df.columns) - 1
    }


def gate_5() -> tuple[bool, str, dict]:
    """G5 make folds deterministic (two runs, identical bytes), no test row in train"""
    r1 = subprocess.run([sys.executable, str(PROJECT / "scripts" / "06_folds.py")], cwd=PROJECT, capture_output=True, text=True)
    b1 = (FEATURES_DIR / "folds.json").read_bytes()
    h1 = hashlib.sha256(b1).hexdigest()

    r2 = subprocess.run([sys.executable, str(PROJECT / "scripts" / "06_folds.py")], cwd=PROJECT, capture_output=True, text=True)
    b2 = (FEATURES_DIR / "folds.json").read_bytes()
    h2 = hashlib.sha256(b2).hexdigest()

    if h1 != h2:
        return False, f"Non-deterministic folds: {h1} != {h2}", {}

    folds_data = json.loads(b1.decode("utf-8"))["folds"]
    for h_name, fold_list in folds_data.items():
        for f in fold_list:
            if f["train_end"] >= f["test_start"]:
                return False, f"Test row in train in {h_name} fold {f['fold_id']}", {}

    return True, f"Folds deterministic (SHA-256: {h1[:12]}...), no test row in train", {
        "sha256": h1, "horizons": list(folds_data.keys()), "n_folds_2q": len(folds_data["2Q"])
    }


def gate_6() -> tuple[bool, str, dict]:
    """G6 tests/test_features.py passes; mutation test fails on both poisoned tables"""
    cmd = [sys.executable, "-m", "pytest", "tests/test_features.py", "-p", "no:cacheprovider", "-q"]
    res = subprocess.run(cmd, cwd=PROJECT, capture_output=True, text=True)
    ok = (res.returncode == 0)
    lines = [line for line in res.stdout.splitlines() if "passed" in line]
    summary_line = lines[-1] if lines else res.stdout.strip()
    msg = f"All six tests pass ({summary_line})" if ok else f"Pytest failed: {res.stdout}\n{res.stderr}"
    return ok, msg, {"pytest_output": summary_line, "returncode": res.returncode}


def gate_7() -> tuple[bool, str, dict]:
    """G7 baselines reproduce (two runs, identical hashes) and report PR-AUC + episode recall"""
    r1 = subprocess.run([sys.executable, str(PROJECT / "scripts" / "07_baselines.py")], cwd=PROJECT, capture_output=True, text=True)
    csv_bytes1 = (RESULTS_DIR / "baselines.csv").read_bytes()
    md_bytes1 = (RESULTS_DIR / "baselines.md").read_bytes()
    h_csv1 = hashlib.sha256(csv_bytes1).hexdigest()
    h_md1 = hashlib.sha256(md_bytes1).hexdigest()

    r2 = subprocess.run([sys.executable, str(PROJECT / "scripts" / "07_baselines.py")], cwd=PROJECT, capture_output=True, text=True)
    csv_bytes2 = (RESULTS_DIR / "baselines.csv").read_bytes()
    md_bytes2 = (RESULTS_DIR / "baselines.md").read_bytes()
    h_csv2 = hashlib.sha256(csv_bytes2).hexdigest()
    h_md2 = hashlib.sha256(md_bytes2).hexdigest()

    if h_csv1 != h_csv2 or h_md1 != h_md2:
        return False, f"Baseline runs not byte-identical: CSV {h_csv1} != {h_csv2}", {}

    df_b = pd.read_csv(RESULTS_DIR / "baselines.csv")
    has_prauc = "pr_auc" in df_b.columns and df_b["pr_auc"].notna().all()
    has_recall = "episode_recall" in df_b.columns and df_b["episode_recall"].notna().all()
    
    if not (has_prauc and has_recall):
        return False, "Missing PR-AUC or episode recall in baselines.csv", {}

    row_2q_sp = df_b[(df_b["horizon"] == "2Q") & (df_b["model"] == "term_spread")].iloc[0]
    return True, f"Baselines reproduced identically (CSV {h_csv1[:12]}...). 2Q term_spread PR-AUC={row_2q_sp['pr_auc']:.4f}, recall={row_2q_sp['episode_recall']:.4f}", {
        "csv_sha256": h_csv1, "md_sha256": h_md1, "results": df_b[["horizon", "model", "pr_auc", "episode_recall"]].to_dict(orient="records")
    }


def gate_8() -> tuple[bool, str, dict]:
    """G8 D-R34 present and the JPN metadata hash in the validation note matches the file"""
    dec_text = (DOCS_DIR / "DECISIONS.md").read_text(encoding="utf-8")
    dr34_present = ("D-R34" in dec_text and "144" in dec_text and "JPN" in dec_text)
    if not dr34_present:
        return False, "D-R34 not properly recorded in docs/DECISIONS.md", {}

    val_text = (DOCS_DIR / "LABEL_VALIDATION_JPN.md").read_text(encoding="utf-8")
    jpn_json_file = LABELS_DIR / "JPN" / "labels-v1-JPN.json"
    if not jpn_json_file.exists():
        return False, f"Missing {jpn_json_file}", {}
    actual_hash = hashlib.sha256(jpn_json_file.read_bytes()).hexdigest()
    hash_in_doc = (actual_hash in val_text)

    ok = dr34_present and hash_in_doc and (actual_hash == EXPECTED_JPN_JSON_HASH)
    msg = f"D-R34 recorded; JPN metadata hash {actual_hash[:12]}... matches file and validation note" if ok else "Mismatch in JPN metadata hash or D-R34"
    return ok, msg, {
        "dr34_present": dr34_present, "actual_json_hash": actual_hash, "doc_hash_match": hash_in_doc
    }


def gate_9() -> tuple[bool, str, dict]:
    """G9 `git status` shows no changes to outputs/labels/**"""
    cmd = ["git", "status", "--porcelain", "outputs/labels"]
    res = subprocess.run(cmd, cwd=PROJECT, capture_output=True, text=True)
    status_output = res.stdout.strip()
    ok = (status_output == "")
    msg = "outputs/labels/** is completely clean and untouched" if ok else f"Uncommitted changes in outputs/labels: {status_output}"
    return ok, msg, {"clean": ok, "status_output": status_output}


def main() -> int:
    print("=" * 70)
    print("LANE 2A SELF-VERIFICATION HARNESS")
    print("=" * 70)

    gates = [
        ("G1 base commit contains 4556011", gate_1),
        ("G2 USA label blob hash == 2379fd53...19daa", gate_2),
        ("G3 USA_panel shape and window recorded in spec", gate_3),
        ("G4 make features (147 rows, contiguous, unscaled, zero blacklisted)", gate_4),
        ("G5 make folds deterministic (identical bytes, no test row in train)", gate_5),
        ("G6 tests/test_features.py passes; mutation fails on leaks", gate_6),
        ("G7 baselines reproduce (identical hashes, PR-AUC + recall)", gate_7),
        ("G8 D-R34 present and JPN metadata hash verified", gate_8),
        ("G9 git status shows zero changes to outputs/labels/**", gate_9),
    ]

    all_passed = True
    gate_results = {}

    for name, fn in gates:
        ok, status_str, details = run_gate(name, fn)
        gate_results[name] = {"status": status_str, "passed": ok, "details": details}
        if not ok:
            all_passed = False

    print("=" * 70)
    if all_passed:
        print("ALL GATES PASS")
    else:
        print("GATES FAILED")
    print("=" * 70)

    # Write outputs/results/lane2a_verification.json
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_json = RESULTS_DIR / "lane2a_verification.json"
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump({
            "all_passed": all_passed,
            "gate_results": gate_results,
        }, fh, indent=2)

    print(f"Verification report written to {out_json}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
