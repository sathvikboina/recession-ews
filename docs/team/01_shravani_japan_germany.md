# Lane Brief 1 — Japan and Germany Labels

**Owner:** Shravani Math
**Role:** Data and label lead
**Lane:** Part 1 of the one-week sprint
**Dates:** Days 1–5 individual; Days 6–7 shared merge and review
**Branch:** `feat/jpn-deu-labels`

---

## 1. Your mission in one paragraph

Build the recession answer key for Japan with the **frozen** estimator, and resolve Germany
far enough to either build its label or write a complete 6-of-8 coverage finding. Japan is
the priority. Germany is a stretch goal, and a complete coverage note is an acceptable
deliverable. You also own the small refactor that lets the existing USA pipeline run for
another country without forking the label math.

## 2. What has already happened (so you do not repeat it)

- **The USA label is built, validated and frozen.** `labels-v3` covers 1990Q1–2026Q3
  (147 quarters), matches all four NBER recessions since 1990, and has zero false episodes.
  Accuracy is 0.993, precision 0.929, recall 1.000, F1 0.963.
- **The estimator is frozen.** One-factor `DynamicFactorMQ`, smoothed factor, BBQ with
  min phase 2, min cycle 5, endpoint censoring 2, diffusion gate 0.50. D-R22–D-R31 record
  the decisions. Do not change them for Japan or Germany.
- **The USA data choices are settled.** Q-02 uses constructed real non-residential business
  fixed investment; Q-04 uses `CE16OV`; Q-05 keeps `HOANBS` with its coverage limitation
  documented. These are USA choices, not automatic choices for Japan or Germany.
- **`labels-v1` and `labels-v2` are archived byte-identically.** `labels-v3` is active. The
  freeze guard refuses to overwrite a frozen label when the canonical input digest changes.
- **The country plumbing is not general yet.** `scripts/harmonize.py` and
  `scripts/03_labels.py` currently hard-code the USA. The label builder itself
  (`src/ews/labels/build.py`) accepts a `country` argument, so the estimator is reusable.
  Generalising the scripts — or adding thin JPN/DEU wrappers — is your Day 1 task.
- **Japan and Germany data are not collected yet.** The scope has 21 JPN and 21 DEU rows.
  The source IDs for JPN/DEU still need verification; do not guess them.
- **India is not your lane.** The India pre-audit finds a best case of 4/8, so India is a
  Label-B case study under O-2. Do not spend your week on India.

**Read first:** `docs/BUILD_CONTRACT.md` (C-01–C-13), `docs/DECISIONS.md`
(D-R22–D-R31), `docs/LABEL_VALIDATION.md`, `scripts/03_labels.py`, `scripts/harmonize.py`,
`src/ews/labels/build.py`, `src/ews/labels/freeze.py`.

## 3. What you own: Days 1–5

| Day | Task | Output | Done when |
|---|---|---|---|
| 1 | Map Japan sources **and** generalise the country plumbing | Japan source map; country-parameterised `scripts/harmonize.py` and `scripts/03_labels.py` (or wrappers); naming convention | 21/21 Japan rows have a source or a written pending reason; USA `labels-v3` hash unchanged after the refactor |
| 2 | Download and harmonise Japan | Raw downloads, manifest rows, JPN levels/growth, coverage table | 6/8 core indicators at ≥70% of 147 quarters (≥103) or a documented failure; no interpolation |
| 3 | Build and freeze the Japan label | `outputs/labels/JPN/*`, `docs/LABEL_VALIDATION_JPN.md` | Label reproducible; ESRI chronology comparison written; `labels-v1-JPN` frozen with hashes |
| 4 | Map and download Germany | DEU source map and clean panel | 21/21 rows resolved or pending with a reason; 1990–91 reunification break documented |
| 5 | Germany coverage and label decision | DEU coverage note, label if eligible, hand-off note | Gate decision recorded; no rule relaxation; hashes listed |

### Suggested daily rhythm

- **09:30 — 15-minute stand-up.** Say what you finished, what you will do, and what is
  blocking you. Ask for help early.
- **Work in small commits.** One logical change per commit; run the relevant tests.
- **17:30 — short hand-off note.** What changed, what is reproducible, what is still open.
- **Day 6:** merge your own branch in the fixed order. **Day 7:** cross-review and sign off.

## 4. What we expect by Day 5

A complete Part 1 hand-off contains:

1. **Japan source map.** One active source row per scope key, with frequency, seasonal
   adjustment, first/last date, retrieval date and SHA-256.
2. **Japan clean panel.** Quarterly, complete quarters only, no interpolation, no forward
   fill. The coverage table shows the 6/8 count and the window share.
3. **Japan label.** `outputs/labels/JPN/JPN_labels.csv`, episodes, turning points and a
   metadata JSON. The estimator, BBQ and diffusion settings are the frozen ones.
4. **Japan chronology note.** `docs/LABEL_VALIDATION_JPN.md`: method, ESRI comparison,
   discrepancies, caveats. Say "validated label", not "forecast".
5. **Germany decision.** Either a frozen German label if 6/8 passes, or a complete coverage
   note naming the missing indicators and the evidence. Do not fake a label.
6. **Evidence that the USA did not move.** Re-run the USA label hash check after the
   country-plumbing refactor. `labels-v3` must stay byte-identical.
7. **A PR on `feat/jpn-deu-labels`** with the commands run, tests passed, hashes changed and
   known gaps.

### How your lane is judged

- **Label gate:** Japan (and Germany if attempted) needs ≥6 of 8 core indicators at ≥70% of
  the 147-quarter window (≥103 quarters), plus a sensible chronology check.
- **Reproducibility:** a fresh run from the raw files and the documented commands produces
  the same label and hashes.
- **Honesty:** a failed gate is written down clearly. A missing indicator is a finding, not
  an exception.
- **No collateral change:** the USA label, the estimator and the eight-indicator structure
  are unchanged.

## 5. How your work combines with the others

| Hand-off | When | What must be true |
|---|---|---|
| H1: Sathvik → all | Day 1 morning | You can state your Day 1 task from this brief and `docs/TEAM_PLAN.md` |
| H3: you → Sathvik | Day 5 end | Japan label + chronology note + Germany 6/8 decision; hashes recorded |
| H6: all → Sathvik + Arshiya | Day 6 morning | One branch, green checks, short hand-off note |
| Day 6 merge | Step 1 | You merge `feat/jpn-deu-labels` first; the team checks label hashes and chronology |
| Day 7 review | — | Arshiya cross-reviews your label lane; write findings, not verbal comments |

Your outputs feed Part 2 (clean activity panels), Part 3 (labels as the target) and Part 4
(the final story). If Japan lands but Germany does not, that is still a usable result: Japan
becomes the second country, Germany becomes a documented coverage finding.

## 6. DOs

- **DO** read `docs/BUILD_CONTRACT.md` and `docs/DECISIONS.md` before writing code.
- **DO** generalise the pipeline by parameter, not by copying the estimator math.
- **DO** keep the USA label byte-identical and prove it with a hash check.
- **DO** use official sources (BOJ, e-Stat, Cabinet Office, OECD, Destatis, BIS) and record
  the exact series ID, retrieval date and SHA-256.
- **DO** apply the complete-quarter rule and leave missing values missing.
- **DO** write a short note for every non-obvious choice and every failed source.
- **DO** add or update tests for the country plumbing and the coverage gate.
- **DO** ask for help on Day 1 if the refactor or a source key is unclear.
- **DO** commit small and keep the branch rebased on `main`.

## 7. DON'Ts

- **DON'T** change the estimator, BBQ parameters, diffusion gate or the eight-indicator
  structure without a new version and a recorded decision.
- **DON'T** relax the 6-of-8 rule or hide a failed country.
- **DON'T** interpolate, forward-fill or impute a partial quarter.
- **DON'T** overwrite `labels-v3`, `labels-v2` or `labels-v1`.
- **DON'T** fork the label math into a separate JPN script that will drift.
- **DON'T** commit restricted raw data; commit metadata, manifests and hashes only.
- **DON'T** claim a forecast or a cross-country result before the out-of-sample work exists.
- **DON'T** silently take over another lane or merge a red branch.

## 8. Allowed creative liberty and educational freedom

You are not a robot following a checklist. Inside the guardrails:

- **Choose your implementation.** Parameterising the existing scripts and adding thin
  wrappers are both acceptable. Pick the one you can test and explain.
- **Add useful extras.** A source-map table, a coverage plot, a short "Japan data notes"
  page, a glossary of Japanese series names, or a small notebook are welcome.
- **Learn while you work.** You may spend up to about half a day (roughly 10% of the lane)
  on the DFM, `statsmodels`, Japanese source documentation or a reproducibility tool. Note
  it in your hand-off.
- **Try an alternative source** if the first choice is blocked, as long as you document the
  substitution and do not relax the coverage rule.
- **Propose a better interface** for country labels before you build it. If it changes a
  shared output, raise it at the stand-up and record it.
- **Write a "what I learned" section** in your chronology note. It helps the next person.

## 9. If you get stuck

1. **Source key unclear?** Write the exact question and the candidate IDs in your note; ask
   the team before guessing.
2. **Refactor getting large?** Protect Japan first. A thin wrapper that reuses the estimator
   is better than a perfect abstraction that misses the week.
3. **Coverage fails?** Write the missing indicators, the window share and the evidence. That
   is a real result, not a failure of the lane.
4. **USA hash moves?** Stop. Fix the cause before continuing. Never patch the hash or the
   label by hand.
5. **Blocked for more than half a day?** Say so at the stand-up. Do not hide it until Day 5.

## 10. Where to look

| Need | File |
|---|---|
| Frozen rules | `docs/BUILD_CONTRACT.md` |
| Decisions and rationale | `docs/DECISIONS.md` |
| USA label evidence | `docs/LABEL_VALIDATION.md` |
| Q-02/Q-04/Q-05 detail | `docs/DECISION_NOTE_Q02_Q04_Q05.md` |
| USA label builder | `scripts/03_labels.py`, `src/ews/labels/build.py` |
| Freeze guard | `src/ews/labels/freeze.py` |
| Harmoniser | `scripts/harmonize.py` |
| Scope and sources | `config/scope.yaml`, `data/scope.csv`, `data/series_resolution.csv` |
| Team plan | `docs/TEAM_PLAN.md`, `Team_Plan.xlsx` |
| Weekly log | `EWS_Work_Log.xlsx` |

---

**Bottom line:** Japan is the deliverable; Germany is a bonus or a well-documented
coverage finding. Reuse the frozen estimator, keep the USA untouched, and write down every
source and every failure. A clear "we could not get 6/8, here is why" is a successful week.
