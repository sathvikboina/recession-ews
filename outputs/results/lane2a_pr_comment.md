# Lane 2A Verification & Test Evidence Handoff

**Author:** Shravani Math (Lane 2A Specification and Verification Owner)  
**Branch:** `feat/features-harness`  
**Status:** ALL GATES PASS (Self-Verification Report: `outputs/results/lane2a_verification.json`)  
**Frozen USA Label SHA-256:** `2379fd53e4c9023538cafcd5668a4835bcdd7b45cfae9e3cbc3d4f306ed19daa` (Verified byte-identical)  
**Deterministic Fold Checksum (SHA-256):** `b59ea4c2bbcc5da3fde3a45ed4b04bc3278ffe3d2a67577489fd40b9eb3ad8a9`  

---

## 1. Feature Firewall Test Suite (`tests/test_features.py`)

All six tests passed cleanly in `0.83s`:

| Test Name | Result | What It Proves |
|---|:---:|---|
| `test_schema` | **PASS** | Exactly 147 rows, contiguous `1990Q1`–`2026Q3`, key `'quarter'`, zero duplicates. |
| `test_blacklist` | **PASS** | Case-insensitive scan proves zero blacklisted tokens (`factor`, `level`, `R`, `n_available`, `deterioration_share`, turning points, `NBER`, `country_id`, `episode_id`). |
| `test_unscaled` | **PASS** | No column standardized ($|\mu|<10^{-9}$ and $|\sigma-1|<10^{-6}$); rate columns (`rate_long`, `unemp`) identically match unscaled source panel values. |
| `test_no_future_leakage` | **PASS** | At cutoffs `2000Q4`, `2010Q2`, `2019Q4`, `2024Q3`, truncated features equal full-table values for all $\le t$ (max diff $< 10^{-9}$). |
| `test_independence` | **PASS** | Zero Pipeline A objects; all 8 `beai_copy_*` columns strictly reproduced from `USA_growth.parquet` alone; zero scaler objects saved. |
| `test_mutation_fails_on_leak` | **PASS** | Deliberately poisoned tables trigger hard failure in `validate_table`. |

### Mutation Test Evidence
- **Poison Variant (a): Target injection (`R=0`).** Raised `ValueError: Blacklisted column detected (exact token): 'R'`.
- **Poison Variant (b): Future shift (`rate_long.shift(-1)`).** Raised `ValueError: Future leakage detected: column 'rate_long' is shifted from future (shift -1Q)`.
- **Poison Variant (b2): Injected novel future shift (`rate_short.shift(-1)`).** Raised `ValueError: Future leakage detected: injected column 'future_leak_col' matches future shift (-1Q) of 'rate_short'`.

---

## 2. Baseline Model Performance (`outputs/results/baselines.csv`)

- **Random Seed:** `42`
- **Threshold:** `0.50` (fixed; no threshold tuning)
- **Evaluation:** Out-of-sample pooled predictions across expanding outer test blocks
- **Term Spread Predictor:** `term_spread_10y_3m` (`GS10 - TB3MS`)

| Horizon | Model | Pooled PR-AUC | ROC-AUC | Episode Recall (Test) | Accuracy | Brier Score | N Test Obs |
|---|---|---:|---:|---:|---:|---:|---:|
| **1Q** | `majority` | 0.0200 | 0.5000 | 0.0000 | 0.9800 | 0.0196 | 100 |
| **1Q** | `term_spread` | 0.0871 | 0.8140 | 0.0000 | 0.9800 | 0.0255 | 100 |
| **1Q** | `plain_logistic` | 0.0445 | 0.7093 | 0.0000 | 0.9800 | 0.0416 | 100 |
| **2Q (primary)** | `majority` | 0.0359 | 0.5000 | 0.0000 | 0.9641 | 0.0346 | 195 |
| **2Q (primary)** | `term_spread` | 0.1535 | 0.8412 | 0.0000 | 0.9641 | 0.0389 | 195 |
| **2Q (primary)** | `plain_logistic` | 0.0879 | 0.7588 | 0.0000 | 0.9590 | 0.0544 | 195 |
| **4Q** | `majority` | 0.0665 | 0.5000 | 0.0000 | 0.9335 | 0.0621 | 376 |
| **4Q** | `term_spread` | 0.2529 | 0.8659 | 1.0000 | 0.9388 | 0.0560 | 376 |
| **4Q** | `plain_logistic` | 0.2040 | 0.8415 | 0.0000 | 0.9335 | 0.0768 | 376 |

---

## 3. Japan Window Closeout & Integrity
- Decision **D-R34** formally added to `docs/DECISIONS.md`: `labels-v1-JPN` covers 144 quarters (`1990Q1–2025Q4`) as an approved documented exception to D-R02/D-R31. Rebuilding `labels-v2-JPN` is deferred to after the official run.
- `outputs/labels/JPN/labels-v1-JPN.json` SHA-256 verified as `3b74d3e63f4b6f19e15c372637c2f776e029903f710eba93c8a6cb395b99ed9a` (identical across raw and LF-normalized working tree bytes).
- Zero changes to any file in `outputs/labels/**`.
