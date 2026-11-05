# Decision Note: Q-02, Q-04, Q-05

Status: **decided and implemented in `labels-v2` (2026-11-04)**. The alternative
comparison below is retained as the evidence record. `labels-v1` is archived
byte-for-byte under `outputs/labels/archive/labels-v1/` and is not amended.

The three selections are:

| Question | Selected option | USA implementation |
|---|---|---|
| Q-02 | **Option B** — concept-correct replacement | Constructed real non-residential business fixed investment from BEA equipment + structures + intellectual property products, deflated by the non-residential implicit price deflator |
| Q-04 | **Option B** — concept-correct replacement | `CE16OV` household-survey employment, quarterly mean (the Q-04 LFS fallback) |
| Q-05 | **Option A** — keep and document | `HOANBS` retained; nonfarm-business sector coverage recorded as the known limitation |

Why these are the best-supported choices:

- **Q-02 B.** Q-02 explicitly forbids total GFCF. `PNFIC1` is the right concept but
  starts in 2007 and fails the 70% coverage gate. The BEA components are available
  from 1947 and the constructed series reproduces `PNFIC1` to under 0.02 billion
  over 2007Q1–2026Q3, so the concept is implemented without a coverage loss.
- **Q-04 B.** OECD QNA employment is not published for the USA (or Japan) in the
  checked dataflow; only Germany returned quarterly employment. `PAYEMS` is an
  establishment survey and is not the Q-04 fallback. `CE16OV` is the permitted LFS
  fallback and is the closest available concept.
- **Q-05 A.** `HOANBS` is the only full-coverage quarterly total-hours series on
  FRED. Q-05's formal rule excludes annual-only data; `HOANBS` is quarterly, and
  the narrower nonfarm-business sector is a documented coverage limitation rather
  than a rule breach. No alternative improves the total-hours concept.

The joint Q-02 + Q-04 re-validation is more stable than either one-at-a-time test:
it keeps all four episodes, moves only the 2009 trough one quarter earlier, and
raises quarter-level NBER F1 from 0.929 to 0.963. The one-at-a-time Q-02 test was
unstable (F1 0.743, nine false positives), which is why the combined package was
re-validated before freezing.

## Evidence base and limits

- Metadata, native frequency, first/last observation and coverage were read from
  FRED on 2026-11-04. Coverage is the share of the 144 quarters in 1990Q1–2025Q4
  with a complete observation at native frequency (monthly series need all three
  months).
- The one-at-a-time chronology sensitivity runs in §2–§4 are **read-only**.
  They replace one label input at a time, keep the frozen DFM, BBQ and diffusion
  parameters, and do not write to `data/clean` or `outputs`. The selected package
  was then re-run jointly (§5) before `labels-v2` was frozen.
- NBER agreement is a plausibility check, not the optimisation target (C-04,
  FW-06). A lower NBER score is a finding to discuss, not automatically a reason
  to reject a concept-correct series.
- The OECD QNA population/employment dataflow was checked directly on 2026-11-04
  (`DF_QNA_POP_EMPNC`); other JPN/DEU dataflow IDs remain unresolved (Q-15), so
  cross-country availability outside that check is stated as expected rather than
  confirmed.

## 1. At a glance

| Question | Current US series | Current concept | Main alternatives | Selection |
|---|---|---|---|---|
| Q-02 investment | `GPDIC1` in v1 (retired); constructed real non-residential total in v2 | Real **gross private domestic** investment: residential + inventories + business | Constructed real nonresidential total; `PNFIC1`; `PNFIC96`; `FPIC1`; equipment only | **Option B selected.** v1 was not Q-02 compliant; v2 uses the only full-coverage strict option. |
| Q-04 employment | `PAYEMS` in v1 (retired); `CE16OV` in v2 | v1: establishment-survey employees, total nonfarm; v2: household-survey employment | `CE16OV` (household/LFS); `PRS85006013` (nonfarm business); `CEU0500000001` (private establishment); BEA persons engaged; OECD QNA | **Option B selected.** US national-accounts quarterly employment is unavailable; `CE16OV` is the Q-04 LFS fallback. |
| Q-05 hours | `HOANBS` | Total hours, **nonfarm business** sector | `PRS85006023` (average weekly hours); `AWHNONAG` (production/nonsupervisory hours); `AWHAETP`; BEA annual hours; OECD total hours | **Option A selected.** Quarterly total hours; nonfarm-business coverage is documented. No FRED alternative improves the concept. |

## 2. Q-02 — business / non-residential fixed investment

**Frozen decision (quote).** "Strict: business (non-residential) fixed investment
only. Total GFCF is not substituted; where business investment is missing the
component counts as missing." (`decisions_log.csv`, Q-02.)

### v1 input: `GPDIC1` (retired)

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
| Constructed real non-residential total | `Y033RC1Q027SBEA` (equipment) + `B009RC1Q027SBEA` (structures) + `Y001RC1Q027SBEA` (intellectual property products), deflated by `A008RD3Q086SBEA` (non-residential implicit price deflator, 2017=100) | BEA NIPA via FRED | Q, SA | 1947Q1–2026Q3 | 144/144 (100%) | **Selected (Option B).** Concept-compliant. It is a derivation, not a single download. Over 2007Q1–2026Q3 it reproduces `PNFIC1` to within about 0.02 billion (mean absolute percentage error ≈ 0.0002%). |
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
| `GPDIC1` (v1) | 1990Q2–1991Q1; 2001Q1–2001Q4; 2007Q4–2009Q3; 2019Q4–2020Q2 | 13 | 2 | 0 | 0.986 | 0.867 | 1.000 | 0.929 |
| Constructed real non-residential | 1990Q1–1991Q2; 2000Q3–2002Q1; 2007Q2–2009Q3; 2019Q4–2020Q2 | 13 | 9 | 0 | 0.938 | 0.591 | 1.000 | 0.743 |
| Equipment only (real) | 1990Q1–1991Q2; 2007Q2–2009Q3; 2019Q3–2020Q2 | 10 | 7 | 3 | 0.931 | 0.588 | 0.769 | 0.667 |
| `PNFIC1` (not gate-compliant) | 1990Q1–1991Q2; 2001Q1–2002Q1; 2007Q2–2009Q3; 2019Q4–2020Q2 | 13 | 7 | 0 | 0.951 | 0.650 | 1.000 | 0.788 |

The strict alternatives move peaks 1–3 quarters earlier and add false positives
when replaced one at a time. That is why Q-02 was **not** frozen from this table
alone: the selected Q-02 + Q-04 package was re-validated jointly (§5), where it
keeps all four episodes and raises F1 to 0.963.

### Selected: Option B — constructed real non-residential total

Implemented in `labels-v2`. The series is derived inside `scripts/harmonize.py`
from four new downloads:

```
(Y033RC1Q027SBEA + B009RC1Q027SBEA + Y001RC1Q027SBEA)
-----------------------------------------------------
             A008RD3Q086SBEA / 100
```

- all four components: quarterly, SA, 1947Q1–2026Q3, 144/144 window coverage;
- reproduces `PNFIC1` over 2007Q1–2026Q3 with max absolute error < 0.02bn;
- recorded as `USA.ACT_INV.Q.STD` (status `DERIVED_AFTER_INPUTS`) in
  `data/series_resolution.csv`, with the four inputs in the manifest;
- `GPDIC1` retired to `data/superseded_series.csv`.

**Options considered (retained for the record).**

- **A. Keep `GPDIC1` and record an explicit deviation from Q-02.** Not selected:
  Q-02 explicitly forbids substituting total GFCF / broad investment.
- **B. Replace with the constructed real non-residential total and re-validate.**
  **Selected and implemented.**
- **C. Drop `ACT_INV` and run with seven indicators.** Not selected: unnecessary,
  because a full-coverage concept-compliant construction exists.
- **D. Defer.** Not selected: the evidence was sufficient to decide.

## 3. Q-04 — employment concept

**Frozen decision (quote).** "Employment: national-accounts quarterly employment
preferred, LFS monthly (quarterly mean) as fallback; one concept is locked per
country at the audit and counted once toward §19." (`decisions_log.csv`, Q-04.)

### v1 input: `PAYEMS` (retired)

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
| `CE16OV` | Employment Level, household survey (LFS analogue) | BLS CPS via FRED | M, SA | 1948M1–2026M9 | 143/144 (99.3%) | **Selected (Option B).** Q-04 **LFS fallback**. Includes self-employed and agricultural workers; CPS sample revisions can create breaks. |
| `PRS85006013` | Nonfarm Business Sector: Employment for All Workers | BLS productivity via FRED | Q, SA | 1947Q1–2026Q2 | 144/144 (100%) | Consistent with `HOANBS`/`OPHNFB`, but a **nonfarm business** concept: excludes government, nonprofit and agriculture. Not total economy. |
| `CEU0500000001` | All Employees, Total Private | BLS CES via FRED | M, NSA | 1939M1–2026M9 | 144/144 (100%) | Establishment concept, excludes government; NSA, so it would need X-13 under D-R07, and it is narrower than `PAYEMS`. |
| `A4601C0A173NBEA` | Persons engaged in production (BEA national accounts) | BEA via FRED | A, NSA | 1929–2022 | 132/144 (91.7%) | National-accounts concept, but **annual and ends 2022**. Q-05-style annual-only data are inadmissible without disaggregation; interpolation is forbidden (C-03). |
| OECD QNA employment | Employment, persons, quarterly | OECD | Q | Expected 1990+ | Unconfirmed | The Q-04 **preferred** concept. Dataflow IDs unresolved (Q-15). This is the only option that directly supports cross-country comparability. |

**Cross-country availability.** OECD QNA employment is the standard quarterly
source for JPN/DEU and is the concept Q-04 names first. A direct check of
`OECD.SDD.NAD,DSD_NAMAIN1@DF_QNA_POP_EMPNC,1.1` on 2026-11-04 returned quarterly
employment for **Germany only** (1991Q1–2022Q4); the USA and Japan returned no
employment observations in that dataflow. The US BEA "persons engaged" series is
annual and ends 2022. A US national-accounts switch is therefore not available,
and `CE16OV` is the Q-04 fallback. `PAYEMS`, `CE16OV` and `PRS85006013` are all
US-only; JPN and DEU will be audited against their own QNA/LFS availability.

**Chronology sensitivity (one input replaced, current parameters).**

| ACT_EMP series | Label episodes 1990–2025 | TP | FP | FN | Accuracy | Precision | Recall | F1 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| `PAYEMS` (v1) | 1990Q2–1991Q1; 2001Q1–2001Q4; 2007Q4–2009Q3; 2019Q4–2020Q2 | 13 | 2 | 0 | 0.986 | 0.867 | 1.000 | 0.929 |
| `CE16OV` | 1990Q2–1991Q1; 2000Q4–2001Q4; 2007Q4–2009Q3; 2019Q4–2020Q2 | 13 | 3 | 0 | 0.979 | 0.812 | 1.000 | 0.897 |
| `PRS85006013` | 1990Q1–1991Q2; 2007Q2–2009Q3; 2019Q4–2020Q2 | 10 | 6 | 3 | 0.938 | 0.625 | 0.769 | 0.690 |
| `CEU0500000001` | 1990Q2–1991Q1; 2000Q4–2001Q4; 2007Q4–2009Q2; 2019Q4–2020Q2 | 13 | 2 | 0 | 0.986 | 0.867 | 1.000 | 0.929 |

`CE16OV` is the lowest-cost conceptual improvement: one extra false-positive
quarter and the 2001 peak moves one quarter earlier in the one-at-a-time test.
`PRS85006013` is too narrow and misses 2001. `CEU0500000001` matches the current
quarter-level metrics but is private-only and NSA. Because the one-at-a-time
`CE16OV` test was no better than v1 on F1, it was re-validated jointly with Q-02
(§5), where the package reaches F1 0.963.

### Selected: Option B — `CE16OV` LFS fallback

Implemented in `labels-v2`:

- source `CE16OV`, monthly SA, aggregated to a quarterly mean with the
  complete-quarter rule; 143/144 (99.3%) window coverage;
- recorded as `USA.ACT_EMP.Q.NA` in the manifest; `PAYEMS` retired to
  `data/superseded_series.csv`;
- one concept is locked for the USA: household-survey employment, not a blend
  with the establishment series.

**Options considered (retained for the record).**

- **A. Keep `PAYEMS` and record an explicit deviation from Q-04.** Not selected:
  `PAYEMS` is an establishment survey, not the named LFS fallback.
- **B. Replace with `CE16OV` and re-validate.** **Selected and implemented.**
- **C. Resolve Q-15 and use OECD QNA employment for USA, JPN and DEU.** Not
  selected for the USA: the checked OECD QNA dataflow returns no US employment.
  Germany can use QNA; Japan will use its own audit.
- **D. Defer.** Not selected: the US source could be settled now.

## 4. Q-05 — hours worked

**Frozen decision (quote).** "Quarterly total hours only. Annual-only means the
component is missing; no temporal disaggregation." (`decisions_log.csv`, Q-05.)
The indicator definition also says "Total hours worked, whole economy"
(`spec.py`, `ACT_HOURS`).

### Selected input: `HOANBS` (kept from v1)

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
| `HOANBS` (v1 and v2) | 1990Q2–1991Q1; 2001Q1–2001Q4; 2007Q4–2009Q3; 2019Q4–2020Q2 | 13 | 2 | 0 | 0.986 | 0.867 | 1.000 | 0.929 |
| `PRS85006023` | 1990Q2–1991Q1; 2000Q4–2001Q4; 2007Q4–2009Q2; 2019Q4–2020Q2 | 13 | 2 | 0 | 0.986 | 0.867 | 1.000 | 0.929 |
| `AWHNONAG` | 1990Q2–1991Q1; 2000Q4–2001Q4; 2007Q4–2009Q2; 2019Q4–2020Q2 | 13 | 2 | 0 | 0.986 | 0.867 | 1.000 | 0.929 |

The per-worker series leave the quarter-level metrics unchanged in this
one-at-a-time test, but move the 2001 peak one quarter earlier and the 2009
trough one quarter earlier. They also change what the factor measures: total
labour input versus hours per worker. That is a concept change, not a data
upgrade.

### Selected: Option A — keep `HOANBS`

Retained unchanged in `labels-v2`:

- quarterly, SA, 144/144 window coverage, 1947Q1–2026Q2;
- concept is total hours in the **nonfarm business** sector, not whole economy;
- Q-05's formal rule only excludes annual-only data, so `HOANBS` passes;
- the sector limitation is recorded in `labels-v2.json` and
  `data/series_resolution.csv`. JPN/DEU will use OECD total hours where it is
  quarterly; annual-only data remain missing.

**Options considered (retained for the record).**

- **A. Keep `HOANBS` and record the sector-coverage limitation.** **Selected.**
- **B. Use OECD total hours worked when it is available quarterly.** Not selected
  for the USA: the available FRED sources do not provide a US whole-economy
  quarterly series. This remains the cross-country option for JPN/DEU.
- **C. Switch to a per-worker hours series.** Not selected: it changes the
  concept from total labour input to hours per worker.
- **D. Defer.** Not selected: keeping a rule-compliant quarterly series requires
  no re-freeze driver.

## 5. What the selected change required

The selected package was implemented in this order:

1. Added the four Q-02 components and `CE16OV` to `scripts/fetch_fred.py`,
   `data/series_resolution.csv`, `data/manifest.csv` and
   `data/fred_verification.csv`; retired `GPDIC1` and `PAYEMS` into
   `data/superseded_series.csv`.
2. Added the Q-02 derivation to `scripts/harmonize.py`. The eight BEAI indicator
   ids and `config/indicators.yaml` semantics are unchanged.
3. Re-ran `make fetch`, `make harmonize`, `make labels` and `make validate`.
4. Re-ran the robustness variants and the frozen-artefact tests. `labels-v1` was
   archived first and remains byte-identical under
   `outputs/labels/archive/labels-v1/`; `labels-v2.json` records the archived v1
   label hash.
5. Updated `docs/DECISIONS.md`, `docs/LABEL_VALIDATION.md`, `docs/STATE.md`,
   `docs/VERIFICATION.md`, `README.md` and this note.

**Joint Q-02 + Q-04 re-validation (selected package).**

| Variant | Label episodes 1990–2025 | TP | FP | FN | Accuracy | Precision | Recall | F1 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| `labels-v1` (`GPDIC1` + `PAYEMS`) | 1990Q2–1991Q1; 2001Q1–2001Q4; 2007Q4–2009Q3; 2019Q4–2020Q2 | 13 | 2 | 0 | 0.986 | 0.867 | 1.000 | 0.929 |
| `labels-v2` (constructed INV + `CE16OV`) | 1990Q2–1991Q1; 2001Q1–2001Q4; 2007Q4–2009Q2; 2019Q4–2020Q2 | 13 | 1 | 0 | 0.993 | 0.929 | 1.000 | 0.963 |
| Q-02 only | 1990Q1–1991Q2; 2000Q3–2002Q1; 2007Q2–2009Q3; 2019Q4–2020Q2 | 13 | 9 | 0 | 0.938 | 0.591 | 1.000 | 0.743 |
| Q-04 only | 1990Q2–1991Q1; 2000Q4–2001Q4; 2007Q4–2009Q3; 2019Q4–2020Q2 | 13 | 3 | 0 | 0.979 | 0.812 | 1.000 | 0.897 |

The factor correlation between v1 and the selected package over 1990Q1–2025Q4 is
0.9966, and the level correlation is 0.9982. The only date change is the 2009
trough, which moves from 2009Q3 to 2009Q2 and now matches NBER exactly. The
selected package is stable, and NBER agreement is a plausibility check rather
than the optimisation target (C-04, FW-06).

## 6. Decision record

| Question | Selected option | Rationale |
|---|---|---|
| Q-02 | **B — constructed real non-residential business fixed investment** | Q-02 forbids total GFCF; `PNFIC1` is too short; the construction is full-coverage and reproduces `PNFIC1` to <0.02bn |
| Q-04 | **B — `CE16OV` LFS fallback** | OECD QNA employment is unavailable for the USA; `PAYEMS` is an establishment survey, not the Q-04 fallback |
| Q-05 | **A — keep `HOANBS`** | Only full-coverage quarterly total-hours series; Q-05 bars annual-only data, not narrower sector coverage |

Decisions are recorded in `decisions_log.csv` (Q-02, Q-04, Q-05) and
`docs/DECISIONS.md` (D-R26–D-R28). The active chronology is `labels-v2`
(`USA_labels.csv` SHA-256
`f5ed42a6c4333aaecbae4fae1f5f6fcab3606ce46dd2b459791a6aa31816dc8e`).
`labels-v1` remains archived with its original hash
`1a1b1f6a566cb2cffe7181cbc59ec20bd07d8ef25e0300d4dd2d96ceb749e29a`.
