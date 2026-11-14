# Baseline Results on the Frozen Folds

- Seed: `42`
- Decision threshold: `0.50` (fixed; no threshold search on test)
- Term-spread predictor: `FIN_SLOPE__level` (10Y minus 3M)
- Imputation and scaling: fitted inside each outer training block only
- Folds: `outputs/folds/folds.json` (D-R37), via `ews.harness.fold_index_splits`

| Horizon | Baseline | Pooled PR-AUC | ROC-AUC | Episode recall | Accuracy | Brier | N test |
|---|---|---:|---:|---:|---:|---:|---:|
| 1Q | `majority` | 0.0154 | 0.0154 | 0.0000 | 0.9848 | 0.0153 | 66 |
| 1Q | `term_spread` | 0.1111 | 0.8769 | 0.0000 | 0.9697 | 0.0246 | 66 |
| 1Q | `plain_logistic` | 0.0476 | 0.6923 | 0.0000 | 0.9697 | 0.0328 | 66 |
| 2Q **(primary)** | `majority` | 0.0236 | 0.0159 | 0.0000 | 0.9692 | 0.0309 | 65 |
| 2Q **(primary)** | `term_spread` | 0.1556 | 0.8730 | 0.0000 | 0.9077 | 0.0639 | 65 |
| 2Q **(primary)** | `plain_logistic` | 0.1080 | 0.8095 | 0.0000 | 0.9385 | 0.0553 | 65 |
| 4Q | `majority` | 0.0410 | 0.0169 | 0.0000 | 0.9365 | 0.0629 | 63 |
| 4Q | `term_spread` | 0.1768 | 0.8093 | 1.0000 | 0.8254 | 0.1320 | 63 |
| 4Q | `plain_logistic` | 0.1973 | 0.8390 | 0.0000 | 0.8889 | 0.0931 | 63 |

Episode recall counts in-window peaks detected by a warning in the preceding `H` quarters. It is a baseline diagnostic, not the official C-13 episode-recall guardrail.

These are baselines only. The official model comparison and the C-13 ensemble verdict belong to Lane 3.
