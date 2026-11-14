# Lane Brief 2B — Feature Table, Walk-Forward Folds and Clean Clone

| Field | Detail |
|---|---|
| **Owner** | Sathvik Boina |
| **Role** | Build owner for Lane 2 and integration owner for the sprint |
| **Reassigned from** | Arshiya Mahammad (resigned) |
| **Branch** | `feat/features-harness` — named branch owner and merger |
| **Blocks** | Pre-work, A, B, C, merge, Day 7 |
| **Date** | 14 November 2026 |
| **Companion brief** | `docs/team/02a_shravani_feature_spec.md` — see `shrav.pdf` |

## 1. Your mission in one paragraph

Turn the verified panel into a predictor-only table and a fair time-based harness on the
147-quarter window, then carry Lane 2 through the merge and the combined clean clone.
Shravani owns the specification and the leak tests; you own the code that must satisfy them.
You also inherit Arshiya's integration duties: the Day 6 merge of Lane 2 and the Day 7
combined clean-clone evidence. Build to the spec, freeze the folds by Sunday night so
Palchhin is not blocked, and never merge a red branch.

## 2. Where we actually stand

Verified on `feat/india-scope-docs` at `4556011`, clean and synced with origin.

| Item | State |
|---|---|
| Current branch | `feat/india-scope-docs@4556011`, clean, synced |
| `origin/master` | `ad9adad` — PR #3 merge of Palchhin's `feat/models-ensemble` |
| Local `master` / worktree | `366ea0f`, four commits behind origin |
| `feat/models-finalization` | `455edc3`, based on `2f6a04d`; wholesale merge would revert Lane 1 and India work |
| USA panel | 267 quarters × 27 columns, 1960Q1–2026Q3 |
| USA label | `labels-v3`, 147 quarters, hash `2379fd53…19daa` |
| Feature table / folds / harness | **do not exist** |
| Test suite | 53 passed, 1 skipped |
| `make check` | 33 ok, 3 warnings, 0 failures |
| Optional model deps | `scikit-learn`, `xgboost` **not installed** |
| Manifest | 40 rows (USA 27, JPN 7, DEU 6); 38 verified, 1 low coverage, 1 pending |
| India | 1/8 (`ACT_IP` only); Label-B-only under O-2 |
| Lane 3 | blocked: no official run, `config/models.yaml` unapproved |

**Two traps to internalise before you write code:**

1. `data/raw` and `data/clean` are git-ignored. A fresh clone needs `make fetch` and
   `make harmonize` before anything works. Your dry-run clone must prove this, not assume it.
2. `outputs/**` is git-ignored **except** a whitelist. `outputs/folds/folds.json` will not be
   committed unless you add a `!outputs/folds/**` rule, or you hand off its SHA-256 instead.
   Decide explicitly and write down which you chose.

## 3. The whole remaining work, and which part is yours

| Workstream | State | Owner |
|---|---|---|
| JPN window closeout: 144 vs 147, label-doc hash drift | open | Shravani |
| Lane 2A — feature spec, firewall tests, baselines | not started | Shravani |
| **Lane 2B** — table, folds, harness, Makefile | not started | **You** |
| **Repo reconciliation** — merge `origin/master`, deps, doc drift | pending | **You** |
| Lane 3 — config freeze, intake gate, official run, C-13 once | blocked on 2+3+4 | Palchhin |
| Lane 4 closeout — India 1/8, scope audit, pitch | complete | **You** |
| **Day 6 merge** in fixed order | pending | each owner; **you coordinate** |
| **Day 7 combined clean clone**, hash table, go/no-go | pending | **You run**; Shravani cross-checks; Palchhin results docs |
| **Dashboard refresh** from official artifacts | pending | **You** |
| Packaging / tag / mirror | blocked, needs explicit approval | **You** |

Your load is Lane 2B, repo reconciliation, the merge, the clean clone, the dashboard and the
build half of Lane 2A. Shravani carries the JPN closeout and the verification half. Palchhin
carries Lane 3. If Lane 3 is still blocked on the day you finish, do not start modelling to
fill the gap — escalate.

## 4. Pre-work — Saturday, ~45 minutes

Do this once, before anyone writes Lane 2 code, so both briefs share one tree.

1. **Back up first.** Confirm `feat/india-scope-docs` is pushed; create a local backup branch
   if you want a safety net.
2. **Merge `origin/master` into `feat/india-scope-docs`.** Palchhin's scaffolding is additive
   (runner, fixtures, `config/models.yaml`, ~18 test files). Expect test-count growth, not
   conflicts. Run `pytest` and `make check` immediately after.
3. **Re-check `455edc3`.** It was based on `2f6a04d`. After the master merge, decide whether
   anything in it is still missing. Cherry-pick only that commit, never the branch.
4. **Install optional deps** (`scikit-learn`, `xgboost`) into `.venv` and re-run `make check`.
   The three warnings should disappear.
5. **Fix the known drift** in `docs/STATE.md`: the fingerprint table is stale for
   `config/scope.yaml`, `data/series_resolution.csv` and `data/manifest.csv`; the manifest is
   40 rows, not 27; JPN/DEU source maps are 18+3 and 17+4, not 21/21. Fix the prose, not the
   data.
6. **Cut `feat/features-harness`** from the reconciled tip. Record in `docs/DECISIONS.md` that
   you are the branch owner and Shravani is a contributor with test ownership.

If step 2 turns red and cannot be fixed in 30 minutes, stop and write the failure down. Do
not start Lane 2 on a broken base.

## 5. What you own

### Block A — Saturday afternoon (2–3 h): scaffolding

- Create `src/ews/features.py` with a single, testable entry point (e.g.
  `build_feature_table(panel, spec) -> DataFrame`).
- Create `scripts/05_features.py` as a thin CLI wrapper and add `make features`.
- Build a **column inventory** from the panel and compare it with Shravani's spec as it
  lands. Report mismatches at once; do not guess a transform.
- Decide and document the `outputs/folds` gitignore question (commit vs hash-only).
- Do not write the table yet. The spec is the gate.

### Block B — Sunday (4–5 h): table and folds

**Feature table**

- 147 rows, 1990Q1–2026Q3, one row per quarter, keyed on `quarter`.
- Unscaled values only; scaling happens inside the fold.
- No `factor`, `level`, `R`, `n_available`, `deterioration_share`, no turning-point flags,
  no `USA.NBER.Q`, no country ID, no country-size level.
- Raw BEAI-eligible series only as separate, clearly named predictor copies with their own
  transform and availability lag. No shared fitted object with Pipeline A.
- Write `data/clean/dataset.parquet`. Never hand-edit it; regenerate.

**Folds and harness**

- `src/ews/harness.py` + `scripts/06_folds.py` + `make folds`.
- Expanding window, time-ordered inner folds, horizons 1Q / 2Q / 4Q with 2Q primary.
- No test row may ever appear in training. Deterministic from a recorded seed.
- Write `outputs/folds/folds.json` with explicit keys, horizons, train/test boundaries and
  inner-fold definitions.
- Freeze a **draft** fold file by Sunday night and hand it to Palchhin. That is the critical
  path for the whole sprint.

### Block C — Monday (3 h): freeze and prove

- Re-run the build from scratch; record the table row count, column list and SHA-256.
- Run Shravani's `tests/test_features.py`; fix the builder, never the test.
- Reproducibility run: one USA country × horizon from a recorded seed, twice, identical output.
- **Dry-run clean clone of current main**: clone into `/tmp`, run `make fetch` and
  `make harmonize`, then `make check test`. Record the exact commands, the skip count and
  every failure. This feeds your existing `docs/team/04b_clean_clone_review.md`.
- Open one PR on `feat/features-harness` with commands, hashes, tests and known gaps.

## 6. Deliverables

1. `src/ews/features.py`, `scripts/05_features.py`, `make features`.
2. `data/clean/dataset.parquet` — generated, 147 rows, unscaled.
3. `src/ews/harness.py`, `scripts/06_folds.py`, `make folds`.
4. `outputs/folds/folds.json` — committed or hash-recorded, per your documented decision.
5. Reproducibility evidence (command, seed, hash, second run).
6. Dry-run clean-clone note of current main.
7. PR on `feat/features-harness`.
8. Day 6 merge of Lane 2 and Day 7 combined clean-clone evidence + hash table.
9. Dashboard refreshed from the official artifacts, if the official run lands.

## 7. Done when — minimal gates

1. `make features` yields 147 rows, 1990Q1–2026Q3, unscaled, keyed on `quarter`, with zero
   blacklisted columns.
2. `make folds` is deterministic; no test row appears in training; 1Q/2Q/4Q exist, 2Q primary.
3. Shravani's mutation test fails on a deliberately leaking table (i.e. her suite is live).
4. USA label hash is still `2379fd53…19daa`; estimator, BBQ, gate and eight-indicator
   structure untouched.
5. One USA country × horizon reproduces from a recorded seed.
6. A fresh clone of the branch, after `make fetch` and `make harmonize`, passes `make check test`.

**Deferred, not required:** extra predictors, missingness plots, fold diagrams, a second
harness implementation, cross-country panels.

## 8. Day 6 merge and Day 7 clean clone

**Merge order (fixed):** Lane 1 labels → Lane 2 features/folds → Lane 3 models → Lane 4 docs.
Each owner merges their own branch. You merge Lane 2 because you own the branch.

After every merge: run `pytest` and `make check`, write the result down, and stop on red.
Never patch around a red branch on main.

**Day 7 combined clean clone** — you run it now, not Arshiya:

1. Clone the combined tree into `/tmp/opencode/`.
2. `make fetch`, `make harmonize`, `make features`, `make folds`.
3. `make check test` and record pass/skip counts.
4. Verify frozen hashes: USA `2379fd53…`, JPN `b20a9f23…`.
5. Rebuild one country × horizon from seed.
6. Write the hash table and draft go/no-go. Shravani cross-checks; Palchhin owns results docs.

Known reality: the clone will show more skips than your working tree because `data/clean`
must be rebuilt. Record that, do not hide it.

## 9. DOs

- DO build to Shravani's spec. If a column is ambiguous, ask before coding it.
- DO keep the table unscaled and the test block untouched.
- DO test the firewall with a deliberately leaking table before you trust the table.
- DO hand the draft folds over Sunday night even if the table still has cosmetic gaps.
- DO record every hash, seed and command in the hand-off.
- DO run checks after every merge and write the result down.
- DO keep the pitch plain: what the label proves, what the model does not prove.

## 10. DON'Ts

- DON'T use the BEAI factor, R, level, diffusion, turning-point flag or NBER column as a feature.
- DON'T use future data, full-sample scaling or full-sample feature selection.
- DON'T interpolate, forward-fill or impute a partial quarter.
- DON'T include a country ID or a raw country-size level.
- DON'T hand-edit `dataset.parquet` or `folds.json`; regenerate them.
- DON'T weaken a failing leak test to make the table pass.
- DON'T merge a red branch, skip a check, or let the Day 4 dry run stand in for Day 7.
- DON'T create a bundle, mirror, zip or tag without explicit approval.
- DON'T absorb Lane 3 because it is blocked. Escalate and re-plan.

## 11. Open decisions you must log

| Decision | Why it matters | Default |
|---|---|---|
| Lane 2 branch ownership | One owner, two contributors | You own `feat/features-harness`; Shravani commits tests/spec |
| `folds.json` committed or hash-only | `outputs/**` is git-ignored | Whitelist `outputs/folds/**` and commit; document it |
| JPN 144 vs 147 quarters | Cross-country features depend on it | Shravani's call; USA-first unaffected |
| `455edc3` still needed? | Avoid reverting Lane 1/India | Re-check after the master merge |

Record each in `docs/DECISIONS.md` with a date and a one-line reason. Rule changes before
results are fine; after results they are not.

## 12. Risks and how to cut

| Risk | Trigger | Cut |
|---|---|---|
| Master merge is not additive | Conflicts in `tests/` or `config/` | Stop, isolate, cherry-pick only; do not force-merge |
| Spec arrives late | Nothing from Shravani by Sunday morning | Build columns with C-05 defaults, flag them, let her correct |
| Folds slip past Sunday | Harness not deterministic | Ship the 2Q expanding fold only; add 1Q/4Q in Block C |
| Clean clone needs data | `make fetch` missing a series | Record the skip; do not commit raw data |
| Palchhin blocked | No approved model config | Do not build models; escalate in writing |

The single most damaging outcome is a table that looks good and leaks. The second is a fold
file that changes after Palchhin has run. Both are avoidable by freezing early and testing
the failure case.

## 13. Where to look

| Need | File |
|---|---|
| Frozen rules | `docs/BUILD_CONTRACT.md` (C-01, C-05–C-08, C-11, C-12, C-13) |
| Decisions and rationale | `docs/DECISIONS.md` |
| USA clean panel | `data/clean/USA_panel.csv` |
| Harmoniser | `scripts/harmonize.py` |
| Scope and window | `config/scope.yaml` |
| Current state and hashes | `docs/STATE.md` |
| Clean-clone checklist | `docs/team/04b_clean_clone_review.md` |
| Merge rehearsal | `docs/team/04c_integration_rehearsal.md` |
| Pitch | `docs/team/04d_pitch.md` |
| Original Lane 2 brief | `docs/team/02_arshiya_features_harness.md` |
| Shravani's spec brief | `docs/team/02a_shravani_feature_spec.md` |

**Bottom line:** you are the bridge between the labels and the models, and then the person
who proves the combined tree still works. Build small, build to spec, freeze the folds early,
and let Shravani's tests — not your confidence — certify the firewall.
