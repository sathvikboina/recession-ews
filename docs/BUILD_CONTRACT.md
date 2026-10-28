# Build Contract

Runtime rules for the implementation. This is the page the code and any AI session
should read instead of the 72 KB `spec.py`. Each rule has an ID; cite the ID in code
comments, tests and commit messages. Section references (§n) point to `plan_ML.docx`.

Status: **frozen 2026-10-29** for rules marked ✅. Rules marked ⏳ still need a human
decision; do not hard-code a choice for them.

---

## C-01 — Two pipelines, one firewall ✅

- Pipeline **A** builds the label. It may use **only** the eight §11 core indicators:
  `ACT_GDP_REAL, ACT_IP, ACT_EMP, ACT_HOURS, ACT_RINC, ACT_CONS, ACT_RETAIL, ACT_INV`.
- Pipeline **B** builds predictors. It may use anything at P0–P1 (later P2) in
  `data/scope.csv` **except** `beai_eligible = Y` rows, which get a separate,
  independent copy with their own transform and lag.
- Unemployment is **not** a BEAI input (Q-01). `LAB_UNEMP.beai_eligible = N`.
- No fitted object is shared between A and B: no scaler, no DFM loading, no factor,
  no threshold.
- BEAI outputs (Fₜ, Rₜ, turning-point flags, diffusion) are **not** predictors (§31).

Enforced by: `tests/test_config.py`, `tests/test_scope.py`, `scripts/00_env.py`.

## C-02 — Label A: BEAI ✅

Per country, independently (never pooled):

1. Take the core indicators that pass coverage (C-03).
2. Convert to an activity-oriented change `gᵢ,ₜ`:
   - level/index/flow series → `Δlog(X)`; rate series (unemployment, if ever added) → first difference;
   - multiply by `−1` where a rise means weaker activity, so **+ = stronger activity**.
3. Standardise within country (training-free at this stage; this is label construction on the final revised series).
4. Estimate a **one-factor** dynamic factor model on the aligned `gᵢ,ₜ`, EM/Kalman for missing cells.
   `statsmodels.tsa.statespace.DynamicFactorMQ` is the reference implementation.
   Use the **smoothed** factor: Pipeline A is ex-post and applies no availability lag (C-05).
5. **Cumulate the factor to a level index** `Fₜ` (log-level). Turning points are dated on `Fₜ`,
   never on growth rates (§12–13).
   The factor is identified with unit variance, so the common component of series `j` is
   `σⱼ·|λⱼ|·fₜ`, not `σⱼ·fₜ`. Convert with `scale = mean(σⱼ·|λⱼ|)` before cumulating; using
   `mean(σⱼ)` overstates the common component by roughly `1/|λ|` (about 3× in the US sample)
   and manufactures long pseudo-recessions.
6. Run BBQ on `Fₜ` with the frozen parameters below.
7. Candidate peak→trough episodes are contractions.
8. Compute episode diffusion `D̄ₑ` = mean over the episode of the share of available core
   indicators deteriorating. Keep the episode only if `D̄ₑ ≥ 0.50`.
9. `Rₜ = 1` for quarters inside a surviving contraction, else 0.
10. Depth is **reported**, not a gate. Flag episodes with depth < 0.10 SD for manual review.

**Estimation sample vs reporting window.** The factor is estimated on the longest
common sample available (US: 1960Q1–2025Q4) and dated turning points are reported for
1990Q1–2025Q4 only. Estimating on the reporting window alone censors the 1990Q3 peak at
the left endpoint. This changes the estimation sample, not the study window (D-R22).

Frozen parameters:

| Parameter | Value | Source |
|---|---|---|
| min phase | 2 quarters | §13, BBQ default |
| min cycle | 5 quarters | §13, BBQ default |
| endpoint censoring | no turning point in last 2 quarters | §13 |
| peak/trough symmetry | symmetric | §13 |
| factor count | 1 | §12 |
| factor estimator | DynamicFactorMQ, factor_orders=1, idiosyncratic_ar1=True | §12 |
| factor smoother | smoothed (ex-post label) | C-05 |
| estimation sample | 1960Q1–2025Q4 (USA) | D-R22 |
| minimum data to date a quarter | 4 of 8 core indicators | §18 |
| diffusion gate | 0.50 | §15 |
| robustness diffusion | 0.60 (Tier-1 only, one re-run) | §15, §58 |
| robustness min phase | 3 quarters (Tier-1 only) | §58 |

## C-03 — Coverage and eligibility ✅

Target window `1990Q1–2025Q4` = **144 quarters**. 70% = 100.8 → **≥101 quarters**.

- A quarter is dated only if **≥4** core indicators are available (§18).
- A country is BEAI-eligible only with **≥6 of 8** core indicators, each covering **≥70%**
  of the window (§19).
- No relaxation for India or China (Q-06). A failure is a reported finding, not an exception.
- No interpolation and no forward-fill of macro series (Q-25). Missing stays missing.
- The 70% rule is extended to predictors (Q-25, flagged as an extension).

## C-04 — Labels B and C ✅

- **B (technical GDP):** two consecutive quarters of negative real GDP growth from
  `ACT_GDP_REAL`. No other input.
- **C (NBER):** external US chronology, robustness only.
- External chronologies (NBER, ESRI, Dua & Banerji, Euro Area) are **plausibility checks**.
  They are never targets, features, or training labels (FW-06).

## C-05 — Timing and availability lags ✅

Prediction origin: **quarter end + 6 weeks**. Features for quarter `t` may use only
observations dated in `t`; post-quarter-end days before the origin are not used in
primary features (Q-20).

| Data class | Lag applied to Pipeline B |
|---|---|
| quarterly national accounts | 1 quarter |
| monthly indicators | 6 weeks |
| financial / market | 0 |
| surveys / confidence | 4 weeks |
| quarterly non-national-accounts (BIS credit, BoP, household accounts, house prices) | 1 quarter |
| weekly claims, CPI-based REER | 6 weeks |
| annual (population, market cap/GDP) | 1 year, last published value carried forward |

Pipeline A applies **no** availability lag: it is an ex-post chronology.

## C-06 — Frequency conversion ✅

Monthly → quarterly: quarterly mean (primary), quarter-end value, intra-quarter change.
A quarter is missing if any constituent month is missing (no partial-quarter imputation).

- flow/index: mean, end value, intra-quarter change;
- market: mean and end value, intra-quarter change;
- weekly: mean by week-ending date, quarter-end value;
- daily: daily → monthly mean → quarterly mean, plus quarter-end value;
- annual: carry forward with the 1-year lag above; no temporal disaggregation.

## C-07 — Predictor transforms ✅

Per `form` in `config/indicators.yaml`:

| form | transforms |
|---|---|
| growth | QoQ and YoY growth; lags 1/2/4; rolling mean, volatility, trend |
| rate | level; 4Q change; lags; rolling statistics |
| ratio | level; 4Q and 8Q change; lags |
| spread | level; 4Q change; lags |
| survey | level; 4Q change; lags |
| price | YoY and QoQ log change; lags; rolling volatility |

- Never use raw country-size levels or a country ID as a feature (§29).
- Store **unscaled** features. Scaling happens inside the fold (C-08).

## C-08 — Validation ✅

- **Expanding-window walk-forward only.** No random split, no k-fold, no shuffle (§40).
- Initial training block and step size live in `config/` (default: 20 years initial, step 1Q).
- Inner tuning folds are **time-ordered** (expanding or blocked), never shuffled (§35, §41).
- Per fold: fit scaler → tune selector → select features → build REWI → tune model →
  choose threshold → **lock** → predict the untouched test block.
- `y(t,H) = 1` iff recession onset occurs in `t+1 … t+H`.
- Test observations never influence scaling, selection, tuning, or the threshold (§53).

## C-09 — Selection and models ✅

- Selector: Elastic Net logistic, tuned inside the fold; report whatever count it selects
  (target ≈10–15, not forced).
- REWI: `Σ β̂ᵢ zᵢ,ₜ`, intercept excluded, z from the training fold only; normalise with
  training-fold mean/sd.
- Models: Logistic, Elastic Net, Random Forest, XGBoost, SVM, MLP. Same time-ordered
  tuning budget and class weights for all.
- MLP: average over ≥3 seeds, early stopping.
- Baselines: majority, term-spread probit/logit, plain logistic.

## C-10 — Metrics ✅

- Primary: **PR-AUC**, computed on out-of-sample probabilities **pooled across folds**.
- Secondary: ROC-AUC, recall, precision, F1, accuracy, Brier, confusion matrix.
- Per fold: Brier, positive count, episode count. A fold with no positives is never scored
  on AUC/PR-AUC alone (§43).
- Episode level: detection rate over `[τ−H, τ−1]`, lead time `τ − t_first`, and
  **false-warning episodes** (a contiguous warning run = one episode), with the denominator stated.
- Report episode counts and an episode-level uncertainty interval; do not rank models on
  differences inside it (§50).

## C-11 — Cross-country 🔲

LOCO is a headline experiment only if: ≥6 eligible countries, ≥20 BEAI episodes, and no
country contributes >40% of episodes (§52). Otherwise it is exploratory and labelled as such.
Held-out country contributes nothing — not scaling, not selection, not tuning, not thresholds (§53).

## C-12 — Reproducibility ✅

Every run stores: data version, series IDs, transform list, feature list, fold boundaries,
model parameters, selected features, threshold, metrics, seed, and a manifest hash (§73).
Raw files are immutable; cleaned data is separate; no full-sample transforms are stored.

---

## Not frozen yet ⏳

These need your decision before the stage that uses them. Defaults shown are what the
scaffolding currently assumes.

| ID | Question | Current default | Needed by |
|---|---|---|---|
| O-1 | Use pre-1990 history for long-series countries? | no (1990–2025 only) | Step 6 |
| O-2 | If India fails §19, is it Label-B-only or dropped from case studies? | Label-B-only, reported | Step 8 |
| O-3 | Threshold objective: max F1, or max recall subject to precision ≥ p? | max F1 | Step 10 |
| O-4 | Widen scope from P0–P1 to P0–P2 (68 → 140 rows)? | P0–P1 first | Step 4 |
| O-5 | COVID 2020: keep ex-post, document BBQ treatment; include the with/without evaluation? | keep, document, evaluate | Step 11 |

## Definition of done per stage

| Stage | Done when |
|---|---|
| config | `make check` passes with 0 failures |
| collection | manifest rows = scope rows, raw files hashed |
| harmonisation | one row per series×quarter, coverage table produced |
| labels | US episodes match NBER 1990/2001/2008; `labels-v1` hash frozen |
| features | leakage test passes; `dataset.parquet` + `folds.json` written |
| harness | one country × one horizon × six models reproducible from a seed |
| experiments | headline table + episode table reproducible via `make run` |
