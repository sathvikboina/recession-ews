# Report Evidence Map

Every number in report/main.tex traces to a file in this repository.

| Number / Claim | Source file | Key |
|---|---|---|
| Panel 267 rows x 27 columns | docs/LABEL_VALIDATION.md | §1 Data |
| Reporting window 1990Q1–2026Q3 | config/scope.yaml, docs/BUILD_CONTRACT.md | WINDOW |
| 147 label-ready quarters | docs/LABEL_VALIDATION.md, outputs/labels/USA_labels.csv | row count |
| 8 core indicators | docs/LABEL_VALIDATION.md §1 | table |
| Label SHA-256 2379fd53…19daa | outputs/labels/USA_labels.csv (git blob) | verified |
| D-R37: 80 init quarters | outputs/folds/folds.json metadata | initial_train_quarters |
| D-R37: 40 inner quarters | outputs/folds/folds.json metadata | inner_train_quarters |
| D-R37: step 1 | outputs/folds/folds.json metadata | step_quarters |
| D-R37: first scored 2010Q1 | outputs/folds/folds.json metadata | first_scored_quarter |
| Prevalence ~3.6% | outputs/results/baselines.csv | n_positives/n_test_obs |
| 149 feature columns | docs/LANE2A_RESULT.md, docs/FEATURES.md | column count |
| 1Q majority PR-AUC 0.0154 | outputs/results/baselines.csv | row 1Q/majority |
| 1Q term_spread PR-AUC 0.1111 | outputs/results/baselines.csv | row 1Q/term_spread |
| 1Q logistic PR-AUC 0.0476 | outputs/results/baselines.csv | row 1Q/plain_logistic |
| 2Q majority PR-AUC 0.0236 | outputs/results/baselines.csv | row 2Q/majority |
| 2Q term_spread PR-AUC 0.1556 | outputs/results/baselines.csv | row 2Q/term_spread |
| 2Q logistic PR-AUC 0.1080 | outputs/results/baselines.csv | row 2Q/plain_logistic |
| 4Q majority PR-AUC 0.0410 | outputs/results/baselines.csv | row 4Q/majority |
| 4Q term_spread PR-AUC 0.1768 | outputs/results/baselines.csv | row 4Q/term_spread |
| 4Q logistic PR-AUC 0.1973 | outputs/results/baselines.csv | row 4Q/plain_logistic |
| MLP 2Q PR-AUC 0.0528 | report/figures/loss_curve.csv + this run | trained epoch 300 |
| MLP final train loss 0.003645 | report/figures/loss_curve.csv | epoch 300 |
| MLP final val loss 0.221028 | report/figures/loss_curve.csv | epoch 300 |
| 4 NBER recessions matched | outputs/results/USA_vs_NBER.md | episode match |
| Zero false episodes | outputs/labels/USA_episodes.csv, docs/LABEL_VALIDATION.md | |
| Japan 144 quarters D-R34 | docs/LABEL_VALIDATION_JPN.md, docs/DECISIONS.md | D-R34 |
| Japan label hash 3b74d3e6… | docs/LABEL_VALIDATION_JPN.md | |
| Germany 5/8 indicators | docs/COVERAGE_DEU.md | coverage table |
| Germany GFCF Q-02 | docs/COVERAGE_DEU.md, docs/DECISIONS.md | Q-02 |

## Items not run in this study
- MLP at 1Q and 4Q horizons
- Full vs beai_copy_* only ablation
- With vs without term-spread ablation (partial evidence from comparison)
- Pre-registered ensemble (Lane 3 official run pending)
