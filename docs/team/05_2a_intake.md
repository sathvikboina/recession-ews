# Lane 2A Intake and Integration Runbook

**Owner of this runbook:** Sathvik Boina
**Applies to:** the hand-off from Shravani Math (Lane 2A)
**Branch:** `feat/features-harness` (Shravani commits; Sathvik owns and merges)
**Status:** executed 2026-11-14. The hand-off arrived as `origin/feat/features-harness@758ae99`;
its useful parts were ported onto the frozen Lane 2B tree and the rest was rejected. Outcome:
`docs/LANE2A_RESULT.md`. The checklist in §8 is green.

This is the exact sequence to run when 2A lands. It assumes the 2A deliverables named in
`docs/team/02a_shravani_feature_spec.md` §5:

| # | Deliverable | Expected path |
|---|---|---|
| 1 | Feature specification §1–4 and dictionary §5 | `docs/FEATURES.md` |
| 2 | Six firewall tests, including the mutation test | `tests/test_feature_firewall.py` |
| 3 | Three baselines on the frozen folds | `scripts/07_baselines.py` |
| 4 | Baseline results note | `outputs/results/baselines.md` or a section in `docs/FEATURES.md` |
| 5 | JPN 144 vs 147 closeout decision | `docs/DECISIONS.md` + affected docs |

If a file arrives under a different name, rename it to the path above before merging so the
report and the contract keep one name for one thing.

## 1. Intake (do not merge on sight)

```bash
git fetch origin --prune
git log --oneline --graph origin/feat/features-harness -15
git diff --stat origin/feat/india-scope-docs...origin/feat/features-harness
```

Read every changed file before running anything. Reject silent edits to:

- `outputs/labels/**` (labels are frozen; any change is a stop-the-line event);
- `src/ews/models/{features,folds,feature_transforms,publication_lags}.py` (Lane 3
  primitives, D-R35);
- `src/ews/features.py` unless the change is a spec reconciliation agreed in writing;
- `tests/test_features.py` (Lane 3, D-R36).

## 2. Run the gates

```bash
git switch feat/features-harness
git pull --ff-only
.venv/bin/python -m pytest                       # full suite
.venv/bin/python -m pytest tests/test_feature_firewall.py -q
make check
make features && sha256sum data/clean/dataset.parquet
make folds    && sha256sum outputs/folds/folds.json
sha256sum outputs/labels/USA_labels.csv outputs/labels/JPN/JPN_labels.csv
```

Expected values before 2A and after any non-label change:

| Artefact | Expected |
|---|---|
| `outputs/labels/USA_labels.csv` | `2379fd53e4c9023538cafcd5668a4835bcdd7b45cfae9e3cbc3d4f306ed19daa` |
| `outputs/labels/JPN/JPN_labels.csv` | `b20a9f23dec8516f12cf2047dfd87f2575a307ed0839c811d30b95f29cd6b6f5` |
| `data/clean/dataset.parquet` | `368b60056872b9883ab8767fa148249d5f5c13ea85ca68abfc4e9437ee4304f4` (unless 2A reconciles the spec) |
| `outputs/folds/folds.json` | `afd51bc5f885f74a84f2e5f29bd6732de78454945cb189f2fee1d8c426afc261` |
| `make test` | 182 passed + 2A's new tests, 1 skipped |

## 3. Spec reconciliation

The machine-readable spec is `FEATURE_SPEC`, `DERIVED_SPECS` and `EXCLUSIONS` in
`src/ews/features.py`. Shravani's `docs/FEATURES.md` is the human spec and is the authority
on **what a legal predictor is**. Reconcile in this order:

1. Build the column inventory and diff it against the written dictionary:

   ```bash
   .venv/bin/python - <<'PY'
   import pandas as pd
   from ews.features import FEATURE_SPEC, DERIVED_SPECS, EXCLUSIONS
   table = pd.read_parquet("data/clean/dataset.parquet")
   spec = [(s.name, s.form, s.lag_class, s.beai_copy) for s in (*FEATURE_SPEC, *DERIVED_SPECS)]
   print(f"table columns: {table.shape[1] - 1}; spec series: {len(spec)}")
   for name, form, lag, copy in spec:
       prefix = "beai_copy_" if copy else ""
       cols = [c for c in table.columns if c.startswith(f"{prefix}{name}__")]
       print(f"{name:20} {form:10} {lag:10} {len(cols):2} cols")
   print("excluded:", sorted(EXCLUSIONS))
   PY
   ```

2. For every disagreement, record one line: column, current builder, written spec, decision.
3. If the written spec wins, change `FEATURE_SPEC`/`DERIVED_SPECS`, rebuild, and record the
   new `dataset.parquet` hash in `docs/STATE.md` and `docs/team/04b_clean_clone_review.md`.
4. If the builder wins, change `docs/FEATURES.md` and say why. Do not let two documents
   describe different tables.
5. A spec change does **not** move the folds: D-R37 depends only on labels and quarters.

## 4. Firewall and baseline checks

- Confirm the mutation test actually fails on a mutated table. Read the test; do not trust a
  green run alone.
- Run the baselines and confirm they use `ews.harness.fold_index_splits` and the frozen
  folds, not hand-built splits.
- Check that no baseline tunes on the test block, searches a threshold on the test block, or
  selects features on the full sample.
- Record the seed and pooled PR-AUC/episode recall in the final report's baseline table.

## 5. JPN 144 vs 147 closeout

If 2A records **Option A** (144 as a documented exception):

- add the decision entry;
- fix the JPN metadata hash in `docs/LABEL_VALIDATION_JPN.md` if it is still wrong;
- make `config/scope.yaml`, D-R02/D-R31 and the validation note agree on the exception.

If 2A records **Option B** (rebuild as `labels-v2-JPN`):

- do **not** run `make labels` in this session; the standing instruction forbids it;
- keep `labels-v1-JPN` byte-identical;
- treat the rebuild as a separate, approved job and record it as such.

## 6. Merge and record

```bash
git switch feat/india-scope-docs
git merge --no-ff feat/features-harness -m "Merge Lane 2A: feature spec, firewall tests, baselines"
.venv/bin/python -m pytest
make check
```

Then update, in the same commit as the merge evidence:

- `docs/STATE.md`: test count, feature-table hash, 2A status;
- `docs/team/04b_clean_clone_review.md`: new hashes and any new skip;
- `docs/team/04c_integration_rehearsal.md`: H4 status;
- `docs/FINAL_REPORT.md`: predictor, firewall and baseline sections.

## 7. Failure policy

| Failure | Action |
|---|---|
| Firewall test fails on the real table | Do not merge. Fix the builder or the spec, then re-run. Never weaken the test. |
| Mutation test passes on a bad table | The test is not a firewall. Send it back; do not merge. |
| Label hash moved | Stop. Restore the frozen label; nothing else is trusted until it matches. |
| Table hash moved without a recorded spec change | Treat as a defect until explained. |
| Baseline uses test data or tunes on test | Reject the baseline; rerun inside the fold. |
| 2A changes Lane 3 modules | Revert that part; ask for it as a separate proposal. |

## 8. What "2A integrated" looks like

- [ ] `docs/FEATURES.md` exists and its inventory matches the built table.
- [ ] `tests/test_feature_firewall.py` passes on the real table and fails on the mutation.
- [ ] `scripts/07_baselines.py` runs on the frozen folds and writes its note.
- [ ] JPN 144/147 is recorded, with docs and config agreeing.
- [ ] USA label, JPN label and frozen fold hashes unchanged.
- [ ] Full suite and `make check` green.
- [ ] `docs/STATE.md` and the final report are updated in the same commit.
