#!/usr/bin/env python3
"""scripts/run_lane2a.py

Executes the Lane 2A pipeline sequentially, mirroring `make lane2a`:
1. features:  scripts/05_features.py   (builds data/clean/dataset.parquet)
2. folds:     scripts/06_folds.py --approved (exports outputs/folds/folds.json under D-R37)
3. baselines: scripts/07_baselines.py  (evaluates baselines across horizons)
4. test:      pytest tests/test_features.py
5. verify:    scripts/08_verify_lane2a.py (runs 9 verification gates)
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]


def run_step(step_name: str, cmd: list[str]) -> None:
    print(f"\n{'='*20} [LANE 2A] {step_name} {'='*20}")
    print(f"Command: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=PROJECT)
    if res.returncode != 0:
        print(f"\n[FAIL] Step '{step_name}' failed with return code {res.returncode}")
        sys.exit(res.returncode)
    print(f"[OK] Step '{step_name}' completed successfully.")


def main() -> int:
    py = sys.executable

    steps = [
        ("1. features", [py, "scripts/05_features.py"]),
        ("2. folds", [py, "scripts/06_folds.py", "--approved"]),
        ("3. baselines", [py, "scripts/07_baselines.py"]),
        ("4. test", [py, "-m", "pytest", "tests/test_features.py", "-p", "no:cacheprovider"]),
        ("5. verify", [py, "scripts/08_verify_lane2a.py"]),
    ]

    for name, cmd in steps:
        run_step(name, cmd)

    print("\n" + "="*60)
    print("ALL LANE 2A STEPS COMPLETED SUCCESSFULLY")
    print("="*60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
