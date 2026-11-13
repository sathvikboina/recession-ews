# India Coverage Audit (Downloaded Data)

Status: **final downloaded-data audit, 2026-11-13.** India is a Tier-1 country in
`config/scope.yaml`, but it is not enabled for the current build. This note replaces
the 2026-11-05 pre-audit and records what the official machine-readable sources
actually return.

Target window: 1990Q1–2026Q3 = **147 quarters**. The §19 gate is **at least 6 of the
8 BEAI indicators, each with at least 70% coverage** (at least 103 quarters). Q-06
says the rule is not relaxed for India or China.

## 1. Result

**India passes 1 of 8 indicators (industrial production only).** The 6-of-8 gate is
not met, so India remains Label-B-only under O-2. No proxy, carry-forward or
relaxation is used.

| BEAI indicator | Downloaded source | Native freq. | First–last | Quarters | Share of 147 | Verdict |
|---|---|---|---:|---|---:|---:|---|
| `ACT_GDP_REAL` | MoSPI NAS, GDP (`indicator_code=5`) | Q | 2011Q2–2026Q2 | 61 | 41.5% | **Fail** — below 70% |
| `ACT_IP` | MoSPI IIP, General (`category_code=4`) | M | 1994Q2–2026Q3 | 130 | 88.4% | **Pass** |
| `ACT_EMP` (monthly) | MoSPI PLFS monthly, UR (`indicator_code=3`) | M | 2025Q2–2026Q3 | 6 | 4.1% | **Fail** — below 70% |
| `ACT_EMP` (quarterly) | MoSPI PLFS quarterly, UR (`indicator_code=3`) | Q | 2018Q2–2026Q3 | 33 | 22.4% | **Fail** — below 70% |
| `ACT_HOURS` | No official quarterly total-hours series found | — | — | 0 | 0.0% | **Fail** — no series |
| `ACT_RINC` | No official quarterly household income series found | — | — | 0 | 0.0% | **Fail** — no series |
| `ACT_CONS` | MoSPI NAS, PFCE (`indicator_code=10`) | Q | 2011Q2–2026Q2 | 61 | 41.5% | **Fail** — below 70% |
| `ACT_RETAIL` | No official monthly retail sales index found | — | — | 0 | 0.0% | **Fail** — no series |
| `ACT_INV` | MoSPI NAS, GFCF (`indicator_code=9`) | Q | 2011Q2–2026Q2 | 61 | 41.5% | **Fail** — below 70% and no business split |

Count by indicator, not by catalogue row: **1 of 8** (`ACT_IP`). The two employment
variants are one indicator and both fail.

The full row-level evidence is in `data/india_core_coverage.csv`, with the exact
query URL and the access note for every row.

## 2. What changed from the pre-audit

The 2026-11-05 pre-audit assumed quarterly national accounts from 1996-97 and put
the best case at 4/8. The downloaded data does not support that assumption:

- The MoSPI NAS API publishes quarterly data only for base years **2011-12** and
  **2022-23**. The 2011-12 *Back* series is **annual only** (1950-51 to 2011-12), and
  an annual series cannot be disaggregated into quarters under C-06.
- Quarterly GDP, PFCE and GFCF therefore cover 2011Q2–2026Q2 = **61 quarters
  (41.5%)**, not 83%.
- The RBI API catalogue exposed by eSankhyiki contains trade, balance-of-payments,
  exchange-rate, debt and reserve series only. It has no GDP, consumption, investment,
  employment or retail series.
- The RBI DBIE portal is reachable, but its modern interface is an interactive
  Angular application. No documented bulk time-series endpoint was found in the
  sprint, so it is recorded as an access limitation, not as downloaded evidence.
- The pre-audit's employment, hours, income and retail failures are confirmed:
  quarterly PLFS starts in 2018Q2, monthly PLFS in April 2025, PLFS wage indicators
  are annual, and no official monthly retail sales index exists.

Even if a legacy quarterly NAS back series were retrieved from RBI DBIE later, the
maximum would be 5 of 8 (GDP, IIP, consumption, investment) minus investment unless
a quarterly business/non-residential split exists. That is still below 6 of 8, so the
decision does not depend on the unresolved legacy path. The current downloaded-data
count is the conservative, reproducible figure.

## 3. Two specific Q-02 / Q-03 checks

- **Q-02 investment split.** Adding `institutional_code=1` (public non-financial
  corporations), `2` (private non-financial corporations), `6` (households) or `9`
  (total GFCF) to the quarterly GFCF query all return `No Data Found`. There is no
  quarterly business/non-residential split. Total GFCF is not an acceptable proxy.
- **Q-03 retail.** The MoSPI product list (NAS, CPI, IIP, PLFS, ASI, HCES, NSS rounds)
  and the RBI API catalogue contain no monthly retail sales index. CPI is a price
  index, not a retail volume. Cards, GST e-way bills and auto sales are barred
  proxies. The 2026 Index of Services Production trial is too recent and is not a
  retail series.

## 4. Decision

This is a coverage finding, not a bug, and not a reason to relax §19.

| Item | Decision |
|---|---|
| Q-06 / §19 | Do not relax the 6-of-8 gate for India. |
| Final count | **1 of 8** from downloaded evidence (`ACT_IP` only). |
| Label A (BEAI) | India is **not eligible**; do not build a BEAI label for India. |
| O-2 | India remains a **Label-B-only case study**, reported as a coverage finding. |
| Cross-country story | Label countries for the first build are **USA, JPN and DEU**. India is a case study, not a fourth label. |
| Scope | India stays in the dictionary and coverage reporting; it does not enter the label pipeline. |

The narrative is "three label countries plus an India coverage case study." That
wording must appear in the README, the proposal addendum and the final report. It
should not be hidden as a missing row.

## 5. Evidence and retrieval

All queries were made on 2026-11-13 against `https://api.mospi.gov.in/api`. Raw
responses are in `/tmp/opencode/india/raw/` for this session; the checked-in
evidence is `data/india_core_coverage.csv`.

| Query | Result |
|---|---|
| NAS `indicator_code=5&frequency_code=2&base_year=2011-12` | 58 rows, 2011-12 Q1 to 2025-26 Q2 |
| NAS `indicator_code=5&frequency_code=2&base_year=2022-23` | 17 rows, 2022-23 Q1 to 2026-27 Q1 |
| NAS `indicator_code=5&frequency_code=1&series=Back` | 62 annual rows, 1950-51 to 2011-12 |
| NAS `indicator_code=9` / `10`, quarterly | Same 2011Q2–2026Q2 span |
| NAS GFCF with `institutional_code=1,2,6,9` | `No Data Found` |
| IIP monthly, `category_code=4`, four base years | 390 months, 1994-04 to 2026-09, no internal gaps |
| PLFS quarterly, `indicator_code=3` | 33 quarters, 2018Q2–2026Q3, 2025Q1 absent |
| PLFS monthly, `indicator_code=3` | Starts April 2025 |
| RBI `getRbiIndicatorList` | No core macro series (trade, BoP, FX, debt, reserves only) |

Access failures and absences are recorded exactly as observed. No series ID was
invented, and no value was interpolated.

## 6. What Part 4 closes

1. `data/india_core_coverage.csv` is filled from downloaded responses.
2. The quarterly business/non-residential GFCF split is confirmed absent.
3. No official monthly retail series covering the window is confirmed.
4. The 6-of-8 count is recomputed from downloaded data: **1 of 8**.
5. Q-06, Q-07, Q-08 and Q-09 are closed in `decisions_log.csv` and
   `unresolved_questions.csv`; `docs/VERIFICATION.md` carries the evidence.
6. India is reported in the final write-up as a coverage case study with the seven
   missing indicators named.
