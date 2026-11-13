"""Episode-id renumbering for the reporting window.

``build()`` numbers episodes over the whole estimation sample (1960 onward).
The frozen label reports 1990Q1-2025Q4, so ``USA_labels.csv`` and
``USA_episodes.csv`` must use the same 1..k window ids. Keeping the mapping in
one helper prevents the two frozen artefacts from drifting apart.
"""
from __future__ import annotations

import pandas as pd


def renumber_window_episodes(
    frame: pd.DataFrame,
    episodes: pd.DataFrame,
    window,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Renumber kept episodes in ``window`` to 1..k and apply the same ids.

    Rejected candidates keep id 0, matching ``build.py``'s convention. The
    frame is copied so the caller's result object is not mutated.
    """
    frame = frame.copy()
    episodes = episodes.copy()
    window_keys = [str(q) for q in window]

    if len(episodes):
        episodes = episodes[episodes["peak"].isin(window_keys)].reset_index(drop=True)

    if len(episodes) and "episode_id" in episodes.columns:
        kept = episodes[episodes["kept"]].sort_values("peak")
        mapping = {int(old): new for new, old in enumerate(kept["episode_id"].tolist(), 1)}
        episodes["episode_id"] = (
            episodes["episode_id"].map(lambda value: mapping.get(int(value), 0) if pd.notna(value) else 0).astype(int)
        )
        if "episode_id" in frame.columns:
            frame["episode_id"] = (
                frame["episode_id"].map(lambda value: mapping.get(int(value), 0) if pd.notna(value) else 0).astype(int)
            )

    return frame, episodes
