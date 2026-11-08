# Proposal Addendum: Pre-Registered Ensemble and Claim Wording

Status: **pre-registered 2026-11-05, before any model was trained or scored.**
This addendum supplements `plan_ML.docx`; it does not amend the canonical
proposal. The eight-indicator label, the firewall, the DFM/BBQ parameters and the
walk-forward protocol in `docs/BUILD_CONTRACT.md` are unchanged.

The purpose is to stop two review problems before they happen:

1. an ensemble added after seeing model scores, and
2. a forecasting claim made before a model has been evaluated.

## 1. Planned ensemble variant

### 1.1 What is pre-committed

The ensemble is a **planned variant**, not an opportunistic addition. It is
defined now, before any single-model or ensemble result exists. The confirmatory
variant is:

> **Equal-weight probability average of the top-3 single-model configurations,
> where the top-3 are ranked by pooled PR-AUC on the inner, time-ordered
> validation folds of the current outer training block.**

The three members are selected inside each outer training block. They are not
selected from the outer test block. The same outer folds, the same feature
pipeline, the same scaling and the same threshold-locking rule are used for the
ensemble and for every single model.

A logistic stack of the six single models is allowed only as a **secondary,
exploratory** variant. It uses non-negative weights fitted on inner-fold
out-of-fold predictions. It is reported separately and never replaces the primary
confirmatory ensemble.

### 1.2 The "must beat the best single model" test

The headline comparison is:

- **Primary metric:** pooled out-of-sample PR-AUC over the same walk-forward
  folds.
- **Comparator:** the best single model chosen by **inner-fold** pooled PR-AUC,
  not by its test score.
- **Margin:** the ensemble must improve pooled PR-AUC by **at least 0.01
  absolute (one percentage point)** over that comparator.
- **Uncertainty:** a paired bootstrap over outer folds (1,000 resamples) must give
  a 95% interval that excludes zero. A point estimate above 0.01 with an interval
  that includes zero is **not** an ensemble gain.
- **Guardrail:** the ensemble must not reduce episode-level recall or the number
  of detected recessions relative to the comparator. If it does, the single model
  remains primary regardless of PR-AUC.

If the ensemble does not clear all three conditions, the best single model is the
headline model and the ensemble is reported as a **negative result**. It is not
quietly dropped, and the rule is not changed after seeing the scores.

### 1.3 Leakage rules

The following are binding for the ensemble exactly as for a single model:

- Every scaler, feature selector, model parameter, ensemble member, weight and
  threshold is fitted **inside the outer training block**.
- Inner tuning folds are time-ordered. No random split, no shuffle, no k-fold.
- The outer test block is untouched until the ensemble is locked.
- No BEAI factor, turning-point flag, diffusion value or label is a feature
  (C-01, §31).
- NBER and other external chronologies are never targets or features.
- A held-out country contributes nothing: no scaling, selection, tuning, weight
  or threshold.
- The ensemble uses the **same folds and the same feature matrix** as the single
  models. A different fold boundary is a different experiment.
- No post-hoc member selection, weight tuning or threshold adjustment after the
  test scores are seen.

### 1.4 Reporting

Every experiment table must show:

| Item | Required |
|---|---|
| Single models | all six, same folds, same tuning budget |
| Best single | named, with the inner-fold selection rule |
| Primary ensemble | equal-weight top-3, with the selected members per fold |
| Secondary stack | exploratory only, clearly labelled |
| Δ PR-AUC | ensemble minus best single, with 95% bootstrap interval |
| Episode metrics | detection rate, lead time, false-warning episodes |
| Negative result | reported with the same prominence as a positive one |

The ensemble is one row in the headline table, not a separate paper.

## 2. Claim wording

### 2.1 Until a model is run

Use:

- "We built and validated a recession label from eight activity measures."
- "The USA label reproduces the NBER chronology in the study window."
- "The label is the target for a later, leakage-controlled predictive evaluation."
- "No predictive model has been trained or scored yet."

Do **not** use:

- "We predict recessions."
- "The system forecasts recession onset."
- "Early-warning performance" before out-of-sample scores exist.
- "Machine-learning framework for predicting..." in the present tense.

The project name may keep "early-warning" as a label, but the current deliverable
is the label and its validation, not a warning system.

### 2.2 After a model is run

A predictive claim is allowed only with:

- pooled out-of-sample results from the frozen walk-forward protocol;
- the horizon stated (1Q, 2Q, 4Q; 2Q primary);
- the country and sample stated;
- episode counts and uncertainty reported;
- the revised-data caveat stated;
- the ensemble decision reported under the rule above.

## 3. Persistent design choices

These are deliberately retained from the current build:

- **Label first.** The label is built from the eight §11 activity measures before
  any predictor or model work. Predictors stay in a separate pipeline.
- **Leakage discipline.** Expanding-window walk-forward, choices inside each
  fold, threshold locked before the test block, held-out-country rule.
- **Frozen artefacts.** `labels-v1` and `labels-v2` are archived byte-identically;
  `labels-v3` is the active 1990Q1–2026Q3 label with recorded hashes; the test suite
  protects all three versions.
- **Honest caveats.** Revised historical data, four US episodes, no claim of
  methodological novelty, and no country result before its label is audited.
- **Pre-committed decision log.** Decisions are recorded when made
  (`decisions_log.csv`, `docs/DECISIONS.md`). The review noted "D-R01 to D-R25";
  the log has since grown to D-R31, which is the intended behaviour.

## 4. Sign-off

| Item | Decision | Date | Owner |
|---|---|---|---|
| Primary ensemble definition | equal-weight top-3, inner-fold selection | 2026-11-05 | Project lead |
| Beat-the-best test | ≥0.01 pooled PR-AUC, bootstrap CI excludes 0, no episode-recall loss | 2026-11-05 | Project lead |
| Secondary stack | exploratory only | 2026-11-05 | Project lead |
| Wording before model results | label validation, not forecasting | 2026-11-05 | Project lead |

This file must not be edited after the first model result without a new dated
version and an explicit note explaining what changed and why. The commit that
introduces this addendum is the pre-registration timestamp.
