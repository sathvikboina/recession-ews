# Baseline Model Evaluation Results

- **Seed**: 42
- **Evaluation**: Pooled out-of-sample predictions across untouched test blocks (D-R37 frozen folds)
- **Primary Operating Point (Headline)**: Training-fold positive prevalence (fixed prevalence rule, recomputed per fold from y_train only, never tuned)
- **Secondary Operating Point**: 0.50 fixed threshold
- **Term Spread Column**: `FIN_SLOPE__level`
- **Standardisation / Imputation**: Fitted strictly inside each training fold

| Horizon | Baseline Model | PR-AUC | ROC-AUC | Episode Recall (Prevalence Rule) | Episode Recall (0.50) | Accuracy (Prev) | Brier Score | N Test Obs |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1Q | `majority` | 0.0154 | 0.0154 | 1.0000 | 0.0000 | 0.0152 | 0.0153 | 66 |
| 1Q | `term_spread` | 0.1111 | 0.8769 | 1.0000 | 0.0000 | 0.5606 | 0.0246 | 66 |
| 1Q | `plain_logistic` | 0.0476 | 0.6923 | 0.0000 | 0.0000 | 0.8788 | 0.0328 | 66 |
| 2Q (primary) | `majority` | 0.0236 | 0.0159 | 1.0000 | 0.0000 | 0.0308 | 0.0309 | 65 |
| 2Q (primary) | `term_spread` | 0.1556 | 0.8730 | 1.0000 | 0.0000 | 0.6308 | 0.0639 | 65 |
| 2Q (primary) | `plain_logistic` | 0.1080 | 0.8095 | 0.0000 | 0.0000 | 0.8769 | 0.0553 | 65 |
| 4Q | `majority` | 0.0410 | 0.0169 | 1.0000 | 0.0000 | 0.0635 | 0.0629 | 63 |
| 4Q | `term_spread` | 0.1768 | 0.8093 | 1.0000 | 1.0000 | 0.6825 | 0.1320 | 63 |
| 4Q | `plain_logistic` | 0.1973 | 0.8390 | 0.0000 | 0.0000 | 0.8413 | 0.0931 | 63 |
