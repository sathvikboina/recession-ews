# Runtime Decisions

The Phase 2 `decisions_log.csv` contains 34 decisions, including documentation and
verification items that do not affect code. This page keeps only the decisions that the
pipeline executes. Full text and plan basis stay in `decisions_log.csv`.

Legend: **FROZEN** = implemented as-is · **CONFIRM** = needs a human sign-off before the
named step · **OPEN** = not decided yet.

| ID | Decision | Source | Status | Needed by |
|---|---|---|---|---|
| D-R01 | Unemployment is predictor-only; BEAI is exactly the eight §11 indicators. | Q-01, §11, §19 | FROZEN | now |
| D-R02 | Study window 1990Q1–2026Q3 (147 quarters); 70% = 103 quarters. | §6, §19 | FROZEN | now |
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
| D-R22 | The DFM is estimated on 1960Q1–2026Q3; labels are reported for 1990Q1–2026Q3. Extending the estimation sample prevents the left endpoint from censoring the 1990Q3 peak. Study window extended by D-R31. | implementation finding | FROZEN | labels |
| D-R23 | US real household income in the label is `W875RX1` (real personal income excluding transfers), not `DPIC96`. Transfer receipts make disposable income counter-cyclical and distort a coincident factor. | §11 + Stock–Watson practice | FROZEN | labels |
| D-R24 | The label uses the **smoothed** factor. Pipeline A is an ex-post chronology and applies no availability lag (C-05); the smoothed factor avoids revision noise in the dates. | §13, C-05 | FROZEN | labels |
| D-R25 | The factor is converted to growth units with `scale = mean(σⱼ·|λⱼ|)`, using the estimated loadings. Not a tuning choice: without it the common component is overstated ~3× and BBQ dates long pseudo-recessions. | implementation finding | FROZEN | labels |
| D-R26 | Q-02 Option B. USA business investment is **constructed real non-residential fixed investment** = (`Y033RC1Q027SBEA` + `B009RC1Q027SBEA` + `Y001RC1Q027SBEA`) / (`A008RD3Q086SBEA`/100). `GPDIC1` (residential + inventories) is retired. The construction reproduces `PNFIC1` to <0.02bn over 2007Q1–2026Q3 and has 147/147 window coverage. Implemented in `labels-v2` and retained unchanged in `labels-v3`. | Q-02, §11 | FROZEN | labels |
| D-R27 | Q-04 Option B. USA employment is `CE16OV`, household-survey employment, quarterly mean. OECD QNA quarterly employment is not published for the USA (checked 2026-11-04); `PAYEMS` is an establishment survey, not the Q-04 fallback. `PAYEMS` is retired from the label. Implemented in `labels-v2` and retained in `labels-v3`. | Q-04, §8, §11 | FROZEN | labels |
| D-R28 | Q-05 Option A. USA hours stay on `HOANBS` (quarterly total hours, nonfarm business). Q-05 bars annual-only data, not narrower sector coverage; the nonfarm-business limitation is recorded. No FRED whole-economy quarterly total-hours series exists. Implemented unchanged in `labels-v2` and `labels-v3`. | Q-05, §11 | FROZEN | labels |
| D-R29 | Ensemble pre-registered before any model result: equal-weight top-3 by inner-fold pooled PR-AUC, same folds and feature matrix as the singles, all fitting inside the outer training block. It must beat the inner-fold-selected best single model by ≥0.01 pooled PR-AUC, with a paired-bootstrap 95% CI excluding zero and no loss of episode recall; otherwise the single model is primary and the ensemble is a reported negative result. A logistic stack is exploratory only. | proposal addendum, C-13 | FROZEN | models |
| D-R30 | India pre-audit: best case 4/8 under §19 because employment, hours, household income and retail are structurally missing. No relaxation; India is Label-B-only under O-2, reported as a coverage case study. The final count from downloaded MoSPI/RBI data is still required, but it cannot make 6/8 reachable. | Q-06, §19, O-2 | CONFIRM (O-2) | India / report |
| D-R31 | **2026 data extension.** The reporting window moves from 1990Q1–2025Q4 (144 quarters) to **1990Q1–2026Q3 (147 quarters)** using FRED observations through 2026-09. `labels-v2` is archived byte-identically; `labels-v3` is active. The estimator, BBQ parameters, diffusion gate and eight-indicator structure are unchanged. The extension adds no new recession episode and keeps 4/4 NBER agreement. | 2026 data request, D-R22 | FROZEN | labels / features / report |

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
  record the substitution; the retired quarterly `DPIC96` duplicate is recorded in
  `data/superseded_series.csv`. The monthly predictor copy is the separate `DSPIC96` row.
- **O-1** is now half-answered: the *estimation* sample extends to 1960, but the *study*
  window is still 1990–2026Q3. Whether to report pre-1990 labels remains open.
- **D-R29** is deliberately fixed before any score exists. Changing the member count,
  weighting, margin, bootstrap rule or recall guardrail after seeing results invalidates
  the confirmatory claim; it becomes a new, exploratory experiment.
- **D-R30** changes the project story, not the §19 rule: the label countries are USA, JPN
  and DEU, and India is a coverage case study. Do not present India as a fourth label.

## USA data sign-off (2026-11-05)

The review asked for explicit closure of the two v1 data defects.

| Item | Sign-off |
|---|---|
| Q-02: `GPDIC1` included housing and inventories, contrary to "business (non-residential) fixed investment". | **Closed for the USA.** `labels-v2` uses the constructed non-residential series (D-R26); `GPDIC1` is retired. |
| Q-04: `PAYEMS` is an establishment survey, not the national-accounts or LFS concept. | **Closed for the USA.** `labels-v2` uses `CE16OV` (D-R27); `PAYEMS` is retired from the label. |
| Q-05: `HOANBS` covers nonfarm business only. | **Closed for the USA.** Retained and documented (D-R28). |

The full evidence table is in `docs/REVIEW_2026-11-05.md` and
`docs/VERIFICATION.md`. JPN/DEU availability remains a collection-time check.

## Verification items still pending (facts, not decisions)

From `decisions_log.csv`: Q-03, Q-06, Q-07, Q-08, Q-09, Q-11, Q-12, Q-15,
Q-16, Q-17, Q-23, Q-27, Q-28. These are closed by the scoped verification pass
(`docs/VERIFICATION.md`), not by a judgement call.

Q-02, Q-04 and Q-05 are **closed for the USA** by D-R26–D-R28, implemented in
`labels-v2` (2026-11-04), retained unchanged in `labels-v3` (2026-11-06) and explicitly
signed off 2026-11-05. Q-02 and Q-05 still
need a country-level availability check when JPN/DEU are collected: non-residential
GFCF components and quarterly total hours may be missing there, in which case the
component counts as missing under the same decisions. Q-04 for JPN/DEU uses their
own audit; German QNA employment is available (1991Q1–2022Q4), while the USA and
Japan returned no employment observations in the checked OECD QNA dataflow.

Q-06 remains `DECIDED_PENDING_VERIFICATION` until the India downloads are counted,
but the pre-audit already fixes the conclusion at **best case 4/8**, so India is
Label-B-only under O-2 (D-R30).

`labels-v1` remains byte-identical under `outputs/labels/archive/labels-v1/` and
`labels-v2` under `outputs/labels/archive/labels-v2/`. The active chronology is
`labels-v3` (2026Q3 window extension); see `docs/DECISION_NOTE_Q02_Q04_Q05.md`
for the comparison, selected options and joint re-validation.
