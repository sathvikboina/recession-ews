# USA Label Validation

Milestone: verify FRED, harmonise the eight §11 core indicators, build the BEAI label,
compare with NBER, freeze the result before any feature or model work.

Status: **passed for `labels-v2` (2026-11-04)**. All four NBER recessions in
1990Q1–2025Q4 are matched, with no false episodes and at most a one-quarter
boundary shift. `labels-v1` is archived byte-for-byte under
`outputs/labels/archive/labels-v1/`; `labels-v2` changes only the Q-02 investment
and Q-04 employment inputs (D-R26, D-R27), while Q-05 keeps `HOANBS` (D-R28).

## 1. Data

Eight core indicators, all ≥93% coverage of the 144-quarter window (`data/clean/coverage.csv`):

| BEAI indicator | FRED id | native | transform |
|---|---|---|---|
| `ACT_GDP_REAL` | `GDPC1` | Q | Δlog |
| `ACT_IP` | `INDPRO` | M → Q mean | Δlog |
| `ACT_EMP` | `CE16OV` | M → Q mean | Δlog |
| `ACT_HOURS` | `HOANBS` | Q | Δlog |
| `ACT_RINC` | `W875RX1` | M → Q mean | Δlog |
| `ACT_CONS` | `PCECC96` | Q | Δlog |
| `ACT_RETAIL` | `RRSFS` | M → Q mean | Δlog |
| `ACT_INV` | constructed from `Y033RC1Q027SBEA`, `B009RC1Q027SBEA`, `Y001RC1Q027SBEA`, `A008RD3Q086SBEA` | Q | Δlog |

Monthly to quarterly is the mean of the three months; a quarter is missing unless all
three months are present. No interpolation, no forward fill. `RRSFS` starts in 1992, so
1990Q1–1991Q4 stays missing; that is 93.1% coverage, above the 70% gate. `CE16OV`
covers 143/144 quarters (99.3%).

`ACT_INV` is constructed as
`(equipment + structures + intellectual property products) / (deflator/100)`,
using the four quarterly SA BEA components. Over 2007Q1–2026Q3 it reproduces
`PNFIC1` (the correct concept, but only available from 2007) to under 0.02 billion.
The construction is recorded as a derived series; the four inputs are in the
manifest. `GPDIC1` (v1) and `PAYEMS` (v1) are retired in
`data/superseded_series.csv`.

Data corrections and decisions are recorded in `docs/VERIFICATION.md` and
`docs/DECISIONS.md`:

- real income uses **income excluding transfers** (`W875RX1`). Real disposable income
  (`DPIC96`) is monthly and counter-cyclical because of transfer payments — it loads
  negatively on the activity factor and distorts dates.
- investment uses the **constructed real non-residential total** (`GPDIC1` included
  residential investment and inventories; `PNFIC1` is too short).
- employment uses **`CE16OV`** (household/LFS fallback). OECD QNA quarterly
  employment is not available for the USA; `PAYEMS` is an establishment survey.

One scope key has exactly one active source row in `data/fred_verification.csv`
and `data/manifest.csv`; retired rows are in `data/superseded_series.csv`.

## 2. Method

1. z-score each growth series (full sample; the label is an ex-post chronology).
2. one-factor `DynamicFactorMQ` on 1960Q1–2025Q4, `factor_orders=1`,
   `idiosyncratic_ar1=True`, Kalman handling of missing cells.
3. take the **smoothed** factor, convert to growth units with
   `scale = mean(σⱼ·|λⱼ|)`, and cumulate to a level `Fₜ`.
4. BBQ on `Fₜ`: local extrema in a ±2 window, min phase 2, min cycle 5, endpoint
   censoring 2.
5. each peak→trough pair is a candidate; keep it if mean diffusion ≥ 0.50, where
   diffusion is the share of available core indicators with negative growth in the
   quarters after the peak.
6. `Rₜ = 1` from the quarter after the peak through the trough.

`Fₜ` is estimated from 1960 so the left endpoint does not censor the 1990Q3 peak.
Labels are reported for 1990Q1–2025Q4 only.

## 3. Result

| NBER peak–trough | label peak–trough | peak diff | trough diff |
|---|---|---:|---:|
| 1990Q3–1991Q1 | 1990Q2–1991Q1 | −1 | 0 |
| 2001Q1–2001Q4 | 2001Q1–2001Q4 | 0 | 0 |
| 2007Q4–2009Q2 | 2007Q4–2009Q2 | 0 | 0 |
| 2019Q4–2020Q2 | 2019Q4–2020Q2 | 0 | 0 |

- 4/4 episodes matched, 0 false episodes.
- Quarter-level: 13 TP, 1 FP, 0 FN, 130 TN → accuracy 0.993, recall 1.000,
  precision 0.929, F1 0.963.
- Diffusion: 0.810 (1990), 0.708 (2001), 0.875 (2008), 0.938 (2020). All above 0.50.

The v1 comparison (archived) was 13 TP, 2 FP, 0 FN, 129 TN → accuracy 0.986,
precision 0.867, F1 0.929. v2 removes the extra 2009Q3 quarter and matches every
NBER trough exactly. The factor correlation between v1 and v2 over the window is
0.9966; the level correlation is 0.9982.

## 4. Discrepancies, and why they are acceptable

- **1990Q2 vs 1990Q3 peak.** The factor peaks in 1990Q2 and turns negative in 1990Q3,
  while the NBER peak is the last quarter of expansion (July 1990). A one-quarter lead at
  a peak is a boundary convention, not a missed recession.
- **One extra flagged quarter** (1990Q3) lowers precision to 0.929. Recall is 1.000.
- **The 2009 trough now matches NBER exactly** (2009Q2, previously 2009Q3 under the
  broad `GPDIC1` proxy).
- **Label B (two consecutive negative GDP quarters)** catches 3/4 episodes and misses 2001
  because revised GDP never has two consecutive negative quarters that year. This is why
  the BEAI factor label is primary and the technical label is robustness only.

## 5. Robustness

| variant | kept episodes |
|---|---|
| baseline (`labels-v2`) | 1990Q2–1991Q1; 2001Q1–2001Q4; 2007Q4–2009Q2; 2019Q4–2020Q2 |
| min phase 3 | same minus 2020 (its duration is 2) |
| diffusion gate 0.60 | all four (every episode ≥ 0.708) |
| sample ends 2019Q4 (no COVID) | 1990Q2–1991Q1; 2000Q4–2002Q1; 2007Q4–2009Q3 |

Dates move by at most one quarter when the estimation sample excludes COVID, so the
label is not an artefact of the 2020 outlier.

## 6. What would falsify this

- a labelled episode with no NBER counterpart (none);
- any NBER episode missed (none);
- dates that move by more than one quarter under the robustness variants (they do not);
- a label that changes when the NBER series is removed from the inputs (it is never read).

## 7. Frozen artefacts

| file | content |
|---|---|
| `outputs/labels/USA_labels.csv` | quarter, factor, level, diffusion, R, episode id (`labels-v2`) |
| `outputs/labels/USA_episodes.csv` | every candidate episode with gate outcome; window ids match the label |
| `outputs/labels/USA_turning_points.csv` | dated peaks and troughs, with an `in_window` flag |
| `outputs/labels/labels-v2.json` | parameters, loadings, decisions, input hashes, output hashes |
| `outputs/labels/archive/labels-v1/` | byte-identical v1 artefacts and SHA-256 sums |
| `outputs/results/USA_vs_NBER.md` | this comparison, regenerated by script |

Regenerate with `make pipeline`. Hashes are in `labels-v2.json` and `docs/STATE.md`.
The active label CSV hash is
`f5ed42a6c4333aaecbae4fae1f5f6fcab3606ce46dd2b459791a6aa31816dc8e`; v1 remains
`1a1b1f6a566cb2cffe7181cbc59ec20bd07d8ef25e0300d4dd2d96ceb749e29a`.
