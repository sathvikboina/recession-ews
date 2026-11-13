# Lane Brief 2 — Feature Table and Walk-Forward Harness

**Owner:** Arshiya
**Role:** ML engineering lead
**Lane:** Part 2 of the one-week sprint
**Dates:** Days 1–5 individual; Days 6–7 shared merge and review
**Branch:** `feat/features-harness`

---

## 1. Your mission in one paragraph

Turn the verified panel into a **predictor-only** table and a fair time-based test harness
on the extended 2026Q3 window. The table must contain no label outputs, no NBER chronology,
no future information, no country ID and no country-size level. Raw BEAI-eligible activity
series are allowed **only** as separate, versioned predictor copies with their own transform
and availability lag. You also own the combined clean-clone check on Day 7.

## 2. What has already happened (so you do not repeat it)

- **The USA clean panel exists.** `data/clean/USA_panel.csv` and `USA_levels.parquet` hold
  the predictor/non-label panel; `USA_growth.parquet` holds the eight label-ready activity
  growth series; `USA_validation.parquet` holds `USA.NBER.Q` and stays out of the feature
  panel. The panel runs through 2026Q3.
- **The USA label is frozen as `labels-v3`.** It covers 1990Q1–2026Q3 (147 quarters), matches
  4/4 NBER recessions and has zero false episodes. Do not rebuild or edit it.
- **The firewall is settled.** C-01 and FW-04 allow raw BEAI-eligible series in Pipeline B
  only as separate copies with their own transform and lag. BEAI-derived outputs — factor,
  `R`, turning-point flags, diffusion — are never predictors. NBER is a validation series,
  not a feature.
- **The 2026 extension is complete.** FRED observations run through 2026-09; the last
  complete quarter is 2026Q3. The extension did not create a new false episode.
- **No feature table and no folds exist yet.** This lane starts from the clean panel, not
  from a half-built feature file. There are no model scores yet.
- **The test suite and CI exist.** 38 tests pass in the working tree; `make check` gives
  33 ok, 3 warnings (optional model packages), 0 failures. A fresh clone shows 36 passed and
  2 explicit skips until the git-ignored `data/clean` is rebuilt.
- **The label is the target, not an input.** Do not use `R`, the factor, the level, the
  diffusion value or any turning-point flag as a feature.

**Read first:** `docs/BUILD_CONTRACT.md` (C-01, C-05, C-06, C-07, C-08, C-11),
`docs/DECISIONS.md` (D-R05, D-R06, D-R08, D-R12–D-R18, D-R22–D-R31),
`data/clean/USA_panel.csv`, `scripts/harmonize.py`, `config/scope.yaml`.

## 3. What you own: Days 1–5

| Day | Task | Output | Done when |
|---|---|---|---|
| 1 | Write the feature spec and audit the 2026 extension | Feature spec and column list | Every column has a source, transform and lag; no BEAI-derived output or NBER input; allowed raw copies documented |
| 2 | Build the USA feature table | `src/ews/features.py`, `scripts/05_features.py`, `dataset.parquet`, `make features` target | One row per USA quarter, 1990Q1–2026Q3; unscaled; keys and row count check out; allowed copies labelled |
| 3 | Add leakage tests and a draft fold file | `tests/test_features.py`, draft `folds.json` | Leakage tests pass; a deliberately leaking table fails; no BEAI-derived or NBER column |
| 4 | Build final expanding-window folds **and** run the dry-run clean clone of current `main` | `src/ews/harness.py`, `scripts/06_folds.py`, final `folds.json`, `make folds` target, dry-run note | `make folds` runs; no test row in training; Part 3 can run the USA headline; current `main` passes the checks |
| 5 | Add baselines, freeze the table/folds, write the feature dictionary and hand-off note | Feature dictionary, frozen hand-off | Part 3 runs from the handed files and a seed; if the frozen files differ from Day 4, Part 3 reruns |

### Suggested daily rhythm

- **09:30 — 15-minute stand-up.** What you finished, what is next, what is blocking you.
- **Small commits.** One logical change at a time; run the leakage tests after each change.
- **17:30 — short hand-off note.** What changed, what is reproducible, what is open.
- **Day 6:** merge your own branch. **Day 7:** run the combined clean clone and sign off.

## 4. What we expect by Day 5

A complete Part 2 hand-off contains:

1. **Feature specification.** Predictor list, transforms, lags, missing-data rules and the
   exact reason each column is safe. The 2026 audit is written down.
2. **USA feature table.** `data/clean/dataset.parquet`, one row per USA quarter,
   1990Q1–2026Q3, unscaled values only. No label output, no NBER, no future observation, no
   country ID, no country-size level.
3. **Allowed raw copies.** The eight BEAI-eligible series may appear only as separate,
   versioned predictor copies with their own transform and availability lag. Name them
   clearly and test that no fitted object is shared with Pipeline A.
4. **Leakage tests.** `tests/test_features.py` proves the firewall. A deliberately shuffled
   or leaking table must fail.
5. **Fold file.** `outputs/folds/folds.json` with expanding-window, time-ordered inner folds,
   horizons 1Q/2Q/4Q (2Q primary). No test row appears in training.
6. **Baselines.** Majority class, term-spread probit/logit and plain logistic.
7. **Feature dictionary and build commands.** Enough that Palchhin can run the table and
   folds without asking you.
8. **Dry-run clean-clone note.** Current `main` passes; the combined clean clone is Day 7.
9. **A PR on `feat/features-harness`** with commands, tests, hashes and known gaps.

### How your lane is judged

- **Feature gate:** no BEAI-derived output, NBER series, future data, country ID or
  country-size level. Allowed raw copies are documented and independent.
- **Fold gate:** every model uses the same folds and features; the test block is untouched.
- **Reproducibility:** one USA country × horizon combination reproduces from a seed.
- **No collateral change:** the label stays byte-identical.

## 5. How your work combines with the others

| Hand-off | When | What must be true |
|---|---|---|
| H1: Sathvik → all | Day 1 morning | You can state your Day 1 task from this brief and `docs/TEAM_PLAN.md` |
| H2: you → Palchhin | Day 3 end | Draft folds with the same keys/horizons as the final file; Part 3 can run a first real pass |
| H4: you → Palchhin + Sathvik | Day 4 end (final folds); Day 5 end (frozen) | Table + final folds available for the USA headline; frozen files and leakage tests complete by Day 5 |
| H6: all → Sathvik + Arshiya | Day 6 morning | One branch, green checks, short hand-off note |
| Day 6 merge | Step 2 | You merge `feat/features-harness`; the team checks leakage and fold boundaries |
| Day 7 review | Step 2 | You run the combined clean clone; Sathvik records the evidence |

Your work is the bridge between the labels and the models. If the folds are wrong, every
model result is meaningless. If the table leaks, the project has no honest result.

## 6. DOs

- **DO** read C-01, C-05–C-08 and C-11 before writing the feature spec.
- **DO** write the feature spec before the table. Every column needs a source, transform,
  lag and a reason it is safe.
- **DO** keep the table unscaled; scaling happens inside the fold.
- **DO** document the allowed raw BEAI-eligible copies separately from the label pipeline.
- **DO** test the firewall with a deliberately leaking table and a shuffled pipeline.
- **DO** make the fold file explicit: keys, horizons, train/test boundaries, inner folds.
- **DO** hand over the Day 4 final folds so Palchhin can run the USA headline.
- **DO** commit small, run the tests, and write a hand-off note the receiver can follow.
- **DO** ask Shravani for panel semantics and Palchhin for fold requirements.

## 7. DON'Ts

- **DON'T** use the BEAI factor, `R`, level, diffusion, turning-point flag or NBER column as
  a feature.
- **DON'T** use future data, full-sample scaling, full-sample feature selection or a
  held-out country's information.
- **DON'T** interpolate, forward-fill or impute a partial quarter.
- **DON'T** include a country ID or a raw country-size level.
- **DON'T** hand-edit `dataset.parquet` or `folds.json`; regenerate them.
- **DON'T** change the label or the frozen rules to make the table easier.
- **DON'T** merge a red branch or silently change a fold boundary.
- **DON'T** overclaim: a good-looking score is not evidence until the leakage tests pass.

## 8. Allowed creative liberty and educational freedom

Inside the guardrails, you have room to think:

- **Choose your implementation.** A single `features.py` or a small package is fine; pick
  what you can test and explain.
- **Add useful extras.** A feature dictionary, a missingness plot, a fold diagram, a short
  notebook, or a "what I learned about leakage" note are welcome.
- **Learn while you work.** You may spend up to about half a day (roughly 10% of the lane)
  on `scikit-learn`, time-series validation, pandas performance or testing tools. Note it in
  your hand-off.
- **Try a better transform or lag** if you document it and it stays inside C-05/C-06. Do not
  use the test block to choose it.
- **Propose an extra predictor** before any model score exists. Add it only if it passes the
  coverage and firewall rules.
- **Write a "what I learned" section** in the feature dictionary. It helps the next person.

## 9. If you get stuck

1. **A column's lag is unclear?** Write the question and the candidate rules; ask before
   building the table.
2. **A predictor fails coverage?** Document the failure and exclude it. Do not impute it.
3. **The fold file is contested?** Bring the exact keys and boundaries to the stand-up.
   Palchhin needs a stable contract, not a moving target.
4. **A leak test fails?** Stop and fix the builder. Do not weaken the test.
5. **Blocked for more than half a day?** Say so at the stand-up. Do not hide it until Day 5.

## 10. Where to look

| Need | File |
|---|---|
| Frozen rules | `docs/BUILD_CONTRACT.md` |
| Decisions and rationale | `docs/DECISIONS.md` |
| USA clean panel | `data/clean/USA_panel.csv`, `USA_levels.parquet` |
| Label-ready growth | `data/clean/USA_growth.parquet` |
| NBER validation series | `data/clean/USA_validation.parquet` |
| Scope and sources | `config/scope.yaml`, `data/scope.csv` |
| Harmoniser | `scripts/harmonize.py` |
| Team plan | `docs/TEAM_PLAN.md`, `Team_Plan.xlsx` |
| Weekly log | `EWS_Work_Log.xlsx` |

---

**Bottom line:** a small, clean, tested table with honest folds is worth more than a large
table with one leak. Build the firewall first, hand the folds over on Day 4, and freeze the
files on Day 5.
