# Part 4 Hand-off and PR Notes

**Branch:** `feat/india-scope-docs`
**Date:** 2026-11-13
**Owner:** Sathvik Boina
**Status:** content complete for the India, docs and integration lane; team-dependent
items are recorded as pending.

## 1. What this branch contains

| File | Purpose |
|---|---|
| `data/india_core_coverage.csv` | Nine India core rows with downloaded status, coverage, query URL and access note |
| `docs/INDIA_COVERAGE_AUDIT.md` | Downloaded-data audit; final India count 1/8 |
| `docs/VERIFICATION.md` | India evidence and log entry |
| `docs/STATE.md` | India status, O-2 default, Part 4 status |
| `docs/DECISIONS.md` | D-R33 added; D-R30 history preserved |
| `decisions_log.csv` | Q-02, Q-03, Q-06, Q-07, Q-08, Q-09 synced with `spec.py` |
| `unresolved_questions.csv` | Regenerated from `spec.py`; Q-06, Q-07, Q-09 closed |
| `spec.py` | India decisions updated; Q-02/Q-03 remaining actions narrowed |
| `tests/test_review_invariants.py` | Q-06 assertion now checks the downloaded-data finding |
| `README.md`, `docs/TEAM_PLAN.md`, `docs/team/01_…`, `docs/team/README.md` | Consistency updates |
| `docs/team/04a_docs_audit.md` | Day 3 docs audit |
| `docs/team/04b_clean_clone_review.md` | Day 4 checklist; Arshiya's evidence recorded as pending |
| `docs/team/04c_integration_rehearsal.md` | Day 5/6 merge checklist; rehearsal recorded as not run |
| `docs/team/04d_pitch.md` | One-page plain-English pitch |
| `docs/EXPLORATORY_MODEL_RUN.md` | Exploratory USA-first model run; explicitly not the pre-registered result |
| `experiments/usa_first_models.py` | Self-contained numpy/scipy walk-forward run behind that note |

`docs/team/03a_palchhin_model_spec.md` and its PDF are part of the working tree but were
added before this lane's final commit; include them only if the branch is intended to carry
the supporting model specification.

## 2. Commands and results

```bash
.venv/bin/python -m pytest
# 54 collected: 53 passed, 1 skipped (after the Lane 1 merge)

make check
# 33 ok, 3 warnings, 0 failures
# warnings: optional model packages sklearn, xgboost, shap not installed

git diff --check
# clean

.venv/bin/python experiments/usa_first_models.py
# exploratory only; ~7.5 min; writes outputs/exploratory/usa_first/ (git-ignored)
```

No `make pipeline` and no `make labels` was run. No estimator, BBQ setting, diffusion gate,
eight-indicator structure, fold boundary or ensemble rule was changed.

## 3. Frozen hashes (re-checked 2026-11-13)

```text
2379fd53e4c9023538cafcd5668a4835bcdd7b45cfae9e3cbc3d4f306ed19daa  outputs/labels/USA_labels.csv
b20a9f23dec8516f12cf2047dfd87f2575a307ed0839c811d30b95f29cd6b6f5  outputs/labels/JPN/JPN_labels.csv
6f1aa66598b1cdf823e3f97a25709c6cb5a7ed851ee8ab1c0a9b8e45402c0a50  outputs/labels/labels-v3.json
f5ed42a6c4333aaecbae4fae1f5f6fcab3606ce46dd2b459791a6aa31816dc8e  outputs/labels/archive/labels-v2/USA_labels.csv
1a1b1f6a566cb2cffe7181cbc59ec20bd07d8ef25e0300d4dd2d96ceb749e29a  outputs/labels/archive/labels-v1/USA_labels.csv
```

All four match the frozen table in `docs/STATE.md`.

## 4. India result

**1 of 8** BEAI indicators passes: `ACT_IP` at 130/147 (88.4%). GDP, consumption and
investment cover 61/147 (41.5%) because quarterly NAS starts in 2011Q2; the Back series is
annual. Quarterly PLFS covers 33/147 (22.4%) and monthly PLFS starts in April 2025. No
quarterly hours or household-income series and no official monthly retail series exist.
The quarterly GFCF institutional split returns `No Data Found`.

O-2 stays Label-B-only. No proxy, carry-forward or relaxation was used.

## 5. Known gaps and blockers

| Item | State | Owner |
|---|---|---|
| Arshiya's Day 4 clean-clone dry run | **Not received** | Arshiya |
| Day 5 integration rehearsal | **Partially run**: Lane 1 merged into `master`; feature/model lanes still absent | Sathvik / all |
| H3 Japan/Germany labels | **Delivered 2026-11-13**: `labels-v1-JPN` frozen; DEU coverage finding | Shravani |
| H4 features/folds | Missing | Arshiya |
| H5 model results / ensemble | Official result missing | Palchhin |
| Day 7 combined clean clone | Blocked on merges | Arshiya |
| Packaging, mirror, zip, tag | Not created; approval required | Sathvik |
| Out-of-sample model result | Official result does not exist; exploratory run only (`docs/EXPLORATORY_MODEL_RUN.md`) | Palchhin (official) |

## 6. Reviewer notes

- The India verdict is conservative. Even if a legacy quarterly NAS path through RBI DBIE
  were retrieved later, the count would reach at most 5/8, still below 6/8. The Label-B
  decision does not depend on that path.
- The pre-audit's 4/8 assumed a 1996-97 quarterly start that the official API does not
  provide. The change is documented rather than hidden.
- The model specification (`03a`) is a supporting document, not a Part 4 deliverable.
- An exploratory USA-first run was made on 2026-11-13 while H4/H5 were missing. It uses
  hand-built features, hand-built folds and numpy/scipy reference models. It fails C-13
  (Δ −0.0017, 95% CI includes zero) and is **not** the official result; do not merge its
  numbers into the results docs as pre-registered evidence.
- Do not present the local 54-test result as a clean-clone result. The Day 4 and Day 7
  clean-clone gates remain open. Lane 1 arrived later on 2026-11-13 and is now merged into
  `master`; its label hashes and docs are part of the combined tree.
