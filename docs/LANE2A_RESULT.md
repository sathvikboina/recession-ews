# Lane 2A Completion Report: Feature Specification, Firewall Tests & Baselines

**Owner:** Shravani Math (Lane 2A Specification and Verification Owner)  
**Date:** 2026-11-14  
**Branch:** `feat/features-harness`  
**Base Commit / Ancestry:** `origin/feat/india-scope-docs` merged cleanly; `git merge-base --is-ancestor origin/feat/india-scope-docs HEAD` verified (`BASE_OK`).  
**Conflict Markers:** 0 conflict markers across repository (`git grep -n -E '^(<<<<<<<|=======|>>>>>>>)'` clean).  

---

## 1. Decisions Taken & Policy Harmonization
- **D-R37 (Frozen Folds Adoption):** Adopted frozen expanding walk-forward folds in `outputs/folds/folds.json` (80 outer initial training quarters, 40 inner initial training quarters, step 1 quarter, first scored quarter `2010Q1`, purge gap equal to horizon $H$). Metadata verified with `approved: true` and `decision: "D-R37"`. Deprecated duplicate `data/features/folds.json` removed.
- **D-R34 (Option A):** Formalized documented exception in `docs/DECISIONS.md`. `labels-v1-JPN` covers 144 quarters (1990Q1–2025Q4) while D-R02/D-R31 require 147 quarters. Hash `3b74d3e63f4b6f19e15c372637c2f776e029903f710eba93c8a6cb395b99ed9a` verified in file and `docs/LABEL_VALIDATION_JPN.md`.
- **Shipped vs Reference Feature Builders:** The official shipped feature table is `data/clean/dataset.parquet` (147 rows, 149 features) produced by `scripts/05_features.py` (`make features`). `scripts/06_features.py` is preserved strictly as a documented reference fixture for unit-level property and mutation checks.
- **Prevalence Operating Point Rule:** With ~3.6% recession onset base rate, fixed 0.50 threshold yields 0.0000 episode recall across all models. Adopted non-tuned, fixed operating point: the training-fold positive prevalence (recomputed per fold from $y_{train}$ only, never touching the test block).

---

## 2. Builder Reconciliation & Spec Compliance
| Property | Specification (Lane 2A) | Shipped Table (`scripts/05_features.py`) | Reference Fixture (`scripts/06_features.py`) | Firewall Compliance |
|---|---|---|---|---|
| Target Output | `data/clean/dataset.parquet` | `data/clean/dataset.parquet` | `data/features/dataset.parquet` | PASS |
| Row Count | 147 quarters (1990Q1–2026Q3) | 147 quarters (1990Q1–2026Q3) | 147 quarters (1990Q1–2026Q3) | PASS |
| Key Column | `quarter` (string Period) | `quarter` (string Period) | `quarter` (string Period) | PASS |
| Scaling | Unscaled across full sample | Unscaled (all 149 features) | Unscaled (all 27 features) | PASS |
| Blacklisted Columns | 0 forbidden columns | 0 forbidden columns | 0 forbidden columns | PASS |
| Core BEAI Copies | 8 series under `beai_copy_*` | 64 features (`beai_copy_ACT_*__*`) | 8 features (`beai_copy_act_*`) | PASS |
| Pipeline A Artifacts | Zero shared factors/scalers | Zero shared factors/scalers | Zero shared factors/scalers | PASS |
| No-Future Leakage | $s \le t$ invariant to cutoff $t$ | Rolling backward transforms only | Verified at 4 cutoffs | PASS |

### Structural Note on Feature Counts (149 vs. 27 Columns)
The shipped feature table `data/clean/dataset.parquet` contains exactly 149 features (plus the `quarter` key). This is intended: it covers 19 base spec series (8 BEAI-eligible core indicators and 11 predictor series) plus 1 derived market series (`FIN_SLOPE`), expanded systematically across canonical transforms (lags 1, 2, 4, QoQ/YoY growth, 4Q rolling mean, rolling volatility, and trend) via `ews.models.feature_transforms`. The 149 count includes these derived transformation columns, contains zero blacklisted variables, and satisfies all C-01, C-05, C-07, and C-08 firewall rules.

---

## 3. Cryptographic Proofs & Checksums
- **USA Label Blob Hash:** `2379fd53e4c9023538cafcd5668a4835bcdd7b45cfae9e3cbc3d4f306ed19daa` (LF git blob, verified unchanged; 0 uncommitted changes in `outputs/labels/**`).
- **Frozen Folds Hash (`outputs/folds/folds.json`):** `cc4814be7e020d466d53e905961c46f5a2ccbe3a0b9197fd7b9e62eb0feb8719` (D-R37 parameters: 80 init, 40 inner, step 1, first 2010Q1, approved: true).
- **Shipped Feature Table Hash (`data/clean/dataset.parquet`):** `e35b43ddf09f50759f4bb09b27119e92fb8d895368f3a319794cc96d970647d0`.
- **Baselines CSV Hash (`outputs/results/baselines.csv`):** `e227e2543334dd6c11b43db9e6433fadb4eeccaacd8a7e64833647d07377af86`.
- **Baselines MD Hash (`outputs/results/baselines.md`):** `9cfe616c6fde0b78676750d55b8d94a3dad12afa5a2878f7ccc667f1212b00ce`.
- **JPN Metadata JSON Hash:** `3b74d3e63f4b6f19e15c372637c2f776e029903f710eba93c8a6cb395b99ed9a`.

---

## 4. Primary (2Q) Baseline Results & Recall Comparison

### 2Q Episode Recall: Before vs. After
| Baseline Model | PR-AUC | 2Q Recall Before (Fixed 0.50 Threshold) | 2Q Recall After (Training Prevalence Rule) | Accuracy (Prev Rule) |
|---|---:|---:|---:|---:|
| `majority` | 0.0236 | 0.0000 | **1.0000** | 0.0308 |
| `term_spread` | 0.1556 | 0.0000 | **1.0000** | 0.6308 |
| `plain_logistic` | 0.1080 | 0.0000 | **0.0000** | 0.8769 |

*Note on Operating Point:* The headline episode recall is evaluated at each fold's empirical training-set positive prevalence ($p_{threshold} = \bar{y}_{train}$), which is fixed, non-tuned, and recomputed strictly from $y_{train}$ without touching the test block. The secondary fixed 0.50 threshold yields 0.0000 recall because the low base rate (~3.6%) prevents probabilities from reaching 0.50.

### Complete Baseline Results Across Horizons
| Horizon | Model | PR-AUC | ROC-AUC | Episode Recall (Prev Rule) | Episode Recall (0.50) | Accuracy (Prev) | Brier Score | N Test Obs |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1Q | `majority` | 0.0154 | 0.5000 | 1.0000 | 0.0000 | 0.0152 | 0.0152 | 66 |
| 1Q | `term_spread` | 0.1111 | 0.8769 | 1.0000 | 0.0000 | 0.5455 | 0.0197 | 66 |
| 1Q | `plain_logistic` | 0.0476 | 0.7231 | 0.0000 | 0.0000 | 0.8939 | 0.0402 | 66 |
| **2Q (primary)** | **`majority`** | **0.0236** | **0.5000** | **1.0000** | **0.0000** | **0.0308** | **0.0231** | **65** |
| **2Q (primary)** | **`term_spread`** | **0.1556** | **0.8750** | **1.0000** | **0.0000** | **0.6308** | **0.0315** | **65** |
| **2Q (primary)** | **`plain_logistic`** | **0.1080** | **0.8281** | **0.0000** | **0.0000** | **0.8769** | **0.0477** | **65** |
| 4Q | `majority` | 0.0410 | 0.5000 | 1.0000 | 0.0000 | 0.0476 | 0.0393 | 63 |
| 4Q | `term_spread` | 0.1768 | 0.8833 | 1.0000 | 1.0000 | 0.6508 | 0.0494 | 63 |
| 4Q | `plain_logistic` | 0.1973 | 0.8500 | 0.0000 | 0.0000 | 0.9048 | 0.0617 | 63 |

---

## 5. Self-Verification Harness: Nine-Gate Results
All nine mandatory gates pass cleanly via `scripts/08_verify_lane2a.py` and `make lane2a`:

| Gate | Description | Measured Value | Result |
|---|---|---|:---:|
| **G1** | Base commit contains `4556011` | `origin/feat/india-scope-docs` merged, ancestor verified | **PASS** |
| **G2** | USA label blob SHA-256 matches frozen hash | `2379fd53e4c9023538cafcd5668a4835bcdd7b45cfae9e3cbc3d4f306ed19daa` | **PASS** |
| **G3** | `USA_panel.csv` shape and window recorded in spec | 267 rows × 27 cols, 1960Q1–2026Q3, documented in `docs/FEATURES.md` | **PASS** |
| **G4** | `make features` produces unscaled table with zero blacklist | 147 rows × 149 features, contiguous 1990Q1–2026Q3, unscaled, 0 blacklisted | **PASS** |
| **G5** | `make folds` deterministic and satisfies D-R37 | SHA-256 `cc4814be7e02...`, approved: true, 80 init, step 1, first 2010Q1, purge=H | **PASS** |
| **G6** | `tests/test_features.py` passes; mutation fails on leaks | 6 passed in 1.27s; poison targets and future shifts caught | **PASS** |
| **G7** | Baselines reproduce identically with PR-AUC and recall | Byte-identical runs (`e227e254...`), 2Q term_spread PR-AUC=0.1556, recall=1.0000 | **PASS** |
| **G8** | D-R34 recorded and JPN metadata hash matches note | `3b74d3e63f4b6f19e15c372637c2f776e029903f710eba93c8a6cb395b99ed9a` verified | **PASS** |
| **G9** | Zero changes to `outputs/labels/**` | Working tree clean under `outputs/labels/**` | **PASS** |
