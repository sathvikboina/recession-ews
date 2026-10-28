#!/usr/bin/env python3
"""Compare the USA BEAI label with the NBER chronology.

External chronologies are plausibility checks only (BUILD_CONTRACT C-04, FW-06):
they are never targets, features or training labels. This script quantifies the
agreement and lists every discrepancy so a human can judge it.

Outputs
-------
outputs/results/USA_vs_NBER.md     readable report
outputs/results/USA_vs_NBER.csv    quarter-level joined table
outputs/results/USA_episode_match.csv
outputs/results/USA_robustness.csv

Run:
    python scripts/04_compare_nber.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from ews.labels import build as build_label  # noqa: E402


def runs(flag: pd.Series) -> list[tuple[str, str]]:
    """Contiguous runs of 1 as (first, last) quarter strings."""
    out = []
    start = None
    prev = None
    for q, v in flag.items():
        if v == 1 and start is None:
            start = q
        if v == 0 and start is not None:
            out.append((str(start), str(prev)))
            start = None
        prev = q
    if start is not None:
        out.append((str(start), str(prev)))
    return out


def overlaps(a: tuple[str, str], b: tuple[str, str]) -> int:
    sa, ea = pd.Period(a[0], "Q"), pd.Period(a[1], "Q")
    sb, eb = pd.Period(b[0], "Q"), pd.Period(b[1], "Q")
    return max(0, min(ea, eb).ordinal - max(sa, sb).ordinal + 1)


def diff_q(a: str, b: str) -> int:
    return pd.Period(a, "Q").ordinal - pd.Period(b, "Q").ordinal


def main() -> int:
    outdir = PROJECT / "outputs" / "results"
    outdir.mkdir(parents=True, exist_ok=True)

    labels = pd.read_csv(PROJECT / "outputs" / "labels" / "USA_labels.csv", index_col=0)
    labels.index = pd.PeriodIndex(labels.index, freq="Q")
    panel = pd.read_parquet(PROJECT / "data" / "clean" / "USA_levels.parquet")
    nber = panel["USA.NBER.Q"].reindex(labels.index).fillna(0).astype(int)

    joined = labels.copy()
    joined["NBER"] = nber
    joined.index.name = "quarter"
    joined.to_csv(outdir / "USA_vs_NBER.csv", float_format="%.6f")

    # ---- quarter-level confusion matrix ---------------------------------
    tp = int(((joined.R == 1) & (joined.NBER == 1)).sum())
    fp = int(((joined.R == 1) & (joined.NBER == 0)).sum())
    fn = int(((joined.R == 0) & (joined.NBER == 1)).sum())
    tn = int(((joined.R == 0) & (joined.NBER == 0)).sum())
    precision = tp / (tp + fp) if tp + fp else float("nan")
    recall = tp / (tp + fn) if tp + fn else float("nan")
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else float("nan")
    accuracy = (tp + tn) / len(joined)

    # ---- episode matching -----------------------------------------------
    nber_eps = runs(nber)
    ep_table = pd.read_csv(PROJECT / "outputs" / "labels" / "USA_episodes.csv")
    # label episodes are peak->trough pairs; the flagged region is peak+1..trough
    label_eps = [
        (row["peak"], row["trough"])
        for _, row in ep_table[ep_table["kept"]].iterrows()
    ]
    # USRECQ flags the period *after* the peak, so the NBER peak quarter is the
    # one before the first flagged quarter. Report both to avoid a one-quarter
    # artificial lead in the comparison.
    def peak_of(run: tuple[str, str]) -> str:
        return str(pd.Period(run[0], "Q") - 1)

    rows = []
    for nep in nber_eps:
        best, best_ov = None, 0
        for lep in label_eps:
            ov = overlaps(nep, lep)
            if ov > best_ov:
                best, best_ov = lep, ov
        rows.append(
            {
                "nber_peak": peak_of(nep),
                "nber_trough": nep[1],
                "nber_flag_start": nep[0],
                "nber_len": overlaps(nep, nep),
                "label_peak": best[0] if best else "",
                "label_trough": best[1] if best else "",
                "overlap_quarters": best_ov,
                "matched": bool(best_ov > 0),
                "peak_diff_q": diff_q(best[0], peak_of(nep)) if best else None,
                "trough_diff_q": diff_q(best[1], nep[1]) if best else None,
            }
        )
    match = pd.DataFrame(rows)

    false_rows = []
    for lep in label_eps:
        if not any(overlaps(lep, nep) > 0 for nep in nber_eps):
            false_rows.append({"label_peak": lep[0], "label_trough": lep[1], "length": overlaps(lep, lep)})
    false_eps = pd.DataFrame(false_rows, columns=["label_peak", "label_trough", "length"])
    match.to_csv(outdir / "USA_episode_match.csv", index=False)
    false_eps.to_csv(outdir / "USA_false_episodes.csv", index=False)

    # ---- robustness runs (C-02) -----------------------------------------
    growth = pd.read_parquet(PROJECT / "data" / "clean" / "USA_growth.parquet")
    variants = [
        ("baseline", dict(min_phase=2, min_cycle=5, diffusion_gate=0.50)),
        ("min_phase=3", dict(min_phase=3, min_cycle=5, diffusion_gate=0.50)),
        ("diffusion=0.60", dict(min_phase=2, min_cycle=5, diffusion_gate=0.60)),
    ]
    rob = []
    for name, kw in variants:
        r = build_label(growth, **kw)
        eps = r.episodes
        eps = eps[eps["peak"].isin([str(q) for q in labels.index])] if len(eps) else eps
        kept = eps[eps["kept"]] if len(eps) else eps
        rob.append(
            {
                "variant": name,
                "candidate_episodes": int(len(eps)),
                "kept_episodes": int(len(kept)),
                "kept_dates": "; ".join(f"{a}->{b}" for a, b in zip(kept["peak"], kept["trough"])) if len(kept) else "",
            }
        )
    # pre-COVID estimation sample: if the dates for 1990/2001/2008 move when the
    # 2020 observations are removed, the label is being driven by the outlier.
    pre = growth.loc[:"2019Q4"]
    rp = build_label(pre, min_phase=2, min_cycle=5, diffusion_gate=0.50)
    pe = rp.episodes
    pe = pe[pe["peak"].isin([str(q) for q in labels.index])] if len(pe) else pe
    pe = pe[pe["kept"]] if len(pe) else pe
    rob.append(
        {
            "variant": "sample ends 2019Q4",
            "candidate_episodes": int(len(rp.episodes)),
            "kept_episodes": int(len(pe)),
            "kept_dates": "; ".join(f"{a}->{b}" for a, b in zip(pe["peak"], pe["trough"])) if len(pe) else "",
        }
    )
    rob_df = pd.DataFrame(rob)
    rob_df.to_csv(outdir / "USA_robustness.csv", index=False)

    # ---- Label B (technical GDP) cross-check ----------------------------
    gdp = growth["ACT_GDP_REAL"]
    neg = gdp < 0
    label_b = (neg & (neg.shift(1) | neg.shift(-1))).astype(int).reindex(labels.index).fillna(0).astype(int)
    lb_eps = runs(label_b)
    pd.DataFrame({"quarter": label_b.index.astype(str), "label_b": label_b.to_numpy()}).to_csv(
        outdir / "USA_labelB.csv", index=False
    )
    lb_matched = sum(1 for nep in nber_eps if any(overlaps(nep, lep) > 0 for lep in lb_eps))

    # ---- markdown report -------------------------------------------------
    lines = [
        "# USA BEAI label vs NBER chronology",
        "",
        f"Window {labels.index[0]}–{labels.index[-1]} ({len(labels)} quarters).",
        "NBER = `USRECQ` (period after peak through trough). Label = DFM factor -> BBQ -> diffusion >= 0.50.",
        "",
        "## Quarter-level agreement",
        "",
        "| | NBER 1 | NBER 0 |",
        "|---|---:|---:|",
        f"| label 1 | {tp} | {fp} |",
        f"| label 0 | {fn} | {tn} |",
        "",
        f"- accuracy {accuracy:.3f} · precision {precision:.3f} · recall {recall:.3f} · F1 {f1:.3f}",
        f"- recession quarters: NBER {tp + fn}, label {tp + fp}",
        "",
        "## Episode matching",
        "",
        "| NBER peak–trough | recession quarters | label peak–trough | overlap | peak diff | trough diff |",
        "|---|---:|---|---:|---:|---:|",
    ]
    for _, r in match.iterrows():
        lines.append(
            f"| {r.nber_peak}–{r.nber_trough} | {r.nber_len} | "
            f"{r.label_peak or '—'}–{r.label_trough or '—'} | {r.overlap_quarters} | "
            f"{r.peak_diff_q if r.peak_diff_q is not None else '—'} | "
            f"{r.trough_diff_q if r.trough_diff_q is not None else '—'} |"
        )
    lines += [
        "",
        f"Matched {int(match.matched.sum())}/{len(match)} NBER episodes; "
        f"{len(false_eps)} label episode(s) with no NBER counterpart.",
        "",
        "## Retained label episodes",
        "",
        "| peak | trough | duration | depth (SD) | diffusion | review flag |",
        "|---|---|---:|---:|---:|---|",
    ]
    eps = pd.read_csv(PROJECT / "outputs" / "labels" / "USA_episodes.csv")
    for _, r in eps[eps["kept"]].iterrows():
        lines.append(
            f"| {r['peak']} | {r['trough']} | {int(r['duration'])} | {r['depth_sd']:.3f} | "
            f"{r['diffusion']:.3f} | {'yes' if r['review_flag'] else 'no'} |"
        )
    lines += [
        "",
        "## Rejected candidate episodes",
        "",
        "| peak | trough | duration | depth (SD) | diffusion | reason |",
        "|---|---|---:|---:|---:|---|",
    ]
    for _, r in eps[~eps["kept"]].iterrows():
        reason = "diffusion < 0.50" if r["diffusion"] < 0.50 else "other"
        lines.append(
            f"| {r['peak']} | {r['trough']} | {int(r['duration'])} | {r['depth_sd']:.3f} | "
            f"{r['diffusion']:.3f} | {reason} |"
        )
    lines += [
        "",
        "## Robustness",
        "",
        "| variant | candidates | kept | kept dates |",
        "|---|---:|---:|---|",
    ]
    for _, r in rob_df.iterrows():
        lines.append(f"| {r.variant} | {int(r.candidate_episodes)} | {int(r.kept_episodes)} | {r.kept_dates} |")
    lines += [
        "",
        "## Label B (technical GDP) cross-check",
        "",
        "Two consecutive quarters of negative real GDP growth, no factor, no gate:",
        "",
        f"- episodes: {', '.join(f'{a}–{b}' for a, b in lb_eps) if lb_eps else 'none'}",
        f"- NBER episodes caught: {lb_matched}/{len(nber_eps)}",
        "- Label B is deliberately crude; it is a robustness label, not the primary target.",
    ]
    lines += [
        "",
        "## Reading the discrepancies",
        "",
        "- A label peak one quarter before the NBER peak is a boundary convention: the NBER date is the",
        "  last quarter of expansion, and a quarterly factor can turn down inside that quarter.",
        "- A label trough one quarter after the NBER trough means the factor stayed below its previous",
        "  peak for one extra quarter; the contraction end is still inside the same episode.",
        "- Episodes rejected by the diffusion gate are listed above with their diffusion value, not hidden.",
    ]
    (outdir / "USA_vs_NBER.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"accuracy {accuracy:.3f}  precision {precision:.3f}  recall {recall:.3f}  F1 {f1:.3f}")
    print(f"NBER episodes {len(nber_eps)}  matched {int(match.matched.sum())}  false {len(false_eps)}")
    print(f"written: {outdir / 'USA_vs_NBER.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
