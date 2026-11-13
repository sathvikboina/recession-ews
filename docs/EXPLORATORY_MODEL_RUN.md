# Exploratory USA-first model run

**Status:** exploratory only — **not** the pre-registered official result, and **not** a
forecasting claim. This file records a run made on 2026-11-13 because the shared feature
table, fold file and model code had not been delivered.

## Why this run exists

`docs/BUILD_CONTRACT.md` and `docs/PROPOSAL_ADDENDUM.md` (C-13) define the official model
protocol. That protocol depends on:

- Arshiya's frozen `dataset.parquet` and `folds.json` (Part 2), and
- Palchhin's six single models plus the ensemble harness (Part 3).

Neither was available. To avoid guessing at the official result, this run builds a
contract-shaped walk-forward experiment from the frozen `labels-v3` target and the existing
clean USA panel. It is deliberately labelled exploratory and must not be copied into
`outputs/results/ensemble/` or reported as the pre-registered result.

## What was run

| Item | Exploratory setting |
|---|---|
| Country | USA |
| Target | `labels-v3` BBQ peaks, H = 2, positive in each of the two quarters before a peak |
| Window | 1990Q1–2026Q1 (145 quarters; 2026Q2–Q3 have no known H=2 target) |
| Positives | 7 quarters: 1990Q1, 2000Q3, 2000Q4, 2007Q2, 2007Q3, 2019Q2, 2019Q3 |
| Features | 186 candidates derived from `data/clean/USA_panel.csv`, screened per fold |
| Folds | four expanding, time-ordered outer folds (below) |
| Models | logistic (L2), elastic net, random forest, gradient boosting ("xgboost-like"), linear SVM (Platt-calibrated), MLP |
| Ensemble | equal-weight top-3 by inner-validation PR-AUC, applied once per fold |
| Threshold | locked from inner validation, then applied unchanged to the outer test block |
| Seed | 42 |

| Fold | Train | Test | Test positives |
|---|---|---|---|
| F1 | 1990Q1–2000Q2 | 2000Q3–2005Q4 | 2 |
| F2 | 1990Q1–2005Q4 | 2006Q1–2010Q4 | 2 |
| F3 | 1990Q1–2014Q4 | 2015Q1–2020Q4 | 2 |
| F4 | 1990Q1–2020Q4 | 2021Q1–2026Q1 | 0 |

## Result

| Metric | Ensemble (top-3) | Best single (MLP) |
|---|---:|---:|
| Pooled PR-AUC | 0.1371 | 0.1388 |
| Pooled ROC-AUC | 0.7449 | 0.7531 |
| Recall at locked threshold | 0.333 | 0.333 |
| Precision at locked threshold | 0.080 | 0.095 |
| Brier | 0.0912 | 0.0912 |
| Episode recall | 0.333 | 0.333 |
| False-positive quarters | 23 | 19 |

- **Delta vs best single:** **−0.0017**.
- **95% bootstrap interval (1,000 resamples):** **[−0.0550, +0.0556]** — includes zero.
- Share of bootstrap resamples with a positive delta: 0.45; with a gain of at least 0.01:
  0.31.

### Pooled metrics by model

```text
        model  pooled_pr_auc  pooled_roc_auc   recall  precision       f1    brier  episode_recall  false_positive_quarters
     logistic       0.117280        0.674897 0.333333   0.055556 0.095238 0.100025        0.333333                       34
  elastic_net       0.078282        0.520576 0.333333   0.100000 0.153846 0.107787        0.333333                       18
random_forest       0.071782        0.448560 0.000000   0.000000 0.000000 0.105450        0.000000                       22
 xgboost_like       0.108261        0.622428 0.333333   0.066667 0.111111 0.166519        0.333333                       28
          svm       0.127714        0.689300 0.333333   0.105263 0.160000 0.092591        0.333333                       17
          mlp       0.138756        0.753086 0.333333   0.095238 0.148148 0.091198        0.333333                       19
     ensemble       0.137073        0.744856 0.333333   0.080000 0.129032 0.091242        0.333333                       23
```

### Per-fold PR-AUC

`NaN` means the test block had no positive quarters, so PR-AUC is undefined.

```text
outer_fold      model  n_pos_test   pr_auc  roc_auc   brier
        F1   ensemble           2 0.196429 0.625000 0.114709
        F2   ensemble           2 0.236111 0.722222 0.088108
        F3   ensemble           2 0.266667 0.818182 0.135872
        F4   ensemble           0      NaN      NaN 0.018635
        F1         mlp           2 0.171429 0.650000 0.117927
        F2         mlp           2 0.325000 0.833333 0.097721
        F3         mlp           2 0.266667 0.818182 0.122118
        F4         mlp           0      NaN      NaN 0.021648
```

### Episode detection

Of the three episodes whose pre-peak windows fall inside a test block, only 2019Q4 was
flagged; 2001Q1 and 2007Q4 were missed.

```text
  peak  detected  lead_quarters
2001Q1         0            NaN
2007Q4         0            NaN
2019Q4         1            2.0
```

### Pre-registered ensemble test (C-13)

| Condition | Result | Pass |
|---|---|---|
| Pooled PR-AUC gain ≥ 0.01 | −0.0017 | no |
| Bootstrap CI excludes zero | [−0.0550, +0.0556] | no |
| No episode-recall loss | 0.333 vs 0.333 | yes |
| Applied once, before results | yes | yes |

**Decision (exploratory):** the ensemble fails the pre-registered rule. On this run the
single model (MLP) is primary and the ensemble is a negative result. Because the run is
not the official one, this decision is recorded for orientation only; it does not satisfy
C-13.

## Honest limitations

1. **Not the official protocol.** No frozen feature table, no `folds.json`, no official
   model code. The four folds here are hand-built expanding windows, not the team's
   pre-registered folds.
2. **Reference implementations.** `scikit-learn` and `xgboost` could not be installed
   (network timeouts). The six families are hand-written numpy/scipy versions. Results can
   differ from the official library versions in tuning, regularisation and tree growth.
3. **Very few positives.** Seven positive quarters across 145 quarters; F1 has one positive
   in training and F4 has none in testing. Fold-level PR-AUC is undefined for F4 and the
   pooled number is dominated by 21 negative F4 quarters.
4. **Inner validation can lack positives.** In F1 the inner validation block has no
   positive, so model ranking falls back to Brier score and inner PR-AUC is `NaN`.
   Thresholds from F1 are therefore weakly identified.
5. **Pooled vs mean fold metric.** The pre-registered rule uses a pooled PR-AUC. Pooling
   across folds with different positive rates and one all-negative fold is pessimistic and
   makes the absolute values hard to compare with published results.
6. **Publication lags are approximate.** Quarterly national-accounts series are lagged one
   quarter; monthly series are treated as available at the quarter origin. The official
   C-05/C-06 vintage logic is not reproduced.
7. **No 2026 forecast.** The window stops at 2026Q1 because the H=2 target is unknown
   after that. Nothing here should be read as a recession probability for 2026Q4.

## Reproduce

```bash
.venv/bin/python experiments/usa_first_models.py
```

Writes to `outputs/exploratory/usa_first/` (git-ignored, like other generated artefacts):

| File | Contents |
|---|---|
| `headline.csv` / `headline.md` | headline metrics, rule decision, fold tables |
| `pooled_metrics.csv` | pooled metrics for all six models plus the ensemble |
| `fold_metrics.csv` | per-fold metrics and locked thresholds |
| `model_selection.csv` | inner-validation ranking and top-3 membership |
| `predictions.csv` | quarter-level probabilities and thresholded flags |
| `episodes.csv` | episode detection and lead |
| `ensemble_bootstrap.csv` | bootstrap delta draws |
| `run_metadata.json` | seed, folds, feature count, provenance note |

Runtime is about 7–8 minutes on this machine.

The same numbers are rendered in `dashboard/index.html` (`make dashboard`). The dashboard
page is a view only: it reads the CSVs and never writes labels, predictions or folds.

## What would replace this

The official result needs Arshiya's `dataset.parquet`/`folds.json` and Palchhin's model
code. When they arrive, rerun under C-13 and replace this note with the official result;
keep this file only as a record of why an interim run was necessary.
