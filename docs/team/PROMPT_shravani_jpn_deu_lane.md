# Master Prompt — Lane 1: Japan & Germany Labels (Shravani Math)

**How to use:** paste everything from §0 to §14 into the coding agent at the start of a
session. Work **one day at a time**; do not skip §3 (pre-flight). Replace `<...>`
placeholders with values confirmed from the repo or the team. The lane brief is
`Shravani.pdf` / `Shravani (1).pdf` (identical, SHA-256
`56FADE936EC7F582002D5AD45309FBBF9AD31CE924B508959E9A9CE5B78A0C59`).

---

## 0. Role and outcome

You are a senior econometric data engineer. Work in `D:\ml_ews\recession-ews` on branch
`feat/jpn-deu-labels`. Owner: **Shravani Math** (data and label lead).

Deliver, by Day 5:

1. a **frozen Japan BEAI label** built with the existing frozen estimator, plus an ESRI
   chronology comparison;
2. a **Germany decision** — either a frozen label if the 6-of-8 gate passes, or a complete
   coverage finding that names the missing indicators and the evidence;
3. a **country-parameterised pipeline** (no forked label math) with proof that the USA
   label did not move;
4. a PR with commands run, tests passed, hashes before/after, and known gaps.

Japan is the deliverable. Germany is a bonus or a well-documented coverage finding.
A clear "we could not get 6/8, here is why" is a successful week.

**Do not start coding until §3 is complete and reported.**

---

## 1. Read first, in this order

1. The lane brief PDF (`Shravani.pdf`), all 5 pages.
2. `docs/BUILD_CONTRACT.md` — frozen rules C-01…C-13 if present; otherwise C-01…C-12.
3. `docs/DECISIONS.md` — D-R22…D-R31 if present; otherwise D-R22…D-R25.
4. `docs/LABEL_VALIDATION.md` — the USA method and the evidence standard to copy.
5. `docs/STATE.md` — current hand-off and hashes.
6. `scripts/harmonize.py` and `scripts/03_labels.py` — both currently hard-code the USA.
7. `src/ews/labels/{build,dfm,bbq,diffusion,freeze,ids}.py` — the reusable estimator.
8. `data/scope.csv` — filter `country_iso3` to `JPN` and `DEU` (21 rows each).
9. `data/series_resolution.csv`, `data/manifest.csv`, `config/scope.yaml`,
   `config/indicators.yaml` (grep the JPN/DEU indicator blocks).
10. `tests/test_config.py`, `tests/test_scope.py`, `tests/test_labels.py`,
    `tests/test_freeze.py`.

Do **not** re-read `spec.py`, `build.py` or `series_catalogue.csv`; they are large and
already summarised in the docs.

---

## 2. Non-negotiable rules

| Rule | What it means in this lane |
|---|---|
| C-01 firewall | The label uses **only** the eight core indicators: `ACT_GDP_REAL, ACT_IP, ACT_EMP, ACT_HOURS, ACT_RINC, ACT_CONS, ACT_RETAIL, ACT_INV`. Never use predictors, never use ESRI/OECD chronology, never share a fitted object with Pipeline B. |
| C-02 estimator | One-factor `DynamicFactorMQ`, `factor_orders=1`, `idiosyncratic_ar1=True`, **smoothed** factor, `scale = mean(sigma_j * abs(lambda_j))`, cumulate to level, BBQ on the level. |
| Frozen parameters | `min_phase=2`, `min_cycle=5`, endpoint `censor=2`, `diffusion_gate=0.50`, depth review at 0.10 SD. **Do not tune per country.** |
| C-03 coverage | ≥6 of 8 core indicators, each covering ≥70% of the reporting window; ≥4 indicators to date a quarter. A failure is a finding, not an exception. |
| C-05 timing | Pipeline A (the label) applies **no** availability lag: it is an ex-post chronology. |
| C-06 aggregation | Monthly → quarterly mean; a quarter is missing unless **all** constituent months are present. Daily → monthly → quarterly with the same rule. |
| C-12 reproducibility | Record data version, series IDs, transforms, parameters, seed, hashes. Raw files immutable. |
| No interpolation | No interpolation, no forward-fill, no partial-quarter imputation. Missing stays missing. |
| No guessing IDs | If a series key cannot be confirmed, leave `PENDING_VERIFICATION` and write the exact question + candidate IDs. |
| No collateral change | The USA label, the estimator, the BBQ/diffusion parameters and the eight-indicator structure must not move. |
| No overwrite | Never overwrite `labels-v1`, `labels-v2`, `labels-v3` or any archived label. |

If the repo and the brief disagree about the label version, window or rule IDs, **stop and
ask the human** (§3.2). Do not fabricate `labels-v3` or invent missing decision records.

---

## 3. Pre-flight (30–60 minutes, before any code)

### 3.1 Establish the baseline

```powershell
git status --short
git branch --show-current
git log --oneline -10
Get-FileHash outputs\labels\USA_labels.csv -Algorithm SHA256
Get-ChildItem outputs\labels
Get-ChildItem docs
```

Record: current branch, HEAD, active label version, label files present, and the USA
`USA_labels.csv` SHA-256. This is the **before** hash for the no-collateral-change proof.

### 3.2 Reconcile the brief with the checkout

The brief describes `labels-v3`, 147 quarters (1990Q1–2026Q3), C-01…C-13 and D-R22…D-R31.
This checkout may be older. Decide explicitly:

| Case | Action |
|---|---|
| **A.** `labels-v3` artefacts and C-13/D-R31 exist (anywhere in the repo/branch) | Use them. Read the v3 freeze record and adopt its window and parameters. |
| **B.** Only `labels-v1`/`v2` exist, or the working tree is mid-upgrade | **Pause.** Report the gap to the human with the exact files/hashes. Do not invent v3 and do not change shared rules. Ask whether to (i) pull the team's newer branch, or (ii) proceed on the active version with the gap documented. |
| **C.** The human says "proceed on the active version" | Derive `WINDOW_START/WINDOW_END` and `MIN_QUARTERS` from `config/scope.yaml` + the contract, not from the PDF. Record the deviation at the top of your hand-off. |

Known trap in this checkout: `scripts/03_labels.py` writes `labels-v2`, `tests/test_freeze.py`
expects `labels-v2.json` and `outputs/labels/archive/labels-v1/`, but `outputs/labels/`
contains only `labels-v1`. **Do not "fix" this by editing a hash or deleting a test.**
It is a pre-existing state issue: report it.

### 3.3 Environment (Windows)

The checked-in `.venv` is a Linux layout (`bin/`, `lib/`). Create a Windows venv:

```powershell
py -3.13 -m venv .venv-win
.venv-win\Scripts\python -m pip install --upgrade pip
.venv-win\Scripts\pip install -e ".[dev]"
.venv-win\Scripts\python scripts\00_env.py
.venv-win\Scripts\python -m pytest -q
```

Do not use the Linux `.venv`, and do not rely on `make` (it defaults to `.venv/bin/python`).
If a dependency fails on Windows, record the exact error and ask before changing versions.

### 3.4 Baseline the tests

Run the suite and record the **pre-existing** failures separately from any you introduce.
If tests already fail because of the v1/v2 mismatch, write that down and do not "fix" it
inside this lane.

### 3.5 Report before coding

Post a short pre-flight note: branch, HEAD, active label/window, USA hash, environment
status, test status, and the §3.2 decision. Only then continue.

---

## 4. Day 1 — Generalise the plumbing + Japan source map

**Goal:** 21/21 Japan rows have a source or a written pending reason; the USA label hash is
unchanged after the refactor.

### 4.1 Inventory Japan scope

```powershell
.venv-win\Scripts\python -c "import pandas as pd; d=pd.read_csv('data/scope.csv'); print(d[d.country_iso3=='JPN'].to_string())"
```

Build a table of the 21 rows: indicator, intended role (label / predictor / both),
priority, preferred source, current `id_status`.

### 4.2 Build the Japan source map

For each of the eight core indicators, confirm a concrete Japanese series:

| Core indicator | Candidate concept (verify, do not guess) |
|---|---|
| `ACT_GDP_REAL` | Real GDP, chain-linked, SA — Cabinet Office SNA |
| `ACT_IP` | Indices of Industrial Production, SA — METI |
| `ACT_EMP` | Employment level — MIC Labour Force Survey, or OECD QNA employment |
| `ACT_HOURS` | Total hours worked — SNA / Monthly Labour Survey (only if quarterly total hours) |
| `ACT_RINC` | Real household income — Cabinet Office SNA |
| `ACT_CONS` | Real household consumption — Cabinet Office SNA |
| `ACT_RETAIL` | Retail sales / commercial sales — METI |
| `ACT_INV` | Non-residential business fixed investment — SNA GFCF components |

Rules for the map:

- One row per `series_key`; columns: `scope_key, concept, source, series_id, frequency,
  SA, first, last, coverage, retrieval_date, sha256, status, note`.
- Use official sources first: BOJ, e-Stat, Cabinet Office/ESRI, METI, MIC, MHLW; OECD SDMX
  for cross-checks.
- Record the exact query/URL and retrieval date for every fact.
- If a key is unresolved, write `PENDING_VERIFICATION` plus the candidate IDs and the exact
  blocking question. Never fill a key by analogy with the USA.
- The USA data choices (Q-02 constructed investment, Q-04 `CE16OV`, Q-05 `HOANBS`) are
  **USA choices**; do not copy them blindly to Japan.

Save the map as `docs/SOURCE_MAP_JPN.md` (and a machine-readable
`data/source_map_JPN.csv` if useful).

### 4.3 Parameterise the harmoniser

Refactor `scripts/harmonize.py` without changing USA behaviour:

- add `--country` (default `USA`) and optional `--window-end`, `--sample-start`;
- replace the hard-coded `USA.` filter with a country filter;
- replace `CORE` with a country-aware mapping loaded from config/source map;
- write `data/clean/<ISO3>_levels.parquet`, `<ISO3>_growth.parquet`, `<ISO3>_panel.csv`,
  `<ISO3>_growth.csv`, and `data/clean/coverage_<ISO3>.csv` (do not overwrite the USA
  `coverage.csv`);
- keep the Q-02 US derivation behind `if country == "USA"` so no other country inherits it;
- keep the complete-quarter rule and the sign-alignment logic exactly as they are;
- derive `SAMPLE_START` from data availability (earliest quarter with ≥4 core indicators),
  never by copying the US 1960Q1.

### 4.4 Parameterise the label builder

Refactor `scripts/03_labels.py`:

- add `--country` (default `USA`) and `--label-version`;
- read `<ISO3>_growth.parquet`;
- write `outputs/labels/<ISO3>/<ISO3>_labels.csv`, `_episodes.csv`, `_turning_points.csv`
  and `labels-v1-<ISO3>.json`;
- derive the reporting window from config, not a literal;
- keep the freeze helpers (`existing_created`, `canonical_frame_sha256`, episode
  renumbering) unchanged;
- do not copy the DFM/BBQ math into a new script.

`src/ews/labels/build.py` already accepts `country=`; reuse it.

### 4.5 Prove the USA did not move

```powershell
.venv-win\Scripts\python scripts\harmonize.py --country USA
.venv-win\Scripts\python scripts\03_labels.py --country USA
Get-FileHash outputs\labels\USA_labels.csv -Algorithm SHA256
```

The hash must equal the §3.1 baseline. If it moved, **stop** and fix the cause; never patch
the hash.

### 4.6 Add tests

Add `tests/test_country_plumbing.py`:

- `harmonize.py --country USA` reproduces the frozen USA label hash;
- `--country JPN` writes only `JPN_*` files and does not touch USA files;
- the JPN output directory/naming is correct;
- the core-indicator list is still exactly eight and country-independent;
- the coverage gate helper returns the documented 6/8 and ≥70% logic.

**Day 1 acceptance:** source map complete; both scripts accept `--country`; USA hash
unchanged; new tests pass; a short note in `docs/STATE.md` (or your hand-off file).

---

## 5. Day 2 — Download and harmonise Japan

**Goal:** 6/8 core indicators at ≥70% of the reporting window, or a documented failure; no
interpolation.

### 5.1 Fetch

- Prefer the BOJ time-series API, e-Stat API, Cabinet Office CSV/XLSX, METI CSV, and OECD
  SDMX. If an API is unstable, download manually and record the URL and retrieval time.
- Raw payloads go to `data/raw/<source>/<YYYY-MM-DD>/` and are **immutable**.
- Add one active row per scope key to `data/manifest.csv` and
  `data/series_resolution.csv`, with SHA-256 and coverage.
- Do not commit raw data; commit only scripts, metadata, manifests and hashes.

### 5.2 Harmonise

```powershell
.venv-win\Scripts\python scripts\harmonize.py --country JPN
```

Check:

- quarterly output, complete quarters only;
- no interpolation/forward-fill;
- the coverage table shows quarters present per series and per core indicator;
- the first quarter with ≥4 indicators is recorded.

### 5.3 Gate

Compute the share of the reporting window covered by each core indicator. Report:

| Core indicator | Source ID | First | Last | Quarters in window | Coverage % | Pass ≥70%? |
|---|---|---:|---:|---:|---:|---|

A country needs **≥6 of 8** passing. If Japan fails, write the finding with the missing
indicators and evidence; do not relax the rule.

**Day 2 acceptance:** `data/clean/JPN_growth.parquet` exists; coverage table complete;
gate result recorded; raw hashes in the manifest.

---

## 6. Day 3 — Build, validate and freeze the Japan label

**Goal:** reproducible label + ESRI chronology note + frozen hashes.

### 6.1 Build

```powershell
.venv-win\Scripts\python scripts\03_labels.py --country JPN --label-version labels-v1-JPN
```

Verify:

- `estimator = dfm` and `converged = True` (if not, record the fallback; never present a
  fallback as the reference result);
- the eight core indicators are the only inputs;
- no ESRI/NBER series is read anywhere in the label path;
- episodes and turning points are written with `in_window` flags.

### 6.2 Robustness

Run the frozen variants only (no tuning):

- `min_phase = 3`;
- `diffusion_gate = 0.60`;
- sample ends before COVID (if applicable).

Dates may move by at most one quarter. If they move more, report it as a finding.

### 6.3 ESRI comparison

- Get the official Japanese business-cycle reference dates (ESRI / Cabinet Office
  "景気基準日付": peak/trough quarters).
- Compare episode by episode: peak diff, trough diff, overlap, missed episodes, false
  episodes.
- ESRI is a **plausibility check only** (C-04). It must never enter the estimator, the
  features or the threshold.
- Explain every discrepancy in one or two sentences (boundary convention, data revision,
  COVID, etc.).

### 6.4 Write `docs/LABEL_VALIDATION_JPN.md`

Sections, mirroring the USA note:

1. Data (eight indicators, sources, coverage, transforms).
2. Method (frozen estimator, parameters, estimation sample vs reporting window).
3. Result (episodes table, ESRI comparison, quarter-level confusion matrix if you build one).
4. Discrepancies and why they are acceptable.
5. Robustness.
6. What would falsify this.
7. Frozen artefacts and hashes.
8. What I learned (required by the brief).

### 6.5 Freeze

- Write `outputs/labels/JPN/labels-v1-JPN.json` with parameters, loadings, input hashes,
  output hashes and the freeze date.
- The freeze guard must refuse to overwrite a frozen label when the canonical input digest
  changes. Do not bypass it.
- Archive, never edit, older versions.

**Day 3 acceptance:** label reproducible from raw + commands; ESRI note written; hashes
recorded; USA hash still unchanged.

---

## 7. Day 4 — Map and download Germany

**Goal:** 21/21 rows resolved or pending with a reason; the 1990–91 reunification break
documented.

### 7.1 Source map

Same table and rules as Japan. Prefer:

- Destatis Genesis-Online for GDP, employment, hours, retail, investment;
- Bundesbank for rates/credit;
- OECD QNA / BIS for cross-checks and house prices.

Do not copy the Japan series IDs or the USA choices. Verify each concept independently.

### 7.2 Reunification break

- Document what happens in 1990–91 (West Germany vs unified Germany, level breaks,
  base-year changes).
- If the break makes pre-1991 data non-comparable, set the German estimation sample to
  start after the break and record why.
- Do not splice or backcast silently; if you chain growth, document it and keep it
  consistent with the frozen rules.

### 7.3 Coverage

Produce the same coverage table and 6/8 gate for Germany. If <6/8, stop here and write the
complete coverage finding (Day 5 deliverable).

**Day 4 acceptance:** `docs/SOURCE_MAP_DEU.md`; `data/clean/DEU_growth.parquet` if eligible;
coverage table; reunification note.

---

## 8. Day 5 — Germany decision + hand-off

### 8.1 Decision

- **If 6/8 passes:** build and freeze `labels-v1-DEU`, with the same validation note
  (`docs/LABEL_VALIDATION_DEU.md`) and an official-chronology comparison (e.g.
  Sachverständigenrat / OECD chronology).
- **If 6/8 fails:** do **not** build a label. Write `docs/COVERAGE_DEU.md` naming the
  missing indicators, their coverage, the evidence, and what would be needed to pass.

Record the gate decision in the hand-off and in `docs/DECISIONS.md` if it is a new decision.

### 8.2 Hand-off note

Create `docs/HANDOFF_JPN_DEU.md`:

- what changed (files, scripts, config);
- commands run, in order;
- tests passed/failed;
- hashes before/after (USA unchanged; JPN/DEU frozen);
- coverage and gate results;
- known gaps and open questions;
- what the next person should do first.

### 8.3 PR

- Branch `feat/jpn-deu-labels`, rebased on main.
- PR description: mission, deliverables, evidence, commands, hashes, known gaps.
- One logical change per commit. Suggested messages:
  `refactor(labels): parameterise harmoniser by country`,
  `feat(jpn): add source map and coverage`,
  `feat(jpn): freeze labels-v1-JPN`,
  `docs(jpn): ESRI chronology comparison`,
  `feat(deu): coverage finding` (or `freeze labels-v1-DEU`).

### 8.4 Merge/review

- Day 6: merge in the fixed order; the team checks label hashes and chronology.
- Day 7: cross-review another lane; write findings, not verbal comments.

**Day 5 acceptance:** all brief deliverables 1–7 are present; a fresh run reproduces the
label and hashes; no USA file moved.

---

## 9. Definition of done (checklist)

- [ ] `docs/SOURCE_MAP_JPN.md` — 21/21 rows resolved or pending with a reason.
- [ ] `data/manifest.csv` — one active row per JPN scope key, with SHA-256.
- [ ] `data/clean/JPN_growth.parquet` — quarterly, no interpolation.
- [ ] `data/clean/coverage_JPN.csv` — 6/8 count and window share.
- [ ] `outputs/labels/JPN/JPN_labels.csv`, `JPN_episodes.csv`, `JPN_turning_points.csv`.
- [ ] `outputs/labels/JPN/labels-v1-JPN.json` — frozen parameters + hashes.
- [ ] `docs/LABEL_VALIDATION_JPN.md` — method, ESRI, discrepancies, robustness, learning.
- [ ] Germany: `docs/SOURCE_MAP_DEU.md` + either a frozen label or `docs/COVERAGE_DEU.md`.
- [ ] `docs/HANDOFF_JPN_DEU.md`.
- [ ] USA `USA_labels.csv` SHA-256 unchanged from the §3.1 baseline.
- [ ] `pytest` green (or pre-existing failures explicitly separated).
- [ ] PR on `feat/jpn-deu-labels` with commands, tests, hashes, known gaps.

---

## 10. Reporting protocol

- **09:30 stand-up:** what I finished, what I will do, what is blocking me.
- **17:30 hand-off:** what changed, what is reproducible, what is still open.
- **Commit small:** one logical change per commit; run the relevant tests before each.
- **Blocked > half a day:** say so at stand-up; do not hide it until Day 5.
- **Every non-obvious choice:** one short note in the hand-off or the chronology note.

---

## 11. When blocked

| Situation | Action |
|---|---|
| Source key unclear | Write the exact question and candidate IDs; ask before guessing. |
| Refactor growing | Protect Japan first; a thin wrapper that reuses the estimator beats a perfect abstraction. |
| Coverage fails | Write the missing indicators, window share and evidence. That is a result. |
| USA hash moves | Stop. Fix the cause. Never patch the hash or the label by hand. |
| Brief/repo mismatch | Stop and ask (§3.2). Do not invent rules or versions. |
| API down | Record the error, try an official CSV/manual download, document the substitution. |

---

## 12. Anti-patterns (do not do these)

- Copying the USA `CORE` dict or the US Q-02/Q-04/Q-05 choices into Japan/Germany.
- Hard-coding `1960Q1` or `1990Q1` for another country.
- Forking `dfm.py`/`bbq.py` into a JPN-only script.
- Interpolating, forward-filling, or filling a partial quarter.
- Feeding ESRI/OECD chronology into the label, the factor or the threshold.
- Changing `min_phase`, `min_cycle`, `censor` or `diffusion_gate` to make a country pass.
- Overwriting a frozen label or editing a hash/test to make it green.
- Committing restricted raw data.
- Claiming a forecast or a cross-country result before the out-of-sample work exists.

---

## 13. Short Day-1 kickoff prompt (if the agent has a small context window)

> You are working in `D:\ml_ews\recession-ews` on branch `feat/jpn-deu-labels`. Read
> `docs/BUILD_CONTRACT.md`, `docs/DECISIONS.md`, `docs/LABEL_VALIDATION.md`,
> `docs/STATE.md`, `scripts/harmonize.py`, `scripts/03_labels.py`,
> `src/ews/labels/build.py` and `src/ews/labels/freeze.py` first. Then do the pre-flight:
> record the USA label hash, reconcile the checkout with the lane brief (labels-v3 vs the
> active version), set up a Windows venv, and run the tests. Do not change any frozen
> parameter. Then complete Day 1 only: (1) build `docs/SOURCE_MAP_JPN.md` for the 21 JPN
> scope rows using official sources, marking unresolved keys `PENDING_VERIFICATION` with
> the exact question; (2) add `--country` to `scripts/harmonize.py` and
> `scripts/03_labels.py` so they write `data/clean/<ISO3>_*` and
> `outputs/labels/<ISO3>/*`, with `USA` as the default and the Q-02 derivation kept
> US-only; (3) add `tests/test_country_plumbing.py`; (4) prove
> `outputs/labels/USA_labels.csv` is byte-identical to the baseline. Report the baseline
> hashes, the files changed, the test results, and any blocker before starting Day 2.

---

## 14. One-line success statement

> Japan has a frozen, reproducible `labels-v1-JPN` that reproduces the eight-indicator
> structure and passes 6/8 coverage, with an honest ESRI comparison; Germany is either
> frozen or documented as a coverage finding; the USA label hash never moved; and every
> source, command and gap is written down.
