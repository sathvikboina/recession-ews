# Runtime Decisions

The Phase 2 `decisions_log.csv` contains 34 decisions, including documentation and
verification items that do not affect code. This page keeps only the decisions that the
pipeline executes. Full text and plan basis stay in `decisions_log.csv`.

Legend: **FROZEN** = implemented as-is · **CONFIRM** = needs a human sign-off before the
named step · **OPEN** = not decided yet.

| ID | Decision | Source | Status | Needed by |
|---|---|---|---|---|
| D-R01 | Unemployment is predictor-only; BEAI is exactly the eight §11 indicators. | Q-01, §11, §19 | FROZEN | now |
| D-R02 | Study window 1990Q1–2025Q4 (144 quarters); 70% = 101 quarters. | §6, §19 | FROZEN | now |
| D-R03 | Horizons 1Q/2Q/4Q, 2Q primary. | §22 | FROZEN | now |
| D-R04 | Coverage gate: ≥6 of 8 core indicators at ≥70%; ≥4 indicators to date a quarter. | Q-06, §18, §19 | FROZEN | now |
| D-R05 | Availability lags by data class (1Q / 6w / 0 / 4w / 1y). | Q-20, §30 | FROZEN | now |
| D-R06 | Quarterly aggregation: mean + quarter-end + intra-quarter change; no partial-quarter imputation. | §27 | FROZEN | Step 6 |
| D-R07 | SA: official SA preferred; NSA BEAI inputs get X-13 only up to the as-of cutoff; NSA predictors use YoY. | Q-19 | FROZEN | Step 6 |
| D-R08 | Annual series: carry the last published value with a 1-year lag; no interpolation. | Q-31 | FROZEN | Step 6 |
| D-R09 | India: re-label fiscal quarters to calendar; splice base years by chaining log growth; no pre-2017 employment backcast. | Q-07, Q-08, Q-09 | FROZEN | Step 6 |
| D-R10 | China: no special treatment; build a level index by chaining SA q/q growth where no level is published. | Q-11 | FROZEN | Step 6 |
| D-R11 | Walk-forward only; inner folds time-ordered; threshold locked before test. | §35, §40, §42 | FROZEN | Step 10 |
| D-R12 | Predictors need ≥70% window coverage (extension of §19 to predictors). | Q-25 | FROZEN | Step 9 |
| D-R13 | Global aggregates are built from training countries only and exclude the target/held-out country. | Q-18, §53 | FROZEN | Step 9 |
| D-R14 | Revised historical data with simulated lags; not a real-time vintage study, and the report must say so. | §30, §77 | FROZEN | report |
| D-R15 | No redistribution of restricted raw data; repository holds scripts and metadata only. | Q-23 | FROZEN | collection |
| D-R16 | Do not complete the 1,883-row catalogue; verify only the series in `data/scope.csv`. | operational | FROZEN | now |
| D-R17 | Use pre-1990 history for long-series countries to raise the episode count. | recommendation | CONFIRM (O-1) | Step 6 |
| D-R18 | India fallback if §19 fails: Label B only, reported as a coverage finding. | recommendation | CONFIRM (O-2) | Step 8 |
| D-R19 | Threshold objective: max F1 vs recall-at-precision. | recommendation | OPEN (O-3) | Step 10 |
| D-R20 | Scope P0–P1 (68 rows) first, widen to P0–P2 (140 rows) after the label gate. | recommendation | CONFIRM (O-4) | Step 4 |
| D-R21 | COVID 2020 kept in the sample; BBQ treatment documented; with/without-2020 evaluation for Tier-1. | §6, §58 | CONFIRM (O-5) | Step 11 |
| D-R22 | The DFM is estimated on 1960Q1–2025Q4; labels are reported for 1990Q1–2025Q4. Extending the estimation sample prevents the left endpoint from censoring the 1990Q3 peak. Study window unchanged. | implementation finding | FROZEN | labels |
| D-R23 | US real household income in the label is `W875RX1` (real personal income excluding transfers), not `DPIC96`. Transfer receipts make disposable income counter-cyclical and distort a coincident factor. | §11 + Stock–Watson practice | FROZEN | labels |
| D-R24 | The label uses the **smoothed** factor. Pipeline A is an ex-post chronology and applies no availability lag (C-05); the smoothed factor avoids revision noise in the dates. | §13, C-05 | FROZEN | labels |
| D-R25 | The factor is converted to growth units with `scale = mean(σⱼ·|λⱼ|)`, using the estimated loadings. Not a tuning choice: without it the common component is overstated ~3× and BBQ dates long pseudo-recessions. | implementation finding | FROZEN | labels |

## Consequences to keep in mind

- **D-R01** is load-bearing. If the team later adds unemployment, the eligibility rule
  becomes 6/9, every `beai_eligible` row changes, and the Summary-sheet checks in the
  workbook must be regenerated. Decide once.
- **D-R02 + D-R17** interact with episode counts. At 1990–2025 the US has four NBER
  episodes; if 2020 fails the 2-quarter minimum phase, three remain. Extending US history
  to 1960 roughly doubles that.
- **D-R04** is the reason India may not receive a primary label. That is a finding, not a bug.
- **D-R22/D-R25** were discovered while building the US label. Both are reproducibility
  fixes, not threshold tuning: they change the *estimator*, not the gate. Before the fix the
  label missed 1990-91 and 2001 entirely; after it, all four NBER episodes are matched with
  at most a one-quarter boundary shift (`outputs/results/USA_vs_NBER.md`).
- **D-R23** changes which FRED series feeds `ACT_RINC.Q.STD`. The scope row and the manifest
  record the substitution; the old `DPIC96` is still downloaded as the monthly predictor copy.
- **O-1** is now half-answered: the *estimation* sample extends to 1960, but the *study*
  window is still 1990–2025. Whether to report pre-1990 labels remains open.

## Verification items still pending (facts, not decisions)

From `decisions_log.csv`: Q-02, Q-03, Q-05, Q-06, Q-07, Q-08, Q-09, Q-11, Q-12, Q-15,
Q-16, Q-17, Q-23, Q-27, Q-28. These are closed by the scoped verification pass
(`docs/VERIFICATION.md`), not by a judgement call.
