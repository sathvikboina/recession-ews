# Part 4 — Day 4 Clean-Clone Review and Packaging Checklist

**Date:** 2026-11-13
**Owner of the dry run:** Arshiya
**Reviewer:** Sathvik Boina
**Scope:** a clean clone of current `main`. This is a dry run, not the Day 7 combined
clean clone.

## 1. Status

**Arshiya's dry-run evidence has not been received.** No clean-clone log or hash table was
available on 2026-11-13, so this note records the gap rather than inventing a result.

What was checked locally on the working tree:

| Check | Result |
|---|---|
| `python -m pytest` | **38 passed** in 5.81s |
| `make check` | **33 ok, 3 warnings, 0 failures** |
| Warnings | optional model packages `sklearn`, `xgboost`, `shap` not installed |
| `git diff --check` | clean |
| Frozen `labels-v3` label hash | `2379fd53e4c9023538cafcd5668a4835bcdd7b45cfae9e3cbc3d4f306ed19daa` |
| Frozen `labels-v3` metadata hash | `6f1aa66598b1cdf823e3f97a25709c6cb5a7ed851ee8ab1c0a9b8e45402c0a50` |
| `labels-v2` label hash | `f5ed42a6c4333aaecbae4fae1f5f6fcab3606ce46dd2b459791a6aa31816dc8e` |
| `labels-v1` label hash | `1a1b1f6a566cb2cffe7181cbc59ec20bd07d8ef25e0300d4dd2d96ceb749e29a` |

These are **working-tree checks**, not a clean-clone result. They do not satisfy the Day 4
deliverable and must not be presented as the Day 7 combined evidence.

## 2. Exact dry-run procedure for Arshiya

Run from a directory outside the repository:

```bash
git clone git@github.com:sathvikboina/recession-ews.git /tmp/opencode/dryrun-main
cd /tmp/opencode/dryrun-main
git checkout main
git log -1 --oneline
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
make config
make scope
make check
make test
```

Record:

- the exact commit hash;
- the Python and package versions (`pip freeze`);
- `make check` summary line;
- `make test` summary line;
- any skip reason;
- the SHA-256 of the frozen label files.

Expected result on a tree equivalent to the current `main`: **36 passed, 2 explicit skips**
until the git-ignored `data/clean` is rebuilt, as recorded in the 2026-11-08 review. If the
clone has the rebuilt clean data, the expected result is **38 passed**. A different count
is a finding, not something to explain away.

## 3. Packaging checklist

Nothing in this checklist authorises a release. All items require explicit approval first.

| Item | Required state | Status 2026-11-13 |
|---|---|---|
| Bundle | not created | OK — none |
| Mirror | not created | OK — none |
| Zip | not created | OK — none |
| Release tag | not created | OK — none |
| Frozen labels | v1/v2 archived, v3 active | OK — hashes unchanged |
| Combined clean clone | Day 7, owned by Arshiya | Pending |
| Combined `make check test` | green on Day 7 | Pending |
| Hash table | recorded by lane owners | Pending |
| Go/no-go note | written after Day 7 review | Pending |

## 4. Blocking gaps

- Arshiya's Day 4 dry-run log is missing.
- The Day 7 combined clean clone cannot be run until all four branches are merged.
- JPN/DEU labels, features, folds and model results are absent, so a clean clone cannot
  prove those lanes.

**Do not mark the Day 4 or Day 7 gate as passed on the strength of this note.**
