"""Assemble the BEAI label: DFM factor -> BBQ dating -> diffusion gate.

Everything here is country-specific and uses only the eight §11 core indicators
(BUILD_CONTRACT C-01, C-02). No predictor, no external chronology, no fitted
object is shared with Pipeline B.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import bbq
from .diffusion import deterioration_share, episode_diffusion
from .dfm import FactorResult, estimate_factor

PARAMS = {
    "min_phase": 2,
    "min_cycle": 5,
    "censor": 2,
    "diffusion_gate": 0.50,
    "factor_count": 1,
    "depth_review_sd": 0.10,
}


@dataclass
class LabelResult:
    frame: pd.DataFrame
    episodes: pd.DataFrame
    turning_points: pd.DataFrame
    factor: FactorResult
    params: dict = field(default_factory=lambda: dict(PARAMS))
    diagnostics: dict = field(default_factory=dict)


def build(
    growth: pd.DataFrame,
    *,
    min_phase: int = 2,
    min_cycle: int = 5,
    censor: int = 2,
    diffusion_gate: float = 0.50,
    method: str = "dfm",
    country: str = "USA",
) -> LabelResult:
    growth = growth.sort_index()
    factor = estimate_factor(growth, method=method)

    tps = bbq.find_turning_points(
        factor.level, min_phase=min_phase, min_cycle=min_cycle, censor=censor
    )
    raw_episodes = bbq.contraction_episodes(factor.level, tps, min_phase=min_phase)

    share = deterioration_share(growth)
    rows = []
    for ep in raw_episodes:
        d = episode_diffusion(growth, ep.peak_index, ep.trough_index)
        rows.append(
            {
                **ep.as_dict(),
                "diffusion": d,
                "kept": bool(np.isfinite(d) and d >= diffusion_gate),
                "review_flag": bool(ep.depth_sd < PARAMS["depth_review_sd"]),
            }
        )
    episodes = pd.DataFrame(rows)

    kept = [ep for ep, row in zip(raw_episodes, rows) if row["kept"]] if len(rows) else []
    flag = bbq.recession_flag(growth.index, kept)

    frame = pd.DataFrame(
        {
            "factor": factor.factor,
            "level": factor.level,
            "n_available": growth.notna().sum(axis=1),
            "deterioration_share": share,
            "R": flag,
        },
        index=growth.index,
    )
    # episode id: 1..k in chronological order, 0 outside a kept contraction
    episode_id = pd.Series(0, index=growth.index, dtype=int)
    for i, ep in enumerate(kept, 1):
        episode_id.iloc[ep.peak_index + 1 : ep.trough_index + 1] = i
    frame["episode_id"] = episode_id

    if len(episodes):
        kept_ids = []
        k = 0
        for _, row in episodes.iterrows():
            if row["kept"]:
                k += 1
                kept_ids.append(k)
            else:
                kept_ids.append(0)
        episodes["episode_id"] = kept_ids

    diagnostics = {
        "country": country,
        "method": factor.method,
        "converged": factor.converged,
        "loglik": factor.loglik,
        "n_series": factor.n_series,
        "n_quarters": int(growth.shape[0]),
        "n_candidate_episodes": int(len(raw_episodes)),
        "n_kept_episodes": int(len(kept)),
        "factor_notes": factor.notes,
        "params": {
            "min_phase": min_phase,
            "min_cycle": min_cycle,
            "censor": censor,
            "diffusion_gate": diffusion_gate,
        },
        "loadings": {k: round(v, 4) for k, v in factor.loadings.items() if np.isfinite(v)},
    }
    return LabelResult(frame, episodes, bbq.as_frame(tps), factor, dict(PARAMS), diagnostics)
