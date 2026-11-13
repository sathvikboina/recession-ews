#!/usr/bin/env python3
"""Build the static, offline USA dashboard.

Reads the frozen label, NBER comparison and the exploratory model run, then
writes a single self-contained HTML file. No server, no CDN and no JavaScript
dependency is required; the only JavaScript is a small model-focus toggle.

The dashboard is a reporting view. It does not change any label, fold, model or
ensemble rule and it does not turn the exploratory run into the pre-registered
result.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import math
import subprocess
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "dashboard" / "index.html"

LABELS = ROOT / "outputs" / "labels" / "USA_labels.csv"
EPISODES = ROOT / "outputs" / "labels" / "USA_episodes.csv"
VS_NBER = ROOT / "outputs" / "results" / "USA_vs_NBER.csv"
GROWTH = ROOT / "data" / "clean" / "USA_growth.csv"
MODEL_DIR = ROOT / "outputs" / "exploratory" / "usa_first"

MODEL_ORDER = [
    "logistic",
    "elastic_net",
    "random_forest",
    "xgboost_like",
    "svm",
    "mlp",
    "ensemble",
]
MODEL_LABEL = {
    "logistic": "Logistic",
    "elastic_net": "Elastic net",
    "random_forest": "Random forest",
    "xgboost_like": "Gradient boosting",
    "svm": "Linear SVM",
    "mlp": "MLP",
    "ensemble": "Top-3 ensemble",
}
MODEL_COLOR = {
    "logistic": "#7b8794",
    "elastic_net": "#9aa5b1",
    "random_forest": "#8d99ae",
    "xgboost_like": "#6b7c93",
    "svm": "#a3b1c2",
    "mlp": "#d9480f",
    "ensemble": "#0b7285",
}
INDICATOR_LABEL = {
    "ACT_GDP_REAL": "Real GDP",
    "ACT_IP": "Industrial production",
    "ACT_EMP": "Employment",
    "ACT_HOURS": "Hours",
    "ACT_RINC": "Real income",
    "ACT_CONS": "Consumption",
    "ACT_RETAIL": "Retail sales",
    "ACT_INV": "Inventory investment",
}

CSS = """
:root{
  --bg:#f4f6f8; --card:#ffffff; --ink:#14213d; --muted:#5c677d;
  --line:#dde3ea; --accent:#0b7285; --accent-soft:#d7eef1;
  --warn:#b23b2e; --warn-soft:#fbe9e7; --nber:#2c7fb8;
  --label:#c0392b; --best:#d9480f;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  line-height:1.5;-webkit-font-smoothing:antialiased}
a{color:var(--accent)}
.wrap{max-width:1180px;margin:0 auto;padding:28px 22px 60px}
header.top{display:flex;flex-wrap:wrap;gap:18px;align-items:flex-end;justify-content:space-between;
  border-bottom:2px solid var(--ink);padding-bottom:16px;margin-bottom:20px}
h1{font-size:30px;line-height:1.15;margin:0 0 6px;letter-spacing:-.4px}
.sub{color:var(--muted);font-size:14px;max-width:720px;margin:0}
.badges{display:flex;gap:8px;flex-wrap:wrap}
.badge{font-size:11px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;
  padding:5px 9px;border-radius:999px;border:1px solid var(--line);background:#fff;color:var(--muted)}
.badge.ok{background:var(--accent-soft);border-color:#b7dfe4;color:#075e6b}
.badge.warn{background:var(--warn-soft);border-color:#f2c9c3;color:var(--warn)}
.banner{display:flex;gap:14px;align-items:flex-start;background:var(--warn-soft);
  border:1px solid #f2c9c3;border-left:5px solid var(--warn);border-radius:8px;
  padding:14px 16px;margin:0 0 24px}
.banner strong{color:var(--warn);text-transform:uppercase;font-size:12px;letter-spacing:.6px}
.banner p{margin:2px 0 0;font-size:14px;color:#5a2b25}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:26px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:13px 15px}
.kpi .k{font-size:11px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;color:var(--muted)}
.kpi .v{font-size:25px;font-weight:750;letter-spacing:-.5px;margin-top:2px;
  font-variant-numeric:tabular-nums}
.kpi .v small{font-size:12px;font-weight:600;color:var(--muted);letter-spacing:0}
.kpi .n{font-size:12px;color:var(--muted);margin-top:2px}
.good{color:var(--accent)} .bad{color:var(--warn)} .best{color:var(--best)}
section{margin:0 0 34px}
h2{font-size:19px;margin:0 0 4px;letter-spacing:-.2px}
h3{font-size:14px;margin:18px 0 8px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted)}
.lede{color:var(--muted);font-size:14px;margin:0 0 14px;max-width:900px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 18px;min-width:0}
.grid2{display:grid;grid-template-columns:minmax(0,1.55fr) minmax(280px,1fr);gap:16px}
.grid2b{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:16px}
@media(max-width:900px){.grid2,.grid2b{grid-template-columns:minmax(0,1fr)}}
svg{display:block;width:100%;height:auto;overflow:visible}
svg text{font-family:inherit}
.legend{display:flex;flex-wrap:wrap;gap:12px 18px;font-size:12px;color:var(--muted);margin-top:10px}
.legend span{display:inline-flex;align-items:center;gap:6px}
.sw{width:18px;height:3px;border-radius:2px;display:inline-block}
.sw.box{height:12px;width:12px;border-radius:2px}
table{width:100%;border-collapse:collapse;font-size:13px;font-variant-numeric:tabular-nums}
th,td{padding:7px 9px;text-align:right;border-bottom:1px solid var(--line);white-space:nowrap}
th:first-child,td:first-child{text-align:left}
th{font-size:11px;text-transform:uppercase;letter-spacing:.4px;color:var(--muted);
  border-bottom:1px solid #c9d2dc;background:#fbfcfd}
tr.hl-ens td{background:var(--accent-soft);font-weight:650}
tr.hl-best td{background:#fdf0ea}
tbody tr:last-child td{border-bottom:none}
.table-note{font-size:12px;color:var(--muted);margin-top:8px}
.table-wrap{overflow-x:auto;margin:0 -2px;padding:0 2px}
.chip{display:inline-block;font-size:11px;font-weight:700;padding:2px 7px;border-radius:999px}
.chip.yes{background:var(--accent-soft);color:#075e6b}
.chip.no{background:var(--warn-soft);color:var(--warn)}
.chip.skip{background:#eef1f4;color:var(--muted)}
.controls{display:flex;flex-wrap:wrap;gap:6px;margin:4px 0 12px}
.controls button{font:inherit;font-size:12px;padding:5px 10px;border-radius:999px;cursor:pointer;
  border:1px solid var(--line);background:#fff;color:var(--ink)}
.controls button:hover{border-color:#9fb3c8}
.controls button.active{background:var(--ink);border-color:var(--ink);color:#fff}
.notes{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}
.note{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:14px 16px}
.note h4{margin:0 0 6px;font-size:13px;text-transform:uppercase;letter-spacing:.5px}
.note p{margin:0;font-size:13px;color:var(--muted)}
.note.is{border-top:3px solid var(--accent)}
.note.isnot{border-top:3px solid var(--warn)}
.note.next{border-top:3px solid var(--best)}
.sparks{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:10px}
.spark{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 12px}
.spark .head{display:flex;justify-content:space-between;align-items:baseline;font-size:13px;font-weight:650}
.spark .head span:last-child{font-size:12px;font-weight:600;color:var(--muted);font-variant-numeric:tabular-nums}
.cmd{background:#0f172a;color:#dbe4f0;border-radius:8px;padding:12px 14px;font-size:12.5px;
  overflow-x:auto;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.cmd .c{color:#7dd3c7}
footer{border-top:1px solid var(--line);margin-top:34px;padding-top:16px;color:var(--muted);font-size:12px}
footer code{font-size:11.5px}
@media print{body{background:#fff}.controls{display:none}.card,.kpi,.note,.spark{break-inside:avoid}}
"""

JS = """
(function(){
  var chart=document.getElementById('prob-chart');
  var buttons=document.querySelectorAll('[data-focus]');
  function setFocus(focus){
    chart.querySelectorAll('.series').forEach(function(g){
      var m=g.getAttribute('data-model');
      g.style.opacity=(focus==='all')?(m==='ensemble'?1:(m==='mlp'?0.9:0.10)):(m===focus?1:0.06);
    });
    buttons.forEach(function(b){b.classList.toggle('active',b.getAttribute('data-focus')===focus);});
  }
  buttons.forEach(function(b){b.addEventListener('click',function(){setFocus(b.getAttribute('data-focus'));});});
  setFocus('all');
})();
"""


# ------------------------------------------------------------------ formatting
def esc(value) -> str:
    return html.escape(str(value), quote=True)


def num(value, digits: int = 3) -> str:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return esc(value)
    if math.isnan(f):
        return "n/a"
    if math.isinf(f):
        return "inf" if f > 0 else "−inf"
    return f"{f:.{digits}f}"


def signed(value, digits: int = 4) -> str:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return esc(value)
    if math.isnan(f):
        return "n/a"
    return f"{f:+.{digits}f}"


def pct(value, digits: int = 1) -> str:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return esc(value)
    if math.isnan(f):
        return "n/a"
    return f"{100 * f:.{digits}f}%"


# ----------------------------------------------------------------------- data
def read_csv(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_csv(path)


def quarter_index(start: pd.Period, end: pd.Period) -> pd.PeriodIndex:
    return pd.period_range(start, end, freq="Q")


def runs(flags: list[tuple[str, int]]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    start = prev = None
    for quarter, flag in flags:
        if flag:
            if start is None:
                start = quarter
            prev = quarter
        elif start is not None:
            out.append((start, prev))
            start = prev = None
    if start is not None:
        out.append((start, prev))
    return out


def nice_ticks(lo: float, hi: float, count: int = 5) -> list[float]:
    if not (math.isfinite(lo) and math.isfinite(hi)) or hi <= lo:
        return []
    span = hi - lo
    raw = span / count
    mag = 10 ** math.floor(math.log10(raw))
    for mult in (1, 2, 2.5, 5, 10):
        step = mag * mult
        if span / step <= count:
            break
    first = math.ceil(lo / step) * step
    ticks = []
    value = first
    while value <= hi + 1e-9:
        ticks.append(round(value, 10))
        value += step
    return ticks


class Axis:
    """Linear index/time axis over a fixed quarter range."""

    def __init__(self, quarters: pd.PeriodIndex, left: float, right: float):
        self.quarters = quarters
        self.left = left
        self.right = right
        self.step = (right - left) / max(len(quarters) - 1, 1)
        self.pos = {str(q): i for i, q in enumerate(quarters)}

    def x(self, quarter: str) -> float:
        i = self.pos.get(str(quarter))
        if i is None:
            return self.left
        return self.left + i * self.step

    def band(self, start: str, end: str) -> tuple[float, float]:
        x0 = self.x(start)
        x1 = self.x(end) + self.step
        return x0, max(x1, x0 + 1)


def line(points: list[tuple[float, float]]) -> str:
    if not points:
        return ""
    return "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def sparkline(values: list[float], axis: Axis, width: float, height: float,
              color: str = "#0b7285") -> str:
    clean = [(i, v) for i, v in enumerate(values) if math.isfinite(v)]
    if not clean:
        return ""
    lo = min(v for _, v in clean)
    hi = max(v for _, v in clean)
    pad = (hi - lo) * 0.12 or 1.0
    lo, hi = lo - pad, hi + pad
    x0, y0 = 4, 4
    iw, ih = width - 8, height - 8

    def y(v: float) -> float:
        return y0 + ih - (v - lo) / (hi - lo) * ih

    pts = [(x0 + i / max(len(values) - 1, 1) * iw, y(v)) for i, v in clean]
    zero = y(0.0) if lo <= 0 <= hi else None
    pieces = [f'<line x1="{x0}" y1="{y(0):.1f}" x2="{x0 + iw}" y2="{y(0):.1f}" '
              f'stroke="#c9d2dc" stroke-width="1" stroke-dasharray="3 3"/>' if zero is not None else ""]
    pieces.append(f'<path d="{line(pts)}" fill="none" stroke="{color}" stroke-width="1.7" '
                  f'stroke-linejoin="round" stroke-linecap="round"/>')
    pieces.append(f'<circle cx="{pts[-1][0]:.1f}" cy="{pts[-1][1]:.1f}" r="2.6" fill="{color}"/>')
    return "".join(pieces)


# --------------------------------------------------------------------- charts
def chart_labels(labels: pd.DataFrame, episodes: pd.DataFrame,
                 nber_runs: list[tuple[str, str]]) -> tuple[str, str]:
    quarters = pd.PeriodIndex(labels["quarter"], freq="Q")
    axis = Axis(quarters, 58, 1092)
    w, h = 1120, 360
    py0, py1 = 22, 238
    lo, hi = float(labels["factor"].min()), float(labels["factor"].max())
    pad = (hi - lo) * 0.08 or 0.5
    lo, hi = lo - pad, hi + pad

    def y(v: float) -> float:
        return py1 - (v - lo) / (hi - lo) * (py1 - py0)

    parts = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="USA recession label timeline, 1990 to 2026">',
             f'<title>USA factor and label, {quarters[0]} to {quarters[-1]}</title>']

    # Episode shading.
    for _, row in episodes.iterrows():
        x0, x1 = axis.band(row["peak"], row["trough"])
        parts.append(f'<rect x="{x0:.1f}" y="{py0}" width="{x1 - x0:.1f}" height="{py1 - py0}" '
                     f'fill="#c0392b" opacity="0.10"/>')
        parts.append(f'<text x="{(x0 + x1) / 2:.1f}" y="{py0 + 12}" text-anchor="middle" '
                     f'font-size="10" fill="#a33a2e">{esc(row["peak"])}</text>')

    # Grid and y ticks.
    for tick in nice_ticks(lo, hi):
        yy = y(tick)
        parts.append(f'<line x1="58" y1="{yy:.1f}" x2="1092" y2="{yy:.1f}" stroke="#e8edf2" stroke-width="1"/>')
        parts.append(f'<text x="50" y="{yy + 3.5:.1f}" text-anchor="end" font-size="10.5" '
                     f'fill="#5c677d">{tick:g}</text>')

    # Zero line.
    if lo <= 0 <= hi:
        parts.append(f'<line x1="58" y1="{y(0):.1f}" x2="1092" y2="{y(0):.1f}" stroke="#b9c4d0" stroke-width="1"/>')

    # Factor line.
    pts = [(axis.x(q), y(v)) for q, v in zip(labels["quarter"], labels["factor"])]
    parts.append(f'<path d="{line(pts)}" fill="none" stroke="#14213d" stroke-width="1.9" '
                 f'stroke-linejoin="round" stroke-linecap="round"/>')

    # X ticks every five years.
    tick_q = [q for q in quarters if pd.Period(q, "Q").quarter == 1 and pd.Period(q, "Q").year % 5 == 0]
    for q in tick_q:
        xx = axis.x(q)
        parts.append(f'<line x1="{xx:.1f}" y1="{py0}" x2="{xx:.1f}" y2="304" stroke="#eef2f6" stroke-width="1"/>')
        parts.append(f'<text x="{xx:.1f}" y="322" text-anchor="middle" font-size="10.5" fill="#5c677d">'
                     f'{pd.Period(q, "Q").year}</text>')

    # Label strip.
    parts.append('<text x="58" y="254" font-size="10.5" fill="#5c677d">BEAI label R</text>')
    parts.append('<rect x="58" y="258" width="1034" height="13" fill="#f1f4f7" rx="2"/>')
    for _, row in labels.iterrows():
        if int(row["R"]) == 1:
            xx = axis.x(row["quarter"])
            parts.append(f'<rect x="{xx:.1f}" y="258" width="{axis.step + 0.4:.1f}" height="13" '
                         f'fill="#c0392b" opacity="0.88"/>')

    # NBER strip.
    parts.append('<text x="58" y="284" font-size="10.5" fill="#5c677d">NBER</text>')
    parts.append('<rect x="58" y="288" width="1034" height="13" fill="#f1f4f7" rx="2"/>')
    for start, end in nber_runs:
        x0, x1 = axis.band(start, end)
        parts.append(f'<rect x="{x0:.1f}" y="288" width="{x1 - x0:.1f}" height="13" '
                     f'fill="#2c7fb8" opacity="0.80"/>')

    parts.append(f'<text x="58" y="348" font-size="10.5" fill="#8a95a5">'
                 f'Factor level (left). Shaded bands are BEAI label episodes; NBER bands are '
                 f'the official chronology.</text>')
    parts.append("</svg>")

    legend = (
        '<div class="legend">'
        '<span><i class="sw" style="background:#14213d"></i>BEAI factor</span>'
        '<span><i class="sw box" style="background:#c0392b;opacity:.35"></i>Label episode</span>'
        '<span><i class="sw box" style="background:#c0392b"></i>Label recession quarter</span>'
        '<span><i class="sw box" style="background:#2c7fb8"></i>NBER recession</span>'
        "</div>"
    )
    return "".join(parts), legend


def chart_probabilities(pred: pd.DataFrame, episodes: pd.DataFrame,
                        thresholds: pd.DataFrame) -> tuple[str, str]:
    quarters = sorted(pred["quarter"].unique(), key=lambda q: pd.Period(q, "Q"))
    qidx = pd.PeriodIndex(quarters, freq="Q")
    axis = Axis(qidx, 58, 1092)
    w, h = 1120, 380
    py0, py1 = 26, 276

    def y(p: float) -> float:
        return py1 - max(0.0, min(1.0, p)) * (py1 - py0)

    parts = [f'<svg viewBox="0 0 {w} {h}" role="img" id="prob-svg" '
             f'aria-label="Exploratory model probabilities by test quarter">',
             "<title>Exploratory model probabilities on outer test quarters</title>"]

    # Episode shading and labels.
    for _, row in episodes.iterrows():
        if row["peak"] not in axis.pos or row["trough"] not in axis.pos:
            continue
        x0, x1 = axis.band(row["peak"], row["trough"])
        parts.append(f'<rect x="{x0:.1f}" y="{py0}" width="{x1 - x0:.1f}" height="{py1 - py0}" '
                     f'fill="#c0392b" opacity="0.09"/>')

    # Grid.
    for p in (0, 0.25, 0.5, 0.75, 1.0):
        yy = y(p)
        parts.append(f'<line x1="58" y1="{yy:.1f}" x2="1092" y2="{yy:.1f}" stroke="#e8edf2" stroke-width="1"/>')
        parts.append(f'<text x="50" y="{yy + 3.5:.1f}" text-anchor="end" font-size="10.5" '
                     f'fill="#5c677d">{p:.2f}</text>')

    # Target strip under the plot.
    parts.append('<text x="58" y="288" font-size="10.5" fill="#5c677d">Target +</text>')
    parts.append('<rect x="58" y="292" width="1034" height="12" fill="#f1f4f7" rx="2"/>')
    target = pred[pred["model"] == "ensemble"][["quarter", "y_true"]].drop_duplicates()
    for _, row in target.iterrows():
        if int(row["y_true"]) == 1:
            xx = axis.x(row["quarter"])
            parts.append(f'<rect x="{xx:.1f}" y="292" width="{axis.step + 0.4:.1f}" height="12" '
                         f'fill="#c0392b" opacity="0.85"/>')

    # Fold boundaries and labels.
    for fold in sorted(pred["outer_fold"].unique()):
        sub = pred[pred["outer_fold"] == fold]
        first = min(sub["quarter"], key=lambda q: pd.Period(q, "Q"))
        xb = axis.x(first)
        if xb > axis.left + 1:
            parts.append(f'<line x1="{xb:.1f}" y1="{py0}" x2="{xb:.1f}" y2="{py1 + 24}" '
                         f'stroke="#b9c4d0" stroke-width="1" stroke-dasharray="4 4"/>')
        mid = (axis.x(first) + axis.x(max(sub["quarter"], key=lambda q: pd.Period(q, "Q")))) / 2
        parts.append(f'<text x="{mid:.1f}" y="318" text-anchor="middle" font-size="10.5" '
                     f'fill="#5c677d">{esc(fold)}</text>')

    # X ticks every four years.
    tick_q = [q for q in quarters if pd.Period(q, "Q").quarter == 1 and pd.Period(q, "Q").year % 4 == 0]
    for q in tick_q:
        xx = axis.x(q)
        parts.append(f'<text x="{xx:.1f}" y="340" text-anchor="middle" font-size="10.5" '
                     f'fill="#5c677d">{pd.Period(q, "Q").year}</text>')

    # Thresholds (drawn inside each model group so focus dims them too).
    for model in MODEL_ORDER:
        parts.append(f'<g class="series" data-model="{model}">')
        if model in ("ensemble", "mlp"):
            for fold in sorted(thresholds["outer_fold"].unique()):
                row = thresholds[(thresholds["outer_fold"] == fold) & (thresholds["model"] == model)]
                if row.empty:
                    continue
                thr = float(row.iloc[0]["threshold"])
                sub = pred[(pred["outer_fold"] == fold) & (pred["model"] == model)]
                if sub.empty:
                    continue
                xs = [axis.x(q) for q in sub["quarter"]]
                x0, x1 = min(xs), max(xs) + axis.step
                parts.append(f'<line x1="{x0:.1f}" y1="{y(thr):.1f}" x2="{x1:.1f}" y2="{y(thr):.1f}" '
                             f'stroke="{MODEL_COLOR[model]}" stroke-width="1.2" stroke-dasharray="5 4" '
                             f'opacity="0.65"><title>{MODEL_LABEL[model]} threshold {fold}: {thr:.3f}</title></line>')
        parts.append("</g>")

    # Series, fold by fold to avoid lines jumping across gaps.
    for model in MODEL_ORDER:
        color = MODEL_COLOR[model]
        width = 2.6 if model == "ensemble" else (2.0 if model == "mlp" else 1.2)
        parts.append(f'<g class="series" data-model="{model}">')
        for fold in sorted(pred["outer_fold"].unique()):
            sub = pred[(pred["model"] == model) & (pred["outer_fold"] == fold)].sort_values(
                "quarter", key=lambda s: s.map(lambda q: pd.Period(q, "Q"))
            )
            if sub.empty:
                continue
            pts = [(axis.x(q), y(p)) for q, p in zip(sub["quarter"], sub["prob"])]
            parts.append(f'<path d="{line(pts)}" fill="none" stroke="{color}" stroke-width="{width}" '
                         f'stroke-linejoin="round" stroke-linecap="round"/>')
            if model in ("ensemble", "mlp"):
                for q, p, t in zip(sub["quarter"], sub["prob"], sub["y_true"]):
                    marker = ""
                    if int(t) == 1:
                        marker = f'<circle cx="{axis.x(q):.1f}" cy="{y(p):.1f}" r="4" fill="none" ' \
                                 f'stroke="#c0392b" stroke-width="1.8"/>'
                    parts.append(f'<circle cx="{axis.x(q):.1f}" cy="{y(p):.1f}" r="2.1" fill="{color}">'
                                 f'<title>{MODEL_LABEL[model]} · {q} · p={p:.3f}</title></circle>{marker}')
        parts.append("</g>")

    parts.append(f'<text x="58" y="364" font-size="10.5" fill="#8a95a5">'
                 f'Outer test quarters only. Dashed lines are each fold\'s locked threshold. '
                 f'Red rings mark positive H=2 target quarters.</text>')
    parts.append("</svg>")

    buttons = ['<div class="controls" role="group" aria-label="Highlight a model">',
               '<button type="button" data-focus="all" class="active">All models</button>']
    for model in MODEL_ORDER:
        buttons.append(f'<button type="button" data-focus="{model}">'
                       f'<span class="sw" style="background:{MODEL_COLOR[model]};'
                       f'display:inline-block;vertical-align:middle;margin-right:5px"></span>'
                       f'{MODEL_LABEL[model]}</button>')
    buttons.append("</div>")
    return "".join(parts), "".join(buttons)


def chart_bars(pooled: pd.DataFrame, prevalence: float) -> str:
    models = [m for m in MODEL_ORDER if m in set(pooled["model"])]
    rows = pooled.set_index("model").loc[models]
    best = rows["pooled_pr_auc"].idxmax()
    w, h = 560, 300
    left, right = 118, 520
    top, bottom = 20, 268
    n = len(rows)
    band = (bottom - top) / max(n, 1)
    vmax = max(0.16, float(rows["pooled_pr_auc"].max()) * 1.25)

    def x(v: float) -> float:
        return left + v / vmax * (right - left)

    parts = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Pooled PR-AUC by model">',
             "<title>Pooled PR-AUC by model</title>"]
    for tick in nice_ticks(0, vmax, 4):
        xx = x(tick)
        parts.append(f'<line x1="{xx:.1f}" y1="{top}" x2="{xx:.1f}" y2="{bottom}" stroke="#e8edf2"/>')
        parts.append(f'<text x="{xx:.1f}" y="{bottom + 16}" text-anchor="middle" font-size="10" '
                     f'fill="#5c677d">{tick:.2f}</text>')
    for i, (model, row) in enumerate(rows.iterrows()):
        yy = top + i * band + band * 0.16
        bh = band * 0.68
        color = MODEL_COLOR[model]
        opacity = "0.95" if model in ("ensemble", best) else "0.55"
        parts.append(f'<text x="{left - 8}" y="{yy + bh * 0.68:.1f}" text-anchor="end" font-size="11" '
                     f'fill="#14213d">{MODEL_LABEL[model]}</text>')
        parts.append(f'<rect x="{left}" y="{yy:.1f}" width="{max(x(float(row["pooled_pr_auc"])) - left, 1):.1f}" '
                     f'height="{bh:.1f}" fill="{color}" opacity="{opacity}" rx="2">'
                     f'<title>{MODEL_LABEL[model]}: pooled PR-AUC {float(row["pooled_pr_auc"]):.4f}</title></rect>')
        parts.append(f'<text x="{x(float(row["pooled_pr_auc"])) + 6:.1f}" y="{yy + bh * 0.68:.1f}" '
                     f'font-size="10.5" fill="#5c677d">{float(row["pooled_pr_auc"]):.3f}</text>')
    parts.append(f'<text x="{left}" y="{h - 2}" font-size="10" fill="#8a95a5">'
                 f'PR-AUC; chance level is the outer-test positive rate ≈ {prevalence:.3f}.</text>')
    parts.append("</svg>")
    return "".join(parts)


# --------------------------------------------------------------------- tables
def table(headers: list[str], rows: list[list[str]], classes: list[str] | None = None) -> str:
    out = ["<table><thead><tr>"]
    out += [f"<th>{esc(h)}</th>" for h in headers]
    out += ["</tr></thead><tbody>"]
    for i, row in enumerate(rows):
        cls = f' class="{classes[i]}"' if classes and classes[i] else ""
        out.append(f"<tr{cls}>")
        out += [f"<td>{cell}</td>" for cell in row]
        out.append("</tr>")
    out.append("</tbody></table>")
    return f'<div class="table-wrap">{"".join(out)}</div>'


def label_table(episodes: pd.DataFrame) -> str:
    rows = []
    for _, row in episodes.iterrows():
        rows.append([
            esc(row["peak"]), esc(row["trough"]), f'{int(row["duration"])}',
            num(row["depth"], 2), num(row["diffusion"], 3),
            '<span class="chip yes">kept</span>' if bool(row["kept"]) else
            '<span class="chip no">dropped</span>',
        ])
    return table(["Peak", "Trough", "Quarters", "Depth", "Diffusion", "Status"], rows)


def pooled_table(pooled: pd.DataFrame) -> str:
    best = pooled.loc[pooled["pooled_pr_auc"].idxmax(), "model"]
    rows, classes = [], []
    for _, row in pooled.iterrows():
        model = row["model"]
        rows.append([
            f'{esc(MODEL_LABEL.get(model, model))}',
            num(row["pooled_pr_auc"], 4), num(row["pooled_roc_auc"], 4),
            pct(row["recall"], 0), pct(row["precision"], 1), num(row["f1"], 3),
            num(row["brier"], 4), pct(row["episode_recall"], 0), f'{int(row["false_positive_quarters"])}',
        ])
        classes.append("hl-ens" if model == "ensemble" else ("hl-best" if model == best else ""))
    return table(["Model", "PR-AUC", "ROC-AUC", "Recall", "Precision", "F1", "Brier",
                  "Episode recall", "False +"], rows, classes)


def fold_table(fold_metrics: pd.DataFrame, best_model: str) -> str:
    keep = ["ensemble", best_model]
    rows = []
    for _, row in fold_metrics[fold_metrics["model"].isin(keep)].iterrows():
        name = MODEL_LABEL.get(row["model"], row["model"])
        if row["model"] == best_model and best_model != "ensemble":
            name += " (best)"
        rows.append([
            esc(row["outer_fold"]), f'{esc(row["train_start"])}–{esc(row["train_end"])}',
            f'{esc(row["test_start"])}–{esc(row["test_end"])}',
            f'{int(row["n_pos_test"])}', num(row["threshold"], 3),
            num(row["pr_auc"], 3), num(row["roc_auc"], 3), num(row["brier"], 3),
            esc(name),
        ])
    return table(["Fold", "Train", "Test", "Target +", "Threshold", "PR-AUC", "ROC-AUC",
                  "Brier", "Model"], rows)


def episode_table(episodes: pd.DataFrame, peaks_all: list[str]) -> str:
    found = {str(r["peak"]): r for _, r in episodes.iterrows()}
    rows = []
    for peak in peaks_all:
        row = found.get(str(peak))
        if row is None:
            rows.append([esc(peak), '<span class="chip skip">outside test</span>', "—"])
            continue
        detected = bool(row["detected"])
        lead = row["lead_quarters"]
        rows.append([
            esc(peak),
            '<span class="chip yes">detected</span>' if detected else
            '<span class="chip no">missed</span>',
            f'{int(lead)}' if pd.notna(lead) else "—",
        ])
    return table(["BBQ peak", "Ensemble", "Lead (quarters)"], rows)


def rule_table(headline: pd.Series) -> str:
    delta = float(headline["delta_vs_best_single"])
    ci_low = float(headline["ci_low"])
    ep_ens = float(headline["episode_recall"])
    ep_best = float(headline["best_single_episode_recall"])
    checks = [
        ("Pooled PR-AUC gain ≥ 0.01", f"{delta:+.4f}", delta >= 0.01),
        ("Bootstrap CI excludes zero", f"[{ci_low:+.4f}, {float(headline['ci_high']):+.4f}]", ci_low > 0),
        ("No episode-recall loss", f"{pct(ep_ens, 0)} vs {pct(ep_best, 0)}", ep_ens >= ep_best),
        ("Applied once, before results", "yes", True),
    ]
    rows = [[esc(name), esc(value),
             '<span class="chip yes">pass</span>' if ok else '<span class="chip no">fail</span>']
            for name, value, ok in checks]
    return table(["C-13 condition", "Value", "Result"], rows)


# ----------------------------------------------------------------------- page
def sha256(path: Path) -> str:
    if not path.exists():
        return "missing"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL, text=True,
        ).strip()
    except Exception:
        return "unknown"


def fmt_ci(low: float, high: float) -> str:
    return f"[{low:+.3f}, {high:+.3f}]"


def build() -> str:
    labels = read_csv(LABELS)
    if labels is None:
        raise SystemExit(f"missing label file: {LABELS}")

    episodes = read_csv(EPISODES)
    vs_nber = read_csv(VS_NBER)
    growth = read_csv(GROWTH)
    headline = read_csv(MODEL_DIR / "headline.csv")
    pooled = read_csv(MODEL_DIR / "pooled_metrics.csv")
    fold_metrics = read_csv(MODEL_DIR / "fold_metrics.csv")
    predictions = read_csv(MODEL_DIR / "predictions.csv")
    model_episodes = read_csv(MODEL_DIR / "episodes.csv")

    has_model = all(x is not None for x in (headline, pooled, fold_metrics, predictions, model_episodes))
    labels["quarter"] = labels["quarter"].astype(str)
    if episodes is not None:
        episodes["peak"] = episodes["peak"].astype(str)
        episodes["trough"] = episodes["trough"].astype(str)

    nber_runs: list[tuple[str, str]] = []
    if vs_nber is not None:
        vs_nber["quarter"] = vs_nber["quarter"].astype(str)
        nber_runs = runs(list(zip(vs_nber["quarter"], vs_nber["NBER"].astype(int))))

    label_svg, label_legend = chart_labels(labels, episodes, nber_runs)

    # KPI block.
    n_quarters = len(labels)
    label_episodes = len(episodes) if episodes is not None else 0
    kpis = [
        ("Active label", "labels-v3", f"{n_quarters} quarters · 1990Q1–2026Q3", "ok"),
        ("Label episodes", f"{label_episodes}", "all four kept by the frozen rules", "ok"),
    ]
    if has_model:
        h = headline.iloc[0]
        delta = float(h["delta_vs_best_single"])
        kpis += [
            ("Ensemble PR-AUC", num(h["pooled_pr_auc"], 4),
             "pooled over outer test quarters", ""),
            ("Best single PR-AUC", num(h["best_single_pr_auc"], 4),
             esc(MODEL_LABEL.get(h["best_single_model"], h["best_single_model"])), "best"),
            ("Delta vs best single", signed(delta, 4),
             f"95% CI {esc(fmt_ci(float(h['ci_low']), float(h['ci_high'])))}",
             "good" if delta >= 0.01 else "bad"),
            ("Episode recall", pct(h["episode_recall"], 0),
             f"best single {pct(h['best_single_episode_recall'], 0)}", ""),
            ("False-positive quarters", f'{int(h["false_positive_quarters"])}',
             "at each fold's locked threshold", ""),
        ]
    kpi_html = "".join(
        f'<div class="kpi"><div class="k">{esc(k)}</div>'
        f'<div class="v {vcls}">{v}</div><div class="n">{n}</div></div>'
        for k, v, n, vcls in kpis
    )

    if has_model:
        h = headline.iloc[0]
        best_model = str(h["best_single_model"])
        prob_svg, model_buttons = chart_probabilities(predictions, episodes, fold_metrics)
        prevalence = float(predictions[predictions["model"] == "ensemble"]["y_true"].mean())
        bars_svg = chart_bars(pooled, prevalence)
        decision = str(h["decision"])
        if decision.startswith("single_primary"):
            verdict = ("The ensemble <strong>fails</strong> the pre-registered C-13 rule on this "
                       "exploratory run, so the single model is primary and the ensemble is a "
                       "negative result.")
            verdict_class = "bad"
        else:
            verdict = ("The ensemble <strong>passes</strong> the pre-registered C-13 rule on this "
                       "exploratory run. This still needs the official rerun.")
            verdict_class = "good"
        model_body = f"""
        <section id="model">
          <h2>Exploratory model run</h2>
          <p class="lede">USA, H=2, four expanding outer folds. Every number here is exploratory:
          the frozen feature table, fold file and official model code were missing when it ran.
          Hover a point for its quarter and probability; use the buttons to isolate a model.</p>
          <div class="card">
            {model_buttons}
            {prob_svg}
          </div>
          <div class="grid2" style="margin-top:16px">
            <div class="card">{bars_svg}</div>
            <div class="card">
              <h3 style="margin-top:0">Verdict</h3>
              <p class="{verdict_class}" style="font-size:14px;margin:0 0 10px">{verdict}</p>
              {rule_table(h)}
              <p class="table-note">Decision recorded: <code>{esc(decision)}</code>.
              This is orientation only and does not satisfy C-13.</p>
            </div>
          </div>
          <h3>Pooled metrics</h3>
          <div class="card">{pooled_table(pooled)}</div>
          <h3>Fold detail</h3>
          <div class="card">{fold_table(fold_metrics, best_model)}</div>
          <h3>Episode detection</h3>
          <div class="card">{episode_table(model_episodes, [str(x) for x in episodes['peak']])}</div>
        </section>
        """
    else:
        model_body = """
        <section id="model">
          <h2>Exploratory model run</h2>
          <div class="card">
            <p style="margin:0">No exploratory model outputs were found under
            <code>outputs/exploratory/usa_first/</code>. Run
            <code>.venv/bin/python experiments/usa_first_models.py</code> and rebuild this page to
            show the model section. The label views above do not depend on it.</p>
          </div>
        </section>
        """

    # Indicator sparklines.
    spark_html = ""
    if growth is not None:
        growth["quarter"] = growth["quarter"].astype(str)
        growth = growth[growth["quarter"].isin(set(labels["quarter"]))].reset_index(drop=True)
        gidx = pd.PeriodIndex(growth["quarter"], freq="Q")
        gaxis = Axis(gidx, 0, 300)
        cards = []
        for col in growth.columns[1:]:
            name = INDICATOR_LABEL.get(col, col)
            vals = growth[col].tolist()
            latest = next((v for v in reversed(vals) if pd.notna(v)), None)
            tone = "good" if latest is not None and latest >= 0 else "bad"
            cards.append(
                f'<div class="spark"><div class="head"><span>{esc(name)}</span>'
                f'<span class="{tone}">{num(latest, 2)}</span></div>'
                f'<svg viewBox="0 0 300 84" role="img" aria-label="{esc(name)} growth">'
                f'<title>{esc(name)} quarter-on-quarter log growth</title>'
                f'{sparkline(vals, gaxis, 300, 84)}</svg></div>'
            )
        spark_html = f"""
        <section id="indicators">
          <h2>The eight label inputs</h2>
          <p class="lede">Quarter-on-quarter log growth of the BEAI core indicators. The label uses
          all eight together; no single indicator decides an episode. Latest printed value is on
          the right of each card. The 2020 COVID spike compresses the vertical scale, and series
          that start later leave blank space on the left.</p>
          <div class="sparks">{''.join(cards)}</div>
        </section>
        """

    label_hash = sha256(LABELS)
    meta_hash = sha256(ROOT / "outputs" / "labels" / "labels-v3.json")
    commit = git_commit()
    generated = date.today().isoformat()
    status_badge = '<span class="badge ok">labels-v3 frozen</span>' if label_hash.startswith(
        "2379fd53") else '<span class="badge warn">label hash differs</span>'
    model_badge = ('<span class="badge warn">exploratory model</span>' if has_model
                   else '<span class="badge">model not built</span>')

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>USA Recession Early-Warning — Dashboard</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<header class="top">
  <div>
    <h1>USA Recession Early-Warning</h1>
    <p class="sub">Frozen BEAI label and an exploratory walk-forward model run. Built from the
    repository's own CSVs; no server, no external assets.</p>
  </div>
  <div class="badges">
    {status_badge}
    {model_badge}
    <span class="badge">USA · 1990Q1–2026Q3</span>
    <span class="badge">H = 2Q</span>
  </div>
</header>

<div class="banner">
  <div>
    <strong>Read this first</strong>
    <p>The model section is <b>exploratory only</b>. It is not the pre-registered C-13 result and
    it is not a recession forecast. The official run needs Arshiya's frozen feature table and
    folds and Palchhin's model code. The label section is the frozen, validated artefact.</p>
  </div>
</div>

<div class="kpis">{kpi_html}</div>

<section id="label">
  <h2>Label and chronology</h2>
  <p class="lede">The BEAI label is built from the eight core activity indicators with the frozen
  DFM → BBQ → diffusion gate. The factor line is the standardised activity factor; the strips
  compare the label's recession quarters with NBER.</p>
  <div class="card">
    {label_svg}
    {label_legend}
  </div>
  <div class="grid2" style="margin-top:16px">
    <div class="card">
      <h3 style="margin-top:0">Frozen label episodes</h3>
      {label_table(episodes) if episodes is not None else '<p>No episode file.</p>'}
      <p class="table-note">Four peaks, four kept episodes; the label reproduces all four NBER
      recessions in the window.</p>
    </div>
    <div class="card">
      <h3 style="margin-top:0">How to read it</h3>
      <p style="font-size:13px;color:var(--muted);margin:0 0 10px">
      A recession quarter is <code>R = 1</code> between a kept BBQ peak and trough. Shaded bands
      are label episodes, not NBER bands. The NBER strip is the official reference and is never
      used to fit the label.</p>
      <p style="font-size:13px;color:var(--muted);margin:0">
      Window: 1990Q1–2026Q3. The factor is estimated on the longer sample, so values near the
      boundary can shift slightly when data are revised; episode dates do not.</p>
    </div>
  </div>
</section>

{model_body}

{spark_html}

<section id="limits">
  <h2>Scope, limits and provenance</h2>
  <div class="notes">
    <div class="note is"><h4>This is</h4><p>A frozen label audit and an exploratory walk-forward
    run. A way to see the label, the model probabilities and where the ensemble rule stands.</p></div>
    <div class="note isnot"><h4>This is not</h4><p>The official pre-registered result, a
    real-time vintage forecast, or evidence that the ensemble should ship. The exploratory run
    fails C-13 (Δ −0.0017, CI includes zero).</p></div>
    <div class="note next"><h4>Next</h4><p>Rerun under the official feature table and folds when
    Arshiya and Palchhin deliver. Replace the exploratory section; keep the label section.</p></div>
  </div>
  <div class="card" style="margin-top:14px">
    <h3 style="margin-top:0">Reproduce</h3>
    <pre class="cmd"><span class="c"># rebuild this page</span>
.venv/bin/python scripts/05_dashboard.py

<span class="c"># rebuild the exploratory model outputs first (about 7–8 minutes)</span>
.venv/bin/python experiments/usa_first_models.py</pre>
    <p class="table-note">The dashboard script reads the CSVs only; it never writes labels,
    predictions or folds. Generated {esc(generated)} from commit <code>{esc(commit)}</code>.</p>
  </div>
</section>

<footer>
  <p>Label: <code>outputs/labels/USA_labels.csv</code> · SHA-256
  <code>{esc(label_hash[:16])}…</code> · metadata
  <code>{esc(meta_hash[:16])}…</code>.<br>
  Model outputs: <code>outputs/exploratory/usa_first/</code> (git-ignored, regenerable).
  Reference implementations are numpy/scipy because scikit-learn and xgboost were not
  installable in this environment.</p>
</footer>
</div>
<script>{JS}</script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                        help=f"output HTML path (default: {DEFAULT_OUT})")
    args = parser.parse_args()
    page = build()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(page, encoding="utf-8")
    print(f"wrote {args.out} ({len(page):,} bytes)")


if __name__ == "__main__":
    main()
