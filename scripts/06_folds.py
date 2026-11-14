#!/usr/bin/env python3
"""Export the draft walk-forward fold file (Lane 2B).

Thin CLI over :mod:`ews.harness`. Fold generation itself lives in
:mod:`ews.models.folds`.

Status: **DRAFT**. The initial training window is not yet approved
(docs/DECISIONS.md). Do not treat the output as frozen.

Usage:
    python scripts/06_folds.py
    python scripts/06_folds.py --initial-train 80 --inner-initial-train 40
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ews.harness import (  # noqa: E402
    HORIZONS,
    build_payload,
    load_labels,
    write_folds,
)

LABELS_PATH = ROOT / "outputs" / "labels" / "USA_labels.csv"
OUTPUT_PATH = ROOT / "outputs" / "folds" / "folds.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, default=LABELS_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--start", default=None)
    parser.add_argument("--last-scored", default=None)
    parser.add_argument("--initial-train", type=int, default=80)
    parser.add_argument("--inner-initial-train", type=int, default=40)
    args = parser.parse_args()

    first, last = load_labels(args.labels)
    start = args.start or first
    last_scored = args.last_scored or last

    payload = build_payload(
        start=start,
        last_scored=last_scored,
        initial_train=args.initial_train,
        inner_initial_train=args.inner_initial_train,
        labels_path=args.labels,
        horizons=HORIZONS,
    )
    write_folds(payload, args.output)

    counts = {h: len(v["outer"]) for h, v in payload["horizons"].items()}
    print(f"wrote {args.output} ({args.output.stat().st_size:,} bytes)")
    print(f"outer folds by horizon: {counts}")
    print("status: DRAFT - initial training window not approved")


if __name__ == "__main__":
    main()
