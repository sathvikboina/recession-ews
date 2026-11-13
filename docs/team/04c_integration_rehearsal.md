# Part 4 — Integration Rehearsal and Merge Checklist

**Date:** 2026-11-13
**Facilitator:** Sathvik Boina
**State:** checklist prepared; **not rehearsed** because the three lane branches do not
exist yet.

## 1. Current branch state

```
master         0cf6573  Align the one-week plan and add four lane briefs
origin/master  0cf6573
```

No `feat/*` lane branch exists on the remote. The only Part 4 branch is
`feat/india-scope-docs`, created from `master` for this lane's documents. H3 (Japan/
Germany labels), H4 (features/folds) and H5 (model results) cannot be rehearsed until
those owners publish their branches.

## 2. Fixed merge order

Each owner merges their own branch. Sathvik coordinates and records the result; Sathvik
does not patch another lane's code on `main`.

| Step | Owner | Branch | What must be true before merge | Checks after merge |
|---|---|---|---|---|
| 1 | Shravani | `feat/jpn-deu-labels` (expected name) | JPN label frozen or a documented gate failure; Germany 6/8 decision; hashes recorded; label docs updated | `make check`; `make test`; `git diff --check`; label hashes |
| 2 | Arshiya | `feat/features-harness` (expected name) | `dataset.parquet`, `folds.json`, feature dictionary; leakage tests; C-01/C-05/C-06/C-07 | same, plus row-count and fold-boundary checks |
| 3 | Palchhin | `feat/models-ensemble` (expected name) | six singles, baselines, REWI, one C-13 application; `headline.md`, `episodes.md`; metadata in every result | same, plus frozen-fold and threshold checks |
| 4 | Sathvik | `feat/india-scope-docs` | India audit, CSV, doc sync, pitch, this checklist | same, plus doc/hash agreement |

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

| Hand-off | Owner | Acceptance | Status |
|---|---|---|---|
| H3 | Shravani | Japan label + chronology note + Germany 6/8 decision; hashes | Pending — no branch |
| H4 | Arshiya | `dataset.parquet` + final `folds.json` + leakage tests | Pending — no branch |
| H5 | Palchhin | USA headline, episode, ablation and ensemble tables; C-13 once | Pending — no branch |
| H6 | All | one branch per lane, green checks, short hand-off note | Pending |
| H7 | Sathvik + Arshiya | combined clean-clone evidence, hash table, draft go/no-go | Pending |

## 5. Rehearsal result

**Not run.** There were no lane branches to merge on 2026-11-13. The checklist above is
the rehearsal script; the Day 6 execution is still owed. This note must not be presented as
proof that the merge order works.

## 6. Day 7 go/no-go inputs

A "go" requires all of the following:

1. combined clean clone from `main` after all four merges;
2. `make check test` green, with skips named;
3. frozen v1/v2/v3 hashes unchanged;
4. India recorded as Label-B-only at 1/8;
5. no unsupported forecast claim in README, report or pitch;
6. no bundle, mirror, zip or tag without explicit approval.

A missing item is a "no-go" or a recorded condition, not a silent omission.
