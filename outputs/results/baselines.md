# Baseline Model Evaluation Results

- **Seed**: 42
- **Evaluation**: Pooled out-of-sample predictions across untouched test blocks
- **Decision Threshold**: 0.50 (fixed, no threshold tuning)
- **Term Spread Column**: `term_spread_10y_3m`
- **Standardisation / Imputation**: Fitted strictly inside each training fold

| Horizon | Baseline Model | Pooled PR-AUC | ROC-AUC | Episode Recall (Test) | Accuracy | Brier Score | N Test Obs |
|---|---|---:|---:|---:|---:|---:|---:|
| 1Q | `majority` | 0.0200 | 0.1667 | 0.0000 | 0.9767 | 0.0230 | 86 |
| 1Q | `term_spread` | 0.0871 | 0.8095 | 0.0000 | 0.9651 | 0.0331 | 86 |
| 1Q | `plain_logistic` | 0.0445 | 0.6131 | 0.0000 | 0.9535 | 0.0426 | 86 |
| 2Q (primary) | `majority` | 0.0359 | 0.0370 | 0.0000 | 0.9529 | 0.0457 | 85 |
| 2Q (primary) | `term_spread` | 0.1535 | 0.8395 | 0.0000 | 0.9059 | 0.0747 | 85 |
| 2Q (primary) | `plain_logistic` | 0.0879 | 0.6944 | 0.0000 | 0.9059 | 0.0695 | 85 |
| 4Q | `majority` | 0.0665 | 0.0267 | 0.0000 | 0.9036 | 0.0904 | 83 |
| 4Q | `term_spread` | 0.2529 | 0.8350 | 1.0000 | 0.8313 | 0.1303 | 83 |
| 4Q | `plain_logistic` | 0.2040 | 0.7733 | 0.0000 | 0.7831 | 0.1357 | 83 |
