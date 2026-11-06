# India Coverage Audit (Pre-Collection)

Status: **provisional pre-audit, 2026-11-05.** India is a Tier-1 country in
`config/scope.yaml`, but it is not enabled for the current build. This note checks
whether India can pass the §19 gate before the team spends collection effort on it.

Target window: 1990Q1–2026Q3 = **147 quarters**. The gate is **≥6 of the 8 BEAI
indicators, each with ≥70% coverage** (≥103 quarters). Q-06 says the rule is not
relaxed for India or China.

## 1. What the evidence already shows

The catalogue has nine India core rows (two employment variants), but every
coverage field is still `PENDING_VERIFICATION`. The source documentation is
enough to bound the answer.

| BEAI indicator | Candidate source | Documented quarterly history | Best-case window coverage | Verdict |
|---|---|---|---|---|
| `ACT_GDP_REAL` | MoSPI quarterly national accounts | Quarterly from 1996-97; new base 2022-23 | 1996Q2–2025Q4 = at least 119/147 = **81.0%** | **Pass** |
| `ACT_IP` | MoSPI IIP, monthly | Monthly IIP with base changes; start date to verify | Likely ≥70%; needs a source check | **Likely pass** |
| `ACT_EMP` | PLFS / national accounts | PLFS quarterly urban-only from 2017; rural+urban only from 2025 | 2017Q3–2025Q4 ≈ 34/147 = **23.1%** | **Fail** |
| `ACT_HOURS` | No confirmed official quarterly total-hours series | None confirmed | 0% | **Fail** |
| `ACT_RINC` | No confirmed quarterly household disposable income | None confirmed | 0% | **Fail** |
| `ACT_CONS` | MoSPI quarterly PFCE | Quarterly from 1996-97 | 1996Q2–2025Q4 = at least 119/147 = **81.0%** | **Pass** |
| `ACT_RETAIL` | No confirmed official monthly retail sales index | None confirmed for the required window | 0% | **Fail** |
| `ACT_INV` | MoSPI quarterly GFCF | Quarterly from 1996-97, but a **business / non-residential split is not confirmed** | 81.0% only if the split exists; otherwise missing under Q-02 | **Pass only if the Q-02 split exists; otherwise fail** |

## 2. The gate result

Even under the most generous reading:

- confirmed passes: GDP, consumption (2);
- likely passes: industrial production, investment (2);
- structural failures: employment, hours, income, retail (4).

**Best case = 4 of 8, which is below the required 6 of 8.** If the business
investment split is unavailable, the best case is 3 of 8. India therefore cannot
build a BEAI-based Label A in this project, regardless of how well GDP, IIP,
consumption or investment are downloaded.

The result is structural, not a temporary data gap:

- PLFS quarterly history starts in 2017 and is urban-only until the 2025 revamp;
- there is no continuous pre-2017 all-India quarterly employment series;
- no official quarterly total-hours series is confirmed;
- no quarterly household disposable-income series is confirmed;
- no official monthly retail sales index covering the window is confirmed.

## 3. Decision

This is a coverage finding, not a bug and not a reason to relax §19.

| Item | Decision |
|---|---|
| Q-06 / §19 | Do not relax the 6-of-8 gate for India. |
| Label A (BEAI) | India is **not eligible**; do not build a BEAI label for India. |
| O-2 default | India remains a **Label-B-only case study**, reported as a coverage finding. |
| Cross-country story | The label countries for the first build are **USA, JPN and DEU**. India is a case study, not a fourth label. |
| Scope | India stays in the dictionary and coverage reporting. It does not enter the label pipeline. |

This changes the narrative from "four-country labels" to "three-country labels plus
an India coverage case study." The change must be stated in the README, the
proposal addendum and the final report. It should not be hidden as a missing row.

## 4. Evidence and source notes

- MoSPI quarterly national accounts methodology: quarterly GDP/GVA starts with
  1996-97; the new national-accounts series has base 2022-23 and new-series
  quarterly estimates from Q1 FY2022-23. The full back series was reported as due
  by December 2026.
- PLFS: quarterly urban-only from 2017; monthly bulletins from April 2025;
  quarterly rural+urban from April–June 2025. No continuous pre-2017 all-India
  quarterly series is confirmed.
- MoSPI IIP is monthly with base changes (2011-12, then 2022-23 reported). The
  exact current-series start date must be verified at download.
- India's national accounts publish PFCE and GFCF quarterly from 1996-97, but a
  business/non-residential investment split is not confirmed in the catalogue.
- No official monthly retail sales index covering 1990–2026 is confirmed. The
  Index of Services Production trial release (2026) is too recent and is not a
  substitute under Q-03.

These facts are consistent with `verification_log.csv` V-03, V-04 and V-06 and
with the India notes in `build.py`/`spec.py`. They are provisional until the
actual series are downloaded, but the four structural failures above do not
depend on the download result.

## 5. What Part 4 of the team plan must still do

1. Download the candidate MoSPI/RBI series and fill
   `data/india_core_coverage.csv` with actual first/last dates, native frequency,
   coverage and status.
2. Confirm whether a quarterly business/non-residential GFCF split exists. If it
   does not, mark `ACT_INV` missing under Q-02, not as total GFCF.
3. Confirm whether any official monthly retail series covers the window. If not,
   leave `ACT_RETAIL` missing.
4. Recompute the 6-of-8 count from the downloaded data, not from this note.
5. Record the final result in `decisions_log.csv`, `unresolved_questions.csv` and
   `docs/VERIFICATION.md`. Keep O-2 as Label-B-only unless the evidence changes.
6. Report India in the final write-up as a coverage case study, with the four
   missing indicators named.

## 6. Why this is worth doing now

The biggest risk in the project is discovering after the model work that a
Tier-1 country cannot produce a label. The pre-audit removes that risk early. It
also stops the team from spending a week on a country that cannot pass a rule the
project has already decided not to relax.
