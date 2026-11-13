"""Coverage gate and eligibility rules (BUILD_CONTRACT C-03, DECISIONS D-R04).

Rules:
- Target window: 1990Q1-2025Q4 = 144 quarters (>=70% = >=101 quarters).
- A country is BEAI-eligible only with >=6 of 8 core indicators, each covering >=70%
  of the reporting window.
- A quarter is datable only if >=4 core indicators are available.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np
import pandas as pd

CORE_INDICATORS = [
    "ACT_GDP_REAL",
    "ACT_IP",
    "ACT_EMP",
    "ACT_HOURS",
    "ACT_RINC",
    "ACT_CONS",
    "ACT_RETAIL",
    "ACT_INV",
]


@dataclass
class IndicatorCoverage:
    indicator: str
    quarters_present: int
    window_quarters: int
    coverage_pct: float
    passed: bool


@dataclass
class CoverageGateResult:
    passed: bool
    n_passing_indicators: int
    min_required: int
    indicators: list[IndicatorCoverage] = field(default_factory=list)
    datable_quarters_count: int = 0
    total_window_quarters: int = 0
    missing_indicators: list[str] = field(default_factory=list)
    failing_indicators: list[str] = field(default_factory=list)

    def summary_table(self) -> pd.DataFrame:
        rows = [
            {
                "indicator": c.indicator,
                "quarters": c.quarters_present,
                "window": c.window_quarters,
                "coverage_pct": c.coverage_pct,
                "pass_70pct": c.passed,
            }
            for c in self.indicators
        ]
        return pd.DataFrame(rows)


def check_coverage_gate(
    growth_or_panel: pd.DataFrame,
    window: pd.PeriodIndex | Sequence[str] | None = None,
    *,
    min_core_indicators: int = 6,
    min_quarters_pct: float = 0.70,
    min_indicators_per_quarter: int = 4,
    core_indicators: list[str] | None = None,
) -> CoverageGateResult:
    """Evaluate C-03 coverage gate on quarterly core growth or level matrix.

    Parameters
    ----------
    growth_or_panel: pd.DataFrame
        Quarterly data indexed by PeriodIndex or quarter strings ('1990Q1', etc.).
    window: PeriodIndex or list of quarter strings, optional
        Reporting window. Default is 1990Q1 to 2025Q4 (144 quarters).
    min_core_indicators: int
        Minimum passing indicators required (default: 6 of 8).
    min_quarters_pct: float
        Minimum window fraction required per indicator (default: 0.70).
    min_indicators_per_quarter: int
        Minimum indicators required to date a single quarter (default: 4).
    core_indicators: list[str], optional
        Core indicator IDs. Defaults to the eight C-01 core indicators.
    """
    if core_indicators is None:
        core_indicators = list(CORE_INDICATORS)

    if window is None:
        window_idx = pd.period_range("1990Q1", "2025Q4", freq="Q")
    elif isinstance(window, pd.PeriodIndex):
        window_idx = window
    else:
        window_idx = pd.PeriodIndex(list(window), freq="Q")

    # Align frame index to PeriodIndex if strings
    frame = growth_or_panel.copy()
    if not isinstance(frame.index, pd.PeriodIndex):
        try:
            frame.index = pd.PeriodIndex(frame.index, freq="Q")
        except Exception:
            pass

    # Window slice
    in_win = frame.reindex(window_idx)
    n_win = len(window_idx)
    threshold_quarters = int(np.ceil(min_quarters_pct * n_win))

    ind_results: list[IndicatorCoverage] = []
    missing_ind: list[str] = []
    failing_ind: list[str] = []
    n_passed = 0

    for ind in core_indicators:
        if ind not in in_win.columns:
            missing_ind.append(ind)
            ind_results.append(
                IndicatorCoverage(
                    indicator=ind,
                    quarters_present=0,
                    window_quarters=n_win,
                    coverage_pct=0.0,
                    passed=False,
                )
            )
            failing_ind.append(ind)
            continue

        n_pres = int(in_win[ind].notna().sum())
        cov_pct = round(n_pres / n_win, 4) if n_win > 0 else 0.0
        passed = n_pres >= threshold_quarters
        if passed:
            n_passed += 1
        else:
            failing_ind.append(ind)

        ind_results.append(
            IndicatorCoverage(
                indicator=ind,
                quarters_present=n_pres,
                window_quarters=n_win,
                coverage_pct=cov_pct,
                passed=passed,
            )
        )

    # Check quarters datability (>= min_indicators_per_quarter)
    avail_cols = [c for c in core_indicators if c in in_win.columns]
    if avail_cols:
        datable_quarters = int((in_win[avail_cols].notna().sum(axis=1) >= min_indicators_per_quarter).sum())
    else:
        datable_quarters = 0

    gate_passed = n_passed >= min_core_indicators

    return CoverageGateResult(
        passed=gate_passed,
        n_passing_indicators=n_passed,
        min_required=min_core_indicators,
        indicators=ind_results,
        datable_quarters_count=datable_quarters,
        total_window_quarters=n_win,
        missing_indicators=missing_ind,
        failing_indicators=failing_ind,
    )
