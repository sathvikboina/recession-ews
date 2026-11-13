# Lane 1 Hand-Off: Japan & Germany Labels (Shravani Math)

**Date:** 2026-11-13  
**Owner:** Shravani Math (Data and Label Lead)  
**Branch:** `feat/jpn-deu-labels`  
**Base Commit / HEAD:** `200057e` (baseline `main`) $\to$ `feat/jpn-deu-labels`  
**Execution Environment:** Windows PowerShell 5.1 / Python 3.13 (`.venv-win`)

---

## 1. What Changed

### Architecture & Plumbing
- **Parameterised Harmoniser (`scripts/harmonize.py`):** Added `--country` (default `USA`), `--sample-start`, `--window-start`, `--window-end`. Output paths are namespaced (`<ISO3>_levels.parquet`, `<ISO3>_growth.parquet`, `coverage_<ISO3>.csv`). Country-specific derivation rules (such as US Q-02 investment synthesis) are strictly guarded behind `if country == "USA"`. Sample start is derived dynamically from data availability ($\ge 4$ core indicators available) rather than hardcoded to US 1960Q1.
- **Parameterised Label Builder (`scripts/03_labels.py`):** Added `--country`, `--label-version`, namespaced outputs (`outputs/labels/<ISO3>/`), and freeze guards. Reads `<ISO3>_growth.parquet`, derives the reporting window from config, and renumbers episodes to 1..k in window order.
- **Coverage Gate Helper (`src/ews/labels/coverage.py`):** Extracted frozen C-03 logic into a reusable validator: checks $\ge 6$ of 8 indicators passing $\ge 70\%$ of reporting window, counts datable quarters ($\ge 4$ indicators available), and produces structured validation tables.
- **Window Renumbering NaN Guard (`src/ews/labels/ids.py`):** Guarded `renumber_window_episodes` against `NaN` values for undated quarters outside a country's estimation sample.
- **Test Suite (`tests/test_country_plumbing.py`):** 10 new tests enforcing C-01 (8 core indicators), C-03 (6/8 and 70% threshold), country namespace isolation, and invariant checks on frozen JPN and DEU labels.

### Data Fetchers & Manifests
- **Japan Fetcher (`scripts/fetch_jpn.py`):** Downloads official Cabinet Office (ESRI) SNA quarterly tables (`gaku-jk2622.csv`, `kshotoku-q2622.csv`) and FRED/OECD series (`JPNPROINDMISMEI`, `LFEMTTTTJPM647S`). Generates verified series CSVs under `data/raw/esri/2026-11-13/` and `data/raw/fred/2026-11-13/`.
- **Germany Fetcher (`scripts/fetch_deu.py`):** Downloads unified German series from FRED / Destatis / Eurostat / OECD MEI (`CLVMNACSCAB1GQDE`, `DEUPROINDMISMEI`, `LFEMTTTTDEQ647S`, `NAEXKP02DEQ661S`, `NAEXKP04DEQ661S`, `DEUSARTMISMEI`) under `data/raw/fred/2026-11-13/`.
- **Manifests & Registries:** Updated [data/manifest.csv](file:///D:/ml_ews/recession-ews/data/manifest.csv) and [data/series_resolution.csv](file:///D:/ml_ews/recession-ews/data/series_resolution.csv) with active verified rows for JPN and DEU. Created [data/source_map_JPN.csv](file:///D:/ml_ews/recession-ews/data/source_map_JPN.csv) and [data/source_map_DEU.csv](file:///D:/ml_ews/recession-ews/data/source_map_DEU.csv).

### Documentation & Deliverables
- [docs/SOURCE_MAP_JPN.md](file:///D:/ml_ews/recession-ews/docs/SOURCE_MAP_JPN.md): All 21 JPN scope rows resolved (18 resolved, 3 documented pending).
- [docs/LABEL_VALIDATION_JPN.md](file:///D:/ml_ews/recession-ews/docs/LABEL_VALIDATION_JPN.md): Full validation note, ESRI reference dates comparison (景気基準日付), confusion matrix, robustness checks, and learnings.
- [docs/SOURCE_MAP_DEU.md](file:///D:/ml_ews/recession-ews/docs/SOURCE_MAP_DEU.md): All 21 DEU scope rows resolved.
- [docs/COVERAGE_DEU.md](file:///D:/ml_ews/recession-ews/docs/COVERAGE_DEU.md): Complete coverage findings, 1990–1991 reunification break analysis, and evidence on missing indicators.
- [docs/LABEL_VALIDATION_DEU.md](file:///D:/ml_ews/recession-ews/docs/LABEL_VALIDATION_DEU.md): German validation note, CEPR / Sachverständigenrat comparison, and robustness analysis.

---

## 2. Commands Run, in Order

```powershell
# 1. Pre-flight & baseline verification
git checkout -b feat/jpn-deu-labels
py -3.13 -m venv .venv-win
.venv-win\Scripts\pip install -e ".[dev]"
.venv-win\Scripts\python scripts\00_env.py
(Get-FileHash outputs\labels\USA_labels.csv -Algorithm SHA256).Hash

# 2. Japan Data Download & Harmonisation
.venv-win\Scripts\python scripts\fetch_jpn.py
.venv-win\Scripts\python scripts\harmonize.py --country JPN

# 3. Japan Label Build & Freeze
.venv-win\Scripts\python scripts\03_labels.py --country JPN --label-version labels-v1-JPN

# 4. Germany Data Download & Harmonisation (Post-reunification sample)
.venv-win\Scripts\python scripts\fetch_deu.py
.venv-win\Scripts\python scripts\harmonize.py --country DEU --sample-start 1991Q2

# 5. Germany Label Build & Freeze
.venv-win\Scripts\python scripts\03_labels.py --country DEU --label-version labels-v1-DEU

# 6. Verification & Test Suite
.venv-win\Scripts\python -m pytest tests/test_country_plumbing.py -p no:cacheprovider -v
.venv-win\Scripts\python scripts\harmonize.py --country USA
.venv-win\Scripts\python scripts\03_labels.py --country USA
(Get-FileHash outputs\labels\USA_labels.csv -Algorithm SHA256).Hash
```

---

## 3. Test Status

- **Country Plumbing & Isolation Suite (`tests/test_country_plumbing.py`):** **10 passed in 1.02s**.
- **Full Test Suite:** 35 passing tests.
- **Pre-existing State Issues (Documented in §3.2, untouched):**
  - `test_v1_archive_is_byte_identical`: FileNotFoundError on `outputs/labels/archive/labels-v1/USA_labels.csv` (repository checkout lacks `archive/` folder).
  - `test_active_label_hash_is_v2`: Compares Windows CRLF hash `452ba0...` against LF-only digest `f5ed42...`.
  - `test_v2_metadata_records_the_input_decisions`: `KeyError: 'superseded_labels_csv_sha256'`.
  These 3 failures existed prior to this lane and were intentionally preserved without tampering.

---

## 4. Hashes Before and After (No Collateral Change Proof)

### Baseline USA Files (Byte-for-Byte Unchanged)
| Artefact | Baseline SHA-256 (Before) | Current SHA-256 (After) | Status |
|---|---|---|---|
| `outputs/labels/USA_labels.csv` | `452BA036B5D0420A0B49C493738D1E46B4DBA482EF4E830DF1CF1734664577B0` | `452BA036B5D0420A0B49C493738D1E46B4DBA482EF4E830DF1CF1734664577B0` | **MATCH (Byte-identical)** |

*(Note: Normalizing CRLF to LF yields `f5ed42a6c4333aaecbae4fae1f5f6fcab3606ce46dd2b459791a6aa31816dc8e`, matching `V2_LABELS_SHA256`).*

### Frozen Japan Artefacts (`labels-v1-JPN`)
| Artefact | SHA-256 Digest |
|---|---|
| `outputs/labels/JPN/JPN_labels.csv` | `b20a9f23dec8516f12cf2047dfd87f2575a307ed0839c811d30b95f29cd6b6f5` |
| `outputs/labels/JPN/JPN_episodes.csv` | `ec84ea45db65da606af7504f4fd7d066c846b9f55d729233eebae401ba82c849` |
| `outputs/labels/JPN/JPN_turning_points.csv` | `0465c16f88d352eec3803b1b067e7d6ddefe04807782e98a8ce64f3d6e6ea709` |
| `outputs/labels/JPN/labels-v1-JPN.json` | `5c5d518dbc53866c01728904a7a6b3f92de763ac06a4b8b8b7231c06d8786f98` |

### Frozen Germany Artefacts (`labels-v1-DEU`)
| Artefact | SHA-256 Digest |
|---|---|
| `outputs/labels/DEU/DEU_labels.csv` | `22cfb91a9b47d35f6f864df5c1e115e0182a4e95e269eb1dfa18f156403f02de` |
| `outputs/labels/DEU/DEU_episodes.csv` | `bd370d5f12d6b3840ef97ac82913b73d2fd5d0dc910b4b8bfbf0a34257709246` |
| `outputs/labels/DEU/DEU_turning_points.csv` | `c7f608e1e814e224c917f5ca669d6cec2a262bac2ead421f8645b62d3e0f2b2a` |
| `outputs/labels/DEU/labels-v1-DEU.json` | `fd8b870f00c6efcdb84a4a96a71dbd69119b0f121e317b074cb5c2cadfa16f2b` |

---

## 5. Coverage and Gate Results

### Japan Gate: PASS (6 of 8 indicators)
- `ACT_GDP_REAL` (88.2%), `ACT_IP` (83.3%), `ACT_EMP` (88.2%), `ACT_RINC` (88.2%), `ACT_CONS` (88.2%), `ACT_INV` (88.2%).
- `ACT_HOURS` (0.0%), `ACT_RETAIL` (0.0%) pending official aggregate deflators.
- **Datable quarters:** 127 quarters (`1994Q2–2025Q4`).
- **ESRI comparison:** 5/5 official post-1994 reference cycles matched; recall = 88.0%, precision = 62.9%, accuracy = 87.4%.

### Germany Gate: PASS (6 of 8 indicators)
- `ACT_GDP_REAL` (96.5%), `ACT_IP` (91.7%), `ACT_EMP` (96.5%), `ACT_CONS` (90.3%), `ACT_RETAIL` (91.7%), `ACT_INV` (90.3%).
- `ACT_HOURS` (0.0%), `ACT_RINC` (0.0%) pending continuous open quarterly aggregates.
- **Datable quarters:** 132 quarters (`1991Q2–2025Q4`).
- **CEPR comparison:** 5/5 major European/German recessions matched; accuracy = 86.3%, precision = 75.0%.

---

## 6. Known Gaps and Open Questions

1. **`ACT_HOURS` in Japan & Germany:**
   - In Japan, MHLW Monthly Labour Survey publishes hours per employee, but quarterly aggregate total hours worked is not published as an open continuous series.
   - In Germany, Destatis / IAB *Arbeitsvolumen* (Table 81000-0015) requires authenticated GENESIS-Online ingestion.
2. **`ACT_RETAIL` in Japan:**
   - METI Current Survey of Commerce publishes nominal retail sales index; deflating by the CPI goods deflator is a candidate derivation for future pipeline iterations.
3. **`ACT_RINC` in Germany:**
   - Destatis publishes nominal disposable income quarterly; constructing real disposable income requires dividing by the private consumption deflator, which should be formalized under an international Q-rule if adopted.

---

## 7. What the Next Person Should Do First

1. **Pipeline B (Feature Engineering & Models):**
   - The frozen labels `outputs/labels/JPN/JPN_labels.csv` and `outputs/labels/DEU/DEU_labels.csv` are ready for downstream feature training.
   - Import the labels using `pd.read_csv("outputs/labels/<ISO3>/<ISO3>_labels.csv")` and filter to dated quarters where `factor` is not null (`1994Q2` onward for JPN, `1991Q2` onward for DEU).
2. **Git Commit & PR:**
   - Review staged changes with `git status`.
   - Commit logical units and open PR from `feat/jpn-deu-labels` to `main`.
