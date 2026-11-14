# Part 3 — Modelling Handoff

## Completed implementation

- Six model interfaces: Logistic Regression, Elastic Net, Random Forest, XGBoost, SVM and MLP.
- Train-only preprocessing, scaling and feature selection.
- Expanding-window validation with horizon-based purging.
- Basic nested walk-forward evaluation and top-three ensemble utilities.
- REWI and feature-stability reporting.
- Automated tests and synthetic model demonstration.

## Reproduction commands

Run from the repository root:

```bash
python -m pytest -q --disable-warnings
python scripts/demo_models.py
```

The demonstration uses synthetic data, not real USA out-of-sample predictions.

## Verification

- Local automated tests completed without failures.
- GitHub Actions checks passed for the modelling PR.
- Raw FRED integration tests are skipped when the external snapshot is missing.

## Integration requirements

Final USA headline and episode results require the approved feature matrix, feature
dictionary, frozen fold definitions and full tuning configuration.

## Validation rules

- Expanding-window walk-forward validation only.
- Purge training observations whose target windows overlap validation/test periods.
- Fit imputation, scaling and feature selection using training data only.
- Apply publication-availability rules before splitting.
- Use training-fold coefficients without intercept for REWI.

## Known gaps

- Full 24-trial hyperparameter tuning has not been verified.
- Official USA headline and episode reports are not yet generated.
- Ablation and robustness experiments are not yet complete.
- End-to-end `make run` reproduction is not yet verified.

## GitHub

Repository: https://github.com/sathvikboina/recession-ews

Modelling PR #3: https://github.com/sathvikboina/recession-ews/pull/3

Finalization PR #4: https://github.com/sathvikboina/recession-ews/pull/4
