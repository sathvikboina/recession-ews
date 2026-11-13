#!/usr/bin/env python3
"""Invariants for the BEAI label pipeline.

These are software invariants, not economic validation. Economic credibility comes
from `outputs/results/USA_vs_NBER.md`, not from this file.

Runs under pytest or standalone:
    python tests/test_labels.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from ews.labels import bbq, build  # noqa: E402
from ews.labels.diffusion import deterioration_share, episode_diffusion  # noqa: E402


def _cycle(n: int = 60, period: int = 20) -> pd.Series:
    idx = pd.period_range("2000Q1", periods=n, freq="Q")
    t = np.arange(n)
    y = 100 + 10 * np.sin(2 * np.pi * t / period) + 0.1 * t
    return pd.Series(y, index=idx)


def _skip(reason: str) -> None:
    """Skip visibly under pytest; print a skip line when run standalone."""
    try:
        import pytest
    except ImportError:  # pragma: no cover - pytest is a dev dependency
        print(f"  skip  {reason}")
        return
    pytest.skip(reason)


def test_bbq_finds_known_cycle() -> None:
    y = _cycle()
    tps = bbq.find_turning_points(y, min_phase=2, min_cycle=5, censor=2)
    assert tps, "no turning points found"
    # alternating by construction
    assert all(a.kind != b.kind for a, b in zip(tps, tps[1:]))
    peaks = [t for t in tps if t.kind == "peak"]
    troughs = [t for t in tps if t.kind == "trough"]
    assert peaks and troughs
    assert max(t.value for t in peaks) > min(t.value for t in troughs)
    # a 20-quarter cycle over 60 quarters cannot be dated more than ~4 times
    assert 2 <= len(peaks) <= 5


def test_bbq_respects_min_phase_and_cycle() -> None:
    y = _cycle(n=120, period=24)
    tps = bbq.find_turning_points(y, min_phase=2, min_cycle=5, censor=2)
    for a, b in zip(tps, tps[1:]):
        assert b.index - a.index >= 2
    for a, b in zip(tps, tps[2:]):
        assert b.index - a.index >= 5


def test_bbq_censors_endpoints() -> None:
    y = _cycle()
    tps = bbq.find_turning_points(y, censor=2)
    assert all(2 <= t.index < len(y) - 2 for t in tps)


def test_recession_flag_is_peak_plus_one_through_trough() -> None:
    idx = pd.period_range("2000Q1", periods=8, freq="Q")
    ep = bbq.Episode("2001Q1", "2001Q4", 4, 7, 3, 1.0, 1.0)
    flag = bbq.recession_flag(idx, [ep])
    assert flag.iloc[4] == 0, "peak quarter is still expansion"
    assert list(flag.iloc[5:8]) == [1, 1, 1], "peak+1 .. trough inclusive"
    assert flag.iloc[3] == 0 and flag.iloc[0] == 0


def test_diffusion_share_ignores_missing() -> None:
    idx = pd.period_range("2000Q1", periods=2, freq="Q")
    g = pd.DataFrame({"a": [-1.0, 1.0], "b": [-1.0, np.nan], "c": [np.nan, -1.0]}, index=idx)
    share = deterioration_share(g)
    assert share.iloc[0] == 1.0          # a and b both down, c missing
    assert share.iloc[1] == 0.5          # c down, b missing, a up -> 1 of 2
    assert episode_diffusion(g, 0, 1) == 0.5


def test_diffusion_gate_drops_weak_episode() -> None:
    # three contraction quarters, but only one of eight indicators weakens
    idx = pd.period_range("2000Q1", periods=24, freq="Q")
    g = pd.DataFrame({f"s{i}": np.full(len(idx), 0.5) for i in range(8)}, index=idx)
    g.iloc[9:12, 0] = -1.0
    d = episode_diffusion(g, 8, 11)
    assert d == 1 / 8, f"expected 0.125, got {d}"
    assert d < 0.5


def test_frozen_labels_present_and_sane() -> None:
    path = PROJECT / "outputs" / "labels" / "USA_labels.csv"
    assert path.exists(), "the frozen labels artefact is tracked and must be present"
    df = pd.read_csv(path, index_col=0)
    assert len(df) == 147
    assert df.index[0] == "1990Q1" and df.index[-1] == "2026Q3"
    assert set(df["R"].unique()) <= {0, 1}
    # every flagged quarter belongs to an episode id and vice versa
    assert ((df["R"] == 1) == (df["episode_id"] > 0)).all()
    # episode ids are contiguous starting at 1 inside the frozen window
    ids = sorted(int(x) for x in df.loc[df["R"] == 1, "episode_id"].unique())
    assert ids == list(range(1, len(ids) + 1))
    # a flagged run never starts in the first quarter
    assert df["R"].iloc[0] == 0


def test_label_pipeline_does_not_use_nber() -> None:
    path = PROJECT / "data" / "clean" / "USA_growth.parquet"
    if not path.exists():
        _skip("data/clean is git-ignored; run `make fetch && make harmonize` first")
        return
    growth = pd.read_parquet(path)
    assert "USA.NBER.Q" not in growth.columns
    assert "NBER" not in "".join(growth.columns)
    result = build(growth, country="USA")
    assert result.diagnostics["method"] in {"dfm", "pca_em"}
    assert set(result.frame["R"].unique()) <= {0, 1}


def test_build_accepts_a_panel_without_validation_series() -> None:
    """The label builder consumes activity growth only, never a chronology."""
    base = _cycle(n=120, period=24)
    growth = pd.DataFrame(
        {
            f"ACT_{i}": base * (1.0 + 0.02 * i) + np.sin(np.arange(120) / (3 + i))
            for i in range(8)
        },
        index=base.index,
    )
    assert "NBER" not in "".join(growth.columns)
    result = build(growth, method="pca_em", country="USA")
    assert result.diagnostics["method"] == "pca_em"
    assert result.frame["R"].isin([0, 1]).all()
    assert result.frame.columns.is_unique


def test_episode_peak_is_before_trough() -> None:
    path = PROJECT / "outputs" / "labels" / "USA_episodes.csv"
    assert path.exists(), "the frozen episode artefact is tracked and must be present"
    eps = pd.read_csv(path)
    assert not eps.empty
    for _, r in eps.iterrows():
        assert r["duration"] >= 2
        assert r["trough_index"] > r["peak_index"]


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  ok    {name}")
            except AssertionError as exc:
                failures += 1
                print(f"  FAIL  {name}: {exc}")
    print(f"\n{'FAILED' if failures else 'passed'}")
    sys.exit(1 if failures else 0)
