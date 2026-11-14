# Feature Specification, Pipeline B Firewall and Feature Dictionary

| Field | Detail |
|---|---|
| **Specification owner** | Shravani Math (Lane 2A, integrated by Sathvik Boina) |
| **Builder** | Sathvik Boina (Lane 2B) |
| **Status** | **FROZEN** (14 November 2026), matches the built table |
| **Scope** | USA, 1990Q1–2026Q3 (147 quarters) |
| **Rules** | `docs/BUILD_CONTRACT.md` C-01, C-05, C-06, C-07, C-08, C-11, C-12 |
| **Decisions** | D-R01, D-R02, D-R03, D-R05, D-R06, D-R08, D-R12, D-R14, D-R22, D-R26–D-R28, D-R31, D-R34–D-R39 |
| **Machine-readable spec** | `FEATURE_SPEC`, `DERIVED_SPECS`, `EXCLUSIONS` in `src/ews/features.py` |
| **Builder CLI** | `make features` → `data/clean/dataset.parquet` |
| **Firewall tests** | `tests/test_feature_firewall.py` |

This document is the written authority on **what a legal predictor is**. The code is the
written spec made executable; if the two disagree, the table is not trusted until they are
reconciled and the rebuilt table hash is recorded.

---

## 1. Window and contract

- **Reporting and evaluation window:** 1990Q1–2026Q3, exactly **147 quarters**, one row per
  calendar quarter.
- **Input history:** the harmonised panel `data/clean/USA_panel.csv` begins in **1960Q1**
  (267 quarters). Transformations may use that earlier history so that early reporting
  quarters are not lost to differencing and rolling windows.
- **Unscaled contract (C-07/C-08):** the table is strictly unscaled. No column is
  standardised across the sample. Imputation and scaling are fitted inside each outer
  training fold and never stored beside the data.
- **Label independence (C-01):** no label output, factor, level index, recession flag,
  diffusion share, turning-point date, NBER chronology or episode identifier may be a
  predictor.
- **Missing stays missing (C-03):** no interpolation, forward fill, backfill or partial
  imputation. A missing source value stays missing through every transform.
- **Availability before transform (C-05):** the publication-availability lag is applied to
  the source series **before** any differencing or rolling statistic. See §3.

The table has **147 rows × 149 predictor columns**, plus the string `quarter` key in the
serialised Parquet file (150 columns on disk).

---

## 2. Column inventory

The 149 predictors come from **19 scope series plus 1 derived series**. The eight
BEAI-eligible core indicators appear only as separate `beai_copy_*` copies: 8 series × 8
columns = **64 columns**. The remaining 11 predictors and the derived slope contribute
**85 columns**.

Each input series is transformed with the C-07 form in the table below. `base` means the
transformed series that later lags and rolling statistics use:

| form | base | columns produced |
|---|---|---|
| `growth` | `100 × Δlog(level)` (QoQ) | `qoq_growth`, `yoy_growth`, `base_lag_1/2/4`, `rolling_mean_4q`, `rolling_volatility_4q`, `trend_4q` — 8 |
| `price` | `100 × Δlog(level)` (QoQ) | `qoq_log_change`, `yoy_log_change`, `base_lag_1/2/4`, `rolling_mean_4q`, `rolling_volatility_4q` — 7 |
| `rate`, `spread`, `survey` | the level itself | `level`, `change_4q`, `base_lag_1/2/4`, `rolling_mean_4q`, `rolling_volatility_4q` — 7 |
| `ratio` | the level itself | `level`, `change_4q`, `change_8q`, `base_lag_1/2/4`, `rolling_mean_4q`, `rolling_volatility_4q` — 8 |

`rolling_*` windows require all four observations; `trend_4q` is the slope of a 4-quarter
linear fit on `base`. Rates, spreads and surveys keep a dimensionless `__level`; activity
and price series enter only as growth or log change, never as raw levels.

### 2.1 BEAI-eligible core copies (64 columns)

| Series name | Source column | Form | Availability | Columns |
|---|---|---|---:|---:|
| `ACT_GDP_REAL` | `USA.ACT_GDP_REAL.Q.NA` | growth | `NA` | 8 |
| `ACT_IP` | `USA.ACT_IP.M.STD` | growth | `MONTHLY` | 8 |
| `ACT_EMP` | `USA.ACT_EMP.Q.NA` | growth | `NA` | 8 |
| `ACT_HOURS` | `USA.ACT_HOURS.Q.STD` | growth | `NA` | 8 |
| `ACT_RINC` | `USA.ACT_RINC.Q.STD` | growth | `NA` | 8 |
| `ACT_CONS` | `USA.ACT_CONS.Q.NA` | growth | `NA` | 8 |
| `ACT_RETAIL` | `USA.ACT_RETAIL.M.STD` | growth | `MONTHLY` | 8 |
| `ACT_INV` | `USA.ACT_INV.Q.STD` | growth | `NA` | 8 |

Every column is prefixed `beai_copy_` and then the series name, for example
`beai_copy_ACT_IP__qoq_growth`. The copies are transformed independently from Pipeline A.

### 2.2 Predictor-only series (85 columns)

| Series name | Source column | Form | Availability | Columns |
|---|---|---|---:|---:|
| `FIN_CREDIT_GDP` | `USA.FIN_CREDIT_GDP.Q.STD` | ratio | `NA` | 8 |
| `FIN_EQUITY` | `USA.FIN_EQUITY.M.STD` | price | `MARKET` | 7 |
| `FIN_HOUSEPRICE_CS` | `USA.FIN_HOUSEPRICE.M.US_CS` | price | `MONTHLY` | 7 |
| `FIN_HOUSEPRICE_BIS` | `USA.FIN_HOUSEPRICE.Q.OECD_BIS` | price | `NA` | 7 |
| `FIN_LONG` | `USA.FIN_LONG.M.STD` | rate | `MARKET` | 7 |
| `FIN_POLICY` | `USA.FIN_POLICY.M.STD` | rate | `MARKET` | 7 |
| `FIN_SHORT` | `USA.FIN_SHORT.M.STD` | rate | `MARKET` | 7 |
| `LAB_UNEMP` | `USA.LAB_UNEMP.M.STD` | rate | `MONTHLY` | 7 |
| `PRC_CPI` | `USA.PRC_CPI.M.STD` | price | `MONTHLY` | 7 |
| `SEN_BCI` | `USA.SEN_BCI.M.STD` | survey | `SURVEY` | 7 |
| `SEN_CCI` | `USA.SEN_CCI.M.STD` | survey | `SURVEY` | 7 |
| `FIN_SLOPE` (derived) | `USA.FIN_SLOPE.M.DERIVED` = `FIN_LONG − FIN_SHORT` | spread | `MARKET` | 7 |

The derived slope is built from the harmonised long and short rates before availability
lags are applied.

**Column count check:** `64 + 8 + 7×10 + 7 = 149`, from 20 input series.

---

## 3. Availability ladder (C-05)

The prediction origin for quarter *t* is the quarter end plus six weeks. A source
observation is used only if its conservative publication date has passed by that origin.
The lag classes are the approved mapping in `ews.models.publication_lags`:

| Class | Publication lag | Typical series |
|---|---|---|
| `NA` | 3 months | national accounts, quarterly credit, quarterly house prices |
| `MONTHLY` | 6 weeks | industrial production, retail, monthly prices and unemployment |
| `MARKET` | 0 days | interest rates, equity prices, derived slope |
| `SURVEY` | 4 weeks | OECD business confidence, consumer sentiment |
| `ANNUAL` | 12 months | annual-only sources (not used in this table) |

`build_available_panel` selects the latest fully available observation, so a quarter-*t*
predictor uses only data published by the origin. The selected value is then transformed;
rolling windows therefore cannot reach into the future through the availability step.

---

## 4. The firewall guarantee

1. **The eight BEAI series appear only as copies.** Pipeline A uses the same eight core
   indicators, ex post, with no publication lag, to estimate a coincident factor. Pipeline B
   applies the C-05 ladder and stores separate `beai_copy_*` predictors. No fitted object,
   factor loading, idiosyncratic variance, level index, diffusion index or recession flag is
   shared.
2. **The copies are reproducible from the harmonised panel alone.** For every copy series,
   applying `build_available_panel` and `transform_quarterly_series` to the panel reproduces
   the table columns exactly. This is asserted in `test_independence`.
3. **No future observation enters a past row.** Rebuilding the table on history truncated at
   a cutoff leaves every value at or before that cutoff byte-identical. This is asserted at
   four cutoffs in `test_no_future_leakage`.
4. **The checks fail on poisoned tables.** Injecting `R`, `factor` or `n_available` makes the
   validator raise; shifting a column one quarter into the future makes the no-future
   comparison fail. This is asserted in `test_mutation_fails_on_leak`. A suite that only
   passes on clean data is not a firewall.

---

## 5. Exclusion blacklist

None of the following may appear in the table or be consumed by Pipeline B models:

1. **BEAI factor (`factor`, `f_t`)** — coincident activity, direct leakage.
2. **Cumulated level index (`level`, `F_t`)** — the BBQ dating input. Note that a
   dimensionless per-series `__level` column for a rate or survey is allowed; the prohibited
   object is Pipeline A's cumulated factor level.
3. **Recession indicator (`R`, `R_t`, `recession`)** — the target.
4. **Availability count (`n_available`)** — a dating artefact, not an economic signal.
5. **Diffusion share (`deterioration_share`)** — a Pipeline A construct.
6. **Turning-point flags (`peak`, `trough`, `turning_point`)** — ex-post dates.
7. **External chronology (`USA.NBER.Q`, `NBER`, `validation`)** — plausibility checks only
   (FW-06).
8. **Country identifiers and country-size levels (`country`, `country_id`, `iso3`)** — no
   country dummies or raw nominal size levels.
9. **Episode identifiers (`episode`, `episode_id`)** — target-derived.
10. **Future observations** — any value dated after the prediction origin, enforced by the
    truncation test.

Additional source columns are documented as excluded in `EXCLUSIONS`:

| Excluded source | Reason |
|---|---|
| `USA.ACT_EMP.M.ESTAB` | BEAI-eligible variant, near-duplicate of `ACT_EMP` |
| `USA.ACT_EMP.M.LFS` | raw source of `ACT_EMP.Q.NA`; duplicate information |
| `USA.ACT_RINC.M.US` | BEAI-eligible variant, near-duplicate of `ACT_RINC` |
| `USA.ACT_INV_EQ.Q.STD` | Q-02 supporting component, not a scope predictor |
| `USA.ACT_INV_STRUCT.Q.STD` | Q-02 supporting component, not a scope predictor |
| `USA.ACT_INV_IPP.Q.STD` | Q-02 supporting component, not a scope predictor |
| `USA.ACT_INV_DEFL.Q.STD` | Q-02 supporting component, not a scope predictor |
| `USA.FIN_CREDIT_GAP.Q.STD` | needs an HP gap; not in the harmonised panel |

---

## 6. 2026 extension audit (D-R31)

The window was extended from 144 quarters to 147 with FRED observations through 2026-09.

- The extension adds 2026Q1–2026Q3. Each row uses only information available at that
  quarter's prediction origin.
- No recession episode was added and no existing episode boundary moved; the label
  estimator is unchanged.
- Forward targets `y(t, H)` are undefined within `H` quarters of 2026Q3. Those rows carry
  `pd.NA` and are dropped from scoring, never silently treated as negatives.

---

## 7. Feature dictionary

`base` is the transformed series from §2. `sign` is the expected direction of a warning
(higher predictor value → more likely recession onset), not a fitted coefficient.

| Predictor family | Units | Interpretation | Expected warning sign | Coverage / notes |
|---|---|:---:|:---:|---|
| `beai_copy_ACT_GDP_REAL__*` | % QoQ | Real GDP growth | negative | complete |
| `beai_copy_ACT_IP__*` | % QoQ | Industrial production growth | negative | complete |
| `beai_copy_ACT_EMP__*` | % QoQ | Household employment growth | negative | Q-04 LFS fallback |
| `beai_copy_ACT_HOURS__*` | % QoQ | Nonfarm business hours growth | negative | Q-05 coverage note |
| `beai_copy_ACT_RINC__*` | % QoQ | Real income ex transfers growth | negative | D-R23 |
| `beai_copy_ACT_CONS__*` | % QoQ | Real consumption growth | negative | complete |
| `beai_copy_ACT_RETAIL__*` | % QoQ | Retail sales growth | negative | FRED starts 1992Q1; missing stays missing |
| `beai_copy_ACT_INV__*` | % QoQ | Constructed non-residential investment growth | negative | D-R26 |
| `FIN_CREDIT_GDP__*` | % of GDP | Private credit-to-GDP level and changes | ambiguous | BIS quarterly |
| `FIN_EQUITY__*` | % QoQ | Equity log return | negative | market |
| `FIN_HOUSEPRICE_CS__*` | % QoQ | Case-Shiller house-price log change | negative | monthly |
| `FIN_HOUSEPRICE_BIS__*` | % QoQ | BIS/FHFA house-price log change | negative | quarterly |
| `FIN_LONG__*` | % | 10-year Treasury level and changes | ambiguous | market |
| `FIN_POLICY__*` | % | Effective federal funds rate level and changes | positive | market |
| `FIN_SHORT__*` | % | 3-month Treasury bill level and changes | positive | market |
| `LAB_UNEMP__*` | % | Unemployment level and changes | positive | D-R01 predictor only |
| `PRC_CPI__*` | % QoQ | CPI log change | ambiguous | monthly |
| `SEN_BCI__*` | index | OECD business confidence level and changes | negative | survey |
| `SEN_CCI__*` | index | Michigan consumer sentiment level and changes | negative | survey |
| `FIN_SLOPE__*` | pp | 10Y minus 3M spread level and changes | negative | canonical inversion signal |

Within each family the suffixes are the column list in §2. A `__base_lag_k` column is the
transformed value delayed by *k* quarters; `__trend_4q` exists only for `growth` families.

---

## 8. Verification and reproduction

```bash
make features
.venv/bin/python -m pytest tests/test_feature_firewall.py -q
.venv/bin/python scripts/08_verify_lane2a.py
```

The frozen table hash is recorded in `docs/STATE.md` and `docs/FINAL_REPORT.md`.
Regenerating from the same panel must reproduce it byte for byte. A hash change without a
recorded spec change is a defect until explained.

---

## 9. What I learned about leakage

1. **Lag aliasing.** When a series exists at both quarterly and monthly frequency (for
   example household employment), the quarterly copy carries the national-accounts lag while
   the monthly copy is available sooner. If the availability class is not explicit, shifting
   one copy can silently reproduce the other and look like a future leak.
2. **In-fold scaling discipline.** Standardising over the full 147-quarter window leaks the
   sample mean and variance into past forecasts and inflates apparent performance. Scalers
   and imputers must be fitted inside each outer training block.
3. **Mutation testing is the point.** A test that only checks a clean table proves very
   little. Poisoning the table with `R` and with a one-quarter future shift, and requiring
   the checks to catch both, is what turns the suite into a firewall.
4. **Availability before transform.** Applying lags after differencing can align the wrong
   quarter to a prediction origin. The order is fixed: availability lag, then transform.
