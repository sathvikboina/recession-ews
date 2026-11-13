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


def check_frozen_input(
    frame: pd.DataFrame,
    meta_path: Path,
    *,
    allow_overwrite: bool = False,
) -> tuple[bool, str]:
    """Refuse to replace an existing frozen label with different input values.

    Returns ``(ok, message)``. ``ok`` is true when there is no existing record,
    when the canonical input values match, or when the caller explicitly opted
    into an overwrite. A non-empty message is printed by the caller.
    """
    if not meta_path.exists():
        return True, ""
    try:
        record = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"refusing to overwrite: cannot read {meta_path}: {exc}"

    expected = record.get("inputs", {}).get("growth_values_sha256")
    actual = canonical_frame_sha256(frame)
    if expected == actual:
        return True, ""

    if allow_overwrite:
        return True, (
            "WARNING: input values differ from the frozen label record; "
            "overwriting because --allow-overwrite was supplied."
        )

    message = (
        "refusing to overwrite the frozen label: current input values do not "
        f"match {meta_path}. Use --allow-overwrite only after creating a new "
        "label version and updating the archive/tests."
    )
    if expected is None:
        message += "\nthe existing metadata has no inputs.growth_values_sha256"
    return False, message
