"""Single runtime source for the study window.

``config/scope.yaml`` is the editable runtime configuration; ``spec.py`` is the
documentation source used by the Phase 2 workbook.  These helpers keep the
collector, harmoniser and label builder from drifting apart, and the test suite
checks the two sources agree.
"""
from __future__ import annotations

import calendar
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parents[2]
SCOPE_PATH = PROJECT / "config" / "scope.yaml"


def load_scope(path: Path | None = None) -> dict:
    with (path or SCOPE_PATH).open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _label_parts(label: str) -> tuple[int, int]:
    year, quarter = label[:4], label[-1]
    if len(label) != 6 or label[4] != "Q" or quarter not in "1234":
        raise ValueError(f"expected a YYYYQn label, got {label!r}")
    return int(year), int(quarter)


def study_window(scope: dict | None = None) -> tuple[str, str]:
    """Return the reporting window as ``(start, end)`` quarter labels."""
    window = (scope or load_scope())["window"]
    return str(window["start"]), str(window["end"])


def estimation_start(scope: dict | None = None) -> str:
    """Return the first quarter of the estimation sample."""
    window = (scope or load_scope())["window"]
    return str(window.get("estimation_start", window["start"]))


def quarter_count(start: str | None = None, end: str | None = None) -> int:
    if start is None or end is None:
        start, end = study_window()
    start_year, start_q = _label_parts(start)
    end_year, end_q = _label_parts(end)
    return 4 * (end_year - start_year) + (end_q - start_q) + 1


def window_bounds(start: str | None = None, end: str | None = None) -> tuple[str, str]:
    """Return ISO dates for the first and last day of the reporting window."""
    if start is None or end is None:
        start, end = study_window()
    start_year, start_q = _label_parts(start)
    end_year, end_q = _label_parts(end)
    start_month = 3 * start_q - 2
    end_month = 3 * end_q
    end_day = calendar.monthrange(end_year, end_month)[1]
    return (
        f"{start_year:04d}-{start_month:02d}-01",
        f"{end_year:04d}-{end_month:02d}-{end_day:02d}",
    )
