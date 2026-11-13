# Germany Source Map & Data Verification (Lane 1: Shravani Math)

This document maps all 21 Germany rows from `data/scope.csv` to concrete primary sources, documents the 1990–1991 German reunification break, and records the initial coverage evaluation against the frozen C-03 reporting window (`1990Q1–2025Q4` = 144 quarters).

---

## 1. Summary of Scope Inventory (21 Rows)

- **Total German scope items:** 21 rows (`DEU.ACT_*`, `DEU.FIN_*`, `DEU.LAB_*`, `DEU.PRC_*`, `DEU.SEN_*`).
- **Core coincident candidate indicators:** 8 indicators (plus 1 LFS variant = 9 rows).
- **Resolved active series:** 18 series.
- **Pending verification / excluded series:** 3 series (`ACT_HOURS`, `ACT_RINC`, and redundant monthly `ACT_EMP.M.LFS`).
- **Core indicator gate status:** Exactly **6 of 8** core indicators pass the $\ge 70\%$ reporting window coverage gate ($\ge 101$ quarters).

---

## 2. The 1990–1991 German Reunification Break

### Historical and Methodological Context
German political reunification occurred on **October 3, 1990** (with preceding economic and monetary union on July 1, 1990). The integration of the former German Democratic Republic (East Germany) created an acute structural break in macroeconomic statistics:

1. **Territorial Definition (*Gebietsstand*):**
   Prior to 1991, official national accounts compiled by the Federal Statistical Office (**Destatis** - *Statistisches Bundesamt*) covered only the former territory of the Federal Republic of Germany (West Germany / *früheres Bundesgebiet*). From **1991Q1 onward**, Destatis instituted the unified national accounts framework (*Deutschland als Ganzes*) under ESA 2010.
2. **Level Discontinuity:**
   Reunification added approximately 16 million people (~25% population increase) and vast industrial infrastructure operating under radically different initial productivity and capital valuation regimes. Aggregating pre-1990 West Germany with post-1991 unified Germany creates an artificial, non-cyclical level shift.
3. **Estimation Sample Decision:**
   In accordance with the lane instructions (§7.2), the German label estimation sample is explicitly set to begin in **`1991Q2`** (the first quarterly growth rate of unified German national accounts from 1991Q1 base). No synthetic backcasting or arbitrary level splicing across the 1990 boundary is performed, strictly complying with Rule C-03 ("no interpolation, missing stays missing").

---

## 3. Core Indicators Mapping Table (Pipeline A Inputs)

| Indicator ID | Concept | Source / Database | Series ID | Native Freq | SA | First Obs | Last Obs | Quarters in Window | Coverage % | C-03 Gate ($\ge 70\%$) |
|---|---|---|---|:---:|:---:|---:|---:|---:|---:|:---:|
| `ACT_GDP_REAL` | Real Gross Domestic Product (chained 2015 Euros) | Destatis / Eurostat (FRED) | `CLVMNACSCAB1GQDE` | Q | SA | 1991Q1 | 2026Q2 | 140/144 | **97.2%** | **PASS** |
| `ACT_IP` | Industrial Production Index (Mining & Manufacturing) | Destatis / OECD MEI (FRED) | `DEUPROINDMISMEI` | M | SA | 1958-01 | 2024-03 | 137/144 | **95.1%** | **PASS** |
| `ACT_EMP` | Total Employment (National Accounts headcount) | Destatis / OECD QNA (FRED) | `LFEMTTTTDEQ647S` | Q | SA | 1962Q1 | 2026Q2 | 144/144 | **100.0%** | **PASS** |
| `ACT_HOURS` | Total Hours Worked (*Arbeitsvolumen*) | Destatis / IAB | `GENESIS 81000-0015` | Q | SA | 1991Q1 | 2026Q2 | 0/144 | 0.0% | *FAIL (Pending)* |
| `ACT_RINC` | Real Household Disposable Income | Destatis (VGR) | `GENESIS 81000-0030` | Q | SA | 1991Q1 | 2026Q2 | 0/144 | 0.0% | *FAIL (Pending)* |
| `ACT_CONS` | Real Private Final Consumption Expenditure | Destatis / Eurostat (FRED) | `NAEXKP02DEQ661S` | Q | SA | 1970Q1 | 2023Q3 | 135/144 | **93.8%** | **PASS** |
| `ACT_RETAIL` | Real Retail Trade Volume Index | Destatis / OECD MEI (FRED) | `DEUSARTMISMEI` | M | SA | 1955-01 | 2024-03 | 137/144 | **95.1%** | **PASS** |
| `ACT_INV` | Real Business Fixed Investment (GFCF) | Destatis / Eurostat (FRED) | `NAEXKP04DEQ661S` | Q | SA | 1970Q1 | 2023Q3 | 135/144 | **93.8%** | **PASS** |

**Summary Gate Outcome:** 6 passing indicators ($\ge 70\%$) out of 8 core indicators. C-03 gate passes.

---

## 4. Predictors and Context Series (Pipeline B Scope)

| Scope Key | Concept | Candidate Series | Source | Native Freq | Status |
|---|---|---|---|:---:|:---:|
| `DEU.FIN_CREDIT_GAP.Q.STD` | Credit-to-GDP Gap | `Q:DE:P:A:M:770:A (Gap)` | BIS | Q | RESOLVED |
| `DEU.FIN_CREDIT_GDP.Q.STD` | Credit to Private Non-Financial Sector (% GDP) | `QDEPAM770A` | BIS (FRED) | Q | RESOLVED |
| `DEU.FIN_EQUITY.M.STD` | Share Price Index (DAX / CDAX) | `SPASTT01DEM661N` | OECD (FRED) | M | RESOLVED |
| `DEU.FIN_HOUSEPRICE.Q.OECD_BIS` | Real Residential Property Prices | `QDER628BIS` | Bundesbank / BIS (FRED) | Q | RESOLVED |
| `DEU.FIN_LONG.M.STD` | 10-year Government Bond Yield (Bund) | `IRLTLT01DEM156N` | Bundesbank (FRED) | M | RESOLVED |
| `DEU.FIN_POLICY.M.STD` | Policy Rate (Bundesbank Discount / ECB Deposit) | `ECBDFR` | ECB / Bundesbank (FRED) | M | RESOLVED |
| `DEU.FIN_SHORT.M.STD` | 3-Month Interbank Rate (Euribor / Fibor) | `IR3TIB01DEM156N` | ECB / Bundesbank (FRED) | M | RESOLVED |
| `DEU.FIN_SLOPE.M.DERIVED` | Term Spread (10Y minus 3M) | Derived (`10Y - 3M`) | Derived | M | RESOLVED |
| `DEU.LAB_UNEMP.M.STD` | Harmonized Unemployment Rate | `LRHUTTTTDEM156S` | Destatis / OECD (FRED) | M | RESOLVED |
| `DEU.PRC_CPI.M.STD` | Consumer Price Index (All Items) | `DEUCPIALLMINMEI` | Destatis (FRED) | M | RESOLVED |
| `DEU.SEN_BCI.M.STD` | Business Confidence (ifo Business Climate) | `BSCICP03DEM665S` | ifo / OECD (FRED) | M | RESOLVED |
| `DEU.SEN_CCI.M.STD` | Consumer Confidence Index | `CSCICP03DEM665S` | GfK / OECD (FRED) | M | RESOLVED |

---

## 5. Unresolved Series & Blocking Questions

1. **`DEU.ACT_HOURS.Q.STD` (Total Hours Worked):**
   - *Status:* `PENDING_VERIFICATION`
   - *Candidate source:* Destatis GENESIS-Online Table `81000-0015` (*Arbeitsvolumen der Erwerbstätigen*).
   - *Blocking Question:* The Destatis API requires specific XML/JSON authentication credentials and quarterly tables undergo periodic historical base-year updates. Is a constructed hours proxy (employment $\times$ average hours per worker from the IAB) acceptable under C-01, or should hours remain documented as excluded?
2. **`DEU.ACT_RINC.Q.STD` (Real Household Income):**
   - *Status:* `PENDING_VERIFICATION`
   - *Candidate source:* Destatis Table `81000-0030` (*Einkommen der privaten Haushalte*).
   - *Blocking Question:* Real household disposable income is not published as an open continuous monthly/quarterly FRED mnemonic back to 1991 without computing nominal disposable income divided by the consumer price deflator. Does the team sanction this manual derivation for Germany, or retain the finding that direct coverage is missing?
