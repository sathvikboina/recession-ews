
import pandas as pd
import pytest
from pathlib import Path
import pytest

FRED_GDP_FILE = Path("data/raw/fred/2026-11-06/GDPC1.csv")

pytestmark = pytest.mark.skipif(
    not FRED_GDP_FILE.exists(),
    reason="Raw FRED snapshot is not available in this environment",
)

from ews.models.predictor_panel import (
    aggregate_available,
    build_predictor_panel,
)


def test_unsupported_frequency():
    observations = pd.DataFrame({
        "observation_date": ["2026-01-01"],
        "value": [100.0],
    })

    with pytest.raises(ValueError):
        aggregate_available(
            observations, "W", "MONTHLY", "2026Q1"
        )


def test_real_panel_shape():
    panel = build_predictor_panel(
        start="2025Q4",
        end="2026Q1",
    )

    assert panel.shape == (2, 25)


def test_gdp_current_quarter_unavailable():
    panel = build_predictor_panel(
        start="2026Q1",
        end="2026Q1",
    )

    assert pd.isna(
        panel.loc[
            "2026Q1", "USA.ACT_GDP_REAL.Q.NA"
        ]
    )


def test_industrial_production_current_quarter_available():
    panel = build_predictor_panel(
        start="2026Q1",
        end="2026Q1",
    )

    assert pd.notna(
        panel.loc[
            "2026Q1", "USA.ACT_IP.M.STD"
        ]
    )


def test_market_current_quarter_available():
    panel = build_predictor_panel(
        start="2026Q1",
        end="2026Q1",
    )

    assert pd.notna(
        panel.loc[
            "2026Q1", "USA.FIN_EQUITY.M.STD"
        ]
    )
