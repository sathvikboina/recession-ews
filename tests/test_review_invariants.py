#!/usr/bin/env python3
"""Review invariants added on 2026-11-05.

Two failure modes are protected here:

1. ``spec.py`` is the generator for ``decisions_log.csv``.  If the two drift, a
   rebuild silently reverts the Q-02/Q-04/Q-05 decisions.  The test compares every
   generated field for every decision.
2. The ensemble must stay pre-registered.  The addendum and contract rule C-13
   must exist and contain the beat-the-best and leakage conditions before any
   model result exists.

Runs under pytest or standalone:
    python tests/test_review_invariants.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

import spec  # noqa: E402

LOG = PROJECT / "decisions_log.csv"
ADDENDUM = PROJECT / "docs" / "PROPOSAL_ADDENDUM.md"
CONTRACT = PROJECT / "docs" / "BUILD_CONTRACT.md"

# Tuple layout of spec.Q: id, area, issue, decision, plan_basis, deviation_type,
# deviation_detail, status, remaining_action, affected_series, priority.
FIELDS = {
    "decision": 3,
    "deviation_detail": 6,
    "status": 7,
    "remaining_action": 8,
}


def test_spec_matches_active_decision_log() -> None:
    with LOG.open(encoding="utf-8", newline="") as fh:
        rows = {r["question_id"]: r for r in csv.DictReader(fh)}

    assert {q[0] for q in spec.Q} == set(rows), "spec.py and decisions_log.csv cover different questions"

    for q in spec.Q:
        qid = q[0]
        for field, index in FIELDS.items():
            assert q[index] == rows[qid][field], (
                f"{qid}.{field} differs between spec.py and decisions_log.csv; "
                "regenerate the CSV from spec.py instead of editing them separately"
            )

    for qid in ("Q-02", "Q-04", "Q-05"):
        row = rows[qid]
        assert "signed off 2026-11-05" in row["deviation_detail"] + row["remaining_action"], (
            f"{qid} is missing the explicit 2026-11-05 USA sign-off"
        )
    assert "best case is 4/8" in rows["Q-06"]["decision"], "Q-06 is missing the India pre-audit finding"


def test_ensemble_preregistration_is_present_and_specific() -> None:
    assert ADDENDUM.exists(), "docs/PROPOSAL_ADDENDUM.md is missing"
    text = ADDENDUM.read_text(encoding="utf-8").lower()

    required = (
        "pre-registered",
        "equal-weight",
        "top-3",
        "inner-fold",
        "0.01",
        "bootstrap",
        "episode-level recall",
        "leakage",
        "negative result",
        "before any model was trained or scored",
    )
    missing = [phrase for phrase in required if phrase not in text]
    assert not missing, f"ensemble addendum is missing: {missing}"

    contract = CONTRACT.read_text(encoding="utf-8")
    assert "## C-13" in contract, "BUILD_CONTRACT.md has no C-13 ensemble rule"
    assert "top-3" in contract and "0.01" in contract, "C-13 is missing the confirmatory test"


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
