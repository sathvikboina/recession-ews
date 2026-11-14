# Lane Brief 2A — Feature Specification, Firewall Tests and Baselines

| Field | Detail |
|---|---|
| **Owner** | Shravani Math |
| **Role** | Feature-specification and verification owner for Lane 2 |
| **Reassigned from** | Arshiya Mahammad (resigned) |
| **Branch** | `feat/features-harness` — you commit; Sathvik owns and merges the branch |
| **Blocks** | A, B, C — see the shared schedule |
| **Date** | 14 November 2026 |
| **Companion brief** | `docs/team/02b_sathvik_features_folds.md` — see `satv.pdf` |

## 1. Your mission in one paragraph

Define, in writing, exactly what a legal predictor is for this project, then prove it with
tests that are designed to fail. Sathvik builds the feature table and the fold file; you own
the specification they must satisfy, the independent leakage tests that police it, and the
first honest baselines. You are not the table builder. Your value is that a second person,
working from the label side, can say "this column is safe, and here is the test that shows
it" without having written the builder. If the table leaks, the project has no honest
result — that is the job you are protecting.

## 2. Where we actually stand

Verified on `feat/india-scope-docs` at `4556011`, clean and synced with origin.

| Item | State |
|---|---|
| USA clean panel | `data/clean/USA_panel.csv`, 267 quarters × 27 columns (key + 26 series), 1960Q1–2026Q3 |
| USA label | `labels-v3` frozen, 147 quarters, 1990Q1–2026Q3, hash `2379fd53…19daa` |
| Label-ready growth | `data/clean/USA_growth.parquet`, eight series |
| NBER validation | `data/clean/USA_validation.parquet` — never a feature |
| Feature table | **does not exist** |
| Fold file | **does not exist** |
| Harness | **does not exist** |
| Test suite | 53 passed, 1 skipped |
| `make check` | 33 ok, 3 warnings (optional model packages), 0 failures |
| India | 1/8 downloaded (`ACT_IP` only); Label-B-only under O-2 |
| Lane 3 | blocked: no official run, `config/models.yaml` unapproved |

**What this means for you:** there is nothing half-built to inherit. You start from a clean
panel and a frozen label. That is the best possible position for writing a spec.

**Why Lane 2 was split.** Arshiya resigned before delivering any of Lane 2. Rather than have
one person build and self-certify, the lane is split: Sathvik builds, you specify and verify.
This is deliberate separation of duties, not a demotion of the work.

## 3. The whole remaining work, and which part is yours

This is the full path from today to the final go/no-go. Your name marks what you own;
"support" means you review or unblock rather than build.

| Workstream | State | Owner |
|---|---|---|
| JPN window closeout: 144 vs 147 quarters, label-doc hash drift | open | **You** |
| **Lane 2A** — feature spec, firewall tests, baselines | not started | **You** |
| Lane 2B — table, folds, harness, Makefile | not started | Sathvik |
| Repo reconciliation: merge `origin/master`, dependency install, doc drift | pending | Sathvik |
| Lane 3 — config freeze, intake gate, official run, C-13 once, results docs | blocked on 2+3+4 | Palchhin (support: you) |
| Lane 4 closeout — India 1/8 recorded, scope audit, pitch | complete | Sathvik |
| Day 6 merge in fixed order | pending | each owner; Sathvik coordinates |
| Day 7 combined clean clone, hash table, go/no-go | pending | Sathvik runs; **you cross-check**; Palchhin results docs |
| Dashboard refresh from official artifacts | pending | Sathvik |
| Packaging / tag / mirror | blocked, needs explicit approval | Sathvik |

You touch the JPN closeout, Lane 2A, and the cross-check half of Day 7. Everything else is
either Sathvik's build or Palchhin's run. Do not absorb Lane 3 to make the story complete.

## 4. What you own

### Block A — Saturday afternoon (2–3 h): the specification

Write `docs/FEATURES.md`. Sections 1–4 are yours; section 5 (dictionary) is Block C.

1. **Purpose and window.** USA predictors, 1990Q1–2026Q3, one row per quarter. State that
   the table is unscaled and that scaling happens inside the fold.
2. **Column inventory.** All 26 panel columns plus the eight label-ready growth series.
   For each: source series ID, native frequency, transform (level, Δlog, quarterly mean,
   etc.), availability lag under C-05, missing-data rule, and one line on why it is safe.
3. **Allowed raw BEAI copies.** The eight BEAI-eligible core series may appear **only** as
   separate, versioned predictor copies with their own transform and lag. Name them
   explicitly (a `beai_copy_` prefix or equivalent), and state that no fitted object, scaler
   or factor loading is shared with Pipeline A. This is the hardest paragraph in the document;
   get it right.
4. **Exclusion blacklist.** Write down every column class that is forbidden and why:
   `factor`, `level`, `R`, `n_available`, `deterioration_share`, turning-point flags,
   `USA.NBER.Q`, country ID, country-size levels, and anything derived from future
   observations.
5. **2026 extension audit.** What changed when the window moved from 2025Q4 to 2026Q3, and
   why it does not create a new leak.

A useful sanity check: every row of the spec should let a stranger rebuild that column
without asking you a question.

### Block B — Sunday (4–5 h): the tests

Write `tests/test_features.py` against Sathvik's builder. The file is yours; do not accept
edits that weaken it.

| Test | What it must prove |
|---|---|
| Schema | 147 rows, `quarter` key, contiguous 1990Q1–2026Q3, no duplicate keys |
| Blacklist | None of the forbidden columns or prefixes appear |
| Unscaled | Values are not standardised; no zero-mean/unit-variance signature per column |
| No future | Deleting all rows after `t` does not change any feature value at `t` |
| Independence | No BEAI-derived object or shared scaler is used in Pipeline B |
| **Mutation** | A deliberately shuffled or leaking copy of the table **fails** the suite |

The mutation test is the important one. A test that only passes on the correct table proves
nothing; a test that fails on a known-bad table proves the firewall.

### Block C — Monday (3 h): dictionary and baselines

- **Feature dictionary** (`docs/FEATURES.md` §5): units, interpretation, expected sign,
  known coverage gaps, and a short "what I learned about leakage" section.
- **Baselines** (`scripts/07_baselines.py`) on Sathvik's frozen folds: majority class,
  term-spread probit/logit, plain logistic. Report pooled PR-AUC and episode recall. No
  tuning, no feature selection on the test block, no threshold search.
- **Hash proof:** re-run the USA label hash check and record `2379fd53…19daa` unchanged.

## 5. Deliverables

1. `docs/FEATURES.md` — spec §1–4, dictionary §5.
2. `tests/test_features.py` — all six tests, including the mutation test.
3. `scripts/07_baselines.py` — three baselines on the frozen folds.
4. A short baseline results note (`outputs/results/baselines.md` or equivalent, or a section
   in `docs/FEATURES.md`) with PR-AUC, recall and the seed.
5. Comment on Sathvik's PR with the test evidence and the label hash.
6. Closeout note on the JPN window (see §7).

## 6. Done when — minimal gates

These five are non-negotiable. Everything else can slip.

1. `make features` yields 147 rows, 1990Q1–2026Q3, unscaled, keyed on `quarter`, with zero
   blacklisted columns — **and you agree it is correct**.
2. `make folds` is deterministic; no test row ever appears in training; 1Q/2Q/4Q exist with
   2Q primary.
3. The mutation test fails on a deliberately leaking table.
4. USA label hash is still `2379fd53…19daa`; estimator, BBQ, diffusion gate and the
   eight-indicator structure are untouched.
5. One USA country × horizon reproduces from a recorded seed.

**Deferred, not required:** extra predictors, missingness plots, fold diagrams, fourth
baseline, cross-country feature panels. Add them only if Blocks A–C finish early.

## 7. Carryover: the Japan window (small, separate)

`labels-v1-JPN` covers 144 quarters (1990Q1–2025Q4). `config/scope.yaml`, D-R02 and D-R31
say 147 (1990Q1–2026Q3). There is no decision-log entry for 144, and
`docs/LABEL_VALIDATION_JPN.md` also records the wrong metadata hash.

Pick one and write it down before any cross-country feature work:

- **Option A (cheap):** record 144 as a documented exception with a decision-log entry, and
  correct the metadata hash in the validation note.
- **Option B (correct, slower):** rebuild the Japan label as `labels-v2-JPN` on the full
  147-quarter window, leaving `labels-v1-JPN` frozen and untouched.

Recommendation: **Option A now**, Option B only if the official run leaves time. The
USA-first headline is not blocked either way. Do not silently let the docs and the label
disagree.

## 8. How your work is judged

- **Feature gate:** no BEAI-derived output, NBER series, future data, country ID or
  country-size level. Allowed raw copies are documented and provably independent.
- **Test independence:** you did not write the builder, and a known-bad table fails your
  suite.
- **No collateral change:** the label stays byte-identical.
- **Honesty:** a predictor that fails coverage is documented and excluded, never imputed.

## 9. Hand-offs

| ID | To | When | What must be true |
|---|---|---|---|
| — | Sathvik | End of Block A | Spec §1–4 is written; he can build without asking you |
| — | Sathvik | End of Block B | Tests run green on his table; mutation test fails on a bad one |
| H2/H4 (adapted) | Palchhin | End of Block B | Draft folds + frozen table; he can run a first real pass |
| H4 | Palchhin | End of Block C | Baselines + dictionary; no tuning after this point |
| Day 7 | Sathvik | After official run | You independently reproduce the clean-clone checks |

## 10. DOs

- DO read C-01, C-05–C-08, C-11 and C-12 before writing a single spec line.
- DO write the spec before Sathvik writes the table. He is blocked on you.
- DO keep the table unscaled and keep the test block untouched.
- DO test the firewall with a deliberately leaking table and a shuffled pipeline.
- DO ask Palchhin what the folds must expose (keys, horizons, inner folds) before you freeze.
- DO commit small, run the suite after each change, and write a hand-off the receiver can follow.

## 11. DON'Ts

- DON'T use the BEAI factor, R, level, diffusion, turning-point flag or NBER column as a feature.
- DON'T use future data, full-sample scaling, or full-sample feature selection.
- DON'T interpolate, forward-fill or impute a partial quarter.
- DON'T include a country ID or a raw country-size level.
- DON'T hand-edit `dataset.parquet` or `folds.json`; regenerate them.
- DON'T weaken a failing leak test to make the table pass.
- DON'T change the label or the frozen rules to make the table easier.
- DON'T overclaim: a good-looking baseline score is not evidence until the leak tests pass.

## 12. Risks and how to cut

| Risk | Trigger | Cut |
|---|---|---|
| Spec becomes a research project | Still writing §2 on Sunday morning | Cap transforms to C-05 defaults; document the rest as open questions |
| Test file fights the builder | Two days of red tests | Freeze on schema + no-future + mutation; move independence to a review note |
| Baselines drag | No folds until late Sunday | Ship majority + logistic only; note probit as deferred |
| Japan window expands | Option B chosen | Defer to after the official run; USA-first is unaffected |

The critical path is the spec. If Block A slips, Sathvik's Block B slips, and Palchhin's run
slips. Send the spec in whatever state it reaches by Saturday night.

## 13. Where to look

| Need | File |
|---|---|
| Frozen rules | `docs/BUILD_CONTRACT.md` (C-01, C-05–C-08, C-11, C-12) |
| Decisions and rationale | `docs/DECISIONS.md` (D-R05, D-R06, D-R08, D-R12–D-R18, D-R22–D-R31) |
| USA clean panel | `data/clean/USA_panel.csv` |
| Label-ready growth | `data/clean/USA_growth.parquet` |
| NBER validation only | `data/clean/USA_validation.parquet` |
| Scope and sources | `config/scope.yaml`, `data/scope.csv` |
| Harmoniser | `scripts/harmonize.py` |
| Your Lane 1 outputs | `docs/LABEL_VALIDATION_JPN.md`, `docs/HANDOFF_JPN_DEU.md` |
| Original Lane 2 brief | `docs/team/02_arshiya_features_harness.md` |
| Sathvik's build brief | `docs/team/02b_sathvik_features_folds.md` |

**Bottom line:** a small, clean, tested table with honest folds beats a large table with
one leak. You are the person who decides what "clean" means and proves it. Write the spec
first, hand it over Saturday night, and let the tests do the arguing.
