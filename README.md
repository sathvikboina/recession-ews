# Cross-Country Recession Early-Warning

Machine-learning framework for predicting recession **onset** at 1, 2 and 4 quarters,
with a leakage-controlled evaluation design. This repository currently contains the
Phase 2 data dictionary, the runtime specification, and the build scaffolding. **No data
has been downloaded and no model has been trained yet.**

Team: Sathvik Boina, Shravani Math, Arshiya, Palchhin.

## Status

| Stage | State |
|---|---|
| Phase 1 — literature matrix | done (`literature_matrix.xlsx`, v4) |
| Phase 2 — data dictionary | done (`recession_ews_data_dictionary.xlsx`, 16 sheets) |
| Phase 3 — scoped verification | **0 of 68 series verified** — next task |
| Phase 4–8 — collect / harmonise / label / features / harness | not started |
| Phase 9+ — experiments, interpretation, dashboard | not started |

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

make config      # regenerate config/*.yaml from spec.py
make scope       # build the 68-row collection shortlist
make check       # environment + configuration gate
make test        # test suite
```

`make bootstrap` runs all four. Without a virtualenv, `python3 scripts/…` works for the
config and scope scripts (they need only `pyyaml`); the modelling dependencies are
required from Step 5 onward.

## Layout

```
config/            runtime configuration (scope, indicators, countries, sources)
data/
  scope.csv        the 68 series this build will actually collect
  scope_coverage.csv  country x indicator availability view
  raw/ interim/ clean/   data stages (git-ignored)
src/ews/           package: fetch, harmonize, labels, features, validation, models
scripts/           00_env, export_spec, scope_catalog, (fetch/harmonize/labels next)
tests/             config, scope, and (later) BBQ and leakage tests
docs/              BUILD_CONTRACT.md, DECISIONS.md, VERIFICATION.md, STATE.md
outputs/           labels, folds, results, figures, runs
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
- Series: **68 rows** (30 BEAI-eligible, 3 derived, 1 global).
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

The scoped verification pass (`docs/VERIFICATION.md`): confirm IDs, frequency, start/end,
units and SA status for the 68 rows, starting with FRED. Then collect, harmonise, and build
the BEAI label for the USA as the first stop/go gate.
