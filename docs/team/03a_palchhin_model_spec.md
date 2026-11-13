# Model Specification: Six Singles, REWI and the Pre-Registered Ensemble

**Prepared for:** Palchhin (Part 3, modelling lead)
**Prepared by:** Sathvik Boina
**Status:** working specification, 2026-11-13
**Scope:** USA-first six-model implementation, REWI, feature stability and the
pre-registered ensemble

This document separates three things:

1. rules that are **already frozen** in `docs/BUILD_CONTRACT.md` and
   `docs/PROPOSAL_ADDENDUM.md`;
2. the exact **input contract** you receive from Part 2 (Arshiya);
3. the numeric tuning choices that are **not yet frozen** and are yours to record on
   Day 1, before any test score exists.

Do not treat a recommendation in section 3 as an existing decision. If you adopt it,
record it; if you change it, record that instead.

---

## 1. REWI — formulation and implementation

### 1.1 Definition

For outer fold `k`, using only that fold's training block:

```text
z(i,t,k) = (x(i,t) - mean_train(i,k)) / sd_train(i,k)

REWI(t,k) = sum over i in S(k) of beta_hat(i,k) * z(i,t,k)
```

- `beta_hat(i,k)` are the coefficients from the fold's **Elastic Net logistic** fit.
- `S(k) = {i : beta_hat(i,k) != 0}` is the selected feature set.
- The **intercept is excluded from REWI**.
- `z` uses **training-fold** mean and standard deviation only.
- Higher REWI means higher recession odds, because `beta` comes from a
  recession-probability model. Do not flip individual signs after seeing results.

For a probability, use the same fitted model:

```text
p(t,k) = sigmoid(beta0(k) + REWI(t,k))
```

The intercept is retained for the probability mapping but excluded from the index
itself.

If a normalized index is needed for reporting:

```text
REWI_star(t) = (REWI(t) - mean_train(REWI)) / sd_train(REWI)
```

Never normalize using test-fold moments.

### 1.2 Implementation order per outer fold (C-08)

1. Take the outer train/test split from `folds.json`. Do not touch the test block.
2. Fit `StandardScaler` on the outer training block.
3. Transform train and test with that scaler.
4. Tune the Elastic Net selector on **time-ordered inner folds** inside the outer
   training block.
5. Freeze `C`, `l1_ratio`, class weight and any other hyperparameters.
6. Refit Elastic Net on the full outer training block.
7. Extract `beta_hat`, excluding the intercept. Record selected features and signs.
8. Build REWI for train and test using the frozen scaler and coefficients.
9. Lock the probability threshold on the inner folds; do not look at the outer test
   block.
10. Predict the outer test block once.

### 1.3 Edge cases

- If Elastic Net selects zero features, report that fold as undefined. Fall back to the
  pre-declared plain-logistic baseline and say so. Do not force features in.
- Do not refit coefficients on the full sample.
- Treat REWI as an interpretable **index/diagnostic**, not a seventh model. Do not add
  it to the ensemble unless there is a new, dated pre-registration.
- The Elastic Net classifier is one of the six single models. REWI is derived from the
  same fold's selector, so report them together but do not count REWI as an extra
  ensemble candidate.

---

## 2. Feature definitions and transformations

### 2.1 Ownership and source

The exact predictor list and column names are **Part 2 / Arshiya's deliverable**, not
yours. Consume the frozen table; do not rebuild transforms inside the model code.

Inputs:

- `data/clean/dataset.parquet` — one row per USA quarter, 1990Q1–2026Q3, **unscaled**.
- `outputs/folds/folds.json` — outer and inner fold boundaries.
- `feature_dictionary.csv` — Arshiya's column list, source, transform, lag and
  missingness rule.
- `outputs/labels/USA_labels.csv` and `USA_episodes.csv` — the target source.

### 2.2 Target

```text
y(t,H) = 1 iff a label recession onset occurs in t+1, ..., t+H
```

- Use the **project label's peak quarter** as onset, not NBER.
- Horizons: `H` in `{1, 2, 4}`; **2Q is primary**.
- NBER is a validation chronology only. It is never a feature or target.

### 2.3 Frozen transform rules (C-07)

| Form | Transforms |
|---|---|
| growth | QoQ and YoY growth; lags 1/2/4; rolling mean, volatility, trend |
| rate | level; 4Q change; lags; rolling statistics |
| ratio | level; 4Q and 8Q change; lags |
| spread | level; 4Q change; lags |
| survey | level; 4Q change; lags |
| price | YoY and QoQ log change; lags; rolling volatility |

### 2.4 Frequency conversion (C-06)

- Monthly to quarterly: quarterly mean (primary), quarter-end value, intra-quarter
  change.
- A quarter is missing if any constituent month is missing. No partial-quarter
  imputation.
- Weekly to quarterly: mean by week-ending date, quarter-end value.
- Daily to monthly mean to quarterly mean, plus quarter-end value.
- Annual: carry forward with a 1-year lag; no temporal disaggregation.

### 2.5 Availability lags (C-05)

| Data class | Pipeline B lag |
|---|---|
| Quarterly national accounts | 1 quarter |
| Monthly indicators | 6 weeks |
| Financial / market | 0 |
| Surveys / confidence | 4 weeks |
| Quarterly non-national-accounts | 1 quarter |
| Weekly claims, CPI-based REER | 6 weeks |
| Annual | 1 year, last published value carried forward |

### 2.6 Hard exclusions

- No BEAI factor `F_t`, no `R_t`, no turning-point flag, no diffusion value, no label.
- No NBER or other external chronology.
- No future observation, no full-sample scaling, no country ID, no raw country-size
  level.
- Raw BEAI-eligible series are allowed **only** as separate, versioned predictor copies
  with their own transform and lag (C-01 / FW-04). They must not share a fitted object
  with Pipeline A.

### 2.7 Missing data

Missing stays missing. No interpolation, forward fill or partial-quarter imputation. If
a model cannot handle missing values, use the fold-safe imputation rule declared in the
feature dictionary. Never use a full-sample rule.

### 2.8 Practical rule for Part 3

Use Arshiya's columns **as named**. Keep the feature matrix identical across all six
models and the ensemble. If you think a transform is wrong, raise it before the table is
frozen; do not silently recompute it in Part 3.

---

## 3. Tuning budget, class weights and MLP seed rule

### 3.1 What is already frozen

- Same time-ordered tuning budget and class weights for all models (C-09).
- Selector: Elastic Net logistic, tuned inside the fold; report the selected count;
  target approximately 10–15 but **not forced** (C-09).
- MLP: average over **at least 3 seeds**, with early stopping (C-09).
- Threshold locked before the outer test block (C-08, D-R11).
- Primary metric: pooled out-of-sample PR-AUC (C-10).

### 3.2 What is not yet frozen

The contract does **not** currently contain numeric values for:

- number of tuning candidates;
- class-weight value;
- MLP seed list;
- early-stopping patience;
- threshold objective.

Those are yours to freeze on Day 1.

### 3.3 Recommended freeze

Adopt these unless you have a strong reason; record any change before Day 2.

| Item | Freeze |
|---|---|
| Inner folds | The time-ordered inner folds in `folds.json`; same for every model |
| Tuning budget | **24 candidate configurations per model per outer fold**, same seed, same inner folds; exhaust the grid if smaller |
| Tuning seed | `42` |
| Selection metric | Pooled inner-fold PR-AUC; tie-break by lower Brier, then fixed model order |
| Class weights | `class_weight="balanced"` on the training fold for all classifiers that support it |
| XGBoost equivalent | `scale_pos_weight = n_negative / n_positive`, computed on the training fold |
| MLP class weights | Balanced sample weights, computed on the training fold |
| MLP seeds | `[0, 1, 2]`; average predicted probabilities, not hard labels |
| MLP early stopping | Patience 10, max 300 epochs, validation = inner fold, restore best weights |
| Scaler | `StandardScaler` fitted inside the fold; same preprocessing pipeline for all models |
| Feature selection | One shared selected set per outer fold for all six models, so the ensemble uses the same feature matrix |
| Threshold objective | **Max F1** (current O-3 default); lock one threshold per outer fold on inner folds |
| Random split | Never |

If the team changes O-3 to "recall at a precision floor", that decision must be made
**before** any outer test score is seen. Otherwise the model comparison is invalid.

Record this as a new decision, for example **D-R32 — model tuning freeze**, in
`decisions_log.csv` and `docs/DECISIONS.md`, before Day 2. The exact numbers matter less
than the fact that they are fixed before scoring and identical across models.

---

## 4. Expected output format

Write under `outputs/results/rewi/` and `outputs/results/ensemble/`. Use long format,
one row per fold/quarter/feature. Include metadata in every file or alongside it.

### 4.1 REWI outputs

**`outputs/results/rewi/rewi_predictions.csv`**

| Column | Meaning |
|---|---|
| `country` | `USA` |
| `horizon` | 1, 2, 4 |
| `outer_fold` | Fold ID |
| `quarter` | `YYYYQn` |
| `split` | `train` / `test` |
| `rewi` | Raw index |
| `prob` | Probability from `sigmoid(beta0 + REWI)` |
| `threshold` | Locked fold threshold |
| `y_true` | Target |
| `n_features` | Selected count |

**`outputs/results/rewi/rewi_coefficients.csv`**

| Column | Meaning |
|---|---|
| `country`, `horizon`, `outer_fold` | Keys |
| `feature` | Feature name from the dictionary |
| `beta` | Coefficient on standardized scale |
| `abs_beta` | Absolute value |
| `rank` | Rank by `abs_beta` within fold |
| `selected` | Boolean |

**`outputs/results/rewi/rewi_fold_metrics.csv`**

```text
country, horizon, outer_fold, train_start, train_end, test_start, test_end,
n_train, n_test, n_pos_train, n_pos_test, n_features, threshold,
pr_auc, roc_auc, recall, precision, f1, brier
```

**`outputs/results/rewi/rewi_stability.csv`**

```text
country, horizon, outer_fold, rewi_mean_train, rewi_sd_train,
rewi_mean_test, rewi_sd_test, corr_rewi_prob_train, corr_rewi_prob_test
```

### 4.2 Feature stability outputs

**`outputs/results/rewi/feature_stability.csv`**

| Column | Meaning |
|---|---|
| `country`, `horizon`, `feature` | Keys |
| `n_folds` | Folds where the feature was available |
| `selection_frequency` | Share of folds with a non-zero coefficient |
| `mean_beta` | Mean coefficient across folds |
| `sd_beta` | SD of coefficient |
| `sign_agreement` | Share of folds matching the majority sign |
| `mean_abs_beta` | Mean absolute coefficient |
| `mean_rank`, `sd_rank` | Stability of rank by absolute coefficient |

**`outputs/results/rewi/rewi_summary.md`**

- Fold-level PR-AUC, ROC-AUC, recall, precision, F1 and Brier table.
- Positive counts and thresholds.
- Top 15 features by selection frequency, with sign agreement.
- Explicit statement of any fold with zero selected features or an undefined metric.
- No narrative claim beyond the out-of-sample numbers.

**`outputs/results/rewi/run_metadata.json`**

Data version and hash, feature-list hash, fold-file hash, model parameters, selected
features, threshold, seed, package versions, exact command and timestamp.

### 4.3 Ensemble outputs

**`outputs/results/ensemble/ensemble_members.csv`**

```text
country, horizon, outer_fold, rank, model, config_id, inner_pr_auc, weight
```

**`outputs/results/ensemble/ensemble_headline.csv`**

```text
country, horizon, model, pooled_pr_auc, delta_vs_best_single,
ci_low, ci_high, episode_recall, n_episodes, decision
```

**`outputs/results/ensemble/ensemble_bootstrap.csv`**

```text
country, horizon, resample, delta_pr_auc
```

**`outputs/results/ensemble/headline.md`** and **`episodes.md`**

- Main table: six singles, best single, ensemble and exploratory stack.
- Delta PR-AUC with the 95% paired-bootstrap interval.
- Episode detection rate, lead time and false-warning episodes.
- A clear `decision` column: `ensemble_primary` or
  `single_primary_negative_ensemble`.
- Negative result written with the same prominence as a positive one.

Every result row must carry the C-12 metadata: data version, features, folds, parameters,
threshold, seed and command.

---

## 5. Build-contract decisions to follow

| Rule | What it means for Part 3 |
|---|---|
| **C-01** | Two pipelines, one firewall. No BEAI output, factor, `R_t`, turning point, diffusion or label as a feature. Raw BEAI-eligible copies only as separate versioned predictors. No fitted object shared with Pipeline A. |
| **C-05** | Apply availability lags by data class. Prediction origin is quarter end + 6 weeks. Do not use post-quarter-end data in primary features. |
| **C-06** | Monthly/weekly/daily/annual conversion rules; a quarter is missing if any month is missing. |
| **C-07** | Use the frozen transforms per form. Store unscaled values; scale inside the fold. |
| **C-08** | Expanding-window walk-forward only. No random split, no k-fold, no shuffle. Inner folds time-ordered. Per fold: scaler, selector, features, REWI, tune model, threshold, lock, predict the untouched test block. |
| **C-09** | Six models: logistic, elastic net, random forest, XGBoost, SVM, MLP. Same tuning budget and class weights. Selector is Elastic Net logistic. MLP averages at least 3 seeds with early stopping. Baselines: majority, term-spread probit/logit, plain logistic. |
| **C-10** | Primary metric is pooled out-of-sample PR-AUC. Secondary: ROC-AUC, recall, precision, F1, accuracy, Brier and confusion matrix. Report episode detection, lead time and false-warning episodes. A fold with no positives is not scored on AUC/PR-AUC alone. |
| **C-12** | Every run stores data version, series IDs, transforms, features, folds, parameters, selected features, threshold, metrics, seed and manifest hash. |
| **C-13** | Equal-weight probability average of the **top-3 single-model configurations**, ranked by pooled PR-AUC on inner time-ordered validation folds of the current outer training block. Same folds and feature matrix as the singles. Members, weights, scalers and threshold fitted inside the outer training block. |
| **D-R11** | Threshold locked before the test block. |
| **D-R14** | Revised historical data with simulated lags, not a real-time vintage study. Say so in the report. |
| **D-R19 / O-3** | Threshold objective is still open; current default is max F1. Record the choice before scoring. |
| **D-R29** | Ensemble rule: at least 0.01 absolute pooled PR-AUC gain over the inner-fold-selected best single; paired bootstrap 1,000 resamples, 95% confidence interval excluding zero; no episode-recall loss. Otherwise the single model is primary and the ensemble is a negative result. A logistic stack is exploratory only. |
| **D-R31** | Reporting window is 1990Q1–2026Q3, 147 quarters. USA first. Do not delay the USA headline for JPN/DEU labels. |

### 5.1 Ensemble details that are easy to get wrong

1. **"Top-3 configurations", not "top-3 model families".** Two configurations from the
   same family are allowed if they rank in the top three.
2. **Rank inside each outer training block**, using inner-fold pooled PR-AUC. Never rank
   using the outer test block.
3. **Average probabilities, not hard labels.** Use one locked ensemble threshold per
   outer fold.
4. **The comparator is the best single model chosen by inner-fold performance**, not the
   best test score.
5. **The bootstrap is paired over outer folds**, 1,000 resamples, 95% interval.
6. **Episode recall is a guardrail.** If it falls, the single model is primary even if
   PR-AUC improves.
7. **No member, weight or threshold changes after test scores are seen.** If the rule
   fails, report the negative result.

---

## 6. Hand-off expectations

- **Day 1 end:** the frozen tuning budget, class weights, MLP seed rule and threshold
  objective recorded in the decisions log. Code need not be final yet.
- **Day 2 end:** six singles and baselines running on a fixture fold, with missing
  optional packages named honestly.
- **Day 3 end:** REWI and feature stability on Arshiya's draft folds.
- **Day 4 end:** USA headline on the final Day 4 folds.
- **Day 5 end:** rerun on the frozen folds if they moved; ablations, robustness,
  `headline.md`, `episodes.md`, `EXPERIMENTS.md`, and a one-branch PR.

**Bottom line:** the contract already fixes the method, the firewall, the metrics and the
ensemble. It deliberately does not fix the numeric tuning choices. Those are your Day 1
freeze, and they must be written down before you see any test score.

---

## 7. Where to look

| Need | File |
|---|---|
| Frozen rules | `docs/BUILD_CONTRACT.md` |
| Ensemble pre-registration | `docs/PROPOSAL_ADDENDUM.md` |
| Decisions and open questions | `docs/DECISIONS.md`, `decisions_log.csv` |
| Current state and hashes | `docs/STATE.md` |
| Lane brief | `docs/team/03_palchhin_models_ensemble.md` |
| Team plan | `docs/TEAM_PLAN.md`, `Team_Plan.xlsx` |
| Feature table and folds | `data/clean/dataset.parquet`, `outputs/folds/folds.json` |
| USA label | `outputs/labels/USA_labels.csv`, `USA_episodes.csv` |
| Week log | `EWS_Work_Log.xlsx` |
