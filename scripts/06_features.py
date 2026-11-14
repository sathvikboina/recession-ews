#!/usr/bin/env python3
"""scripts/06_features.py

Reference implementation of the Lane 2A feature specification contract.
Lane 2B owner may replace or extend it -- the test suite targets the resulting
artifacts and invariants, not this specific implementation.

Builds unscaled quarterly predictors for USA over 1990Q1-2026Q3 (147 quarters).
Under Rule C-01, Pipeline B predictors are strictly firewalled from Pipeline A.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
CLEAN_DIR = PROJECT / "data" / "clean"
FEATURES_DIR = PROJECT / "data" / "features"

# Frozen study window bounds (Rule C-03 / D-R02 / D-R31)
WINDOW_START = "1990Q1"
WINDOW_END = "2026Q3"
EXPECTED_ROWS = 147

# Explicit blacklist of forbidden column substrings / exact tokens (case-insensitive)
BLACKLIST_EXACT = {
    "factor", "level", "r", "r_t", "rt", "recession", "n_available",
    "deterioration_share", "turning_point", "peak", "trough", "nber",
    "validation", "usa_validation", "country_id", "country", "iso3",
    "episode_id", "episode"
}
BLACKLIST_SUBSTRINGS = [
    "factor", "deterioration_share", "turning_point", "n_available",
    "nber", "usa_validation", "episode_id"
]


def validate_table(df: pd.DataFrame, reference_df: pd.DataFrame | None = None) -> None:
    """Validate feature table against schema, blacklist, scaling, and no-future leakage rules.

    Raises ValueError if any rule is violated.
    """
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Feature table must be a pandas DataFrame")

    # 1. Schema: key 'quarter', contiguous 1990Q1-2026Q3, exactly 147 rows, no duplicates
    if "quarter" in df.columns:
        quarters = df["quarter"].astype(str).tolist()
        cols_to_check = [c for c in df.columns if c != "quarter"]
    else:
        quarters = df.index.astype(str).tolist()
        cols_to_check = list(df.columns)

    if len(quarters) != EXPECTED_ROWS:
        raise ValueError(f"Expected {EXPECTED_ROWS} rows, got {len(quarters)}")

    expected_quarters = [str(q) for q in pd.period_range(WINDOW_START, WINDOW_END, freq="Q")]
    if quarters != expected_quarters:
        raise ValueError("Quarters must be contiguous 1990Q1-2026Q3 without gaps or duplicates")

    if len(set(quarters)) != len(quarters):
        raise ValueError("Duplicate quarter keys found")

    # 2. Blacklist scan (case-insensitive)
    for col in df.columns:
        col_lower = str(col).strip().lower()
        if col_lower in BLACKLIST_EXACT:
            raise ValueError(f"Blacklisted column detected (exact token): '{col}'")
        for sub in BLACKLIST_SUBSTRINGS:
            if sub in col_lower:
                raise ValueError(f"Blacklisted column detected (substring '{sub}'): '{col}'")
        if col_lower == "r" or col_lower.startswith("r_"):
            raise ValueError(f"Blacklisted recession label column detected: '{col}'")
        if col_lower.startswith("peak") or col_lower.startswith("trough"):
            raise ValueError(f"Blacklisted turning-point column detected: '{col}'")

    # 3. Unscaled check: no column should be standardized to mean 0 and std 1
    for col in cols_to_check:
        s = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(s) > 1:
            m = abs(float(s.mean()))
            std = float(s.std(ddof=1))
            if m < 1e-9 and abs(std - 1.0) < 1e-6:
                raise ValueError(f"Column '{col}' appears standardized (|mean|<1e-9, |std-1|<1e-6)")

    # 4. No-future leakage / future-shift mutation check
    # Check if any column is shifted from future (e.g. shift(-1))
    if reference_df is None:
        try:
            panel_path = CLEAN_DIR / "USA_panel.csv"
            growth_path = CLEAN_DIR / "USA_growth.parquet"
            if panel_path.exists() and growth_path.exists():
                panel_ref = pd.read_csv(panel_path)
                growth_ref = pd.read_parquet(growth_path)
                reference_df = build_features(panel_ref, growth_ref)
        except Exception:
            reference_df = None

    if reference_df is not None:
        ref_df_aligned = reference_df.copy()
        if "quarter" in ref_df_aligned.columns:
            ref_df_aligned = ref_df_aligned.set_index("quarter")
        df_aligned = df.copy()
        if "quarter" in df_aligned.columns:
            df_aligned = df_aligned.set_index("quarter")

        for col in cols_to_check:
            s_test = df_aligned[col].dropna()
            if len(s_test) < 10:
                continue

            if col in ref_df_aligned.columns:
                # If this column exists in reference, check if it was shifted from the future
                s_ref_future = ref_df_aligned[col].shift(-1).dropna()
                common_idx = s_test.index.intersection(s_ref_future.index)
                if len(common_idx) >= 10:
                    diff = np.abs(s_test.loc[common_idx].to_numpy() - s_ref_future.loc[common_idx].to_numpy())
                    if np.nanmax(diff) < 1e-6:
                        raise ValueError(f"Future leakage detected: column '{col}' is shifted from future (shift -1Q)")
            else:
                # If a new column was injected, check if it matches a future shift of any reference column
                for rcol in ref_df_aligned.columns:
                    s_ref_future = ref_df_aligned[rcol].shift(-1).dropna()
                    common_idx = s_test.index.intersection(s_ref_future.index)
                    if len(common_idx) >= 10:
                        diff = np.abs(s_test.loc[common_idx].to_numpy() - s_ref_future.loc[common_idx].to_numpy())
                        if np.nanmax(diff) < 1e-6:
                            raise ValueError(f"Future leakage detected: injected column '{col}' matches future shift (-1Q) of '{rcol}'")


def build_features(
    panel: pd.DataFrame,
    growth: pd.DataFrame,
    cutoff: str | None = None
) -> pd.DataFrame:
    """Pure function building unscaled quarterly predictors for USA.

    Args:
        panel: USA_panel.csv DataFrame (1960Q1-2026Q3 levels)
        growth: USA_growth.parquet DataFrame (1960Q1-2026Q3 unscaled activity growth)
        cutoff: Optional quarter string (e.g. "2005Q2"). If set, input history
                beyond cutoff is truncated, ensuring strict no-future leakage.

    Returns:
        DataFrame indexed by quarter "1990Q1".."2026Q3" (147 rows), unscaled.
    """
    p = panel.copy()
    g = growth.copy()

    # Ensure period index
    if "quarter" in p.columns:
        p["quarter"] = pd.PeriodIndex(p["quarter"], freq="Q")
        p = p.set_index("quarter")
    elif not isinstance(p.index, pd.PeriodIndex):
        p.index = pd.PeriodIndex(p.index, freq="Q")

    if not isinstance(g.index, pd.PeriodIndex):
        g.index = pd.PeriodIndex(g.index, freq="Q")

    p = p.sort_index()
    g = g.sort_index()

    # If cutoff is specified, mask out any observations after cutoff
    if cutoff is not None:
        c_period = pd.Period(cutoff, freq="Q")
        p = p.loc[p.index <= c_period]
        g = g.loc[g.index <= c_period]

    # Target window is 1990Q1 to 2026Q3 (147 quarters)
    target_window = pd.period_range(WINDOW_START, WINDOW_END, freq="Q")
    out = pd.DataFrame(index=target_window)

    # -------------------------------------------------------------------------
    # 1. Allowed Raw BEAI Copies (8 indicators)
    # Reconstructed from USA_growth.parquet alone.
    # Lags applied under C-05:
    #   - NA (quarterly national accounts): 1 quarter lag
    #   - Monthly indicators: 6 weeks (available at origin t+6w, so 0Q shift)
    # -------------------------------------------------------------------------
    core_beai_lags = {
        "beai_copy_act_gdp_real": ("ACT_GDP_REAL", 1),    # NA lag 1Q
        "beai_copy_act_ip": ("ACT_IP", 0),                # Monthly lag 6w (at origin: 0Q)
        "beai_copy_act_emp": ("ACT_EMP", 1),              # NA lag 1Q (Q-04 quarterly fallback)
        "beai_copy_act_hours": ("ACT_HOURS", 1),          # NA lag 1Q (quarterly total hours)
        "beai_copy_act_rinc": ("ACT_RINC", 1),            # NA lag 1Q (real income ex transfers)
        "beai_copy_act_cons": ("ACT_CONS", 1),            # NA lag 1Q (quarterly real PCE)
        "beai_copy_act_retail": ("ACT_RETAIL", 0),        # Monthly lag 6w (at origin: 0Q)
        "beai_copy_act_inv": ("ACT_INV", 1),              # NA lag 1Q (constructed non-res fixed)
    }

    for col_name, (src_col, lag_q) in core_beai_lags.items():
        if src_col in g.columns:
            s_shifted = g[src_col].shift(lag_q)
            out[col_name] = s_shifted.reindex(target_window)
        else:
            out[col_name] = np.nan

    # -------------------------------------------------------------------------
    # 2. Panel Predictors (non-core panel series)
    # Lags applied under C-05:
    #   - NA / BIS: 1 quarter lag
    #   - Monthly: 6 weeks (0Q shift at origin)
    #   - Market: 0 days (0Q shift at origin)
    #   - Survey: 4 weeks (0Q shift at origin)
    # -------------------------------------------------------------------------
    # Growth transforms: 100 * (log(x_t) - log(x_{t-1}))
    # Notice: we compute growth on p BEFORE shifting by C-05 availability lag.

    # Q-02 investment components (NA lag: 1 quarter)
    inv_components = {
        "inv_eq": "USA.ACT_INV_EQ.Q.STD",
        "inv_struct": "USA.ACT_INV_STRUCT.Q.STD",
        "inv_ipp": "USA.ACT_INV_IPP.Q.STD",
        "inv_defl": "USA.ACT_INV_DEFL.Q.STD",
    }
    for feat_name, src_key in inv_components.items():
        if src_key in p.columns:
            s_growth = 100.0 * np.log(p[src_key]).diff(1)
            out[feat_name] = s_growth.shift(1).reindex(target_window)
        else:
            out[feat_name] = np.nan

    # Monthly activity predictor copies (Monthly lag 6w -> 0Q shift)
    monthly_activity = {
        "emp_estab": "USA.ACT_EMP.M.ESTAB",
        "emp_lfs": "USA.ACT_EMP.M.LFS",
        "rinc_m": "USA.ACT_RINC.M.US",
    }
    for feat_name, src_key in monthly_activity.items():
        if src_key in p.columns:
            s_growth = 100.0 * np.log(p[src_key]).diff(1)
            out[feat_name] = s_growth.reindex(target_window)
        else:
            out[feat_name] = np.nan

    # Credit / GDP ratio (NA/BIS lag 1Q -> level shifted 1Q)
    if "USA.FIN_CREDIT_GDP.Q.STD" in p.columns:
        out["credit_gdp"] = p["USA.FIN_CREDIT_GDP.Q.STD"].shift(1).reindex(target_window)
    else:
        out["credit_gdp"] = np.nan

    # Equity return (Market lag 0 -> 0Q shift)
    if "USA.FIN_EQUITY.M.STD" in p.columns:
        s_growth = 100.0 * np.log(p["USA.FIN_EQUITY.M.STD"]).diff(1)
        out["equity"] = s_growth.reindex(target_window)
    else:
        out["equity"] = np.nan

    # House price indices
    if "USA.FIN_HOUSEPRICE.M.US_CS" in p.columns:
        # Case-Shiller monthly lag 6w -> 0Q shift
        s_growth = 100.0 * np.log(p["USA.FIN_HOUSEPRICE.M.US_CS"]).diff(1)
        out["houseprice_cs"] = s_growth.reindex(target_window)
    else:
        out["houseprice_cs"] = np.nan

    if "USA.FIN_HOUSEPRICE.Q.OECD_BIS" in p.columns:
        # FHFA quarterly lag 1Q -> shift 1Q
        s_growth = 100.0 * np.log(p["USA.FIN_HOUSEPRICE.Q.OECD_BIS"]).diff(1)
        out["houseprice_oecd"] = s_growth.shift(1).reindex(target_window)
    else:
        out["houseprice_oecd"] = np.nan

    # Interest rates (Market lag 0 -> unscaled level)
    rates = {
        "rate_long": "USA.FIN_LONG.M.STD",
        "rate_policy": "USA.FIN_POLICY.M.STD",
        "rate_short": "USA.FIN_SHORT.M.STD",
    }
    for feat_name, src_key in rates.items():
        if src_key in p.columns:
            out[feat_name] = p[src_key].reindex(target_window)
        else:
            out[feat_name] = np.nan

    # Unemployment rate (Monthly lag 6w -> level)
    if "USA.LAB_UNEMP.M.STD" in p.columns:
        out["unemp"] = p["USA.LAB_UNEMP.M.STD"].reindex(target_window)
    else:
        out["unemp"] = np.nan

    # CPI inflation (Monthly lag 6w -> YoY growth)
    if "USA.PRC_CPI.M.STD" in p.columns:
        out["cpi"] = (100.0 * np.log(p["USA.PRC_CPI.M.STD"]).diff(4)).reindex(target_window)
    else:
        out["cpi"] = np.nan

    # Confidence surveys (Survey lag 4w -> level)
    if "USA.SEN_BCI.M.STD" in p.columns:
        out["bci"] = p["USA.SEN_BCI.M.STD"].reindex(target_window)
    else:
        out["bci"] = np.nan

    if "USA.SEN_CCI.M.STD" in p.columns:
        out["cci"] = p["USA.SEN_CCI.M.STD"].reindex(target_window)
    else:
        out["cci"] = np.nan

    # Term spread: 10Y - 3M (Market lag 0 -> level)
    if "rate_long" in out.columns and "rate_short" in out.columns:
        out["term_spread_10y_3m"] = out["rate_long"] - out["rate_short"]

    # Reset index to string column 'quarter'
    out = out.reset_index()
    out = out.rename(columns={"index": "quarter"})
    out["quarter"] = out["quarter"].astype(str)

    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Build USA feature table (Lane 2A)")
    parser.add_argument("--panel", type=Path, default=CLEAN_DIR / "USA_panel.csv")
    parser.add_argument("--growth", type=Path, default=CLEAN_DIR / "USA_growth.parquet")
    parser.add_argument("--out-dir", type=Path, default=FEATURES_DIR)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    if not args.panel.exists():
        raise FileNotFoundError(f"Clean panel not found: {args.panel}")
    if not args.growth.exists():
        raise FileNotFoundError(f"Clean growth not found: {args.growth}")

    panel_df = pd.read_csv(args.panel)
    growth_df = pd.read_parquet(args.growth)

    features = build_features(panel_df, growth_df)
    validate_table(features)

    parquet_path = args.out_dir / "dataset.parquet"
    manifest_path = args.out_dir / "manifest.json"

    features.to_parquet(parquet_path, index=False)

    cols_list = [c for c in features.columns if c != "quarter"]
    manifest = {
        "n_rows": int(len(features)),
        "n_columns": int(len(cols_list)),
        "quarter_start": str(features["quarter"].iloc[0]),
        "quarter_end": str(features["quarter"].iloc[-1]),
        "columns": cols_list,
    }
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)

    print(f"Features written: {parquet_path} ({len(features)} rows x {len(cols_list)} predictors)")
    print(f"Manifest written: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
