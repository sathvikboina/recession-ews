# Feature Specification, Pipeline B Firewall and Feature Dictionary

| Field | Detail |
|---|---|
| **Author** | Shravani Math (Lane 2A Specification & Verification Owner) |
| **Builder Handoff** | Sathvik Boina (Lane 2B Build Owner) |
| **Status** | **FROZEN** (14 November 2026) |
| **Scope / Country** | USA (1990Q1–2026Q3, 147 quarters) |
| **Rules Enforced** | `docs/BUILD_CONTRACT.md` C-01, C-05, C-06, C-07, C-08, C-11, C-12 |
| **Decisions Applied** | D-R01, D-R02, D-R03, D-R05, D-R06, D-R08, D-R12, D-R14, D-R22, D-R26–D-R28, D-R31, D-R34 |

---

## 1. Purpose and Window

This document defines the complete and unambiguous specification of legal predictors for Pipeline B for the United States. A stranger following this specification must be able to independently reproduce every column of the feature table without requesting clarifications or making discretionary modeling choices.

### 1.1 Study Window vs. Estimation Sample
- **Reporting & Evaluation Window:** **1990Q1–2026Q3** (exactly **147 quarters**, one row per calendar quarter).
- **Estimation History (Context):** The harmonised clean panel (`data/clean/USA_panel.csv`) begins in **1960Q1** (267 quarters total). Features requiring growth differencing or rolling statistics compute transformations over available pre-1990 history so that initial reporting quarters (e.g. 1990Q1) are not artificially lost to differencing lags.
- **Unscaled Contract (Rule C-07 / C-08):** The feature dataset is strictly **UNSCALED**. No column in `data/clean/dataset.parquet` is standardized to zero mean or unit variance across the sample. All feature scaling (e.g. `StandardScaler`) and imputation (`SimpleImputer`) must be fitted **strictly inside each outer training fold**. Test blocks must remain entirely untouched during scaling.
- **Label Independence (Rule C-01):** Pipeline A builds the ex-post recession chronology ($R_t$). Pipeline B builds early-warning predictors. **No label output is ever a predictor.** Under no circumstance may any factor index ($F_t$), level, recession indicator ($R_t$), turning-point date, diffusion share, or NBER chronology column enter the predictor table.

### 1.2 Shipped Table Builder vs. Reference Fixture
- **Official Shipped Table:** The official shipped feature table is `data/clean/dataset.parquet` (147 rows, 149 features covering 1990Q1–2026Q3), produced by `scripts/05_features.py` (and invoked via `make features`). It reads `data/clean/USA_panel.csv`, applies conservative C-05 publication availability lags, and expands features using `ews.models.feature_transforms`.
- **Reference Fixture:** `scripts/06_features.py` serves strictly as a documented reference fixture for testing and mutation checks (e.g. testing no-future leakage across arbitrary cutoffs and validating that poison mutations raise exceptions). `tests/test_features.py` polices the official shipped table `data/clean/dataset.parquet`.

---

## 2. Column Inventory

The feature table contains exactly 27 legal predictors spanning all 26 series present in `data/clean/USA_panel.csv` and the eight core indicators of `data/clean/USA_growth.parquet`. Under Rule C-01, core indicators appear exclusively as versioned `beai_copy_*` predictors with explicit C-05 availability lags. Missing observations stay missing (Rule C-03; no forward filling or interpolation).

| # | Feature Name | Source Series ID / Key | Native Freq | Transformation | C-05 Availability Lag | Missing Rule | Why It Is Safe |
|---|---|---|:---:|---|:---:|---|---|
| 1 | `beai_copy_act_gdp_real` | `GDPC1` (`USA.ACT_GDP_REAL.Q.NA`) | Q | $\Delta\log$ growth (QoQ) | 1 Quarter (NA) | Missing stays missing | Pure lagged copy; shares no factor loadings or parameters with Pipeline A. |
| 2 | `beai_copy_act_ip` | `INDPRO` (`USA.ACT_IP.M.STD`) | M | Quarterly mean $\Delta\log$ | 6 Weeks (Monthly) | Missing stays missing | Coincident industrial activity; available at prediction origin ($t+6w$). |
| 3 | `beai_copy_act_emp` | `CE16OV` (`USA.ACT_EMP.Q.NA`) | Q | Quarterly mean $\Delta\log$ | 1 Quarter (NA) | Missing stays missing | Lagged 1Q per Q-04 LFS quarterly fallback; no Pipeline A objects shared. |
| 4 | `beai_copy_act_hours` | `HOANBS` (`USA.ACT_HOURS.Q.STD`) | Q | $\Delta\log$ growth (QoQ) | 1 Quarter (NA) | Missing stays missing | Lagged 1Q per nonfarm business hours; no future lookahead. |
| 5 | `beai_copy_act_rinc` | `W875RX1` (`USA.ACT_RINC.Q.STD`) | Q | $\Delta\log$ growth (QoQ) | 1 Quarter (NA) | Missing stays missing | Lagged 1Q; excludes government transfers (D-R23) to avoid counter-cyclical bias. |
| 6 | `beai_copy_act_cons` | `PCECC96` (`USA.ACT_CONS.Q.NA`) | Q | $\Delta\log$ growth (QoQ) | 1 Quarter (NA) | Missing stays missing | Lagged 1Q national accounts consumption; unscaled. |
| 7 | `beai_copy_act_retail` | `RRSFS` (`USA.ACT_RETAIL.M.STD`) | M | Quarterly mean $\Delta\log$ | 6 Weeks (Monthly) | Missing stays missing | Monthly retail trade volume; available at origin $t+6w$. |
| 8 | `beai_copy_act_inv` | Constructed (`USA.ACT_INV.Q.STD`) | Q | $\Delta\log$ growth (QoQ) | 1 Quarter (NA) | Missing stays missing | Lagged 1Q; constructed non-residential fixed investment (D-R26). |
| 9 | `inv_eq` | `Y033RC1Q027SBEA` | Q | $\Delta\log$ growth (QoQ) | 1 Quarter (NA) | Missing stays missing | Lagged 1Q; equipment investment component; unscaled. |
| 10 | `inv_struct` | `B009RC1Q027SBEA` | Q | $\Delta\log$ growth (QoQ) | 1 Quarter (NA) | Missing stays missing | Lagged 1Q; non-residential structures investment; unscaled. |
| 11 | `inv_ipp` | `Y001RC1Q027SBEA` | Q | $\Delta\log$ growth (QoQ) | 1 Quarter (NA) | Missing stays missing | Lagged 1Q; intellectual property products investment; unscaled. |
| 12 | `inv_defl` | `A008RD3Q086SBEA` | Q | $\Delta\log$ growth (QoQ) | 1 Quarter (NA) | Missing stays missing | Lagged 1Q; non-residential investment deflator inflation. |
| 13 | `emp_estab` | `PAYEMS` (`USA.ACT_EMP.M.ESTAB`) | M | Quarterly mean $\Delta\log$ | 6 Weeks (Monthly) | Missing stays missing | Establishment payroll employment growth; available at $t+6w$. |
| 14 | `emp_lfs` | `CE16OV` (`USA.ACT_EMP.M.LFS`) | M | Quarterly mean $\Delta\log$ | 6 Weeks (Monthly) | Missing stays missing | Household LFS monthly employment growth; unscaled. |
| 15 | `rinc_m` | `DSPIC96` (`USA.ACT_RINC.M.US`) | M | Quarterly mean $\Delta\log$ | 6 Weeks (Monthly) | Missing stays missing | Monthly real disposable personal income growth; unscaled. |
| 16 | `credit_gdp` | `QUSPAM770A` (`USA.FIN_CREDIT_GDP.Q.STD`) | Q | Level (%) | 1 Quarter (NA/BIS) | Missing stays missing | Lagged 1Q; BIS private non-financial credit-to-GDP level. |
| 17 | `equity` | `NASDAQCOM` (`USA.FIN_EQUITY.M.STD`) | M/D | Quarterly mean $\Delta\log$ | 0 Days (Market) | Missing stays missing | Equity market return; market series available immediately at quarter end. |
| 18 | `houseprice_cs` | `CSUSHPISA` (`USA.FIN_HOUSEPRICE.M.US_CS`) | M | Quarterly mean $\Delta\log$ | 6 Weeks (Monthly) | Missing stays missing | S&P/Case-Shiller national home price index growth. |
| 19 | `houseprice_oecd` | `USSTHPI` (`USA.FIN_HOUSEPRICE.Q.OECD_BIS`) | Q | $\Delta\log$ growth (QoQ) | 1 Quarter (NA) | Missing stays missing | Lagged 1Q; FHFA all-transactions house price index growth. |
| 20 | `rate_long` | `GS10` (`USA.FIN_LONG.M.STD`) | M | Quarterly mean level (%) | 0 Days (Market) | Missing stays missing | 10-year Treasury constant maturity yield; unscaled level equals source. |
| 21 | `rate_policy` | `FEDFUNDS` (`USA.FIN_POLICY.M.STD`) | M | Quarterly mean level (%) | 0 Days (Market) | Missing stays missing | Effective Federal Funds policy rate; unscaled level equals source. |
| 22 | `rate_short` | `TB3MS` (`USA.FIN_SHORT.M.STD`) | M | Quarterly mean level (%) | 0 Days (Market) | Missing stays missing | 3-month Treasury bill rate; unscaled level equals source. |
| 23 | `unemp` | `UNRATE` (`USA.LAB_UNEMP.M.STD`) | M | Quarterly mean level (%) | 6 Weeks (Monthly) | Missing stays missing | Predictor only (D-R01); civilian unemployment rate; unscaled level. |
| 24 | `cpi` | `CPIAUCSL` (`USA.PRC_CPI.M.STD`) | M | YoY $\Delta\log$ inflation | 6 Weeks (Monthly) | Missing stays missing | Headline 4-quarter CPI inflation rate; unscaled. |
| 25 | `bci` | `BSCICP03USM665S` (`USA.SEN_BCI.M.STD`) | M | Quarterly mean level | 4 Weeks (Survey) | Missing stays missing | OECD composite business confidence; available at $t+6w$. |
| 26 | `cci` | `UMCSENT` (`USA.SEN_CCI.M.STD`) | M | Quarterly mean level | 4 Weeks (Survey) | Missing stays missing | University of Michigan consumer sentiment index; unscaled. |
| 27 | `term_spread_10y_3m` | Derived (`GS10` $-$ `TB3MS`) | M | Quarterly mean spread (pp) | 0 Days (Market) | Missing stays missing | 10Y minus 3M yield curve spread; canonical recession early-warning signal. |

---

## 3. Allowed Raw BEAI Copies (Firewall Paragraph)

The eight core BEAI series (`ACT_GDP_REAL`, `ACT_IP`, `ACT_EMP`, `ACT_HOURS`, `ACT_RINC`, `ACT_CONS`, `ACT_RETAIL`, `ACT_INV`) appear in the predictor matrix **strictly and exclusively** as versioned `beai_copy_<NAME>` predictors:
- `beai_copy_act_gdp_real`
- `beai_copy_act_ip`
- `beai_copy_act_emp`
- `beai_copy_act_hours`
- `beai_copy_act_rinc`
- `beai_copy_act_cons`
- `beai_copy_act_retail`
- `beai_copy_act_inv`

**The Firewall Guarantee:**
1. **Independent Transformations and Lags:** Pipeline A processes core series ex-post with zero publication lag to estimate a coincident economic factor. In contrast, Pipeline B applies conservative C-05 publication availability lags: quarterly national accounts series (`gdp_real`, `emp`, `hours`, `rinc`, `cons`, `inv`) are lagged by **one full quarter** ($t-1$), ensuring they could genuinely have been observed at prediction origin ($t + 6\text{ weeks}$). Monthly indicators (`ip`, `retail`) use observation quarter $t$, as their third month releases prior to $t + 6\text{ weeks}$.
2. **Zero Shared Artifacts:** Pipeline B shares **no fitted object, no dynamic factor loading ($\lambda_j$), no idiosyncratic variance ($\sigma_j$), no cumulated level index ($F_t$), no diffusion index ($D_t$), and no recession state flag ($R_t$)** with Pipeline A.
3. **Pure Reproducibility:** Every `beai_copy_*` column is 100% reproducible directly from the unstandardized activity growth rates in `data/clean/USA_growth.parquet` alone by shifting by its designated availability lag, without running the factor model, BBQ, or the diffusion gate.

---

## 4. Exclusion Blacklist

The following column classes, prefixes, and variables are strictly prohibited from appearing in the feature table or being consumed by Pipeline B models:

1. **BEAI Coincident Output (`factor`):** The dynamic factor $f_t$ captures coincident economic activity across the economy. Using it as a predictor would leak contemporaneous activity into an early-warning forecasting model.
2. **Cumulated Level Factor (`level`, $F_t$):** The integrated factor index used by the BBQ dating algorithm. Prohibited.
3. **Recession Indicator (`R`, `R_t`, `recession`):** The binary target variable constructed by Pipeline A. Any appearance in the feature matrix constitutes direct target leakage.
4. **Availability Count (`n_available`):** Derived solely during label dating to verify rule C-03 ($\ge 4$ indicators). Not an economic signal.
5. **Diffusion Share (`deterioration_share`):** The fraction of core indicators deteriorating in quarter $t$. Pipeline A construct; strictly forbidden.
6. **Turning Point Flags (`peak`, `trough`, `turning_point`):** Ex-post dated cyclical peaks and troughs. Leakage of future turning points.
7. **External Chronology (`USA.NBER.Q`, `NBER`, `validation`):** Rule C-04 / FW-06: External chronologies are plausibility checks, never features, targets, or training inputs.
8. **Country Identifiers and Country-Size Levels (`country_id`, `country`, `iso3`):** Rule C-07 / §29 explicitly bars country dummies or raw size levels (e.g. nominal dollar GDP, population level) to prevent models from learning trivial scale memorisation instead of cyclical signals.
9. **Episode Identifiers (`episode_id`, `episode`):** Identifiers marking contiguous recession episodes. Target-derived.
10. **Future Data / Future Shifts ($t+1, t+2$):** Any feature computed using observations dated after the prediction origin $t$. Enforced by the no-future leakage test.

---

## 5. 2026 Extension Audit

Under Decision D-R31, the reporting window was extended from 144 quarters (`1990Q1–2025Q4`) to **147 quarters (`1990Q1–2026Q3`)** using FRED observations through 2026-09.

### Audit Findings:
- **No Temporal Leakage:** The 2026 extension adds three quarters (`2026Q1`, `2026Q2`, `2026Q3`) using actual historical vintage downloads. Each quarter's features are constructed using only information available as of that quarter's origin ($t + 6\text{ weeks}$).
- **No Revision Contamination:** The label extension retained the exact BBQ parameters, diffusion gate (0.50), and 4/4 NBER agreement. No new recession episode was dated in 2026, and no existing episode boundary shifted.
- **Endpoint Handling:** For forward-looking targets $y(t, H)$, quarters within $H$ steps of the endpoint `2026Q3` (e.g. `2026Q3` for 1Q; `2026Q2–2026Q3` for 2Q; `2025Q4–2026Q3` for 4Q) cannot observe subsequent recession peaks. Following `ews.models.targets`, these terminal quarters carry `pd.NA` for the target and are excluded from out-of-sample evaluation, preventing truncation artifacts.

---

## 6. Feature Dictionary

Comprehensive catalog of every predictor in `data/features/dataset.parquet`:

| Feature Name | Units | Economic Interpretation | Expected Sign | Known Coverage Gaps / Notes |
|---|---|---|:---:|---|
| `beai_copy_act_gdp_real` | % QoQ | Real GDP growth (lagged 1Q) | Negative (slowdown $\implies$ warning) | None; complete across 147 quarters. |
| `beai_copy_act_ip` | % QoQ | Industrial production growth | Negative | Complete; high cyclical sensitivity. |
| `beai_copy_act_emp` | % QoQ | Household employment growth (lagged 1Q) | Negative | 146/147 quarters covered; Q-04 LFS fallback. |
| `beai_copy_act_hours` | % QoQ | Nonfarm business hours growth (lagged 1Q) | Negative | Complete; sensitive leading labour margin. |
| `beai_copy_act_rinc` | % QoQ | Real personal income ex transfers (lagged 1Q) | Negative | Complete; transfer payments excluded per D-R23. |
| `beai_copy_act_cons` | % QoQ | Real personal consumption growth (lagged 1Q) | Negative | Complete; core demand anchor. |
| `beai_copy_act_retail` | % QoQ | Real retail trade sales growth | Negative | 138/147 quarters (starts 1992Q1 in FRED); missing stays missing. |
| `beai_copy_act_inv` | % QoQ | Constructed real non-res investment (lagged 1Q) | Negative | Complete; constructed per D-R26 from 3 BEA components. |
| `inv_eq` | % QoQ | Real equipment investment growth (lagged 1Q) | Negative | Complete; early cyclical capital spending indicator. |
| `inv_struct` | % QoQ | Real structures investment growth (lagged 1Q) | Negative | Complete; non-residential construction cycle. |
| `inv_ipp` | % QoQ | Real intellectual property investment (lagged 1Q) | Negative | Complete; resilient secular component. |
| `inv_defl` | % QoQ | Investment goods price deflator inflation (lagged 1Q) | Ambiguous | Complete; capital goods inflation pressure. |
| `emp_estab` | % QoQ | Total nonfarm payroll employment growth | Negative | Complete; benchmark establishment survey. |
| `emp_lfs` | % QoQ | Household survey employment growth | Negative | Complete; captures self-employment and small business. |
| `rinc_m` | % QoQ | Monthly real disposable personal income growth | Negative | Complete; disposable income purchasing power. |
| `credit_gdp` | % GDP | Private non-financial credit-to-GDP level (lagged 1Q) | Positive (debt overhang $\implies$ vulnerability) | Complete; BIS quarterly credit gap indicator. |
| `equity` | % QoQ | Nasdaq Composite quarterly return | Negative (market sell-off $\implies$ warning) | Complete; forward-looking equity valuation shock. |
| `houseprice_cs` | % QoQ | Case-Shiller national house price inflation | Negative (property slump $\implies$ warning) | Complete; residential wealth effect proxy. |
| `houseprice_oecd` | % QoQ | FHFA all-transactions house price growth (lagged 1Q) | Negative | Complete; broad geographical price index. |
| `rate_long` | % | 10-year Treasury constant maturity yield | Ambiguous | Complete; long-term financing benchmark. |
| `rate_policy` | % | Effective Federal Funds rate | Positive (monetary tightening $\implies$ slowdown) | Complete; monetary policy stance. |
| `rate_short` | % | 3-month Treasury bill secondary market rate | Positive | Complete; short-term money market rate. |
| `unemp` | % | Civilian unemployment rate | Positive (rising joblessness $\implies$ recession) | Complete; Sahm-rule style labour slack indicator. |
| `cpi` | % YoY | Headline Consumer Price Index inflation | Positive (overheating/stagflation risk) | Complete; price stability gauge. |
| `bci` | Index | OECD composite business confidence | Negative (pessimism $\implies$ warning) | Complete; business expectations. |
| `cci` | Index | Michigan consumer sentiment index | Negative (pessimism $\implies$ warning) | Complete; consumer sentiment survey. |
| `term_spread_10y_3m` | pp | 10Y minus 3M Treasury yield spread | Negative (inverted yield curve $\implies$ warning) | Complete; canonical yield curve inversion indicator. |

---

## 7. What I Learned About Leakage

1. **Subtle Lag Aliasing:** When an indicator exists in both quarterly and monthly frequencies (e.g. `CE16OV` household employment), the quarterly variant is subject to National Accounts availability rules (1-quarter lag, observing $t-1$ at origin $t+6w$), whereas the monthly variant is available at origin $t+6w$ observing $t$. If not explicitly firewalled and documented, shifting the lagged quarterly copy by $-1Q$ exactly reproduces the monthly copy, creating an apparent future shift that trips automated leakage tests.
2. **In-Fold Scaling Discipline:** Standardizing features over the entire 147-quarter window leaks future sample mean and variance into past forecasts. This leakage artificially inflates cross-validation performance. Imputers and scalers must be instantiated and fitted *inside* each outer fold using training indices only.
3. **The Power of Mutation Testing:** A test suite that only verifies that a clean table passes proves very little about the sensitivity of the firewall. Actively injecting poisoned tables—one containing the prohibited target $R_t$ and another containing a $-1Q$ future shift—proves that the test harness actively catches leaks before any modeling code runs.
