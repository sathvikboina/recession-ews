"""Deterministic helpers for the frozen label record (D-R22..D-R25).

The frozen record must not change just because the builder is re-run. Two things
are handled here:

* the ``created`` date is preserved from an existing ``labels-v1.json``;
* input data are hashed by their *values*, not by the bytes of a parquet file,
  because parquet bytes can change when pyarrow changes.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


def existing_created(path: Path, default: str) -> str:
    """Return the recorded creation date, or ``default`` if it cannot be read."""
    if path.exists():
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return default
        value = record.get("created")
        if isinstance(value, str) and value:
            return value
    return default


def canonical_frame_sha256(frame: pd.DataFrame) -> str:
    """Hash a frame's values through a canonical CSV rendering.

    A parquet byte hash is environment-dependent. This digest changes only when
    the values (or their order/index) change, which is what a freeze record
    should protect.
    """
    text = frame.round(10).to_csv(float_format="%.10f", lineterminator="\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
