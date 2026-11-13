# Germany Coverage Finding & Data Architecture Report (Lane 1: Shravani Math)

This report details the C-03 coverage evaluation for Germany, documents the 1990–1991 German reunification structural break, explains the resolution of the six passing core indicators, and presents the evidence regarding the two excluded indicators (`ACT_HOURS` and `ACT_RINC`).

---

## 1. Executive Summary & Gate Decision

- **Gate Standard (BUILD_CONTRACT C-03):** Target reporting window `1990Q1–2025Q4` (144 quarters; $70\% = \ge 101$ quarters). A country is BEAI-eligible only with $\ge 6$ of 8 core indicators meeting the $70\%$ threshold; $\ge 4$ indicators are required to date a quarter. Missing stays missing (no interpolation, no forward fill).
- **Gate Outcome:** **PASS (6 of 8 indicators pass)**.
- **Decision:** Build and freeze `labels-v1-DEU` on the 6 passing indicators across the post-reunification sample `1991Q2–2025Q4` (139 quarters; 132 quarters with all 6 indicators available).

| BEAI Indicator ID | Concept | Source ID | Native Freq | Window Quarters | Coverage % | C-03 Gate ($\ge 70\%$) |
|---|---|---|:---:|---:|---:|:---:|
| `ACT_GDP_REAL` | Real Gross Domestic Product | `CLVMNACSCAB1GQDE` | Q | 139 | 96.5% | **PASS** |
| `ACT_IP` | Industrial Production Index | `DEUPROINDMISMEI` | M | 132 | 91.7% | **PASS** |
| `ACT_EMP` | Total Employment (QNA) | `LFEMTTTTDEQ647S` | Q | 139 | 96.5% | **PASS** |
| `ACT_CONS` | Real Private Consumption | `NAEXKP02DEQ661S` | Q | 130 | 90.3% | **PASS** |
| `ACT_RETAIL` | Retail Trade Volume Index | `DEUSARTMISMEI` | M | 132 | 91.7% | **PASS** |
| `ACT_INV` | Real Business Fixed Investment | `NAEXKP04DEQ661S` | Q | 130 | 90.3% | **PASS** |
| `ACT_HOURS` | Total Hours Worked | `GENESIS Table 81000-0015` | Q | 0 | 0.0% | **FAIL (Excluded)** |
| `ACT_RINC` | Real Household Income | `GENESIS Table 81000-0030` | Q | 0 | 0.0% | **FAIL (Excluded)** |

---

## 2. The 1990–1991 German Reunification Break

### The Discontinuity
On October 3, 1990, the former East Germany (GDR) was integrated into the Federal Republic of Germany. Destatis (*Statistisches Bundesamt*) established **1991Q1** as the first period for unified German national accounts (*Volkswirtschaftliche Gesamtrechnungen* under ESA 2010). 

Prior to 1991:
1. Destatis series reflect West Germany only (*früheres Bundesgebiet*).
2. The sudden inclusion of the eastern states increased the population by ~16 million (~25%) and added productive capacity that was initially valued under non-convertible currency regimes.
3. Level time series (such as total employment `LFEMTTTTDEQ647S` and retail sales `SLRTTO01DEQ659S`) show abrupt non-cyclical jumps between 1989Q4 and 1990Q4:
   - Employment jumped from 35.3M in 1989Q4 to 37.0M in 1990Q1.
   - Retail sales jumped $+13.5\%$ in 1990Q3 during the monetary union currency conversion.

### Pipeline A Estimation Sample Protocol
Rule C-03 forbids forward-fill, interpolation, or ad-hoc statistical splicing. Consequently:
- The German estimation sample is set to **`1991Q2–2025Q4`**.
- `1991Q1` serves as the initial level base for differencing; `1991Q2` is the first unified quarterly growth rate.
- Pre-1991 quarters in the 144-quarter reporting window (`1990Q1–1991Q1`) are left as unassigned ($R_t = 0$, $n_{\text{avail}} = 0$, factor/level missing).

---

## 3. Deep Dive into Excluded Indicators

### 1. `ACT_HOURS` (Total Hours Worked)
- **Candidate Source:** Destatis Table `81000-0015` / IAB (*Arbeitsvolumen der Erwerbstätigen*).
- **Why It Failed Coverage:**
  1. No continuous quarterly aggregate hours worked series for Germany is hosted on open, unauthenticated international mirrors (such as FRED or OECD SDMX) covering the 1990–2025 window.
  2. Conference Board / Penn World Table series on FRED (`AVHWPEDEA065NRUG`) are strictly annual (`A`).
  3. Manufacturing weekly hours series (`HOHWMN02DEA661N`) are marked as discontinued by the OECD.
  4. Synthesizing total hours via $\text{employment} \times \text{hours per worker}$ would require ad-hoc partial imputations forbidden by C-01 and C-03.
- **Evidence:** Left as `PENDING_VERIFICATION` in `data/series_resolution.csv`.

### 2. `ACT_RINC` (Real Household Income)
- **Candidate Source:** Destatis Table `81000-0030` (*Verfügbares Einkommen der privaten Haushalte*).
- **Why It Failed Coverage:**
  1. Unlike the United States (where `W875RX1` and `DSPIC96` are published monthly/quarterly by the BEA), Destatis compiles household disposable income primarily on an annual basis or as nominal quarterly flows without an official deflated volume index.
  2. Deflating nominal disposable income by the consumer price index or private consumption deflator requires a multi-component mathematical derivation. Under Build Contract C-01, derived indicator math must be formally frozen across all countries rather than improvised for one country.
- **Evidence:** Left as `PENDING_VERIFICATION` in `data/series_resolution.csv`.

---

## 4. Resolution of the Six Passing Indicators

1. **`ACT_GDP_REAL` (`CLVMNACSCAB1GQDE`):** Chained 2015 Euros, quarterly, seasonally and working-day adjusted. Published by Eurostat and Destatis. 140 quarters available in window ($97.2\%$).
2. **`ACT_IP` (`DEUPROINDMISMEI`):** Total Industry excluding construction, monthly, seasonally adjusted. Index 2015=100. Aggregated to quarterly mean via complete-quarter rule C-06. 132 complete quarters in window ($91.7\%$).
3. **`ACT_EMP` (`LFEMTTTTDEQ647S`):** Domestic concept total employment, quarterly, seasonally adjusted. 139 quarters available in window ($96.5\%$).
4. **`ACT_CONS` (`NAEXKP02DEQ661S`):** Private final consumption expenditure, chained 2015 Euros, quarterly, seasonally adjusted. 130 quarters available in window ($90.3\%$).
5. **`ACT_RETAIL` (`DEUSARTMISMEI`):** Retail trade volume index (except of motor vehicles), monthly, seasonally adjusted. Index 2015=100. Converted to quarterly mean via rule C-06. 132 complete quarters in window ($91.7\%$).
6. **`ACT_INV` (`NAEXKP04DEQ661S`):** Gross fixed capital formation, chained 2015 Euros, quarterly, seasonally adjusted. 130 quarters available in window ($90.3\%$).

---

## 5. Path Forward for Future Pipeline Iterations

If future pipeline iterations seek to expand Germany from 6 to 8 core indicators:
1. **Authenticated Destatis GENESIS API Fetcher:** Develop an authenticated fetcher for Destatis Table `81000-0015` to ingest quarterly IAB *Arbeitsvolumen*.
2. **Standardized Income Deflation Rule:** Formally define an international counterpart to the US Q-02/Q-05 rule that specifies how nominal household disposable income should be deflated by the national accounts consumption deflator across non-US economies.
