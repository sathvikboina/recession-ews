# Part 4 — Clean-Clone Review and Packaging Checklist

**Date:** 2026-11-14
**Owner of the dry run:** Sathvik Boina
**Reviewer:** Shravani Math (label hashes)
**Scope:** a clean clone of `feat/india-scope-docs` at `82d1137`, the integration tip that
contains Lane 2A/2B, PR #4, PR #5 and the master merge. This is a **Lane 2B / integration**
dry run. It is **not** the Day 7 combined clean clone, because Lane 3 official results do
not exist yet.

## 1. Result

Run from outside the repository:

```bash
git clone git@github.com:sathvikboina/recession-ews.git /tmp/opencode/ews-clean2
cd /tmp/opencode/ews-clean2
git switch feat/india-scope-docs
git log -1 --oneline        # 82d1137 Merge origin/master (PR #5) ...
```

| Check | Result |
|---|---|
| `make check` | **33 ok, 1 warning, 0 failures** |
| Warning | `shap` not installed; it is unused by the current code |
| `make test` before clean data exists | **181 passed, 3 skipped** |
| `make test` after `make harmonize` | **183 passed, 1 skipped** |
| Remaining skip | `tests/test_country_plumbing.py` raw-hash test (see finding F1) |
| `make harmonize` | regenerated the USA quarterly panel from the raw snapshot |
| `make features` | 147 rows × 149 unscaled features, 64 `beai_copy_*` columns |
| `dataset.parquet` SHA-256 | `368b60056872b9883ab8767fa148249d5f5c13ea85ca68abfc4e9437ee4304f4` — **matches** |
| `make folds` | 67 outer folds per horizon (1/2/4), frozen under D-R37 |
| `folds.json` SHA-256 | `afd51bc5f885f74a84f2e5f29bd6732de78454945cb189f2fee1d8c426afc261` — **matches** |
| Frozen `labels-v3` label hash | `2379fd53e4c9023538cafcd5668a4835bcdd7b45cfae9e3cbc3d4f306ed19daa` — unchanged |
| `labels-v2` label hash | `f5ed42a6c4333aaecbae4fae1f5f6fcab3606ce46dd2b459791a6aa31816dc8e` — unchanged |
| `labels-v1` label hash | `1a1b1f6a566cb2cffe7181cbc59ec20bd07d8ef25e0300d4dd2d96ceb749e29a` — unchanged |

The first `folds.json` run in a clone produced a different hash because the export embedded
an absolute labels path. That was a genuine reproducibility bug; commit `be185ac` records
the repo-relative path, and the hash above is identical in the working tree and in the
clone.

## 2. What this dry run does not prove

- **No network fetch.** `FRED_API_KEY` is empty in this environment, so `make fetch` was
  not run. The git-ignored `data/raw/` snapshot was copied in to rebuild the clean panel.
  A true from-scratch clone still needs a FRED key or the team-approved raw snapshot.
- **No model results.** Lane 3 has no frozen tuning config and no official run, so the
  clone cannot reproduce a headline, an episode table or the C-13 decision.
- **Not the Day 7 gate.** The combined clean clone is still owed after the model results
  land.

## 3. Finding F1 — the raw-hash test skips even when raw data exists

`tests/test_country_plumbing.py:177` skips when no raw hash was checked. In a clone with
the full `data/raw/` snapshot it still skips, because the label metadata contains no
`raw_hashes` mapping for the test to iterate over. The test therefore does not currently
verify any raw input. This is a Lane 1 test, so it is reported here rather than changed.

**Required fix (Lane 1):** either publish the raw hashes in the label metadata/`data/manifest.csv`
and read them in the test, or rename/repurpose the test so it does not imply coverage it
does not have.

## 4. Packaging checklist

Nothing here authorises a release. All items require explicit approval first.

| Item | Required state | Status 2026-11-14 |
|---|---|---|
| Bundle | not created | OK — none |
| Mirror | not created | OK — none |
| Zip | not created | OK — none |
| Release tag | not created | OK — none |
| Frozen labels | v1/v2 archived, v3 active | OK — hashes unchanged |
| Combined clean clone | Day 7, after model results | Pending — Lane 3 results absent |
| Combined `make check test` | green on Day 7 | Pending |
| Hash table | recorded by lane owners | Partial — labels, table and folds recorded |
| Go/no-go note | written after Day 7 review | Pending |

## 5. Blocking gaps

- Lane 3 has no frozen `config/models.yaml`, no official USA run and no
  `docs/EXPERIMENTS.md`.
- Lane 2A is integrated on `feat/features-harness`: `docs/FEATURES.md`,
  `tests/test_feature_firewall.py`, baselines, `scripts/08_verify_lane2a.py` and the JPN
  decision (D-R38). The combined Day 7 clone must still be re-run on the merged tree.
- The JPN/DEU labels are frozen/decided, but the cross-country feature table is USA-only.

**Do not mark the Day 7 gate as passed on the strength of this note.**
