# One-Week Sprint — Lane Briefs

Status: **active; last reviewed 2026-11-08.** Four people, four lanes, one shared merge.
Days 1–5 are individual work; Days 6–7 are shared combining, cross-review and sign-off.

These briefs are the short, self-contained version of `docs/TEAM_PLAN.md`. Read your own
brief first, then the plan. They describe what you own, what already exists, what is
expected, what to do, what not to do, where you have creative freedom, and the schedule.

## The four lanes

| Lane | Owner | Brief | Branch | Main output |
|---|---|---|---|---|
| 1. Japan and Germany labels | Shravani Math | [01_shravani_japan_germany.md](01_shravani_japan_germany.md) | `feat/jpn-deu-labels` | Japan label + chronology note; Germany label or coverage note |
| 2. Feature table and walk-forward harness | Arshiya | [02_arshiya_features_harness.md](02_arshiya_features_harness.md) | `feat/features-harness` | `dataset.parquet`, `folds.json`, leakage tests |
| 3. Models, ensemble and experiments | Palchhin | [03_palchhin_models_ensemble.md](03_palchhin_models_ensemble.md) | `feat/models-ensemble` | USA headline, episodes, ablations, ensemble decision |
| 4. India, scope, integration and pitch | Sathvik | [04_sathvik_india_integration.md](04_sathvik_india_integration.md) | `feat/india-scope-docs` | India verdict, consistent docs, merge and review |

## Schedule at a glance

| Day | Mode | Everyone |
|---|---|---|
| 1 | Individual | Source maps/specs; country-plumbing refactor; India downloads start |
| 2 | Individual | Japan data, USA feature table, model interfaces on a fixture, India count |
| 3 | Individual | Japan label, draft folds, REWI, India verdict; first hand-off |
| 4 | Individual | Germany, final folds + dry-run clean clone, USA headline, docs review |
| 5 | Individual | Freeze outputs, write notes and the pitch, hand off; all lanes close |
| 6 | Shared | Merge 1 → 2 → 3 → 4; each owner merges their own branch; checks after each |
| 7 | Shared | Cross-review, combined clean clone, go/no-go; packaging only with approval |

Days are a guide. A lane that finishes early reviews its own outputs and helps test the
hand-off; it does not start another lane's work. A slipping lane says so on Day 5.

## Key hand-offs

| ID | From → to | When | What |
|---|---|---|---|
| H1 | Sathvik → all | Day 1 morning | Briefs and plan understood; Day 1 task stated |
| H2 | Arshiya → Palchhin | Day 3 end | Draft folds with stable keys and horizons |
| H3 | Shravani → Sathvik | Day 5 end | Japan label, chronology note, Germany decision, hashes |
| H4 | Arshiya → Palchhin + Sathvik | Day 4 end (folds); Day 5 end (frozen) | Table + folds for the USA headline; frozen files later |
| H5 | Palchhin → Sathvik | Day 5 end | USA headline, episodes, ablations, ensemble decision |
| H6 | All → Sathvik + Arshiya | Day 6 morning | One branch per lane, green checks, short hand-off note |
| H7 | Sathvik + Arshiya → all | Day 7 morning | Clean-clone evidence, hash table, draft go/no-go |

## Review matrix (Day 7)

| Lane | Author | Reviewer |
|---|---|---|
| 1. Labels | Shravani | Arshiya |
| 2. Features/folds | Arshiya | Shravani |
| 3. Models/ensemble | Palchhin | Sathvik |
| 4. India/docs/integration | Sathvik | Palchhin |

Write findings, not verbal comments. Verification is shared: Arshiya owns the combined clean
clone, Palchhin the results docs, Shravani the label docs, and Sathvik coordinates.

## The rules that do not bend

- `labels-v1` and `labels-v2` stay byte-identical; `labels-v3` is active and frozen.
- Do not change the estimator, BBQ, diffusion gate or eight-indicator structure without a
  new version and a recorded decision.
- The ensemble is pre-registered: equal-weight top-3, ≥0.01 pooled PR-AUC gain, bootstrap CI
  excluding zero, no episode-recall loss. Applied once.
- India stays Label-B-only under O-2; the 6-of-8 rule is not relaxed.
- No forecast claim before out-of-sample model results.
- No bundle, mirror, zip or release tag without explicit approval.
- Missing stays missing: no interpolation, forward fill or partial-quarter imputation.
- One active source row per scope key; provenance goes in the manifest and resolution files.

## What "done" looks like

USA and Japan have frozen BEAI labels with chronology checks; Germany has a label or a
complete coverage note. India has a downloaded-data verdict or a recorded access failure. The
predictor table has no BEAI-derived outputs and passes the leakage tests. The USA model and
the pre-registered ensemble are reported exactly once; JPN/DEU model results only if their
labels land. `make check test` is green, and a clean clone of the **combined** tree
reproduces the label hashes.

## Where to read more

| Need | File |
|---|---|
| Full plan | `docs/TEAM_PLAN.md`, `Team_Plan.xlsx` |
| Current state and hashes | `docs/STATE.md` |
| Frozen rules | `docs/BUILD_CONTRACT.md` |
| Ensemble and claim wording | `docs/PROPOSAL_ADDENDUM.md` |
| India pre-audit | `docs/INDIA_COVERAGE_AUDIT.md` |
| Decisions | `docs/DECISIONS.md`, `decisions_log.csv` |
| Verification evidence | `docs/VERIFICATION.md` |
| Weekly log | `EWS_Work_Log.xlsx` |
