# Germany Coverage Finding & Data Architecture Report (Lane 1: Shravani Math)

This report provides the formal evaluation of the C-03 coverage gate for Germany under `docs/BUILD_CONTRACT.md` and `docs/DECISION_NOTE_Q02_Q04_Q05.md`. It documents the disqualification of total GFCF under Decision Q-02, the 1990–1991 German reunification structural break, the coverage metrics for all eight core indicators, and the reference chronology comparison against the German Council of Economic Experts (GCEE / Sachverständigenrat).

---

## 1. Executive Summary & Gate Decision

- **Gate Standard (BUILD_CONTRACT C-03):** Target reporting window `1990Q1–2025Q4` (144 quarters; $70\% = \ge 101$ quarters). A country is BEAI-eligible only with $\ge 6$ of 8 core indicators meeting the $70\%$ threshold; $\ge 4$ indicators are required to date a quarter. Missing stays missing (no interpolation, no forward fill).
- **Rule Q-02 Compliance (Decision Note Q-02):** "Strict: business (non-residential) fixed investment only. Total GFCF is not substituted; where business investment is missing the component counts as missing."
- **Gate Outcome:** **FAIL (5 of 8 indicators pass)**.
- **Decision:** Germany does **NOT qualify** for a frozen BEAI label. The preliminary freeze (`labels-v1-DEU`) has been revoked and removed from HEAD. Germany is delivered as an honest **Coverage Finding** documenting the exact data requirements needed for future qualification.

### Core Indicator Coverage Table (Both Metrics Reported)

| BEAI Indicator ID | Concept | Source ID | Native Freq | Raw Window Coverage | Estimator Sample Coverage | Status under Q-02 / C-03 |
|---|---|---|:---:|:---:|:---:|:---:|
| `ACT_GDP_REAL` | Real Gross Domestic Product | `FRED:CLVMNACSCAB1GQDE` | Q | 140 / 144 (97.2%) | 139 / 144 (96.5%) | **PASS** |
| `ACT_IP` | Industrial Production Index | `FRED:DEUPROINDMISMEI` | M | 137 / 144 (95.1%) | 132 / 144 (91.7%) | **PASS** |
| `ACT_EMP` | Total Employment (QNA) | `FRED:LFEMTTTTDEQ647S` | Q | 144 / 144 (100.0%) | 139 / 144 (96.5%) | **PASS** |
| `ACT_CONS` | Real Private Consumption | `FRED:NAEXKP02DEQ661S` | Q | 135 / 144 (93.8%) | 130 / 144 (90.3%) | **PASS** |
| `ACT_RETAIL` | Retail Trade Volume Index | `FRED:DEUSARTMISMEI` | M | 137 / 144 (95.1%) | 132 / 144 (91.7%) | **PASS** |
| `ACT_INV` | Real Business Fixed Investment | `Destatis VGR (S.11)` | Q | 0 / 144 (0.0%) | 0 / 144 (0.0%) | **FAIL (Q-02 non-compliant)** |
| `ACT_HOURS` | Total Hours Worked | `GENESIS Table 81000-0015` | Q | 0 / 144 (0.0%) | 0 / 144 (0.0%) | **FAIL (Excluded)** |
| `ACT_RINC` | Real Household Income | `GENESIS Table 81000-0030` | Q | 0 / 144 (0.0%) | 0 / 144 (0.0%) | **FAIL (Excluded)** |

*Reconciliation of metrics:* `raw_window_coverage` evaluates complete quarters of the raw downloaded series inside `1990Q1–2025Q4` (C-03 gate input), whereas `estimator_sample_coverage` evaluates quarters available after applying the post-reunification sample start (`1991Q2`) and growth first-differencing.

---

## 2. Decision Q-02 Evaluation: Why Total GFCF Cannot Ship

The audit of Lane 1 identified that the preliminary German build utilized FRED series `NAEXKP04DEQ661S` for `ACT_INV`. 

1. **Substantive Defect:** `NAEXKP04DEQ661S` measures **Total Gross Fixed Capital Formation** (*Bruttoanlageinvestitionen*), encompassing residential housing construction (*Wohnungsbau*) and general government public infrastructure (*Staatliche Anlageinvestitionen*).
2. **Strict Rule Prohibition:** `docs/DECISION_NOTE_Q02_Q04_Q05.md:62-64` explicitly establishes:
   > *"Strict: business (non-residential) fixed investment only. Total GFCF is not substituted; where business investment is missing the component counts as missing."*
3. **Empirical Evaluation of Alternative German Datasets:** Rather than asserting data unavailability, three direct candidate sources were empirically retrieved, measured, and evaluated against the requirements of Decision Q-02 (private non-residential corporate investment, deflated/constant-price, post-reunification sample $\ge 108$ quarters):

### Empirical Evaluation of German Investment Series Candidates

| Attempt | Source & Dataset ID | Concept / Series Scope | Available Range | Quarters in Window (`1990Q1–2025Q4`) | Price Basis | Strips Housing? | Strips General Gov (S.13)? | Q-02 / C-03 Compliance |
|:---:|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | Eurostat `nasq_10_nf_tr` | S.11 Non-financial corporations GFCF (`P51G`, `SCA`) | `1999Q1–2026Q2` | 108 / 144 (75.0%) | Nominal only (`CP_MEUR`) | **No** (contains corporate dwellings) | **Yes** (S.11 isolated) | **FAIL**: Nominal only; includes housing; no deflator in dataset. |
| **2** | Eurostat `namq_10_an6` / `nama_10_an6` | GFCF by asset: Equipment (`N11MG`) + Other buildings (`N112G`) + IPP (`N117G`) | `1991Q1–2026Q2` | 140 / 144 (97.2%) | Deflated (`CLV15_MEUR`) | **Yes** (`N111G` dwellings excluded) | **No** (Total Economy S.1; includes Gov S.13 roads, schools, defense) | **FAIL**: Total economy; contaminated by general government investment. |
| **3** | Destatis Genesis Table `81000-0020` / `-0024` | Quarterly national accounts: GFCF by sector and asset | `1999Q1–2026Q2` | 108 / 144 (75.0%) | Nominal only (*in jeweiligen Preisen*) | **No** (dwellings included under S.11) | **Yes** (S.11 isolated) | **FAIL**: Nominal only; pre-1999 is strictly annual; no quarterly chained deflators by sector. |
| **—** | FRED `NAEXKP04DEQ661S` (Audit Baseline) | Total Economy GFCF (*Bruttoanlageinvestitionen*) | `1970Q1–2023Q3` | 135 / 144 (93.8%) | Deflated (Chained 2015 EUR) | **No** (includes residential) | **No** (includes government) | **FAIL**: Total GFCF expressly forbidden by Decision Q-02. |

4. **Empirical Gate Impact & Final Decision:** None of the candidate series satisfies Decision Q-02 and Rule C-03 simultaneously:
   - Eurostat `nasq_10_nf_tr` and Destatis `81000` provide institutional sector isolation (S.11) but exist only at current prices (nominal) without quarterly deflators and without stripping corporate dwellings.
   - Eurostat `namq_10_an6` successfully strips housing and is deflated, but is compiled only for the total economy (S.1), contaminating the series with general government infrastructure and defence expenditures.
   Consequently, Germany strictly yields **5 passing indicators**, failing the $\ge 6/8$ threshold of Rule C-03. In accordance with Build Contract §0, the finding stands on empirical data, not assertion: Germany is delivered as an honest **Coverage Finding**.

---

## 3. The 1990–1991 German Reunification Break

### Cited Historical Evidence & Sources
- **Destatis VGR Revision 2014:** Statistisches Bundesamt, *Wirtschaft und Statistik*, "Revision der Volkswirtschaftlichen Gesamtrechnungen 2014 für den Zeitraum 1991 bis 2014" (Heft 9/2014). Destatis formally establishes **1991Q1** as the first quarter of official unified German national accounts under ESA 2010.
- **Deutsche Bundesbank Monthly Report:** Deutsche Bundesbank, *Monatsbericht*, Oktober 1990: "Zur Entwicklung der Wirtschaft und der öffentlichen Finanzen im vereinten Deutschland". Documents the structural discontinuity and non-comparability of economic levels across the July 1990 economic/monetary union and October 1990 political reunification.

### Pipeline A Estimation Protocol
- Pre-1991 data represents West Germany only (*früheres Bundesgebiet*). Splicing pre- and post-reunification levels produces massive false growth spikes (e.g. $+13.5\%$ in retail turnover and $+1.7\text{M}$ workers in employment).
- Rule C-03 strictly forbids ad-hoc statistical splicing. Therefore, Germany's sample start is formally codified in `config/scope.yaml` as **`1991Q2`** (with `1991Q1` providing the initial level base for differencing).
- Pre-1991 quarters in the reporting window (`1990Q1–1991Q1`) remain unassigned.

---

## 4. Chronology Evaluation Against GCEE (Sachverständigenrat)

To evaluate the informational properties of the 5-to-6 indicator German data, an experimental Dynamic Factor Model was estimated on the post-reunification sample `1991Q2–2025Q4` (139 quarters; 132 quarters datable with $\ge 4$ indicators). 

Following Step 2c, chronology validation uses **ONE official reference standard — the German Council of Economic Experts (GCEE / Sachverständigenrat zur Begutachtung der gesamtwirtschaftlichen Entwicklung)** — for every episode. Any turning point gap exceeding 1 quarter is explicitly labeled as **"Late"** (not "Matched").

### Episode Comparison Table

| Episode | GCEE Reference Cycle | BEAI Factor Dates | Peak Diff | Trough Diff | Validation Status | Economic Assessment |
|:---:|:---|:---|:---:|:---:|:---:|:---|
| **1** | 1992Q1–1993Q2 | 1992Q1–1993Q2 | 0 | 0 | **Exact Match** | Post-reunification slump & ERM currency crisis. |
| **—** | *None* | 1995Q3–1996Q1 | — | — | *Mini-Cycle (Unmatched)* | 2-quarter industrial soft patch during fiscal retrenchment. |
| **2** | 2001Q1–2003Q2 | 2002Q3–2003Q1 | **+6Q** | −1Q | **Late (+6Q peak)** | Prolonged stagnation ("Sick Man" era); BBQ identifies the acute contraction phase. |
| **—** | *None* | 2004Q2–2004Q4 | — | — | *Mini-Cycle (Unmatched)* | 2-quarter dip during Hartz IV labour market reforms. |
| **3** | 2008Q1–2009Q1 | 2008Q1–2009Q1 | 0 | 0 | **Exact Match** | Global Financial Crisis. |
| **4** | 2011Q3–2013Q1 | 2012Q3–2013Q1 | **+4Q** | 0 | **Late (+4Q peak)** | Peripheral Eurozone crisis peaked in 2011; German industrial contraction lagged until late 2012. |
| **5** | 2019Q4–2020Q2 | 2019Q3–2020Q2 | −1Q | 0 | **Lead 1Q (Matched)** | COVID-19 pandemic shutdown. |

*Secondary Cross-Check (CEPR Euro Area):* The CEPR Euro Area Business Cycle Dating Committee dates similar peaks (2001Q1, 2008Q1, 2011Q3, 2019Q4). However, CEPR reflects aggregate Eurozone dynamics; peripheral stress in 2001 and 2011 preceded German domestic contraction by over a year, explaining the +6Q and +4Q peak lags.

### Headline Quarter-Level Classification Metrics
Evaluated on the 139-quarter sample (`1991Q2–2025Q4`) against official GCEE recession quarters:
- **True Positives (TP):** 15 quarters
- **False Positives (FP):** 5 quarters (`1995Q4, 1996Q1, 2004Q3, 2004Q4, 2019Q4`)
- **False Negatives (FN):** 14 quarters (protracted slow-growth quarters in 2001–2002 and 2011–2012)
- **True Negatives (TN):** 105 quarters
- **Accuracy:** **86.3%**
- **Precision:** **75.0%**
- **Recall:** **51.7%**
- **F1 Score:** **0.612**

The headline recall of $51.7\%$ directly reflects the +6Q and +4Q peak lags, where German activity plateaued rather than contracted immediately, producing 14 false negative quarters.

---

## 5. Specification of Requirements for Future Qualification

To qualify Germany in future pipeline iterations under Rule C-03 and Decision Q-02:
1. **Destatis GENESIS-Online S.11 Fixed Investment Pipeline:**
   Ingest quarterly table `81000` (National Accounts - Gross Capital Formation by Sector and Asset):
   - Extract non-financial corporations (S.11) investment in machinery & equipment (*Ausrüstungsinvestitionen*) and non-residential buildings (*Sonstige Bauten*).
   - Deflate with Destatis chain price index for non-residential capital goods.
   - Target coverage: $\ge 101$ quarters in `1990Q1–2025Q4`.
2. **Destatis GENESIS Table `81000-0015` (Arbeitsvolumen):**
   Automate ingestion of quarterly IAB total hours worked (*Arbeitsvolumen aller Erwerbstätigen*) to resolve `ACT_HOURS`.
3. **Standardized Disposable Income Deflator:**
   Implement a cross-country rule for deflating Destatis nominal quarterly disposable income (`81000-0030`) by the private consumption deflator to resolve `ACT_RINC`.