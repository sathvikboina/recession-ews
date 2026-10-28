"""BEAI label construction (Pipeline A)."""

from .build import LabelResult, build
from .dfm import FactorResult, estimate_factor

__all__ = ["LabelResult", "FactorResult", "build", "estimate_factor"]
