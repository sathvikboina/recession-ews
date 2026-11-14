# Part 4 — Integration Rehearsal and Merge Checklist

**Date:** 2026-11-14
**Facilitator:** Sathvik Boina
**State:** the Lane 2B merge has been rehearsed on `feat/india-scope-docs`. The final
Day 6 merge on `master` is still owed because Lane 3 has no results yet.

## 1. Current branch state

```
origin/master                  6a80819  Merge PR #5 (feat/india-scope-docs)
origin/feat/models-finalization c9c93a4  PR #4 source
origin/feat/jpn-deu-labels     366ea0f  merged into master via PR #2/#5 ancestry
origin/feat/features-harness   be185ac  Lane 2B: table, frozen folds, portability fix
origin/feat/india-scope-docs   82d1137  integration tip (this rehearsal)
```

`feat/models-ensemble` (PR #3) and `feat/models-finalization` (PR #4) are already in
`master`. Lane 3 still has no official run, so no model branch is waiting to merge.

## 2. Fixed merge order

Each owner merges their own branch. Sathvik coordinates and records the result; Sathvik
does not patch another lane's code.

| Step | Owner | Branch | What must be true before merge | Checks after merge |
|---|---|---|---|---|
| 1 | Shravani | `feat/jpn-deu-labels` | JPN label frozen or a documented gate failure; Germany 6/8 decision; hashes recorded | `make check`; `make test`; label hashes |
| 2 | Shravani (2A) + Sathvik (2B) | `feat/features-harness` | `dataset.parquet`, frozen `folds.json`, harness; firewall tests from 2A | same, plus row-count and fold-boundary checks |
| 3 | Palchhin | `feat/models-*` | six singles, baselines, REWI, one C-13 application; `headline.md`, `episodes.md`; metadata in every result | same, plus frozen-fold and threshold checks |
| 4 | Sathvik | `feat/india-scope-docs` | India audit, doc sync, pitch, this checklist | same, plus doc/hash agreement |

If a merge is red, stop. The owner fixes their branch; the next merge waits.

## 3. Command sequence after each merge

```bash
git checkout main
git pull --ff-only
git merge --no-ff <lane-branch>
make check
make test
git diff --check
sha256sum outputs/labels/USA_labels.csv outputs/labels/labels-v3.json
```

Record the output verbatim in the Day 6 integration note. Do not summarise a red check as
"minor".

## 4. Hand-off acceptance

| Hand-off | Owner | Acceptance | Status 2026-11-14 |
|---|---|---|---|
| H3 | Shravani | Japan label + chronology note + Germany 6/8 decision; hashes | Label frozen; Germany coverage decision written |
| H4 | Shravani (2A) + Sathvik (2B) | `dataset.parquet` + frozen `folds.json` + harness; firewall tests from 2A | **2B done**: table, frozen folds, adapter, clean-clone evidence. **2A outstanding**: `docs/FEATURES.md`, `tests/test_feature_firewall.py`, baselines, JPN 144/147 decision |
| H5 | Palchhin | USA headline, episode, ablation and ensemble tables; C-13 once | **Pending** — no frozen tuning config, no official run |
| H6 | All | one branch per lane, green checks, short hand-off note | Partial — lanes 1, 2B and 4 green; Lane 3 pending |
| H7 | Sathvik | combined clean-clone evidence, hash table, draft go/no-go | Partial — Lane 2B clean clone recorded; combined gate pending |

## 5. Rehearsal result

Rehearsed on `feat/india-scope-docs`, not on `master`:

| Merge | Result |
|---|---|
| `origin/master` (PR #4) into `feat/features-harness` | clean; 175 passed |
| `feat/features-harness` into `feat/india-scope-docs` | clean; 175 passed |
| `origin/master` (PR #5, itself from this branch) into `feat/india-scope-docs` | clean; 183 passed |
| Lane 2B final merge (`be185ac`) into `feat/india-scope-docs` | clean; 183 passed, 1 skipped |

After every merge: `make check` **33 ok, 1 warning, 0 failures**; the frozen label hashes
were unchanged; `dataset.parquet` and `folds.json` reproduced byte-identically in a fresh
clone (`docs/team/04b_clean_clone_review.md`).

The merge order above has therefore been proven for steps 1, 2 and 4 on the integration
branch. Step 3 has no branch to merge, so the **Day 6 combined merge on `master` is still
owed**.

## 6. Day 7 go/no-go inputs

A "go" requires all of the following:

1. combined clean clone from `main` after all four merges;
2. `make check test` green, with skips named;
3. frozen v1/v2/v3 hashes unchanged;
4. India recorded as Label-B-only at 1/8;
5. no unsupported forecast claim in README, report or pitch;
6. no bundle, mirror, zip or tag without explicit approval.

A missing item is a "no-go" or a recorded condition, not a silent omission.
