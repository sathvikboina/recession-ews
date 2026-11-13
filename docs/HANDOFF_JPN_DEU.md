# Lane 1 Hand-Off: Japan & Germany Labels (Shravani Math)

**Date:** 2026-11-13  
**Owner:** Shravani Math (Data and Label Lead)  
**Branch:** `feat/jpn-deu-labels`  
**Base Commit / Branch Point:** `fa57a1c` (baseline `master`) $\to$ `feat/jpn-deu-labels`  
**Reporting Window Decision:** **144 quarters (1990Q1–2025Q4)** (confirmed decision on 2026-11-13; documented deviation from the 147-quarter brief to preserve master repo consistency and prevent collateral hash churn across pipelines).  
**Execution Environment:** Windows PowerShell 5.1 / Python 3.13 (`.venv-win`)

---

## 1. Executive Summary & Lane Deliverables

Lane 1 deliverables under `docs/BUILD_CONTRACT.md` Rules C-01–C-12 and the Lane 1 Master Prompt:

1. **Frozen Japan BEAI Label (`labels-v1-JPN`)**: Delivered and frozen. Exactly 6 of 8 core indicators pass C-03 ($88.9\%$ raw window coverage; $83.3\%$ post-differencing sample coverage). DFM converged cleanly (`loglik = -903.87`). 7 contraction episodes dated, matching all 5 official post-1994 Cabinet Office (ESRI) business cycle reference dates (景気基準日付) with 0 missed cycles (episode-level match 5/5; quarter-level recall 88.0%, precision 62.9%, accuracy 87.4%). Documented in [docs/LABEL_VALIDATION_JPN.md](file:///D:/ml_ews/recession-ews/docs/LABEL_VALIDATION_JPN.md).
2. **Germany Decision (Honest Coverage Finding)**: Delivered as a formal **Coverage Finding Report** ([docs/COVERAGE_DEU.md](file:///D:/ml_ews/recession-ews/docs/COVERAGE_DEU.md)). Decision Q-02 strictly forbids substituting total GFCF (`NAEXKP04DEQ661S`) for business fixed investment. Excluding total GFCF leaves Germany with only 5 passing indicators, which fails the $\ge 6/8$ threshold of Rule C-03. Preliminary freeze `labels-v1-DEU` has been revoked from HEAD (preserved in git commit history `61a8eb0`). Chronology is benchmarked against official GCEE reference cycles (quarter-level recall 51.7%, precision 75.0%, accuracy 86.3%) with late peak lags explicitly identified.
3. **Country-Parameterised Pipeline (Zero Forked Math)**: `scripts/harmonize.py` and `scripts/03_labels.py` parameterised with `--country <ISO3>`. Output paths are strictly namespaced (`data/clean/<ISO3>_*`, `outputs/labels/<ISO3>/`). Sample starts are config-driven in `config/scope.yaml` (DEU `1991Q2`, USA `1960Q1`, JPN dynamic).
4. **USA No-Collateral-Change Proof**: `outputs/labels/USA_labels.csv` is **100% byte-for-byte identical to master** (`452BA036B5D0420A0B49C493738D1E46B4DBA482EF4E830DF1CF1734664577B0`).
5. **Audit Remediation**: All 5 ranked defects from [docs/AUDIT_JPN_DEU.md](file:///D:/ml_ews/recession-ews/docs/AUDIT_JPN_DEU.md) resolved.

---

## 2. Architecture & Plumbing

- **Parameterised Harmoniser (`scripts/harmonize.py`):** Added `--country` (default `USA`), `--sample-start`, `--window-start`, `--window-end`. Output paths are namespaced (`<ISO3>_levels.parquet`, `<ISO3>_growth.parquet`, `coverage_<ISO3>.csv`). Country-specific derivations (e.g. US Q-02 investment synthesis) are isolated behind `if country == "USA"`. Sample starts are resolved from `config/scope.yaml`.
- **Dual Coverage Reporting (`scripts/harmonize.py`):** Computes and writes both `raw_window_coverage` (quarters in 1990Q1–2025Q4; C-03 gate input) and `estimator_sample_coverage` (quarters available in the estimation sample) into `coverage_<ISO3>.csv`.
- **Parameterised Label Builder (`scripts/03_labels.py`):** Accepts `--country`, `--label-version`, namespaced outputs (`outputs/labels/<ISO3>/`), and freeze guards. Records exact downloaded series IDs and raw file SHA-256 digests in JSON metadata.
- **Coverage Gate Helper (`src/ews/labels/coverage.py`):** Extracted reusable C-03 logic enforcing 6/8 indicators, $\ge 70\%$ coverage, and $\ge 4$ indicators per quarter.
- **Tests (`tests/test_country_plumbing.py`):** 14 passing tests (1 skipped for revoked DEU label) enforcing C-01, C-02, C-03, C-06, C-12, raw hash verification, and country isolation.

---

## 3. Coverage Arithmetic (Both Metrics Reported)

### Metric Reconciliation (Audit A5 / Step 3)
*The metrics differ because `raw_window_coverage` evaluates complete quarters of the underlying raw series across the entire 144-quarter window (`1990Q1–2025Q4`), whereas `estimator_sample_coverage` measures quarters available after sample start truncation (`1994Q2` for JPN, `1991Q2` for DEU) and growth first-differencing.*

### Japan (`data/clean/coverage_JPN.csv`) — GATE PASS (6 of 8)

| BEAI Indicator ID | Concept | Source ID | Raw Window Coverage | Estimator Sample Coverage | C-03 Gate |
|---|---|---|:---:|:---:|:---:|
| `ACT_GDP_REAL` | Real Gross Domestic Product | `ESRI:tables/gaku-jk2622.csv (Col 1)` | 128 / 144 (88.9%) | 127 / 144 (88.2%) | **PASS** |
| `ACT_IP` | Industrial Production Index | `FRED:JPNPROINDMISMEI` | 137 / 144 (95.1%) | 120 / 144 (83.3%) | **PASS** |
| `ACT_EMP` | Total Employment | `FRED:LFEMTTTTJPM647S` | 144 / 144 (100.0%) | 127 / 144 (88.2%) | **PASS** |
| `ACT_RINC` | Real Compensation of Employees | `ESRI:tables/kshotoku-q2622.csv (Col 3)` | 128 / 144 (88.9%) | 127 / 144 (88.2%) | **PASS** |
| `ACT_CONS` | Real Private Consumption | `ESRI:tables/gaku-jk2622.csv (Col 2)` | 128 / 144 (88.9%) | 127 / 144 (88.2%) | **PASS** |
| `ACT_INV` | Real Business Fixed Investment | `ESRI:tables/gaku-jk2622.csv (Col 6)` | 128 / 144 (88.9%) | 127 / 144 (88.2%) | **PASS** |
| `ACT_HOURS` | Total Hours Worked | `MHLW Table 0003058864` | 0 / 144 (0.0%) | 0 / 144 (0.0%) | **FAIL** |
| `ACT_RETAIL` | Real Retail Sales Volume | `METI Table 0003195026` | 0 / 144 (0.0%) | 0 / 144 (0.0%) | **FAIL** |

*Note on 1990–1994 data:* Prior to 1994Q1, only 2 indicators exist for Japan (`ACT_IP` and `ACT_EMP`). Under Rule C-03, a quarter cannot be dated with fewer than 4 indicators. Therefore, starting the estimation sample before 1994Q2 is mathematically prohibited by C-03, discards zero datable cycles, and changes no episode outcomes.

### Germany (`data/clean/coverage_DEU.csv`) — GATE FAIL (5 of 8)

| BEAI Indicator ID | Concept | Source ID | Raw Window Coverage | Estimator Sample Coverage | C-03 Gate |
|---|---|---|:---:|:---:|:---:|
| `ACT_GDP_REAL` | Real Gross Domestic Product | `FRED:CLVMNACSCAB1GQDE` | 140 / 144 (97.2%) | 139 / 144 (96.5%) | **PASS** |
| `ACT_IP` | Industrial Production Index | `FRED:DEUPROINDMISMEI` | 137 / 144 (95.1%) | 132 / 144 (91.7%) | **PASS** |
| `ACT_EMP` | Total Employment | `FRED:LFEMTTTTDEQ647S` | 144 / 144 (100.0%) | 139 / 144 (96.5%) | **PASS** |
| `ACT_CONS` | Real Private Consumption | `FRED:NAEXKP02DEQ661S` | 135 / 144 (93.8%) | 130 / 144 (90.3%) | **PASS** |
| `ACT_RETAIL` | Retail Trade Volume Index | `FRED:DEUSARTMISMEI` | 137 / 144 (95.1%) | 132 / 144 (91.7%) | **PASS** |
| `ACT_INV` | Real Business Fixed Investment | `Destatis VGR (S.11)` | 0 / 144 (0.0%) | 0 / 144 (0.0%) | **FAIL (Q-02)** |
| `ACT_HOURS` | Total Hours Worked | `GENESIS Table 81000-0015` | 0 / 144 (0.0%) | 0 / 144 (0.0%) | **FAIL** |
| `ACT_RINC` | Real Household Income | `GENESIS Table 81000-0030` | 0 / 144 (0.0%) | 0 / 144 (0.0%) | **FAIL** |

*Note on Q-02:* Total GFCF (`NAEXKP04DEQ661S`) includes residential housing construction and public investment. Decision Q-02 strictly forbids total GFCF substitution. Without compliant S.11 corporate investment, Germany achieves 5 passing indicators and does not qualify for a frozen label.

---

## 4. Chronology Validation & Honesty

### Japan vs Official Cabinet Office (ESRI) Reference Dates
- **Episode-Level Match:** **5 of 5 post-1994 official ESRI cycles matched** (0 missed cycles).
- **Cycle Details:**
  - Cycle 12 (1997Q2–1999Q1): BEAI 1997Q1–1999Q1 (Peak −1Q, Trough exact)
  - Cycle 13 (2000Q4–2002Q1): BEAI 2001Q1–2001Q4 (Nested match)
  - Cycle 14 (2008Q1–2009Q1): BEAI 2007Q2–2009Q1 (Peak −3Q lead on export slump, Trough exact)
  - Cycle 15 (2012Q1–2012Q4): BEAI 2012Q1–2012Q3 (Peak exact, Trough −1Q)
  - Cycle 16 (2018Q4–2020Q2): BEAI 2018Q2–2020Q2 (Peak −2Q lead on IP slump, Trough exact)
  - Non-ESRI dated contractions: 2010Q3–2011Q2 (Tohoku disaster) and 2023Q1–2024Q1 (Recent slowdown).
- **Headline Quarter-Level Classification Metrics (`1994Q2–2025Q4` = 127 quarters):**
  - **TP:** 22, **FP:** 13, **FN:** 3, **TN:** 89
  - **Accuracy:** **87.4%**
  - **Precision:** **62.9%**
  - **Recall:** **88.0%** (22/25 ESRI quarters; 3 FN quarters from 1Q boundary leads/lags)
  - **F1 Score:** **0.733**

### Germany vs GCEE / Sachverständigenrat Reference Dates
- **Single Reference Standard:** German Council of Economic Experts (GCEE / Sachverständigenrat).
- **GCEE Turning Point Gaps:**
  - 1992Q1–1993Q2: BEAI 1992Q1–1993Q2 (Exact Match, 0Q gap)
  - 2001Q1–2003Q2: BEAI 2002Q3–2003Q1 (**Late +6Q peak**; BBQ identifies acute phase)
  - 2008Q1–2009Q1: BEAI 2008Q1–2009Q1 (Exact Match, 0Q gap)
  - 2011Q3–2013Q1: BEAI 2012Q3–2013Q1 (**Late +4Q peak**; German industrial downturn lagged peripheral Eurozone crisis)
  - 2019Q4–2020Q2: BEAI 2019Q3–2020Q2 (Lead 1Q, 0Q trough gap)
- **Headline Quarter-Level Classification Metrics (`1991Q2–2025Q4` = 139 quarters):**
  - **TP:** 15, **FP:** 5, **FN:** 14, **TN:** 105
  - **Accuracy:** **86.3%**
  - **Precision:** **75.0%**
  - **Recall:** **51.7%** (directly reflecting +6Q and +4Q peak lags during plateau phases)
  - **F1 Score:** **0.612**

---

## 5. Hashes Before and After (No Collateral Change Proof)

### Baseline USA Files (Byte-for-Byte Unchanged)
| Artefact | Baseline SHA-256 (Before) | Current SHA-256 (After) | Status |
|---|---|---|---|
| `outputs/labels/USA_labels.csv` | `452BA036B5D0420A0B49C493738D1E46B4DBA482EF4E830DF1CF1734664577B0` | `452BA036B5D0420A0B49C493738D1E46B4DBA482EF4E830DF1CF1734664577B0` | **MATCH (Byte-identical)** |

*(CRLF digest matches master `outputs/labels/USA_labels.csv` exactly; LF normalization yields `f5ed42a6c4333aaecbae4fae1f5f6fcab3606ce46dd2b459791a6aa31816dc8e`).*

### Frozen Japan Artefacts (`labels-v1-JPN`)
| Artefact | SHA-256 Digest | Status |
|---|---|---|
| `outputs/labels/JPN/JPN_labels.csv` | `b20a9f23dec8516f12cf2047dfd87f2575a307ed0839c811d30b95f29cd6b6f5` | **FROZEN** |
| `outputs/labels/JPN/JPN_episodes.csv` | `ec84ea45db65da606af7504f4fd7d066c846b9f55d729233eebae401ba82c849` | **FROZEN** |
| `outputs/labels/JPN/JPN_turning_points.csv` | `0465c16f88d352eec3803b1b067e7d6ddefe04807782e98a8ce64f3d6e6ea709` | **FROZEN** |
| `outputs/labels/JPN/labels-v1-JPN.json` | `835aff6e9dc3fa526175c20153e8ca714a1d4d9eb00dd1a5cdfdf73c65b715c5` | **FROZEN (Provenance verified)** |

### Germany Artefacts
- **Status:** **REVOKED (Finding Delivered)**.
- Preliminary files (`DEU_labels.csv`, `labels-v1-DEU.json`) removed from HEAD to honor Decision Q-02.

---

## 6. Test Suite Evidence

```text
============================= test session starts =============================
platform win32 -- Python 3.13.0, pytest-8.3.3
rootdir: D:\ml_ews\recession-ews
configfile: pyproject.toml
collected 45 items

tests/test_config.py ......                                              [ 13%]
tests/test_country_plumbing.py ..............s                           [ 46%]
tests/test_freeze.py .FF....F                                            [ 64%]
tests/test_labels.py ..................                                  [100%]

=========================== short test summary info ===========================
FAILED tests/test_freeze.py::test_v1_archive_is_byte_identical - FileNotFoundError (missing archive/ on master)
FAILED tests/test_freeze.py::test_active_label_hash_is_v2 - AssertionError (CRLF 452ba... vs LF f5ed4...)
FAILED tests/test_freeze.py::test_v2_metadata_records_the_input_decisions - KeyError ('superseded_labels_csv_sha256')
41 passed, 1 skipped, 3 failed in 1.48s
```
- **New Tests:** All 14 tests in `tests/test_country_plumbing.py` pass cleanly (1 skipped for revoked DEU label).
- **Pre-existing Failures:** The 3 failures in `tests/test_freeze.py` were proved byte-for-byte identical on `master` via a throwaway detached worktree `%TEMP%\audit-master` (Audit A2). No failures were introduced by Lane 1.

---

## 7. Known Gaps and Future Roadmap

1. **Destatis S.11 Fixed Investment API Pipeline:** To qualify Germany in future iterations, develop an authenticated fetcher for Destatis GENESIS Table 81000 (S.11 non-residential GFCF by asset) and matching price deflator to resolve `DEU.ACT_INV`.
2. **Total Hours Worked (`ACT_HOURS`):**
   - JPN: Evaluate MHLW aggregate hours vs per-worker index.
   - DEU: Ingest Destatis Table `81000-0015` (IAB Arbeitsvolumen).
3. **Retail & Real Income:**
   - JPN `ACT_RETAIL`: Deflate METI nominal retail sales index by CPI goods deflator.
   - DEU `ACT_RINC`: Deflate Destatis quarterly nominal disposable income (`81000-0030`) with standardized national accounts consumption deflator.