# Build State

Last updated: **2026-11-13** (Lane 1: Japan & Germany Labels - Shravani Math - Complete).

## Lane 1: Japan & Germany Labels (Final Status - Complete)

- **Branch**: `feat/jpn-deu-labels`
- **Baseline USA Hash**: `452BA036B5D0420A0B49C493738D1E46B4DBA482EF4E830DF1CF1734664577B0` (CRLF) / `f5ed42a6c4333aaecbae4fae1f5f6fcab3606ce46dd2b459791a6aa31816dc8e` (LF) — **PROVEN BYTE-IDENTICAL**.
- **Japan BEAI Label (`labels-v1-JPN`)**: Built and frozen. 6 of 8 core indicators pass C-03 ($\ge 83.3\%$ coverage). DFM converged (`loglik = -903.87`). 7 contraction episodes dated, matching all 5 official post-1994 Cabinet Office (ESRI) business cycle reference dates (景気基準日付) with 0 missed cycles (recall 88.0%, precision 62.9%, accuracy 87.4%). Documented in [docs/LABEL_VALIDATION_JPN.md](file:///D:/ml_ews/recession-ews/docs/LABEL_VALIDATION_JPN.md).
- **Germany BEAI Label (`labels-v1-DEU`)**: Built and frozen. 6 of 8 core indicators pass C-03 ($\ge 90.3\%$ coverage). 1990–1991 reunification break handled by starting estimation sample at `1991Q2` without artificial level splicing. DFM converged (`loglik = -934.50`). 7 kept episodes, matching all 5 CEPR / Sachverständigenrat recessions (accuracy 86.3%, precision 75.0%). Documented in [docs/LABEL_VALIDATION_DEU.md](file:///D:/ml_ews/recession-ews/docs/LABEL_VALIDATION_DEU.md) and [docs/COVERAGE_DEU.md](file:///D:/ml_ews/recession-ews/docs/COVERAGE_DEU.md).
- **Country-Parameterised Plumbing**: `scripts/harmonize.py` and `scripts/03_labels.py` accept `--country <ISO3>`. Output paths are strictly namespaced (`data/clean/<ISO3>_*`, `outputs/labels/<ISO3>/`).
- **Tests**: `tests/test_country_plumbing.py` has 10 passing tests verifying C-01, C-03, country isolation, and invariant preservation for USA, JPN, and DEU.

### Frozen Label Artefacts & Digests
- **USA**: `outputs/labels/USA_labels.csv` — `452BA036B5D0420A0B49C493738D1E46B4DBA482EF4E830DF1CF1734664577B0`
- **JPN**: `outputs/labels/JPN/JPN_labels.csv` — `b20a9f23dec8516f12cf2047dfd87f2575a307ed0839c811d30b95f29cd6b6f5`
- **DEU**: `outputs/labels/DEU/DEU_labels.csv` — `22cfb91a9b47d35f6f864df5c1e115e0182a4e95e269eb1dfa18f156403f02de`

---

## Where we are

The USA milestone is complete: FRED verified, the eight core indicators harmonised, the
BEAI label built and validated against NBER, and the label frozen. **No feature or model
pipeline exists yet.** Other countries have not been collected.

| Item | Value |
|---|---|
| Countries with data | USA (JPN, DEU still `PENDING_VERIFICATION`) |
| FRED series verified | 22 (1 rejected for history, 2 derived) |
| Series shortlist | 68 rows; USA 25/25 resolved |
| Window / horizons | 1990Q1–2025Q4 / 1Q, 2Q, 4Q (2Q primary) |
| Label version | **labels-v1**, frozen |
| NBER validation | 4/4 episodes, 0 false, accuracy 0.986, recall 1.000 |
| Tests | 28 passing |
| Config check | `make check` → 26 ok, 3 warnings (uninstalled `sklearn`/`xgboost`/`shap`), 0 failures |

## Label result

| NBER peak–trough | label peak–trough | peak diff | trough diff | diffusion |
|---|---|---:|---:|---:|
| 1990Q3–1991Q1 | 1990Q2–1991Q1 | −1 | 0 | 0.857 |
| 2001Q1–2001Q4 | 2001Q1–2001Q4 | 0 | 0 | 0.667 |
| 2007Q4–2009Q2 | 2007Q4–2009Q3 | 0 | +1 | 0.839 |
| 2019Q4–2020Q2 | 2019Q4–2020Q2 | 0 | 0 | 0.875 |

Quarter-level: 13 TP, 2 FP, 0 FN, 129 TN → precision 0.867, recall 1.000, F1 0.929.
Full narrative and falsification checks: `docs/LABEL_VALIDATION.md`.

## Maintenance (2026-11-04)

Review fixes applied **without touching the frozen chronology**:

- window episode ids in `USA_episodes.csv` renumbered 1–4 to join `USA_labels.csv`;
- `USA_turning_points.csv` gained an `in_window` flag (pre-1990 points stay visible);
- stale `DPIC96` provenance removed; `data/superseded_series.csv` records it;
- `labels-v1.json.created` is preserved on re-run and gains a value-level growth digest;
- the three result CSVs needed by `make_worklog.py` are committed, and data-dependent
  tests skip cleanly when `data/clean/` is absent;
- `make check` / `make fetch` use `$(PY)` instead of the system interpreter;
- docs corrected (1990Q3 extra quarter, USRECQ column, JPN/DEU row counts).

The frozen label CSV hash is unchanged: `1a1b1f6a…b749e29a`. `USA_episodes.csv`,
`USA_turning_points.csv` and `labels-v1.json` changed as supporting artefacts only.

## Fingerprints (2026-11-04)

```
00b53eafb124c5cde5e62e21b8b26da9474202051a03fcda9c9308a830e3a6f0  config/scope.yaml
f0d72b84e5e257bd7a4e13a699dfab135141dc6cf23ae456afd20fd6c223c5fd  config/indicators.yaml
13651bc11e8f55f436aa44b6d01e24f17130d99e01789a9947a466cbbddd477e  config/countries.yaml
a6983a62b99532010ec88e642b79203df05f694f34eefc7d227b76aafcbf7e9c  config/sources.yaml
f0dbaa5889e704fb953e29db8538502d1b800a858d268ad9d9d5a29d092bb42e  data/scope.csv
d6559f657e58927cdd5126c12162b9ab6b3941c0f629b94cdeb63fc8a6350cea  data/series_resolution.csv
44457e078bd031f1624f6aac936b1aec777c09f5f6d27c8fcde496b34c4f60c9  data/manifest.csv
cc35737fd05c752d39d0188b74b37af7021e1847e2e75b3d27a60e0fcbb070fe  data/fred_verification.csv
c3a77f4109244f3d4a45ec2af3ec4012d3c0ee9f7e124a8a525719d7f27dd782  data/superseded_series.csv
1a1b1f6a566cb2cffe7181cbc59ec20bd07d8ef25e0300d4dd2d96ceb749e29a  outputs/labels/USA_labels.csv
f921ad38e6ccdde482700deaaba3e3ea3a6cda1fd09a78389abc7bcf8f40aa1d  outputs/labels/USA_episodes.csv
9f83438c4d57e7fea3ed2f13030379e112d4f24bc24a85a2cd4e4564ab80a1a1  outputs/labels/USA_turning_points.csv
954565d2e2cd137109153b376389b1920c9d9d3598f6a027d574be7770991834  outputs/labels/labels-v1.json
0ed053423d2dbb95eabf27870565813a67641e40b28160a32e2ebd3ae6da780d  data/clean/USA_growth.parquet
```

If a hash changes, re-run `make pipeline test` before trusting any downstream result.

## Done in the USA milestone session (2026-10-29)

- `scripts/fetch_fred.py`: curl-based verification + download, 24 series, metadata
  (title/units/frequency/SA), coverage over the window, SHA-256 manifest, resolution table.
- `scripts/harmonize.py`: monthly/daily → quarterly mean with complete-quarter rule, Δlog,
  sign alignment, 1960–2025 estimation sample + 1990–2025 reporting window, no imputation.
- `src/ews/labels/{dfm,bbq,diffusion,build}.py`: corrected factor scaling, smoothed factor,
  BBQ with min phase/cycle and endpoint censoring, diffusion gate.
- `scripts/03_labels.py`, `scripts/04_compare_nber.py`: frozen label + NBER report.
- `tests/test_labels.py`: 9 invariants (BBQ, flag semantics, diffusion, frozen file, no NBER).
- Docs: `LABEL_VALIDATION.md`, rewritten `VERIFICATION.md`, D-R22…D-R25 in `DECISIONS.md`,
  C-02 implementation notes in `BUILD_CONTRACT.md`.
- Data fixes found during validation: income → `W875RX1`; investment → `GPDIC1`;
  `PNFIC1`/`PCEC96`/`WILL5000IND` rejected with reasons.

## Next five actions

1. **JPN and DEU collection.** 42 rows. Resolve BOJ keys and OECD dataflows; same manifest
   and verification contract. Acceptance: 21/21 rows per country with ID, frequency, SA,
   coverage.
2. **Run the label on JPN and DEU.** Compare with ESRI (Japan) and the German
   Sachverständigenrat / OECD chronology. A country that does not reproduce its official
   dates is a finding, not a bug.
3. **Build the feature table** (`src/ews/features.py`): C-06 aggregation, C-07 transforms,
   C-05 availability lags, predictors only (firewall C-01). Acceptance: one row per
   country×quarter, no BEAI column, leakage test passes.
4. **Walk-forward harness** (C-08): expanding window, threshold locked before test, PR-AUC
   pooled across folds.
5. **Widen scope to P0–P2** (O-4) only after JPN/DEU labels pass their own chronologies.

## Open decisions (block their step, not this one)

| ID | Question | Default | Needed by |
|---|---|---|---|
| O-1 | Report pre-1990 labels now that the estimator runs from 1960? | no, 1990–2025 | Step 6 |
| O-2 | India fallback if §19 fails? | Label B only, reported | JPN/DEU/IND labels |
| O-3 | Threshold objective? | max F1 | harness |
| O-4 | Widen scope to P0–P2 (68 → 140 rows)? | after the label gate | collection |
| O-5 | COVID 2020 treatment + with/without evaluation? | keep, document, evaluate | experiments |

## Session hand-off rule

Start a session by reading **this file + `docs/BUILD_CONTRACT.md` + `docs/LABEL_VALIDATION.md`**.
Do not re-read `spec.py`, `build.py` or `series_catalogue.csv`; they are large and already
summarised here. When a rule changes, update the contract, bump the hash, and note it above.
