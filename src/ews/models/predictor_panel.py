
"""Build a source-quarter-aligned, publication-aware predictor panel.

This is a draft Pipeline B input panel, not a final feature matrix.
It does not modify labels, folds, or existing harmonized files.
"""

import pandas as pd

from ews.models.fred_loader import (
    load_fred_manifest,
    load_fred_observations,
)
from ews.models.quarterly_aggregation import (
    available_monthly_quarterly_mean,
    available_quarterly_values,
    available_daily_quarterly_mean,
)


# Explicit provisional classifications.
# Review NA_ASSUMED and source-specific exceptions before approval.
LAG_OVERRIDES = {
    "USA.ACT_GDP_REAL.Q.NA": "NA",
    "USA.ACT_IP.M.STD": "MONTHLY",
    "USA.ACT_EMP.Q.NA": "NA",
    "USA.ACT_HOURS.Q.STD": "NA",
    "USA.ACT_RINC.Q.STD": "NA",
    "USA.ACT_CONS.Q.NA": "NA",
    "USA.ACT_RETAIL.M.STD": "MONTHLY",
    "USA.ACT_INV_EQ.Q.STD": "NA",
    "USA.ACT_INV_STRUCT.Q.STD": "NA",
    "USA.ACT_INV_IPP.Q.STD": "NA",
    "USA.ACT_INV_DEFL.Q.STD": "NA",
    "USA.ACT_EMP.M.ESTAB": "MONTHLY",
    "USA.ACT_EMP.M.LFS": "MONTHLY",
    "USA.ACT_RINC.M.US": "NA",
    "USA.FIN_CREDIT_GDP.Q.STD": "NA_ASSUMED",
    "USA.FIN_EQUITY.M.STD": "MARKET",
    "USA.FIN_HOUSEPRICE.M.US_CS": "NA_ASSUMED",
    "USA.FIN_HOUSEPRICE.Q.OECD_BIS": "NA_ASSUMED",
    "USA.FIN_LONG.M.STD": "MARKET",
    "USA.FIN_POLICY.M.STD": "MARKET",
    "USA.FIN_SHORT.M.STD": "MARKET",
    "USA.LAB_UNEMP.M.STD": "MONTHLY",
    "USA.PRC_CPI.M.STD": "MONTHLY",
    "USA.SEN_BCI.M.STD": "SURVEY",
    "USA.SEN_CCI.M.STD": "SURVEY",
}


def aggregate_available(observations, frequency, lag_class, target):
    """Aggregate observations eligible at the target origin."""

    if frequency == "M":
        return available_monthly_quarterly_mean(
            observations, lag_class, target
        )

    if frequency == "Q":
        return available_quarterly_values(
            observations, lag_class, target
        )

    if frequency == "D":
        return available_daily_quarterly_mean(
            observations, lag_class, target
        )

    raise ValueError(
        f"Unsupported native frequency: {frequency}"
    )


def build_predictor_panel(
    start="1990Q1",
    end="2026Q3",
    manifest_path="data/manifest.csv",
    raw_root="data/raw/fred",
):
    """Return an origin-indexed panel of source-quarter values.

    For each prediction origin, retain only observations that
    have become available by that origin.

    A cell at origin t represents the value for source quarter t.
    If quarter t is unavailable, it remains NaN; it is NOT
    replaced with an older quarter's value.
    """

    manifest = load_fred_manifest(manifest_path)

    quarters = pd.period_range(start, end, freq="Q")
    panel = pd.DataFrame(index=quarters)

    for series_key, lag_class in LAG_OVERRIDES.items():
        observations, frequency = load_fred_observations(
            series_key,
            manifest,
            raw_root=raw_root,
        )

        values = []

        for target in quarters:
            aggregated = aggregate_available(
                observations,
                frequency,
                lag_class,
                target,
            )

            # Preserve source-quarter alignment.
            # Do not substitute the latest older quarter.
            if target in aggregated.index:
                values.append(
                    aggregated.loc[target]
                )
            else:
                values.append(float("nan"))

        panel[series_key] = pd.to_numeric(
            values, errors="coerce"
        )

    panel.index.name = "prediction_quarter"

    return panel
