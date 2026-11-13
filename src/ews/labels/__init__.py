"""BEAI label construction (Pipeline A)."""

from .build import LabelResult, build
from .coverage import (
    CORE_INDICATORS,
    CoverageGateResult,
    IndicatorCoverage,
    check_coverage_gate,
)
from .dfm import FactorResult, estimate_factor

__all__ = [
    "LabelResult",
    "FactorResult",
    "build",
    "estimate_factor",
    "check_coverage_gate",
    "CoverageGateResult",
    "IndicatorCoverage",
    "CORE_INDICATORS",
]
