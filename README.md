# Cross-Country Recession Early-Warning

Machine-learning framework for predicting recession **onset** at 1, 2 and 4 quarters,
with a leakage-controlled evaluation design. This repository currently contains the
Phase 2 data dictionary, the runtime specification, the USA data, and a **validated,
frozen recession label**. No feature table and no model have been built yet.

Team: Sathvik Boina, Shravani Math, Arshiya, Palchhin.

## Status

| Stage | State |
|---|---|
| Phase 1 — literature matrix | done (`literature_matrix.xlsx`, v4) |
| Phase 2 — data dictionary | done (`recession_ews_data_dictionary.xlsx`, 16 sheets) |
| Phase 3 — scoped verification | USA 25/25 resolved; JPN/DEU 42 rows, 40 pending + 2 derived |
| Phase 4 — collect + harmonise | USA done; JPN/DEU not started |
| Phase 5 — BEAI label | **USA validated and frozen (`labels-v2`; `labels-v1` archived)** |
| Phase 6–8 — features / harness / models | not started |
| Phase 9+ — experiments, interpretation, dashboard | not started |

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

make config      # regenerate config/*.yaml from spec.py
make scope       # build the 68-row collection shortlist
make fetch       # verify + download the FRED series (no API key needed)
make pipeline    # harmonise -> label -> NBER validation
make check       # environment + configuration gate
make test        # test suite
```

`make bootstrap` runs config, scope, check and test. The pipeline scripts need pandas,
statsmodels and pyarrow (installed by `pip install -e ".[dev]"`).

## USA milestone result

| NBER peak–trough | label peak–trough | peak diff | trough diff |
|---|---|---:|---:|
| 1990Q3–1991Q1 | 1990Q2–1991Q1 | −1 | 0 |
| 2001Q1–2001Q4 | 2001Q1–2001Q4 | 0 | 0 |
| 2007Q4–2009Q2 | 2007Q4–2009Q2 | 0 | 0 |
| 2019Q4–2020Q2 | 2019Q4–2020Q2 | 0 | 0 |

4/4 episodes matched, 0 false episodes, quarter accuracy 0.993, precision 0.929,
recall 1.000, F1 0.963. The label uses the Q-02 constructed real non-residential
business fixed investment series and the Q-04 `CE16OV` LFS fallback; Q-05 keeps
`HOANBS` with its nonfarm-business coverage documented. `labels-v1` remains
byte-identical in `outputs/labels/archive/labels-v1/`.
Method, discrepancy discussion and falsification checks: `docs/LABEL_VALIDATION.md`.
Selected options and the alternative comparison: `docs/DECISION_NOTE_Q02_Q04_Q05.md`.
Rejected data variants and substitutions: `docs/VERIFICATION.md`.

## Layout

```
config/            runtime configuration (scope, indicators, countries, sources)
data/
  scope.csv        the 68 series this build will actually collect
  scope_coverage.csv  country x indicator availability view
  superseded_series.csv  retired source ids, kept for provenance
  raw/ interim/ clean/   data stages (git-ignored)
src/ews/labels/    dfm.py, bbq.py, diffusion.py, build.py
scripts/           00_env, export_spec, scope_catalog, fetch_fred, harmonize, 03_labels,
                   04_compare_nber, make_worklog
tests/             config, scope, label invariants (BBQ, flag, diffusion, frozen file)
docs/              BUILD_CONTRACT.md, DECISIONS.md, VERIFICATION.md, STATE.md,
                   DECISION_NOTE_Q02_Q04_Q05.md
outputs/           labels, folds, results, figures, runs
EWS_Work_Log.xlsx  generated work log: every action, source, test and decision
```

Root-level files are the **Phase 2 deliverable** and stay in place:

- `recession_ews_data_dictionary.xlsx` — 16-sheet master workbook with live firewall checks.
- `series_catalogue.csv` — 1,883 candidate series × 80 columns (a superset, not a to-do list).
- `collection_priority.csv`, `collection_batches.csv` — prioritised collection plan (B01–B10).
- `schema.csv`, `controlled_vocabularies.csv` — CSV schema and allowed values.
- `decisions_log.csv` (34 decisions), `unresolved_questions.csv` (17 open items).
- `indicator_dictionary.csv`, `country_source_rules.csv`, `source_registry.csv`,
  `label_firewall_rules.csv`, `label_references.csv`, `verification_log.csv`.
- `spec.py` / `build.py` — generator for the workbook and CSVs. `spec.py` is the
  documentation source of truth; runtime code reads `config/*.yaml` instead.

## Regenerating the Phase 2 dictionary

```bash
pip install openpyxl
EWS_OUT=build python3 build.py     # writes build/csv/*.csv + workbook
```

`build.py` no longer writes into the project root, so regenerating cannot overwrite the
checked-in deliverables. Set `EWS_OUT=/path` to choose the destination.

## What is in scope for the first build

- Countries: **USA, JPN, DEU** (edit `config/scope.yaml` to add the rest of Tier 1/2).
- Indicators: **P0 + P1** — the eight §11 core indicators plus 13 core predictors.
- Series: **68 rows** (30 BEAI-eligible, 4 derived, 1 global).
- Window: 1990Q1–2025Q4 (144 quarters); horizons 1Q/2Q/4Q, 2Q primary.
- Labels: BEAI (primary), technical GDP and NBER-US (robustness).

Widening to P0 + P2 takes the shortlist from 68 to 140 rows and is a one-line change in
`config/scope.yaml` (decision O-4).

## Frozen rules

Read `docs/BUILD_CONTRACT.md` before writing any pipeline code. It contains the firewall,
the BEAI label algorithm and its parameters, coverage thresholds, the lag table, feature
forms, the walk-forward protocol, metrics and the LOCO gate. `docs/DECISIONS.md` maps
those rules to the Phase 2 decision log and lists the five items still awaiting sign-off.

## Data policy

- Raw downloads are immutable and stored under `data/raw/<source>/<date>/` with a SHA-256
  in the manifest.
- No restricted raw data is redistributed; the repository keeps scripts and metadata.
- Missing values stay missing: no interpolation or forward-fill of macro series.
- Revised historical data with simulated publication lags — results are **not** equivalent
  to a real-time vintage forecast and must be described that way.

## Next task

Extend collection to Japan and Germany (42 rows), run the same label pipeline, and compare
with ESRI and the German official chronology. Then build the predictor feature table and the
walk-forward harness. Do not widen to P0–P2 until the other two countries pass their own
label checks.
