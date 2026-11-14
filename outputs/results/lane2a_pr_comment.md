# Lane 2A Verification & Test Evidence Handoff

**Author:** Shravani Math (Lane 2A Specification and Verification Owner)  
**Branch:** `feat/features-harness`  
**Status:** ALL GATES PASS (Self-Verification Report: `outputs/results/lane2a_verification.json`)  
**Frozen USA Label SHA-256:** `2379fd53e4c9023538cafcd5668a4835bcdd7b45cfae9e3cbc3d4f306ed19daa` (Verified byte-identical)  
**Frozen Folds Checksum (SHA-256):** `cc4814be7e020d466d53e905961c46f5a2ccbe3a0b9197fd7b9e62eb0feb8719` (D-R37: 80 init, step 1, 2010Q1 first scored, purge=H)  
**Shipped Feature Dataset SHA-256:** `e35b43ddf09f50759f4bb09b27119e92fb8d895368f3a319794cc96d970647d0` (`data/clean/dataset.parquet`)  

---

## 1. Feature Firewall Test Suite (`tests/test_features.py`)

All six tests passed cleanly against the shipped table:

| Test Name | Result | What It Proves |
|---|:---:|---|
| `test_schema` | **PASS** | Exactly 147 rows, contiguous `1990Q1`–`2026Q3`, key `'quarter'`, zero duplicates. |
| `test_blacklist` | **PASS** | Case-insensitive scan proves zero blacklisted tokens (`factor`, `level`, `R`, `n_available`, `deterioration_share`, turning points, `NBER`, `country_id`, `episode_id`). |
| `test_unscaled` | **PASS** | No column standardized ($|\mu|<10^{-9}$ and $|\sigma-1|<10^{-6}$); rate columns (`FIN_LONG__level`, `LAB_UNEMP__level`) identically match unscaled source panel values. |
| `test_no_future_leakage` | **PASS** | At cutoffs `2000Q4`, `2010Q2`, `2019Q4`, `2024Q3`, truncated features equal full-table values for all $\le t$ (max diff $< 10^{-9}$). |
| `test_independence` | **PASS** | Zero Pipeline A objects; all 8 core series appear strictly under `beai_copy_*`; zero scaler objects saved. |
| `test_mutation_fails_on_leak` | **PASS** | Deliberately poisoned tables trigger hard failure in `validate_table`. |

### Mutation Test Evidence
- **Poison Variant (a): Target injection (`R=0`).** Raised `ValueError: Blacklisted column detected (exact token): 'R'`.
- **Poison Variant (b): Future shift (`rate_long.shift(-1)`).** Raised `ValueError: Future leakage detected: column 'rate_long' is shifted from future (shift -1Q)`.
- **Poison Variant (b2): Injected novel future shift (`rate_short.shift(-1)`).** Raised `ValueError: Future leakage detected: injected column 'future_leak_col' matches future shift (-1Q) of 'rate_short'`.

---

## 2. Baseline Model Performance (`outputs/results/baselines.csv`)

- **Random Seed:** `42`
- **Primary Operating Point (Headline):** Training-fold positive prevalence (fixed prevalence rule, recomputed strictly per fold from $y_{train}$ only, never tuned)
- **Secondary Operating Point:** `0.50` fixed threshold
- **Evaluation:** Out-of-sample pooled predictions across D-R37 expanding outer test blocks
- **Term Spread Predictor:** `FIN_SLOPE__level`

### 2Q Primary Horizon Episode Recall (Before vs. After)
| Baseline Model | PR-AUC | 2Q Recall Before (0.50 Threshold) | 2Q Recall After (Prevalence Rule) | Accuracy (Prev) |
|---|---:|---:|---:|---:|
| `majority` | 0.0236 | 0.0000 | **1.0000** | 0.0308 |
| `term_spread` | 0.1556 | 0.0000 | **1.0000** | 0.6308 |
| `plain_logistic` | 0.1080 | 0.0000 | **0.0000** | 0.8769 |

### All Horizons Baseline Summary
| Horizon | Model | PR-AUC | ROC-AUC | Episode Recall (Prev) | Episode Recall (0.50) | Accuracy (Prev) | Brier Score | N Test Obs |
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

## 3. Builder Reconciliation & Shipped Table
- **Shipped Production Table:** `data/clean/dataset.parquet` (147 rows, 149 features covering 1990Q1–2026Q3), produced by `scripts/05_features.py`. Policed by `tests/test_features.py`.
- **Reference Fixture:** `scripts/06_features.py` retained as documented reference implementation for pure-function testing.

---

## 4. Nine Mandatory Verification Gates
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
