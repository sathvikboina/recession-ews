# Decision Note: Q-02, Q-04, Q-05

Status: **decision requested — no replacement selected**. This note compares the
current USA inputs with the alternatives that were checked on 2026-11-04. It does
not amend Q-02, Q-04 or Q-05, does not change the eight BEAI inputs, and does not
change the frozen `labels-v1` chronology.

The current label is a validated **USA activity chronology**. It is not yet a
strict implementation of the three concept decisions below. That gap is why these
questions need an explicit decision before JPN and DEU are collected.

## Evidence base and limits

- Metadata, native frequency, first/last observation and coverage were read from
  FRED on 2026-11-04. Coverage is the share of the 144 quarters in 1990Q1–2025Q4
  with a complete observation at native frequency (monthly series need all three
  months).
- The chronology sensitivity runs in §5 are **read-only**. They replace one label
  input at a time, keep the frozen DFM, BBQ and diffusion parameters, and do not
  write to `data/clean` or `outputs`. They are indicative, not a re-freeze.
- NBER agreement is a plausibility check, not the optimisation target (C-04,
  FW-06). A lower NBER score is a finding to discuss, not automatically a reason
  to reject a concept-correct series.
- OECD dataflow IDs for JPN/DEU are still unresolved (Q-15), so cross-country
  availability below is stated as "expected from OECD QNA" where it could not be
  confirmed from a downloaded series.

## 1. At a glance

| Question | Current US series | Current concept | Main alternatives | Verdict for the note |
|---|---|---|---|---|
| Q-02 investment | `GPDIC1` | Real **gross private domestic** investment: residential + inventories + business | Constructed real nonresidential total; `PNFIC1`; `PNFIC96`; `FPIC1`; equipment only | Current series is **not Q-02 compliant**. The only full-coverage strict option is a derived series. |
| Q-04 employment | `PAYEMS` | Establishment-survey employees, total nonfarm | `CE16OV` (household/LFS); `PRS85006013` (nonfarm business); `CEU0500000001` (private establishment); BEA persons engaged; OECD QNA | Current series is a **third concept**, not the Q-04 preferred national accounts or LFS fallback. |
| Q-05 hours | `HOANBS` | Total hours, **nonfarm business** sector | `PRS85006023` (average weekly hours); `AWHNONAG` (production/nonsupervisory hours); `AWHAETP`; BEA annual hours; OECD total hours | Current series is quarterly total hours but **narrower than whole economy**. No FRED alternative improves the total-hours concept. |

## 2. Q-02 — business / non-residential fixed investment

**Frozen decision (quote).** "Strict: business (non-residential) fixed investment
only. Total GFCF is not substituted; where business investment is missing the
component counts as missing." (`decisions_log.csv`, Q-02.)

### Current: `GPDIC1`

| Property | Value |
|---|---|
| Title | Real Gross Private Domestic Investment |
| Source | BEA NIPA via FRED |
| Frequency / SA | Quarterly, SA |
| Units | Billions of chained 2017 dollars |
| History | 1947Q1–2026Q3 |
| Window coverage | 144/144 (100%) |
| Concept | **All** private domestic investment: non-residential fixed investment **plus residential fixed investment plus change in private inventories** |

This is broader than Q-02 in two directions: it includes residential investment
and inventories. It is a complete, long, quarterly series, but it is not the §11
"business investment" component.

### Alternatives

| Series | Title / construction | Source | Freq / SA | History | Coverage | Fit and constraints |
|---|---|---|---|---|---|---|
| Constructed real non-residential total | `Y033RC1Q027SBEA` (equipment) + `B009RC1Q027SBEA` (structures) + `Y001RC1Q027SBEA` (intellectual property products), deflated by `A008RD3Q086SBEA` (non-residential implicit price deflator, 2017=100) | BEA NIPA via FRED | Q, SA | 1947Q1–2026Q3 | 144/144 (100%) | **Concept-compliant.** It is a derivation, not a single download. Over 2007Q1–2026Q3 it reproduces `PNFIC1` to within about 0.02 billion (mean absolute percentage error ≈ 0.0002%). |
| `PNFIC1` | Real Private Nonresidential Fixed Investment | BEA via FRED | Q, SA | 2007Q1–2026Q3 | 76/144 (52.8%) | Correct concept, **fails the 70% coverage gate**. Cannot be the sole 1990–2025 input. |
| `PNFIC96` | Real Private Nonresidential Fixed Investment (discontinued) | BEA via FRED | Q, SA | 1999Q1–2017Q2 | 74/144 (51.4%) | Correct concept, discontinued, ends 2017, **fails coverage**. |
| `FPIC1` | Real Private Fixed Investment | BEA via FRED | Q, SA | 2007Q1–2026Q3 | 76/144 (52.8%) | Still includes residential investment; fails coverage. |
| `Y033RC1Q027SBEA` deflated by `Y033RD3Q086SBEA` | Non-residential **equipment only** | BEA via FRED | Q, SA | 1947Q1–2026Q3 | 144/144 (100%) | Too narrow: excludes structures and intellectual property products. |

**Cross-country availability.** The Q-02 concept is normally available from OECD
QNA as gross fixed capital formation by asset and institutional sector
(non-residential / business investment), quarterly for most OECD countries. The
project's OECD dataflow IDs are unresolved (Q-15), so this is expected, not yet
verified. `GPDIC1` is a US-only broad concept; the constructed US series is also
US-specific, but the same decomposition can be implemented from OECD QNA
components for JPN/DEU.

**Chronology sensitivity (one input replaced, current parameters).**

| ACT_INV series | Label episodes 1990–2025 | TP | FP | FN | Accuracy | Precision | Recall | F1 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| `GPDIC1` (current) | 1990Q2–1991Q1; 2001Q1–2001Q4; 2007Q4–2009Q3; 2019Q4–2020Q2 | 13 | 2 | 0 | 0.986 | 0.867 | 1.000 | 0.929 |
| Constructed real non-residential | 1990Q1–1991Q2; 2000Q3–2002Q1; 2007Q2–2009Q3; 2019Q4–2020Q2 | 13 | 9 | 0 | 0.938 | 0.591 | 1.000 | 0.743 |
| Equipment only (real) | 1990Q1–1991Q2; 2007Q2–2009Q3; 2019Q3–2020Q2 | 10 | 7 | 3 | 0.931 | 0.588 | 0.769 | 0.667 |
| `PNFIC1` (not gate-compliant) | 1990Q1–1991Q2; 2001Q1–2002Q1; 2007Q2–2009Q3; 2019Q4–2020Q2 | 13 | 7 | 0 | 0.951 | 0.650 | 1.000 | 0.788 |

The strict alternatives move peaks 1–3 quarters earlier and add false positives.
The current chronology is therefore partly supported by the broad investment
proxy. This is a substantive trade-off, not a cosmetic data substitution.

### Options (none selected)

- **A. Keep `GPDIC1` and record an explicit deviation from Q-02**, with the
  residential/inventory content and the US-only scope documented. No re-freeze.
- **B. Replace with the constructed real non-residential total and re-validate.**
  Requires a new derived series, a resolution/manifest entry, a new label version
  and a full NBER/robustness re-run. The sensitivity above suggests the dates and
  precision will change.
- **C. Drop `ACT_INV` and run with seven indicators.** §19 still permits a label
  with 7/8 core indicators; this avoids a concept deviation but changes the label
  definition and requires re-validation.
- **D. Defer.** Keep `labels-v1` as the USA milestone and decide before JPN/DEU.

## 3. Q-04 — employment concept

**Frozen decision (quote).** "Employment: national-accounts quarterly employment
preferred, LFS monthly (quarterly mean) as fallback; one concept is locked per
country at the audit and counted once toward §19." (`decisions_log.csv`, Q-04.)

### Current: `PAYEMS`

| Property | Value |
|---|---|
| Title | All Employees, Total Nonfarm |
| Source | BLS Current Employment Statistics (establishment survey) via FRED |
| Frequency / SA | Monthly, SA (aggregated to quarterly mean with the complete-quarter rule) |
| History | 1939M1–2026M9 |
| Window coverage | 144/144 (100%) |
| Concept | Establishment payroll employees, total nonfarm. Includes government; excludes self-employed, agriculture, private household and nonprofit workers. |

This is neither the national-accounts concept nor the LFS fallback named in Q-04.

### Alternatives

| Series | Title / concept | Source | Freq / SA | History | Coverage | Fit and constraints |
|---|---|---|---|---|---|---|
| `CE16OV` | Employment Level, household survey (LFS analogue) | BLS CPS via FRED | M, SA | 1948M1–2026M9 | 143/144 (99.3%) | Closest to the Q-04 **LFS fallback**. Includes self-employed and agricultural workers; CPS sample revisions can create breaks. |
| `PRS85006013` | Nonfarm Business Sector: Employment for All Workers | BLS productivity via FRED | Q, SA | 1947Q1–2026Q2 | 144/144 (100%) | Consistent with `HOANBS`/`OPHNFB`, but a **nonfarm business** concept: excludes government, nonprofit and agriculture. Not total economy. |
| `CEU0500000001` | All Employees, Total Private | BLS CES via FRED | M, NSA | 1939M1–2026M9 | 144/144 (100%) | Establishment concept, excludes government; NSA, so it would need X-13 under D-R07, and it is narrower than `PAYEMS`. |
| `A4601C0A173NBEA` | Persons engaged in production (BEA national accounts) | BEA via FRED | A, NSA | 1929–2022 | 132/144 (91.7%) | National-accounts concept, but **annual and ends 2022**. Q-05-style annual-only data are inadmissible without disaggregation; interpolation is forbidden (C-03). |
| OECD QNA employment | Employment, persons, quarterly | OECD | Q | Expected 1990+ | Unconfirmed | The Q-04 **preferred** concept. Dataflow IDs unresolved (Q-15). This is the only option that directly supports cross-country comparability. |

**Cross-country availability.** OECD QNA employment is the standard quarterly
source for JPN/DEU and is the concept Q-04 names first. The US quarterly national
accounts employment series is not available on FRED in the required form (BEA
persons engaged is annual and ends 2022), so a US switch to national accounts
would require the OECD dataflow. `PAYEMS`, `CE16OV` and `PRS85006013` are all
US-only.

**Chronology sensitivity (one input replaced, current parameters).**

| ACT_EMP series | Label episodes 1990–2025 | TP | FP | FN | Accuracy | Precision | Recall | F1 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| `PAYEMS` (current) | 1990Q2–1991Q1; 2001Q1–2001Q4; 2007Q4–2009Q3; 2019Q4–2020Q2 | 13 | 2 | 0 | 0.986 | 0.867 | 1.000 | 0.929 |
| `CE16OV` | 1990Q2–1991Q1; 2000Q4–2001Q4; 2007Q4–2009Q3; 2019Q4–2020Q2 | 13 | 3 | 0 | 0.979 | 0.812 | 1.000 | 0.897 |
| `PRS85006013` | 1990Q1–1991Q2; 2007Q2–2009Q3; 2019Q4–2020Q2 | 10 | 6 | 3 | 0.938 | 0.625 | 0.769 | 0.690 |
| `CEU0500000001` | 1990Q2–1991Q1; 2000Q4–2001Q4; 2007Q4–2009Q2; 2019Q4–2020Q2 | 13 | 2 | 0 | 0.986 | 0.867 | 1.000 | 0.929 |

`CE16OV` is the lowest-cost conceptual improvement: one extra false-positive
quarter and the 2001 peak moves one quarter earlier. `PRS85006013` is too narrow
and misses 2001. `CEU0500000001` matches the current quarter-level metrics but is
private-only and NSA.

### Options (none selected)

- **A. Keep `PAYEMS` and record an explicit deviation from Q-04**, documenting
  the establishment concept and the government/nonfarm scope.
- **B. Replace with `CE16OV` (LFS fallback) and re-validate.** Conceptually
  closer, US-only, modest chronology cost.
- **C. Resolve Q-15 and use OECD QNA employment for USA, JPN and DEU.** Best
  cross-country consistency; requires collection and a full re-run.
- **D. Defer until the JPN/DEU collection shows which concept is actually
  available quarterly.**

## 4. Q-05 — hours worked

**Frozen decision (quote).** "Quarterly total hours only. Annual-only means the
component is missing; no temporal disaggregation." (`decisions_log.csv`, Q-05.)
The indicator definition also says "Total hours worked, whole economy"
(`spec.py`, `ACT_HOURS`).

### Current: `HOANBS`

| Property | Value |
|---|---|
| Title | Nonfarm Business Sector: Hours Worked for All Workers |
| Source | BLS productivity and costs via FRED |
| Frequency / SA | Quarterly, SA |
| Units | Index 2017=100 |
| History | 1947Q1–2026Q2 |
| Window coverage | 144/144 (100%) |
| Concept | Total hours worked in the **nonfarm business** sector. Excludes government, nonprofit, agriculture and some other sectors. |

It is a genuine quarterly total-hours series, but narrower than "whole economy".

### Alternatives

| Series | Title / concept | Source | Freq / SA | History | Coverage | Fit and constraints |
|---|---|---|---|---|---|---|
| `PRS85006023` | Nonfarm Business Sector: Average Weekly Hours for All Workers | BLS productivity via FRED | Q, SA | 1947Q1–2026Q2 | 144/144 (100%) | **Hours per worker**, not total hours. Much smoother than total hours (growth SD 0.34 vs 1.58 in 1990–2025). |
| `AWHNONAG` | Average Weekly Hours of Production and Nonsupervisory Employees, Total Private | BLS CES via FRED | M, SA | 1964M1–2026M9 | 144/144 (100%) | Hours per worker, production/nonsupervisory only. Very smooth (SD 0.24). |
| `AWHAETP` | Average Weekly Hours of All Employees, Total Private | BLS CES via FRED | M, SA | 2006M3–2026M9 | 79/144 (54.9%) | Hours per worker, all private employees, but **fails coverage**. |
| `B4701C0A222NBEA` | Hours worked by full-time and part-time employees | BEA via FRED | A, NSA | 1948–2022 | 132/144 (91.7%) | Annual and ends 2022. Q-05 explicitly says annual-only means **missing**; not admissible. |
| `PRS85006013 × PRS85006023` | Employment × average weekly hours | BLS productivity via FRED | Q, SA | 1947Q1–2026Q2 | 144/144 (100%) | Reconstructs the same nonfarm-business total-hours concept as `HOANBS`; not a new concept. |
| OECD total hours worked | Total hours, national accounts / productivity | OECD | Q or A (country-dependent) | Expected 1990+ | Unconfirmed | The cross-country concept Q-05 wants; quarterly availability is unresolved (Q-15, and Q-05 itself flags annual-only risk). |

**Cross-country availability.** OECD total hours worked is the natural
cross-country source, but many countries publish it annually or with a lag;
Q-05 already anticipates that annual-only means the component is missing. FRED
offers no US total-economy quarterly hours series: BEA hours are annual and end
2022, and the monthly BLS hours series are per-worker measures. `HOANBS` is the
only full-coverage quarterly total-hours series available on FRED.

**Chronology sensitivity (one input replaced, current parameters).**

| ACT_HOURS series | Label episodes 1990–2025 | TP | FP | FN | Accuracy | Precision | Recall | F1 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| `HOANBS` (current) | 1990Q2–1991Q1; 2001Q1–2001Q4; 2007Q4–2009Q3; 2019Q4–2020Q2 | 13 | 2 | 0 | 0.986 | 0.867 | 1.000 | 0.929 |
| `PRS85006023` | 1990Q2–1991Q1; 2000Q4–2001Q4; 2007Q4–2009Q2; 2019Q4–2020Q2 | 13 | 2 | 0 | 0.986 | 0.867 | 1.000 | 0.929 |
| `AWHNONAG` | 1990Q2–1991Q1; 2000Q4–2001Q4; 2007Q4–2009Q2; 2019Q4–2020Q2 | 13 | 2 | 0 | 0.986 | 0.867 | 1.000 | 0.929 |

The per-worker series leave the quarter-level metrics unchanged in this
one-at-a-time test, but move the 2001 peak one quarter earlier and the 2009
trough one quarter earlier. They also change what the factor measures: total
labour input versus hours per worker. That is a concept change, not a data
upgrade.

### Options (none selected)

- **A. Keep `HOANBS` and record the sector-coverage deviation** ("total hours,
  nonfarm business") in the decision record. No re-freeze.
- **B. Use OECD total hours worked when it is available quarterly** for USA,
  JPN and DEU; if it is annual-only, Q-05 says the component is missing.
- **C. Switch to a per-worker hours series (`PRS85006023` or `AWHNONAG`).**
  Preserves quarter-level NBER agreement here but weakens the total-hours
  concept and shifts dates.
- **D. Defer until JPN/DEU hours availability is verified.**

## 5. What a change would require

Any selected replacement would need the same sequence, in order:

1. Add the source (or derivation) to `data/series_resolution.csv`,
   `data/manifest.csv` and `data/fred_verification.csv`; if it replaces a source,
   record the retired row in `data/superseded_series.csv`.
2. Update `config/indicators.yaml` only if the indicator semantics change; the
   eight BEAI indicator ids stay the same.
3. Re-run `harmonize.py`, `03_labels.py` and `04_compare_nber.py`.
4. Re-run the robustness variants and the frozen-artefact tests.
5. Issue a new label version, update `docs/DECISIONS.md`, `docs/LABEL_VALIDATION.md`
   and `docs/STATE.md`, and re-freeze. The current `labels-v1` stays untouched
   until that decision is made.

## 6. Decision requested

| Question | Option A (keep + record deviation) | Option B (concept-correct replacement) | Option C (alternative) | Option D |
|---|---|---|---|---|
| Q-02 | Keep `GPDIC1`, document residential/inventory content | Constructed real non-residential total; re-validate | Drop `ACT_INV` (7/8) | Defer |
| Q-04 | Keep `PAYEMS`, document establishment concept | `CE16OV` LFS fallback; re-validate | OECD QNA employment (resolve Q-15) | Defer |
| Q-05 | Keep `HOANBS`, document nonfarm-business scope | OECD total hours when quarterly | Per-worker hours series | Defer |

No option is selected in this note. The current frozen chronology remains
`labels-v1` with the unchanged `USA_labels.csv` hash
`1a1b1f6a566cb2cffe7181cbc59ec20bd07d8ef25e0300d4dd2d96ceb749e29a`.
