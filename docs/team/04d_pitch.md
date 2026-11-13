# Plain-English Pitch — One Page

## What we built

We built and validated a **recession label** for the United States: a dated indicator of
when the economy was in recession from **1990Q1 to 2026Q3** (147 quarters). The label uses
eight measures of activity — GDP, industrial production, employment, hours, income,
consumption, retail sales and business investment — combined with a dynamic factor model
and the Bry–Boschan dating rules.

We also checked whether India could support the same label. It cannot, on the official
data available now.

## What the label proves

- It matches **all four NBER recessions** in the window: 1990, 2001, 2007–09 and 2020.
- It creates **no false recession episodes**.
- At the quarter level: accuracy **0.993**, precision **0.929**, recall **1.000**, F1
  **0.963**.
- The dates are stable: at most a one-quarter boundary shift from the NBER dates.
- The result is reproducible: `labels-v3` is frozen, `labels-v1` and `labels-v2` are
  archived byte-identically, and the hashes are recorded.

## What it does not prove

**It does not prove that we can forecast a recession.**

The label is an **ex-post chronology**. It is built after the fact from data that would
not all have been available in real time. No feature table, no walk-forward model and no
out-of-sample score exist yet. We have not shown that a model can warn of a recession
before it starts.

The model work is pre-registered: six single models, a fixed walk-forward protocol, and
one equal-weight top-3 ensemble tested against the best single model. The rule requires a
≥0.01 PR-AUC gain, a bootstrap interval excluding zero, and no loss of episode recall. If
it fails, the single model is primary and the negative result is reported.

## India

India is a **coverage case study, not a fourth label country**. The official sources pass
only **1 of 8** indicators:

- industrial production: 130/147 quarters (88.4%) — passes;
- quarterly GDP, consumption and investment: only 2011Q2–2026Q2 (61/147, 41.5%) — fail;
- quarterly employment: 2018Q2–2026Q3 (33/147, 22.4%) — fails;
- hours, household income and retail: no official series found — fail;
- investment has no quarterly business/non-residential split — fails under Q-02.

The 6-of-8 gate is not relaxed, no proxy is substituted, and India stays Label-B-only under
O-2.

## What is next

1. Finish the Japan and Germany label work, or record the gate failure.
2. Build the USA feature table and the frozen walk-forward folds.
3. Run the six single models and apply the pre-registered ensemble once.
4. Report the first honest out-of-sample result — positive or negative.
5. Package nothing until the team explicitly approves it.

**Bottom line:** we have a trustworthy recession chronology, not a forecasting product.
The next result will be judged by the pre-registered rules, not by a better story.
