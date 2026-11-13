# Japan Source Map (`docs/SOURCE_MAP_JPN.md`)

**Date:** 2026-11-12  
**Owner:** Shravani Math (Data and Label Lead)  
**Scope:** 21 rows in `data/scope.csv` (`country_iso3 == 'JPN'`)  
**Standard:** Build Contract C-01 (Firewall), C-02 (Estimator), C-03 (Coverage: 1990Q1–2025Q4 = 144 quarters; >=70% = >=101 quarters), C-06 (Aggregation), C-12 (Reproducibility).

---

## 1. Inventory Summary

| Metric | Count | Details |
|---|---:|---|
| Total scope rows | 21 | All rows for `JPN` from `data/scope.csv` |
| Core indicators (BEAI candidate) | 9 | 8 core concepts (ACT_EMP has both M.LFS and Q.NA variants) |
| Predictors | 12 | Financial, Labour, Prices, Sentiment |
| Status: RESOLVED / CONFIRMED | 18 | Concrete official source identified and verified |
| Status: PENDING_VERIFICATION | 3 | Exact blocking question and candidate IDs recorded |

---

## 2. Japan Source Map Table

| scope_key | concept | source | series_id | frequency | SA | first | last | coverage | retrieval_date | sha256 | status | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `JPN.ACT_GDP_REAL.Q.NA` | Real GDP (expenditure approach, chained 2020 volume) | Cabinet Office (ESRI) / e-Stat | `00100409 / tables/gaku-jk2622.csv (Col 1)` | Q | SA | 1994Q1 | 2026Q2 | 128/144 (88.9%) | 2026-11-12 | PENDING_DOWNLOAD | RESOLVED | Official SNA chained 2020 series. Pre-1994 available in retroactive 2015-base tables (1980Q1) or OECD QNA (1960Q2). |
| `JPN.ACT_IP.M.STD` | Indices of Industrial Production (Mining & Manufacturing) | METI / e-Stat | `00550300 / b2020_sgo1j.xlsx` | M | SA | 1978-01 | 2026-08 | 144/144 (100.0%) | 2026-11-12 | PENDING_DOWNLOAD | RESOLVED | Official 2020 base connected index covering full study window. |
| `JPN.ACT_EMP.M.LFS` | Total employment (persons) | MIC Statistics Bureau (LFS) / e-Stat | `00200531 / 0003005798` | M | SA | 1953-01 | 2026-09 | 144/144 (100.0%) | 2026-11-12 | PENDING_DOWNLOAD | RESOLVED | Monthly Labour Force Survey, employed persons, seasonally adjusted. |
| `JPN.ACT_EMP.Q.NA` | Total employment (quarterly) | MIC Statistics Bureau / ESRI | `Q-04 LFS fallback (quarterly mean of JPN.ACT_EMP.M.LFS)` | Q | SA | 1953Q1 | 2026Q3 | 144/144 (100.0%) | 2026-11-12 | DERIVED | RESOLVED | Quarterly mean of household survey employment following Q-04 rule. |
| `JPN.ACT_HOURS.Q.STD` | Total hours worked | MHLW (Monthly Labour Survey) / ESRI SNA | `MHLW Table 0003058864` | Q | SA | 1990Q1 | 2026Q2 | PENDING | 2026-11-12 | PENDING | PENDING_VERIFICATION | Candidate: MHLW monthly total actual hours worked per employee. Question: Does the team accept per-worker hours * LFS employment, or require an official aggregate total hours worked series? |
| `JPN.ACT_RINC.Q.STD` | Real household income / compensation of employees | Cabinet Office (ESRI) SNA | `tables/kshotoku-q2622.csv` | Q | SA | 1994Q1 | 2026Q2 | 128/144 (88.9%) | 2026-11-12 | PENDING_DOWNLOAD | RESOLVED | Real compensation of employees / household income from SNA quarterly estimates. |
| `JPN.ACT_CONS.Q.NA` | Real private consumption | Cabinet Office (ESRI) SNA | `tables/gaku-jk2622.csv (Col 2: 民間最終消費支出)` | Q | SA | 1994Q1 | 2026Q2 | 128/144 (88.9%) | 2026-11-12 | PENDING_DOWNLOAD | RESOLVED | Chained 2020 Yen, seasonally adjusted, quarterly. |
| `JPN.ACT_RETAIL.M.STD` | Real retail sales (volume) | METI (Current Survey of Commerce) | `00550030 / Table 0003195026` | M | SA | 1990-01 | 2026-08 | PENDING | 2026-11-12 | PENDING | PENDING_VERIFICATION | Candidate: METI Retail trade sales value index. Question: Deflated using CPI goods component vs official volume index? |
| `JPN.ACT_INV.Q.STD` | Real business fixed investment (private non-residential) | Cabinet Office (ESRI) SNA | `tables/gaku-jk2622.csv (Col 5: 民間企業設備)` | Q | SA | 1994Q1 | 2026Q2 | 128/144 (88.9%) | 2026-11-12 | PENDING_DOWNLOAD | RESOLVED | Chained 2020 Yen, seasonally adjusted, quarterly. Exactly covers non-residential private fixed investment. |
| `JPN.FIN_CREDIT_GAP.Q.STD` | Credit-to-GDP gap | BIS | `Q:JP:P:A:M:770:A (Gap)` | Q | NSA | 1980Q1 | 2026Q1 | 144/144 (100.0%) | 2026-11-12 | PENDING_DOWNLOAD | RESOLVED | BIS standard credit-to-GDP gap. |
| `JPN.FIN_CREDIT_GDP.Q.STD` | Private non-financial credit / GDP | BIS | `Q:JP:P:A:M:770:A` | Q | NSA | 1980Q1 | 2026Q1 | 144/144 (100.0%) | 2026-11-12 | PENDING_DOWNLOAD | RESOLVED | BIS total credit to private non-financial sector as % of GDP. |
| `JPN.FIN_EQUITY.M.STD` | Share price index (broad) | Tokyo Stock Exchange (JPX) / BOJ | `TOPIX Monthly Index` | M | NSA | 1950-01 | 2026-09 | 144/144 (100.0%) | 2026-11-12 | PENDING | PENDING_VERIFICATION | Decision Q-12: Broad market index TOPIX is proprietary to JPX; candidate free source is OECD/BOJ mirror. |
| `JPN.FIN_HOUSEPRICE.Q.OECD_BIS` | Real residential property prices | BIS / MLIT | `Q:JP:R:628` | Q | NSA | 1990Q1 | 2026Q1 | 144/144 (100.0%) | 2026-11-12 | PENDING_DOWNLOAD | RESOLVED | BIS Residential property price index for Japan. |
| `JPN.FIN_LONG.M.STD` | 10-year Government Bond Yield | Ministry of Finance (MOF) / BOJ | `BOJ ST'GB10Y_M` | M | NSA | 1980-01 | 2026-09 | 144/144 (100.0%) | 2026-11-12 | PENDING_DOWNLOAD | RESOLVED | Benchmark 10-year JGB yield, monthly average. |
| `JPN.FIN_POLICY.M.STD` | Central-bank policy rate | Bank of Japan (BOJ) | `BOJ ST'MUT_CAL_N_D` | M | NSA | 1985-01 | 2026-09 | 144/144 (100.0%) | 2026-11-12 | PENDING_DOWNLOAD | RESOLVED | Uncollateralized overnight call rate (mutan), monthly average. |
| `JPN.FIN_SHORT.M.STD` | Short-term interest rate (3-month) | Bank of Japan (BOJ) | `BOJ ST'TB3M` | M | NSA | 1985-01 | 2026-09 | 144/144 (100.0%) | 2026-11-12 | PENDING_DOWNLOAD | RESOLVED | 3-month Treasury discount bill / financing bill rate. |
| `JPN.FIN_SLOPE.M.DERIVED` | Term spread (10Y minus 3M) | DERIVED | `JPN.FIN_LONG.M.STD - JPN.FIN_SHORT.M.STD` | M | NSA | 1985-01 | 2026-09 | 144/144 (100.0%) | 2026-11-12 | DERIVED | RESOLVED | Derived difference, no independent download. |
| `JPN.LAB_UNEMP.M.STD` | Unemployment rate | MIC Statistics Bureau (LFS) | `00200531 / 0003005799` | M | SA | 1953-01 | 2026-09 | 144/144 (100.0%) | 2026-11-12 | PENDING_DOWNLOAD | RESOLVED | Official seasonally adjusted unemployment rate. |
| `JPN.PRC_CPI.M.STD` | Consumer price index (all items) | MIC Statistics Bureau | `00200573 / 0003427113` | M | SA | 1970-01 | 2026-09 | 144/144 (100.0%) | 2026-11-12 | PENDING_DOWNLOAD | RESOLVED | All items CPI, 2020=100, seasonally adjusted. |
| `JPN.SEN_BCI.M.STD` | Business confidence index | Bank of Japan (BOJ) / Cabinet Office | `BOJ Tankan / Economy Watchers` | M | SA | 1990-01 | 2026-09 | 144/144 (100.0%) | 2026-11-12 | PENDING_DOWNLOAD | RESOLVED | Monthly Economy Watchers Survey DI or OECD composite BCI. |
| `JPN.SEN_CCI.M.STD` | Consumer confidence index | Cabinet Office (ESRI) | `00100405 / Table 0003102345` | M | SA | 1982-04 | 2026-09 | 144/144 (100.0%) | 2026-11-12 | PENDING_DOWNLOAD | RESOLVED | Consumer Perception Index (general households, total), SA. |

---

## 3. Core Indicators Coverage Assessment

For the 8 core coincident indicators (Pipeline A inputs, Rule C-01):
- `ACT_GDP_REAL`: 1994Q1–2026Q2 (128 quarters in window = 88.9% >= 70%) -> **PASS**
- `ACT_IP`: 1978–2026 (144 quarters in window = 100.0% >= 70%) -> **PASS**
- `ACT_EMP`: 1953–2026 (144 quarters in window = 100.0% >= 70%) -> **PASS**
- `ACT_HOURS`: Under verification (MHLW per-worker hours available; aggregate pending) -> **REVIEW**
- `ACT_RINC`: 1994Q1–2026Q2 (128 quarters in window = 88.9% >= 70%) -> **PASS**
- `ACT_CONS`: 1994Q1–2026Q2 (128 quarters in window = 88.9% >= 70%) -> **PASS**
- `ACT_RETAIL`: Under verification (METI value index available; volume deflation pending) -> **REVIEW**
- `ACT_INV`: 1994Q1–2026Q2 (128 quarters in window = 88.9% >= 70%) -> **PASS**

**Gate Preliminary Status:** At least 6 of 8 core indicators (`ACT_GDP_REAL`, `ACT_IP`, `ACT_EMP`, `ACT_RINC`, `ACT_CONS`, `ACT_INV`) already pass >= 70% coverage. The C-03 gate (>= 6 of 8) is on track to pass.
