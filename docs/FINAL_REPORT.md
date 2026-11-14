# Final Report — Cross-Country Recession Early Warning

> **STATUS: DRAFT — NOT A FINAL REPORT.**
> Stable sections (data, labels, features, folds, reproducibility) are complete.
> Every section marked **PENDING** waits on Lane 3 (official model run). The Lane 2A
> specification, firewall tests and baselines are integrated; their numbers are baseline
> context, not the official out-of-sample result. Do not present this document as a
> forecasting claim until §8 is filled and signed off.

| Field | Value |
|---|---|
| Document status | Draft for internal review |
| Date | 2026-11-14 |
| Integration tip | `feat/features-harness@57faa46` (Lane 2A integrated) |
| Authors | Sathvik Boina, Shravani Math, Palchhin |
| Lane 2A status | integrated: `docs/FEATURES.md`, `tests/test_feature_firewall.py`, baselines, D-R38 |
| Frozen label versions | USA `labels-v3`; JPN `labels-v1-JPN`; DEU no label (coverage finding) |
| Feature table | `data/clean/dataset.parquet` (generated) |
| Frozen folds | `outputs/folds/folds.json` (D-R37) |
| Official model result | **PENDING — Lane 3** |

---

## 1. Executive summary

This project builds a **recession chronology** from official activity data and a separate,
leakage-controlled **early-warning harness**. The chronology is complete and validated for
the United States and Japan; Germany is delivered as a coverage finding because it fails
the frozen 6-of-8 rule.

**What is established:**

- The USA label (`labels-v3`, 1990Q1–2026Q3, 147 quarters) matches all four NBER
  recessions in the window with no false episodes: quarter-level accuracy 0.993, precision
  0.929, recall 1.000, F1 0.963.
- The Japan label (`labels-v1-JPN`) matches 5 of 5 post-1994 ESRI episodes at episode level,
  with quarter-level recall 88.0% and precision 62.9%.
- India passes only 1 of 8 official indicators, so it is a **Label-B coverage case study**
  under O-2; the 6-of-8 gate is not relaxed.
- The USA predictor table is built and unscaled: 147 rows × 149 features, including 64
  separate `beai_copy_*` columns for the eight BEAI-eligible core series.
- The walk-forward folds are frozen: expanding window, 80 outer / 40 inner quarters, step
  1, horizons 1Q/2Q/4Q with 2Q primary, first scored quarter 2010Q1.

**What is not established:** whether the predictors forecast a recession out of sample.
There is no official model result yet. The only model run so far is exploratory, fails the
pre-registered C-13 ensemble test and is explicitly not the headline result.

**Bottom line:** a trustworthy recession chronology and a frozen evaluation protocol, not a
forecasting product. The next section that matters is §8, and it is empty on purpose.

---

## 2. Scope and claims

### 2.1 In scope

| Item | Decision |
|---|---|
| Label countries | USA, Japan; Germany only if the 6-of-8 gate passes |
| India | Label-B coverage case study, not a fourth label (O-2, D-R33) |
| First modelling country | USA (labels and panel already frozen) |
| Reporting window | 1990Q1–2026Q3, 147 quarters |
| Horizons | 1Q, 2Q, 4Q; 2Q primary |
| Evaluation | expanding-window walk-forward, time-ordered inner folds |

### 2.2 Claims this report does **not** make

- No claim of real-time forecasting skill. The data are revised history with **simulated**
  publication lags (D-R14); this is not a vintage study.
- No claim that the label is a real-time recession call. It is an ex-post chronology.
- No claim that India can support the main label.
- No claim that the ensemble helps before the official C-13 run.

---

## 3. Data and provenance

- **Sources and provenance:** `data/manifest.csv`, `data/series_resolution.csv`,
  `docs/SOURCE_MAP_JPN.md`, `docs/SOURCE_MAP_DEU.md`.
- **Raw data are not redistributed** (D-R15). The repository ships scripts and metadata; a
  clean clone fetches or supplies the approved raw snapshot.
- **FRED registry:** 30 entries = 27 downloads + 3 derived series.
- **Manifest:** 40 rows — 38 `VERIFIED`, 1 `LOW_COVERAGE` (`USA.ACT_CONS.M.US`), 1
  `PENDING_VERIFICATION` (`DEU.ACT_INV.Q.STD`).
- **Missing stays missing:** no interpolation, forward fill or partial-quarter imputation.
- **Availability:** C-05 lag classes are applied before any transform, so a predictor at
  quarter *t* uses only data published by the prediction origin.

| Country | Status | Note |
|---|---|---|
| USA | 25/25 series resolved | full 147-quarter label and predictor panel |
| Japan | 18/21 resolved, 3 pending | `labels-v1-JPN` covers 144 quarters (1990Q1–2025Q4) |
| Germany | 18/21 resolved, 3 pending | strict Q-02 leaves 5/8 → coverage finding, no label |
| India | 1/8 official series | Label-B only under O-2 |

---

## 4. Recession labels

### 4.1 USA — `labels-v3`

| NBER peak–trough | Label peak–trough | Peak diff | Trough diff | Diffusion |
|---|---|---:|---:|---:|
| 1990Q3–1991Q1 | 1990Q2–1991Q1 | −1 | 0 | 0.810 |
| 2001Q1–2001Q4 | 2001Q1–2001Q4 | 0 | 0 | 0.708 |
| 2007Q4–2009Q2 | 2007Q4–2009Q2 | 0 | 0 | 0.875 |
| 2019Q4–2020Q2 | 2019Q4–2020Q2 | 0 | 0 | 0.938 |

Quarter-level: 13 TP, 1 FP, 0 FN, 133 TN → accuracy **0.993**, precision **0.929**,
recall **1.000**, F1 **0.963**.

Frozen rules: DFM + BBQ + diffusion gate + eight core indicators, unchanged across v1–v3.
`labels-v1` and `labels-v2` are archived byte-identically. The only date change in v2 was
the 2009 trough (2009Q3 → 2009Q2); v3 extended the window to 2026Q3 without changing the
episodes.

Evidence: `docs/LABEL_VALIDATION.md`, `docs/DECISION_NOTE_Q02_Q04_Q05.md`,
`docs/REVIEW_2026-11-05.md`.

### 4.2 Japan — `labels-v1-JPN`

- 6 of 8 indicators pass; fiscal quarters re-labelled to calendar quarters.
- 5 of 5 post-1994 ESRI episodes matched at episode level.
- Quarter-level recall **88.0%**, precision **62.9%**.
- Window: 144 quarters, 1990Q1–2025Q4, recorded as a documented exception under **D-R38**.
  Cross-country work must align on 147 quarters or use the 144-quarter window explicitly;
  the frozen label is not rebuilt.

Evidence: `docs/LABEL_VALIDATION_JPN.md`, `docs/HANDOFF_JPN_DEU.md`.

### 4.3 Germany — coverage finding

- Strict Q-02 (business non-residential investment) leaves **5 of 8**; the gate fails.
- No German label is claimed. The deliverable is the coverage note.
- The 1990–1991 reunification break is documented and not spliced silently.

Evidence: `docs/COVERAGE_DEU.md`, `docs/SOURCE_MAP_DEU.md`, `docs/LABEL_VALIDATION_DEU.md`.

### 4.4 India — Label B only

- Official downloaded-data count: **1 of 8** (`ACT_IP`, 130/147 = 88.4%).
- Quarterly NAS covers 61/147 (41.5%), quarterly PLFS 33/147 (22.4%); no quarterly hours,
  household income or official monthly retail series.
- No proxy, no carry-forward, no relaxed threshold.

Evidence: `docs/INDIA_COVERAGE_AUDIT.md`, `data/india_core_coverage.csv`, D-R33.

---

## 5. Predictors and the feature table

The table is built by `src/ews/features.py` from the harmonised quarterly panel and written
by `make features`. It is **unscaled**; scaling belongs inside each training fold.

| Property | Value |
|---|---|
| Rows | 147 (1990Q1–2026Q3) |
| Features | 149 |
| Input series | 19 spec series + 1 derived (term spread) |
| BEAI-eligible copies | 8 series → 64 `beai_copy_*` columns |
| Excluded | 8 columns, listed in `EXCLUSIONS` |
| Hash | `368b60056872b9883ab8767fa148249d5f5c13ea85ca68abfc4e9437ee4304f4` |
| Rebuild | byte-identical |

**Firewall design.**

- No label output, NBER chronology, factor, `R`, level, diffusion, turning-point flag,
  country identifier or country-size level enters the table.
- The eight BEAI-eligible core series appear only as separate `beai_copy_*` predictors with
  their own transform and availability lag. No fitted object, scaler or factor loading is
  shared with Pipeline A.
- Availability lags (C-05) are applied before transforms; transforms come from
  `ews.models.feature_transforms` (C-07).
- Activity and price series enter as growth/change, not raw levels; rates keep a
  dimensionless `__level`.

**Written specification and firewall.** `docs/FEATURES.md` is the authority on what a legal
predictor is; it lists the 20 input series, the 149 columns, the availability ladder and the
exclusion blacklist. `tests/test_feature_firewall.py` checks the table independently:

- schema: 147 contiguous quarters, 149 columns;
- blacklist: no label, factor, chronology or identifier column, and the validator raises on
  an injected `R`, `factor` or `n_available`;
- unscaled: no standardised column and rate levels equal the source series;
- no future leakage: rebuilding on truncated history at 2000Q4, 2010Q2, 2019Q4 and 2024Q3
  leaves all past values identical;
- independence: all 64 `beai_copy_*` columns are reproducible from the harmonised panel
  alone with no fitted object stored;
- mutation: a one-quarter future shift and injected forbidden columns are both caught.

`scripts/08_verify_lane2a.py` runs eight gates (labels, table, panel, folds, firewall,
baselines, JPN closeout, untouched labels) and all pass.

---

## 6. Walk-forward protocol and folds

Frozen under **D-R37**. The generator is `ews.models.folds`; `make folds` serialises it.

| Property | Value |
|---|---|
| Method | expanding window, time-ordered |
| Window | 1990Q1–2026Q3 |
| Step | 1 quarter |
| Horizons | 1Q, 2Q, 4Q; **2Q primary** |
| Initial outer training | 80 quarters (20 years) |
| Initial inner validation | 40 quarters (10 years) |
| Purge | equals the horizon before every test/validation block |
| First scored quarter | 2010Q1 |
| Outer folds | 67 per horizon |
| Hash | `afd51bc5f885f74a84f2e5f29bd6732de78454945cb189f2fee1d8c426afc261` |

Rules enforced by `ews.harness.validate_payload` and the fold tests:

- no test row ever appears in training;
- every inner validation split lies inside the parent outer training block;
- the purge gap equals the horizon for outer and inner splits;
- a deliberately leaking fold is rejected;
- `ews.harness.fold_index_splits` maps quarter boundaries onto table row positions for
  `ews.models.nested_runner`.

**PENDING (Lane 3):** the model-side intake gate that accepts `folds.json`, and the frozen
tuning configuration (`config/models.yaml` still says "requires team approval"; D-R32 is
reserved).

---

## 7. Models, baselines and ensemble rule

**Pre-registered before any result** (`docs/PROPOSAL_ADDENDUM.md`):

- Six model families: logistic, elastic net, random forest, XGBoost, SVM, MLP.
- Train-only imputation, scaling and feature selection.
- Equal-weight probability average of the **top 3** configurations by inner-fold pooled
  PR-AUC.
- Ensemble accepted only if it gains **≥ 0.01** pooled PR-AUC over the best single model,
  the paired-bootstrap 95% interval (1,000 resamples) excludes zero, and episode recall does
  not fall.
- Applied **once** (C-13).
- Threshold objective: **max F1** on inner validation, locked before the outer test
  (D-R19).
- REWI: coefficients from training folds only, intercept excluded, stability reported.

**Lane 2A baselines (integrated, supplementary).** Seed 42, fixed threshold 0.50, fitted
inside each outer training block, on the frozen folds and the 149-column table. Pooled
out-of-sample at the primary 2Q horizon (65 scored quarters):

| Baseline | Pooled PR-AUC | ROC-AUC | Episode recall |
|---|---:|---:|---:|
| Majority prevalence | 0.0236 | 0.0159 | 0.0000 |
| Yield-curve slope logistic | **0.1556** | 0.8730 | 0.0000 |
| Plain logistic (all 149) | 0.1080 | 0.8095 | 0.0000 |

The slope baseline has ranking skill over the 2.4% prevalence, but no baseline crosses 0.50
in the two quarters before the 2019Q4 peak, so 2Q episode recall is zero. At 4Q the slope
baseline reaches 0.1768 PR-AUC and detects that peak. These are baselines under D-R39, not
the official result.

**PENDING (Lane 3):** the official run. The existing exploratory run is **not** a
substitute: it fails C-13 (Δ −0.0017, 95% CI includes zero) and is documented as
exploratory only (`docs/EXPLORATORY_MODEL_RUN.md`).

---

## 8. Out-of-sample results

> **PENDING — Lane 3.** This section must contain the official pooled PR-AUC, Brier score,
> per-horizon results, episode recall and the C-13 verdict, all produced from the frozen
> fold file and the frozen table. Do not copy numbers from the exploratory run.

Planned tables:

| Table | Contents |
|---|---|
| 8.1 Headline | best single model vs ensemble, by horizon, with threshold and seed |
| 8.2 Episodes | detected episodes vs label episodes, peak/trough offsets |
| 8.3 Baselines | majority, probit/logit, plain logistic |
| 8.4 REWI | selected features and stability across folds |
| 8.5 Ensemble verdict | Δ pooled PR-AUC, bootstrap interval, episode-recall guardrail |

---

## 9. Robustness and ablations

> **PENDING — Lane 3.** Planned: leave-one-country-out where labels exist, COVID with and
> without 2020, alternative thresholds, and feature-group ablations. The exploratory run's
> ablations are not the official result.

---

## 10. Reproducibility

### 10.1 Commands

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

make check
make test
make features     # data/clean/dataset.parquet
make folds        # outputs/folds/folds.json (frozen)
make baselines    # outputs/results/baselines.csv + .md (Lane 2A)
make lane2a       # eight-gate Lane 2A verification
```

### 10.2 Verified clean clone

A fresh clone of the integration tip was cloned from GitHub, rebuilt from the raw snapshot,
and checked on 2026-11-14:

| Check | Result |
|---|---|
| `make check` | 33 ok, 1 warning (`shap`, unused), 0 failures |
| `make test` after `make harmonize` | 190 passed, 1 skipped |
| Feature table hash | reproduced exactly |
| Fold hash | reproduced exactly |
| Firewall suite | 7 tests pass, including the two mutation checks |
| Baseline hashes | reproducible across two runs |
| Frozen label hashes | unchanged |

Evidence and caveats: `docs/team/04b_clean_clone_review.md`. `make fetch` was not run
because `FRED_API_KEY` is empty in this environment; the approved raw snapshot was reused.
The combined Day 7 clone is still owed after the official run.

### 10.3 Hash table

| Artefact | SHA-256 |
|---|---|
| `outputs/labels/USA_labels.csv` | `2379fd53e4c9023538cafcd5668a4835bcdd7b45cfae9e3cbc3d4f306ed19daa` |
| `outputs/labels/JPN/JPN_labels.csv` | `b20a9f23dec8516f12cf2047dfd87f2575a307ed0839c811d30b95f29cd6b6f5` |
| `outputs/labels/JPN/labels-v1-JPN.json` | `3b74d3e63f4b6f19e15c372637c2f776e029903f710eba93c8a6cb395b99ed9a` |
| `outputs/labels/labels-v3.json` | `6f1aa66598b1cdf823e3f97a25709c6cb5a7ed851ee8ab1c0a9b8e45402c0a50` |
| `outputs/labels/archive/labels-v2/USA_labels.csv` | `f5ed42a6c4333aaecbae4fae1f5f6fcab3606ce46dd2b459791a6aa31816dc8e` |
| `outputs/labels/archive/labels-v1/USA_labels.csv` | `1a1b1f6a566cb2cffe7181cbc59ec20bd07d8ef25e0300d4dd2d96ceb749e29a` |
| `data/clean/dataset.parquet` (generated) | `368b60056872b9883ab8767fa148249d5f5c13ea85ca68abfc4e9437ee4304f4` |
| `outputs/folds/folds.json` | `afd51bc5f885f74a84f2e5f29bd6732de78454945cb189f2fee1d8c426afc261` |

---

## 11. Limitations and threats to validity

1. **Revised data, simulated lags.** Results are not equivalent to a real-time vintage
   experiment. This must appear in any public description (D-R14).
2. **Ex-post label.** The chronology is built after the fact; it is not a real-time
   recession call.
3. **USA-first.** The out-of-sample result, when it exists, is USA-only until JPN/DEU
   features and labels are aligned.
4. **Small event count.** Four USA episodes in the window; episode-level conclusions are
   fragile even when quarter-level metrics look strong.
5. **Japan window exception.** `labels-v1-JPN` covers 144 quarters (1990Q1–2025Q4) under
   D-R38; cross-country work must align on 147 or use the 144-quarter window explicitly.
6. **Germany below gate.** No German label; cross-country claims cannot include Germany.
7. **India excluded.** The Label-B finding is a coverage result, not a modelling result.
8. **Optional dependencies.** `shap` is not installed; if it becomes a required analysis,
   the environment and the report must say so.

---

## 12. Decisions that must not move silently

| Decision | Rule |
|---|---|
| Labels | `labels-v1`/`labels-v2` byte-identical; `labels-v3` frozen; JPN `labels-v1-JPN` frozen |
| Estimator | DFM, BBQ, diffusion gate and eight-indicator structure unchanged without a new version |
| Coverage | 6-of-8 at ≥70% of the window; not relaxed |
| Folds | D-R37: 80/40 quarters, step 1, horizons 1/2/4, 2Q primary |
| Threshold | D-R19: max F1 on inner validation, locked before test |
| Ensemble | C-13, applied once; no post-hoc changes |
| India | Label-B-only under O-2 |
| Packaging | No bundle, mirror, zip or release tag without explicit approval |

---

## 13. Pending work and owners

| Item | Owner | Blocks |
|---|---|---|
| ~~`docs/FEATURES.md`, `tests/test_feature_firewall.py`, `scripts/07_baselines.py`~~ | ~~Shravani (2A)~~ | **integrated** (see §5, §7, `docs/LANE2A_RESULT.md`) |
| ~~JPN 144/147 closeout~~ | ~~Shravani (2A)~~ | **closed as D-R38** (documented exception) |
| `config/models.yaml` tuning freeze (D-R32) | Palchhin | official run |
| Official USA run, C-13 once, episodes, ablations | Palchhin | §8, §9, headline claim |
| `docs/EXPERIMENTS.md` | Palchhin | results documentation |
| Dashboard refresh from official artifacts | Sathvik | public-facing view |
| Combined Day 7 clean clone and go/no-go | Sathvik | release decision |
| PR to `master`, packaging, tag | Sathvik, **only with approval** | release |

---

## Appendix A — Document map

| Need | File |
|---|---|
| Current status and fingerprints | `docs/STATE.md` |
| Frozen rules and gates | `docs/BUILD_CONTRACT.md` |
| Decision log | `docs/DECISIONS.md` |
| USA label validation | `docs/LABEL_VALIDATION.md` |
| Japan label validation | `docs/LABEL_VALIDATION_JPN.md` |
| Germany coverage | `docs/COVERAGE_DEU.md` |
| India audit | `docs/INDIA_COVERAGE_AUDIT.md` |
| Pre-registered ensemble | `docs/PROPOSAL_ADDENDUM.md` |
| Exploratory run (not official) | `docs/EXPLORATORY_MODEL_RUN.md` |
| Feature specification and firewall | `docs/FEATURES.md` |
| Lane 2A integration result | `docs/LANE2A_RESULT.md` |
| Lane 2A intake | `docs/team/05_2a_intake.md` |
| Clean-clone evidence | `docs/team/04b_clean_clone_review.md` |
| Integration rehearsal | `docs/team/04c_integration_rehearsal.md` |
