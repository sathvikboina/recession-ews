#!/usr/bin/env python3
"""scripts/06_folds.py

Deterministic expanding-window folds generator for horizons 1Q, 2Q (primary), and 4Q.
Implements frozen decision D-R37:
- Expanding window
- Initial outer training quarters: 80
- Inner initial training quarters: 40
- Step: 1 quarter
- Purge / embargo: equal to horizon
- First scored quarter: 2010Q1
- Output: outputs/folds/folds.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parents[1]
OUTPUT_FILE = PROJECT / "outputs" / "folds" / "folds.json"
LABELS_FILE = PROJECT / "outputs" / "labels" / "USA_labels.csv"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic expanding folds under D-R37")
    parser.add_argument("--output", type=Path, default=OUTPUT_FILE)
    parser.add_argument("--labels", type=Path, default=LABELS_FILE)
    parser.add_argument("--start", default=None)
    parser.add_argument("--last-scored", default=None)
    parser.add_argument("--initial-train", type=int, default=80)
    parser.add_argument("--inner-initial-train", type=int, default=40)
    parser.add_argument("--approved", action="store_true", default=True, help="mark the fold file as frozen under D-R37")
    args = parser.parse_args()

    sys.path.insert(0, str(PROJECT / "src"))
    from ews.harness import (
        HORIZONS,
        PRIMARY_HORIZON,
        STEP_QUARTERS,
        build_payload,
        load_labels,
        write_folds,
    )

    if not args.labels.exists():
        raise FileNotFoundError(f"Labels file not found: {args.labels}")

    first, last = load_labels(args.labels)
    start = args.start or first
    last_scored = args.last_scored or last

    try:
        labels_rel = args.labels.resolve().relative_to(PROJECT).as_posix()
    except ValueError:
        labels_rel = str(args.labels)

    payload = build_payload(
        start=start,
        last_scored=last_scored,
        initial_train=args.initial_train,
        inner_initial_train=args.inner_initial_train,
        labels_path=args.labels,
        labels_file=labels_rel,
        horizons=HORIZONS,
        step_quarters=STEP_QUARTERS,
        approved=args.approved,
    )

    out_path = write_folds(payload, args.output)
    content = out_path.read_bytes()
    digest = hashlib.sha256(content).hexdigest()

    print(f"wrote {out_path} ({len(content):,} bytes)")
    print(f"SHA-256: {digest}")
    counts = {h: len(v["outer"]) for h, v in payload["horizons"].items()}
    print(f"outer folds by horizon: {counts}")

    # Remove any deprecated draft folds in data/features
    deprecated_folds = PROJECT / "data" / "features" / "folds.json"
    if deprecated_folds.exists():
        deprecated_folds.unlink()
        print(f"Removed deprecated draft folds: {deprecated_folds}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
