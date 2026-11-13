#!/usr/bin/env python3
"""Dashboard smoke test.

The dashboard is a generated artefact but its generator is source. This test
runs the generator into a temporary directory and checks the page is
self-contained and keeps the exploratory-only warning. It must also work on a
fresh clone where the git-ignored exploratory outputs are absent.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT / "scripts" / "05_dashboard.py"


def test_dashboard_builds_offline(tmp_path):
    out = tmp_path / "index.html"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--out", str(out)],
        cwd=PROJECT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    page = out.read_text(encoding="utf-8")

    assert "<!doctype html>" in page
    assert "USA Recession Early-Warning" in page
    assert "labels-v3" in page
    assert "exploratory only" in page
    assert "pre-registered C-13 result" in page
    assert "C-13" in page

    # Self-contained: no external script or stylesheet references.
    assert "<script src=" not in page
    assert "<link" not in page
    assert "https://" not in page
