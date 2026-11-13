# Germany Label Validation & Finding Report (Lane 1: Shravani Math)

**Milestone:** Ingest German economic series, evaluate the C-03 coverage gate on the eight §11 core indicators, address the 1990–1991 German reunification structural break, examine Decision Q-02 compliance, benchmark against official Sachverständigenrat (German Council of Economic Experts / GCEE) reference dates, and document the final qualification decision.

**Status:** **Coverage Finding / Gate FAIL under Rule C-03 & Decision Q-02**.  
Without substituting total GFCF (strictly forbidden by Decision Q-02), Germany achieves only 5 passing core indicators (`ACT_GDP_REAL`, `ACT_IP`, `ACT_EMP`, `ACT_CONS`, `ACT_RETAIL`). Because Rule C-03 requires $\ge 6$ of 8 core indicators, Germany is **not eligible for a frozen BEAI label**. The preliminary freeze (`labels-v1-DEU`) has been revoked. This document records the experimental findings of the 6-indicator model for research provenance.

---

## 1. Data & Coverage Evaluation

Coverage evaluation across the 144-quarter reporting window (`1990Q1–2025Q4`) following Rules C-01, C-03, and Decision Q-02:

| BEAI Core Indicator | Source | Series ID / Table | Native Freq | Raw Window Coverage | Estimator Sample Coverage | C-03 Gate Status | Transform |
|---|---|---|:---:|---:|---:|:---:|---|
| `ACT_GDP_REAL` | Destatis / Eurostat (FRED) | `FRED:CLVMNACSCAB1GQDE` | Q | 140/144 (97.2%) | 139/144 (96.5%) | **PASS** | $\Delta\log$ |
| `ACT_IP` | Destatis / OECD MEI (FRED) | `FRED:DEUPROINDMISMEI` | M $\to$ Q mean | 137/144 (95.1%) | 132/144 (91.7%) | **PASS** | $\Delta\log$ |
| `ACT_EMP` | Destatis / OECD QNA (FRED) | `FRED:LFEMTTTTDEQ647S` | Q | 144/144 (100.0%) | 139/144 (96.5%) | **PASS** | $\Delta\log$ |
| `ACT_HOURS` | Destatis / IAB | `GENESIS Table 81000-0015` | Q | 0/144 (0.0%) | 0/144 (0.0%) | **FAIL** | N/A |
| `ACT_RINC` | Destatis (VGR) | `GENESIS Table 81000-0030` | Q | 0/144 (0.0%) | 0/144 (0.0%) | **FAIL** | N/A |
| `ACT_CONS` | Destatis / Eurostat (FRED) | `FRED:NAEXKP02DEQ661S` | Q | 135/144 (93.8%) | 130/144 (90.3%) | **PASS** | $\Delta\log$ |
| `ACT_RETAIL` | Destatis / OECD MEI (FRED) | `FRED:DEUSARTMISMEI` | M $\to$ Q mean | 137/144 (95.1%) | 132/144 (91.7%) | **PASS** | $\Delta\log$ |
| `ACT_INV` | Destatis VGR (S.11) | `Non-compliant: NAEXKP04DEQ661S` | Q | 0/144 (0.0%) | 0/144 (0.0%) | **FAIL (Q-02)** | $\Delta\log$ |

*Reconciliation of metrics:* `raw_window_coverage` evaluates complete quarters of the underlying raw series inside the 144-quarter window (1990Q1–2025Q4; monthly = all 3 constituent months present), while `estimator_sample_coverage` measures quarters available after applying the post-reunification sample start (`1991Q2`) and growth first-differencing.

### The 1990–1991 Reunification Break
- **Structural Discontinuity:** On October 3, 1990, East Germany was integrated into the Federal Republic. Destatis national accounts under ESA 2010 establish **1991Q1** as the definitive baseline for unified Germany (*Deutschland als Ganzes*). Pre-1991 figures cover West Germany only (*früheres Bundesgebiet*). (Citations: Statistisches Bundesamt, *Wirtschaft und Statistik* 9/2014; Deutsche Bundesbank, *Monatsbericht*, Oktober 1990).
- **No Splicing (Rule C-03):** To prevent artificial, non-cyclical level shifts (~25% population increase) from distorting factor estimates, the German estimation sample starts in **`1991Q2`** (the first unified quarterly growth rate from the 1991Q1 base). Quarters `1990Q1–1991Q1` remain documented as unassigned in accordance with C-03.
- **Config-Driven:** Configured centrally in `config/scope.yaml` under `window.sample_start.DEU: "1991Q2"`.

---

## 2. Decision Q-02 Disqualification of Total GFCF

In the initial exploratory run, FRED series `NAEXKP04DEQ661S` was examined for `ACT_INV`. However:
1. `NAEXKP04DEQ661S` is **Total Gross Fixed Capital Formation** (*Bruttoanlageinvestitionen*), encompassing residential construction (*Wohnungsbau*) and general government public investment.
2. `docs/DECISION_NOTE_Q02_Q04_Q05.md:62-64` explicitly establishes:
   > *"Strict: business (non-residential) fixed investment only. Total GFCF is not substituted; where business investment is missing the component counts as missing."*
3. Empirical evaluation of alternative data sources (Eurostat `nasq_10_nf_tr`, Eurostat `namq_10_an6`, and Destatis Genesis Table `81000`) confirms that no compliant private non-residential deflated series covering $\ge 108$ quarters exists without government or housing contamination (see details in docs/COVERAGE_DEU.md).
4. Dropping total GFCF leaves Germany with **5 passing indicators**, failing Rule C-03. Consequently, Germany does not qualify for a frozen label.

---

## 3. Exploratory DFM & Chronology Comparison (GCEE Reference Standard)

To evaluate the informational value of the available German data, an exploratory DFM + BBQ + diffusion model was fitted on `1991Q2–2025Q4`.

Following Step 2c, chronology validation uses **ONE official reference standard — the German Council of Economic Experts (GCEE / Sachverständigenrat)** — for every episode. Any turning point difference exceeding 1 quarter is explicitly marked as **"Late"** (not "Matched").

### Episode Comparison Table

| Episode | GCEE Reference Cycle | BEAI Factor Dates | Peak Diff | Trough Diff | Validation Status | Economic Assessment |
|:---:|:---|:---|:---:|:---:|:---:|:---|
| **1** | 1992Q1–1993Q2 | 1992Q1–1993Q2 | 0 | 0 | **Exact Match** | Post-reunification slump & ERM currency crisis. |
| **—** | *None* | 1995Q3–1996Q1 | — | — | *Mini-Cycle (Unmatched)* | 2-quarter industrial slowdown during tax reform. |
| **2** | 2001Q1–2003Q2 | 2002Q3–2003Q1 | **+6Q** | −1Q | **Late (+6Q peak)** | Prolonged stagnation ("Sick Man" era); BBQ identifies the acute contraction phase. |
| **—** | *None* | 2004Q2–2004Q4 | — | — | *Mini-Cycle (Unmatched)* | 2-quarter dip during Hartz IV labour market reforms. |
| **3** | 2008Q1–2009Q1 | 2008Q1–2009Q1 | 0 | 0 | **Exact Match** | Global Financial Crisis. |
| **4** | 2011Q3–2013Q1 | 2012Q3–2013Q1 | **+4Q** | 0 | **Late (+4Q peak)** | Peripheral Eurozone crisis peaked in 2011; German industrial contraction lagged until late 2012. |
| **5** | 2019Q4–2020Q2 | 2019Q3–2020Q2 | −1Q | 0 | **Lead 1Q (Matched)** | COVID-19 pandemic shutdown. |

*Secondary Cross-Check (CEPR Euro Area):* The CEPR Euro Area Business Cycle Dating Committee dates similar peaks (2001Q1, 2008Q1, 2011Q3, 2019Q4). However, CEPR reflects aggregate Eurozone dynamics; peripheral stress in 2001 and 2011 preceded German domestic contraction by over a year, explaining the +6Q and +4Q peak lags.

### Headline Quarter-Level Classification Metrics
Evaluated across all 139 quarters of the estimation sample (`1991Q2–2025Q4`) against official GCEE recession quarters:
- **True Positives (TP):** 15 quarters
- **False Positives (FP):** 5 quarters (`1995Q4, 1996Q1, 2004Q3, 2004Q4, 2019Q4`)
- **False Negatives (FN):** 14 quarters (protracted slow-growth quarters in 2001–2002 and 2011–2012)
- **True Negatives (TN):** 105 quarters
- **Accuracy:** **86.3%**
- **Precision:** **75.0%**
- **Recall:** **51.7%**
- **F1 Score:** **0.612**

---

## 4. Final Disposition

Germany is delivered as a **Coverage Finding Report** ([docs/COVERAGE_DEU.md](file:///D:/ml_ews/recession-ews/docs/COVERAGE_DEU.md)). No frozen German label is shipped in HEAD. Qualification is deferred until compliant S.11 private non-residential business fixed investment and total hours worked can be ingested via authenticated Destatis APIs.