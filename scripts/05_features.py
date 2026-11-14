#!/usr/bin/env python3
"""Build the USA predictor table (Lane 2B).

Reads ``data/clean/USA_panel.csv``, applies the C-05 availability lags and the
C-07 transforms, and writes an unscaled ``data/clean/dataset.parquet``.

The table is generated, never hand-edited. Regenerate after any spec change:

    make features

The BEAI-eligible core series appear only as ``beai_copy_*`` predictors; no
label output or NBER series is included.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ews.features import (  # noqa: E402
    DEFAULT_END,
    DEFAULT_START,
    FEATURE_SPEC,
    build_feature_table,
    load_panel,
    to_frame,
)

PANEL = ROOT / "data" / "clean" / "USA_panel.csv"
OUTPUT = ROOT / "data" / "clean" / "dataset.parquet"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel", type=Path, default=PANEL)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=DEFAULT_END)
    args = parser.parse_args()

    panel = load_panel(args.panel)
    table = build_feature_table(panel, start=args.start, end=args.end)
    frame = to_frame(table)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(args.output, index=False)

    digest = hashlib.sha256(args.output.read_bytes()).hexdigest()
    copies = [c for c in frame.columns if c.startswith("beai_copy_")]
    print(f"wrote {args.output}")
    print(f"rows: {len(frame)}  quarters: {args.start}-{args.end}")
    print(f"features: {len(frame.columns) - 1}  beai_copy columns: {len(copies)}")
    print(f"sha256: {digest}")
    print(f"spec series: {len(FEATURE_SPEC)} + {1} derived")


if __name__ == "__main__":
    main()
