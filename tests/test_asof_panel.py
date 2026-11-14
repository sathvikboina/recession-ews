
import pandas as pd
import pytest
from pathlib import Path
import pytest

FRED_GDP_FILE = Path("data/raw/fred/2026-11-06/GDPC1.csv")

pytestmark = pytest.mark.skipif(
    not FRED_GDP_FILE.exists(),
    reason="Raw FRED snapshot is not available in this environment",
)

from ews.models.asof_panel import build_asof_panel


@pytest.fixture(scope="module")
def panels():
    return build_asof_panel("2025Q4", "2026Q1")


def test_asof_panel_shape(panels):
    values, sources = panels

    assert values.shape == (2, 25)
    assert sources.shape == (2, 25)


def test_gdp_uses_previous_quarter(panels):
    values, sources = panels

    assert sources.loc[
        "2026Q1", "USA.ACT_GDP_REAL.Q.NA"
    ] == "2025Q4"

    assert values.loc[
        "2026Q1", "USA.ACT_GDP_REAL.Q.NA"
    ] == pytest.approx(24125.479)


def test_ip_uses_current_quarter(panels):
    values, sources = panels

    assert sources.loc[
        "2026Q1", "USA.ACT_IP.M.STD"
    ] == "2026Q1"

    assert pd.notna(
        values.loc["2026Q1", "USA.ACT_IP.M.STD"]
    )


def test_no_future_source_quarters(panels):
    _, sources = panels

    for target in sources.index:
        for source in sources.loc[target].dropna():
            assert pd.Period(source, freq="Q") <= target
