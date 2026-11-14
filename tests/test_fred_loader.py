
import hashlib

import pandas as pd
import pytest

from ews.models.fred_loader import (
    load_fred_manifest,
    load_fred_observations,
)


def make_fixture(tmp_path, status="VERIFIED"):
    run = tmp_path / "raw" / "run001"
    run.mkdir(parents=True)

    csv_path = run / "TEST.csv"
    csv_path.write_text(
        "observation_date,value\n"
        "2026-01-01,100.0\n",
        encoding="utf-8",
    )

    sha = hashlib.sha256(
        csv_path.read_bytes()
    ).hexdigest()

    manifest = pd.DataFrame([{
        "series_key": "USA.TEST.M.STD",
        "source_id": "TEST",
        "native_freq": "M",
        "retrieved_at": "run001",
        "sha256": sha,
        "status": status,
    }])

    return manifest, tmp_path / "raw", csv_path


def test_load_verified_series(tmp_path):
    manifest, root, _ = make_fixture(tmp_path)

    data, frequency = load_fred_observations(
        "USA.TEST.M.STD",
        manifest,
        raw_root=root,
    )

    assert frequency == "M"
    assert data["value"].tolist() == [100.0]


def test_reject_low_coverage_series(tmp_path):
    manifest, root, _ = make_fixture(
        tmp_path, status="LOW_COVERAGE"
    )

    with pytest.raises(ValueError):
        load_fred_observations(
            "USA.TEST.M.STD",
            manifest,
            raw_root=root,
        )


def test_reject_modified_raw_file(tmp_path):
    manifest, root, csv_path = make_fixture(tmp_path)

    csv_path.write_text(
        "observation_date,value\n"
        "2026-01-01,999.0\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="SHA256"):
        load_fred_observations(
            "USA.TEST.M.STD",
            manifest,
            raw_root=root,
        )


def test_reject_duplicate_manifest_key(tmp_path):
    manifest, root, _ = make_fixture(tmp_path)

    manifest = pd.concat(
        [manifest, manifest],
        ignore_index=True,
    )

    with pytest.raises(ValueError):
        load_fred_observations(
            "USA.TEST.M.STD",
            manifest,
            raw_root=root,
        )


def test_load_real_manifest():
    manifest = load_fred_manifest()

    assert "GDPC1" in manifest["source_id"].values
    assert "NASDAQCOM" in manifest["source_id"].values
