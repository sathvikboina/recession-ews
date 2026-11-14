
"""Load FRED observations using the verified manifest."""

from pathlib import Path
import hashlib

import pandas as pd


def load_fred_manifest(path="data/manifest.csv"):
    """Read the FRED manifest and validate required fields."""

    manifest = pd.read_csv(path)

    required = {
        "series_key",
        "source_id",
        "native_freq",
        "retrieved_at",
        "sha256",
        "status",
    }

    missing = required - set(manifest.columns)

    if missing:
        raise ValueError(
            f"Missing manifest columns: {sorted(missing)}"
        )

    if manifest["series_key"].duplicated().any():
        raise ValueError("Duplicate series keys in manifest")

    return manifest


def load_fred_observations(
    series_key,
    manifest,
    raw_root="data/raw/fred",
):
    """Load a verified FRED series and check its SHA256 hash."""

    matches = manifest.loc[
        manifest["series_key"] == series_key
    ]

    if len(matches) != 1:
        raise ValueError(
            f"Expected one manifest row for {series_key}"
        )

    row = matches.iloc[0]

    if row["status"] != "VERIFIED":
        raise ValueError(
            f"Series is not VERIFIED: {series_key}"
        )

    source_id = str(row["source_id"])
    run_id = str(row["retrieved_at"])

    path = (
        Path(raw_root)
        / run_id
        / f"{source_id}.csv"
    )

    if not path.is_file():
        raise FileNotFoundError(path)

    actual_hash = hashlib.sha256(
        path.read_bytes()
    ).hexdigest()

    if actual_hash != str(row["sha256"]):
        raise ValueError(
            f"SHA256 mismatch for {series_key}"
        )

    observations = pd.read_csv(path)

    required = {"observation_date", "value"}

    if not required.issubset(observations.columns):
        raise ValueError(
            f"Invalid observation columns: {series_key}"
        )

    return observations, str(row["native_freq"])
