# Lane Brief 3 — Models, Pre-Registered Ensemble and Experiments

**Owner:** Palchhin
**Role:** Modelling lead
**Lane:** Part 3 of the one-week sprint
**Dates:** Days 1–5 individual; Days 6–7 shared merge and review
**Branch:** `feat/models-ensemble`

---

## 1. Your mission in one paragraph

Run six single models, the baselines and the **one pre-registered ensemble** on the same
folds, then report what actually happens — positive or negative. The first model result is
**USA-first**. Japan and Germany join only if their labels pass and time allows. You own
the model results and the caveats, and you must not change the ensemble rule after seeing
scores.

## 2. What has already happened (so you do not repeat it)

- **The USA label is frozen as `labels-v3`.** It covers 1990Q1–2026Q3 (147 quarters), matches
  4/4 NBER recessions and has zero false episodes. It is the target, not an input.
- **The ensemble is already pre-registered.** On 2026-11-05 the project fixed an
  equal-weight probability average of the top-3 single models by inner-fold pooled PR-AUC.
  It must beat the inner-fold-selected best single model by at least **0.01 absolute pooled
  PR-AUC**, with a paired-bootstrap 95% interval excluding zero and no episode-recall loss.
  If it fails, the best single model is primary and the ensemble is a reported negative
  result. A logistic stack is exploratory only. See `docs/PROPOSAL_ADDENDUM.md` and C-13.
- **No model exists yet.** There is no feature table, no fold file and no out-of-sample
  score. This lane starts from a fixture and moves to real folds when Part 2 hands them over.
- **The optional packages are not installed yet.** `make check` warns that `sklearn`,
  `xgboost` and `shap` are missing. Install them early. If a package was already installed,
  the warning disappears and the count changes.
- **The rules that matter are fixed.** Walk-forward only; every scaler, selector, model
  parameter, weight and threshold is fitted inside the training fold; the test block is
  untouched; the threshold is locked before the test block.
- **The label is not a feature.** Never use `R`, the factor, the level, diffusion or a
  turning-point flag as a predictor. NBER is a validation chronology, not a feature.
- **There is no forecasting claim yet.** Until your out-of-sample result exists, the project
  says "we built and validated a recession label", not "we predict recessions".

**Read first:** `docs/PROPOSAL_ADDENDUM.md`, `docs/BUILD_CONTRACT.md` (C-08, C-09, C-10,
C-13), `docs/DECISIONS.md` (D-R11, D-R14, D-R19–D-R21, D-R29), `docs/LABEL_VALIDATION.md`.

## 3. What you own: Days 1–5

| Day | Task | Output | Done when |
|---|---|---|---|
| 1 | Build one model interface for logistic, elastic net, random forest, XGBoost, SVM and MLP; freeze the tuning budget, class weights and MLP seed rule | Model code skeleton | Every available model accepts the same table and fold object; budget and seed rule written down |
| 2 | Run six singles and baselines on a fixture fold; check shapes, probabilities and in-fold preprocessing | Results table v0 | All available models run; fixture leakage checks pass; missing packages named honestly |
| 3 | Implement REWI and inner-fold tuning on Part 2's draft folds; use training-fold coefficients only; exclude the intercept | REWI results and stability table | No full-sample weights; stability table produced |
| 4 | Implement the C-13 ensemble and run the **USA headline** on Part 2's Day 4 final folds | Ensemble code, `headline.md`, `episodes.md`, `make run` target | Rule matches `docs/PROPOSAL_ADDENDUM.md` exactly; every row has metadata |
| 5 | Rerun on the frozen folds if they differ from Day 4; run ablations and robustness; write the results note; add JPN/DEU only if labels land; report a negative ensemble honestly | `ablations.md`, `robustness.md`, `docs/EXPERIMENTS.md` | Claims match out-of-sample numbers; negative result kept; JPN/DEU only if labels landed |

### Suggested daily rhythm

- **09:30 — 15-minute stand-up.** What you finished, what is next, what is blocking you.
- **Small commits.** One logical change at a time; run the fixture after each change.
- **17:30 — short hand-off note.** What changed, what is reproducible, what is open.
- **Day 6:** merge your own branch and reproduce the USA headline. **Day 7:** review
  docs/India and audit the result tables.

## 4. What we expect by Day 5

A complete Part 3 hand-off contains:

1. **Model interface.** Logistic, elastic net, random forest, XGBoost, SVM and MLP behind
   one interface. If a package is unavailable, the installed subset is named; no model is
   faked.
2. **Frozen budget.** Tuning budget, class weights and MLP seed rule fixed before scoring.
3. **USA headline.** `outputs/results/headline.md` with pooled PR-AUC, episode tables,
   false-warning counts and the ensemble decision.
4. **Episode table.** `outputs/results/episodes.md` with episode-level recall and the
   quarters that drive it.
5. **REWI and stability.** Training-fold coefficients only, intercept excluded, selected
   features and stability reported.
6. **Ablations and robustness.** Track 1 categories; Track 2 I/II/III; COVID with and
   without 2020. A negative ensemble is reported with the same prominence as a positive one.
7. **Result metadata.** Every row records data version, features, folds, parameters,
   threshold, seed and the exact command.
8. **`make run` target.** A clean clone can reproduce the USA headline from a seed.
9. **A PR on `feat/models-ensemble`** with commands, tests, hashes and known gaps.

### How your lane is judged

- **Model gate:** every model uses the same folds and features; the threshold is locked
  before the test block; the ensemble rule is applied exactly once.
- **No leakage:** preprocessing, selection, tuning and thresholds are fitted inside the
  training fold.
- **Honesty:** a negative result is a result. Missing packages and failed models are named.
- **Reproducibility:** the USA headline reproduces from a clean clone and a seed.
- **Claim discipline:** no forecast claim the out-of-sample numbers do not support.

## 5. How your work combines with the others

| Hand-off | When | What must be true |
|---|---|---|
| H1: Sathvik → all | Day 1 morning | You can state your Day 1 task from this brief and `docs/TEAM_PLAN.md` |
| H2: Arshiya → you | Day 3 end | Draft folds with the same keys/horizons; you can run a first real pass |
| H4: Arshiya → you + Sathvik | Day 4 end (final folds); Day 5 end (frozen) | The USA headline runs on the Day 4 folds; rerun if the frozen files differ |
| H5: you → Sathvik | Day 5 end | USA headline, episode, ablation and ensemble tables; C-13 applied once |
| H6: all → Sathvik + Arshiya | Day 6 morning | One branch, green checks, short hand-off note |
| Day 6 merge | Step 3 | You merge `feat/models-ensemble`; the team reproduces the USA headline |
| Day 7 review | Step 1 | You review docs/India; Sathvik reviews your model lane |

Your results are the first real test of whether the predictors help. They feed Part 4's
story and the final go/no-go. If the ensemble fails, that is a finding, not a failure of the
week.

## 6. DOs

- **DO** install the full development environment before Day 3; do not wait until the
  headline run.
- **DO** freeze the tuning budget, class weights and MLP seed rule before scoring.
- **DO** use the same folds and features for every model and for the ensemble.
- **DO** fit every scaler, selector, parameter, weight and threshold inside the training fold.
- **DO** lock the threshold before the test block.
- **DO** record metadata for every result row: data version, features, folds, parameters,
  threshold, seed and command.
- **DO** report the USA result first; add JPN/DEU only if their labels land.
- **DO** report a negative ensemble honestly and keep the single model as primary.
- **DO** add the `make run` target and test it from a clean clone.
- **DO** ask Arshiya for fold semantics and Sathvik for claim wording.

## 7. DON'Ts

- **DON'T** change the ensemble rule, the top-3 selection, the weights or the beat-the-best
  test after seeing scores.
- **DON'T** tune on the test block or use future data.
- **DON'T** fit preprocessing, feature selection or the threshold outside the training fold.
- **DON'T** use the label, NBER chronology or a BEAI-derived output as a feature.
- **DON'T** drop a model silently or fake a result when a package is missing.
- **DON'T** overclaim: a good PR-AUC is not a forecasting system.
- **DON'T** hand-edit a result table to improve the story.
- **DON'T** merge a red branch or change a fold boundary without agreement.

## 8. Allowed creative liberty and educational freedom

Inside the guardrails, you have real room to explore:

- **Choose your implementations.** Different libraries or wrappers are fine as long as the
  interface, folds and metadata contract stay the same.
- **Choose a sensible tuning grid** inside the frozen budget. Record it before scoring.
- **Add useful extras.** PR curves, calibration plots, a confusion matrix, an episode
  timeline, a short notebook, or a "what I learned about leakage" note are welcome.
- **Try a simpler model** or a diagnostic baseline; label it clearly and keep it out of the
  pre-registered ensemble.
- **Propose an exploratory model** before results if you think it is worth testing. It must
  be clearly marked exploratory and must not replace the pre-registered comparison.
- **Learn while you work.** You may spend up to about half a day (roughly 10% of the lane)
  on XGBoost, calibration, PR-AUC or reproducibility. Note it in your hand-off.
- **Write a "what I learned" section** in the results note.

## 9. If you get stuck

1. **A package is missing?** Install it early; if it still fails, name the missing model and
   run the installed subset. Do not fake it.
2. **Folds are unclear?** Ask Arshiya for the exact keys and boundaries. Do not invent a
   second fold scheme.
3. **The ensemble fails?** Report the single model as primary and the ensemble as a negative
   result. That is an acceptable outcome.
4. **A score looks too good?** Check for leakage before celebrating. Run the firewall tests.
5. **Blocked for more than half a day?** Say so at the stand-up. Do not hide it until Day 5.

## 10. Where to look

| Need | File |
|---|---|
| Ensemble rule and claim wording | `docs/PROPOSAL_ADDENDUM.md` |
| Frozen model/validation rules | `docs/BUILD_CONTRACT.md` (C-08, C-09, C-10, C-13) |
| Decisions and rationale | `docs/DECISIONS.md` |
| Label evidence | `docs/LABEL_VALIDATION.md` |
| Feature table and folds | `data/clean/dataset.parquet`, `outputs/folds/folds.json` |
| USA label | `outputs/labels/USA_labels.csv` |
| Team plan | `docs/TEAM_PLAN.md`, `Team_Plan.xlsx` |
| Weekly log | `EWS_Work_Log.xlsx` |

---

**Bottom line:** run the pre-registered comparison exactly once, on the same folds, with
the threshold locked. Report the USA result honestly, including a negative ensemble. A
clear negative result is worth more than a tuned number that cannot be defended.
