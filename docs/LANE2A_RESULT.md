# Lane 2A Completion Report: Feature Specification, Firewall Tests & Baselines

**Owner:** Shravani Math (Lane 2A Specification and Verification Owner)  
**Date:** 2026-11-14  
**Branch:** `feat/features-harness`  
**Base Commit:** `4556011` (ancestor verified via `git merge-base --is-ancestor 4556011 HEAD`)  

---

## 1. Decisions Taken
- **D-R34 (Option A):** Formalized documented exception in `docs/DECISIONS.md`. `labels-v1-JPN` covers 144 quarters (1990Q1–2025Q4) while D-R02/D-R31 require 147 quarters. Cross-country models must align on 147 or handle 144 explicitly; `labels-v2-JPN` deferred to post-official run.
- **Firewall & Unscaled Contract (C-01, C-05, C-07, C-08):** Predictors stored strictly unscaled in `data/features/dataset.parquet`. Imputation and standardisation fitted strictly inside training folds. Zero shared Pipeline A objects.

## 2. Exact Commands Run
```bash
git fetch origin --prune
git switch -c feat/features-harness origin/feat/india-scope-docs
.venv-win\Scripts\python scripts/harmonize.py --country USA
.venv-win\Scripts\python scripts/04_compare_nber.py
.venv-win\Scripts\python scripts/06_features.py
.venv-win\Scripts\python scripts/06_folds.py
.venv-win\Scripts\python -m pytest tests/test_features.py -p no:cacheprovider
.venv-win\Scripts\python scripts/07_baselines.py
.venv-win\Scripts\python scripts/08_verify_lane2a.py
make lane2a
```

## 3. Data & Artifact Shapes
- `data/clean/USA_panel.csv`: **267 rows × 27 columns**, window **1960Q1–2026Q3** (147 label-ready rows 1990Q1–2026Q3).
- `data/clean/USA_growth.parquet`: **267 rows × 8 columns**, window **1960Q1–2026Q3**.
- `data/features/dataset.parquet`: **147 rows × 28 columns** (1 `quarter` key + **27 unscaled predictors**), window **1990Q1–2026Q3**.
- `data/features/folds.json`: **22 outer folds per horizon** (1Q, 2Q primary, 4Q). Initial train: 60Q, test blocks: 4Q, gap: $H$ quarters.

## 4. Cryptographic Proofs & Checksums
- **USA Label Hash Before & After:** `2379fd53e4c9023538cafcd5668a4835bcdd7b45cfae9e3cbc3d4f306ed19daa` (LF git blob, byte-identical, 0 modifications under `outputs/labels/**`).
- **Folds File Checksum:** `b59ea4c2bbcc5da3fde3a45ed4b04bc3278ffe3d2a67577489fd40b9eb3ad8a9` (reproducible across independent runs).
- **Baselines CSV Checksum:** `e1e4319b3cdedb0b9c1e7f007ac5e519a90fb087229e68243b807f51d171ad1a`
- **Baselines MD Checksum:** `0adc771c604a29176e1c1bd2f2617cbb7ff7d2e3258499072bd54abe66ba685b`
- **JPN Metadata JSON Hash:** `3b74d3e63f4b6f19e15c372637c2f776e029903f710eba93c8a6cb395b99ed9a` (matches working tree and `docs/LABEL_VALIDATION_JPN.md`).

## 5. Test Suite & Mutation Proof
All 6 tests in `tests/test_features.py` passed in 0.83s:
1. `test_schema`: PASS (147 rows, contiguous 1990Q1–2026Q3, no duplicates)
2. `test_blacklist`: PASS (zero blacklisted tokens or prefixes)
3. `test_unscaled`: PASS (no zero-mean/unit-std columns; `rate_long` and `unemp` equal source values)
4. `test_no_future_leakage`: PASS (identical values at $\le t$ across cutoffs 2000Q4, 2010Q2, 2019Q4, 2024Q3)
5. `test_independence`: PASS (zero Pipeline A outputs; all 8 `beai_copy_*` reproduced from `USA_growth.parquet` alone; no scalers saved)
6. `test_mutation_fails_on_leak`: PASS
   - **Poison A (Target Injection `R=0`):** Caught with `ValueError: Blacklisted column detected (exact token): 'R'`.
   - **Poison B (Future Shift `rate_long.shift(-1)`):** Caught with `ValueError: Future leakage detected: column 'rate_long' is shifted from future (shift -1Q)`.
   - **Poison B2 (Injected novel shift `rate_short.shift(-1)`):** Caught with `ValueError: Future leakage detected: injected column 'future_leak_col' matches future shift (-1Q) of 'rate_short'`.

## 6. Baseline Model Results (Seed 42, Fixed Threshold 0.50)
| Horizon | Model | PR-AUC | ROC-AUC | Episode Recall (Test) | Accuracy | Brier Score | N Test Obs |
|---|---|---:|---:|---:|---:|---:|---:|
| 1Q | majority | 0.0200 | 0.5000 | 0.0000 | 0.9800 | 0.0196 | 100 |
| 1Q | term_spread | 0.0871 | 0.8140 | 0.0000 | 0.9800 | 0.0255 | 100 |
| 1Q | plain_logistic | 0.0445 | 0.7093 | 0.0000 | 0.9800 | 0.0416 | 100 |
| **2Q (primary)** | **majority** | **0.0359** | **0.5000** | **0.0000** | **0.9641** | **0.0346** | **195** |
| **2Q (primary)** | **term_spread** | **0.1535** | **0.8412** | **0.0000** | **0.9641** | **0.0389** | **195** |
| **2Q (primary)** | **plain_logistic** | **0.0879** | **0.7588** | **0.0000** | **0.9590** | **0.0544** | **195** |
| 4Q | majority | 0.0665 | 0.5000 | 0.0000 | 0.9335 | 0.0621 | 376 |
| 4Q | term_spread | 0.2529 | 0.8659 | 1.0000 | 0.9388 | 0.0560 | 376 |
| 4Q | plain_logistic | 0.2040 | 0.8415 | 0.0000 | 0.9335 | 0.0768 | 376 |

## 7. Open Items & Handoff to Sathvik (Lane 2B)
- **`gh` CLI status:** Not installed on current Windows environment; PR comment prepared at `outputs/results/lane2a_pr_comment.md`.
- **Lane 3 Intake:** Lane 2A outputs (`docs/FEATURES.md`, `tests/test_features.py`, `scripts/06_features.py`, `scripts/06_folds.py`, `scripts/07_baselines.py`, `data/features/folds.json`) are frozen and ready for Sathvik's clean clone and Palchhin's official model execution.
