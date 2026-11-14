# Lane 2A Integration Result — Feature Firewall and Baselines

| Field | Detail |
|---|---|
| **Lane 2A owner (hand-off)** | Shravani Math |
| **Integration owner** | Sathvik Boina (Lane 2B / branch owner) |
| **Date** | 14 November 2026 |
| **Integrated on** | `feat/features-harness` → `feat/india-scope-docs` |
| **Evidence** | `tests/test_feature_firewall.py`, `docs/FEATURES.md`, `outputs/results/baselines.csv`, `outputs/results/lane2a_verification.json` |

## 1. What was accepted

| Deliverable | Integrated path | Notes |
|---|---|---|
| Written feature specification and dictionary | `docs/FEATURES.md` | Rewritten to describe the **149-column** table, not the hand-off's 27-column prototype |
| Six firewall tests plus inventory test | `tests/test_feature_firewall.py` | Adapted to `ews.features.build_feature_table` / `validate_feature_table`; mutation test retained |
| Baselines | `scripts/07_baselines.py` | Rewritten for `data/clean/dataset.parquet` and the frozen `outputs/folds/folds.json` (D-R37) |
| Baseline results | `outputs/results/baselines.csv`, `.md` | Seed 42, fixed threshold 0.50 |
| Verification harness | `scripts/08_verify_lane2a.py` | Eight gates over labels, table, folds, firewall, baselines and the JPN closeout |
| JPN 144 vs 147 closeout | `docs/DECISIONS.md` **D-R38**, `docs/LABEL_VALIDATION_JPN.md` | Recorded as Option A (documented exception); D-R34 was not reused |

## 2. What was deliberately not merged

The hand-off branch also contained artefacts that conflicted with the frozen Lane 2B
contract and were **not** merged:

| Rejected artefact | Why |
|---|---|
| `Makefile` with conflict markers | Not runnable; would break `make` |
| `scripts/06_features.py`, `data/features/dataset.parquet` | Parallel 27-predictor pipeline; the contract table is `src/ews/features.py` → `data/clean/dataset.parquet` (149 features) |
| `scripts/06_folds.py`, `data/features/folds.json` | 22 folds / 60Q initial train / 4Q test blocks; conflicts with D-R37 (67 folds, 80/40, 1Q step) |
| Overwritten `tests/test_features.py` | Lane 3 owns that file (D-R36); the suite belongs in `tests/test_feature_firewall.py` |
| `outputs/folds/folds.json` reverted to `draft: true` | The file is frozen under D-R37 and must stay `approved: true` |
| `scripts/harmonize.py` silent LF/vintage fallback | Relaxes raw SHA-256 checks without a recorded decision |
| `make.bat`, `data/features/.gitkeep` | Not part of the Linux contract; the Windows helper is unnecessary |

The JPN decision in the hand-off reused **D-R34**, which already means "Lane 2 ownership".
The exception is therefore recorded as **D-R38**.

## 3. Firewall result

`tests/test_feature_firewall.py` passes on the real table and fails on poisoned tables:

1. **Schema** — 147 contiguous quarters, 149 columns, no duplicate columns.
2. **Blacklist** — no label, factor, chronology, identifier or episode column; the validator
   rejects an injected `R`, `factor` or `n_available`.
3. **Unscaled** — no standardised column; rate `__level` columns equal their harmonised
   source series.
4. **No future leakage** — rebuilding on history truncated at 2000Q4, 2010Q2, 2019Q4 and
   2024Q3 leaves every past value identical.
5. **Independence** — all 64 `beai_copy_*` columns are reproduced from the panel alone with
   `build_available_panel` + `transform_quarterly_series`; no scaler or fitted object is
   stored beside the data.
6. **Mutation** — a future-shifted column and injected forbidden columns are both caught.
7. **Inventory** — the machine-readable spec, the written dictionary and the built table all
   agree at 149 columns.

## 4. Baseline result (primary horizon 2Q)

Pooled out-of-sample over 65 scored quarters, fixed threshold 0.50, seed 42:

| Baseline | Pooled PR-AUC | ROC-AUC | Episode recall |
|---|---:|---:|---:|
| Majority prevalence | 0.0236 | 0.0159 | 0.0000 |
| Yield-curve slope logistic | **0.1556** | 0.8730 | 0.0000 |
| Plain logistic (all 149) | 0.1080 | 0.8095 | 0.0000 |

The slope baseline has real ranking skill relative to the 2.4% prevalence, but no baseline
crosses 0.50 in the two quarters before the 2019Q4 peak, so 2Q episode recall is zero. At 4Q
the slope baseline reaches 0.1768 PR-AUC and detects the 2019 peak. These are **baselines**,
not the official result: the six-model comparison and the C-13 verdict remain Lane 3.

## 5. Reproduce

```bash
make features
make folds
make baselines
.venv/bin/python -m pytest tests/test_feature_firewall.py -q
.venv/bin/python scripts/08_verify_lane2a.py
```

Expected frozen file hashes:

| Artefact | SHA-256 |
|---|---|
| `outputs/labels/USA_labels.csv` | `2379fd53e4c9023538cafcd5668a4835bcdd7b45cfae9e3cbc3d4f306ed19daa` |
| `outputs/labels/JPN/JPN_labels.csv` | `b20a9f23dec8516f12cf2047dfd87f2575a307ed0839c811d30b95f29cd6b6f5` |
| `data/clean/dataset.parquet` (generated) | `368b60056872b9883ab8767fa148249d5f5c13ea85ca68abfc4e9437ee4304f4` |
| `outputs/folds/folds.json` | `afd51bc5f885f74a84f2e5f29bd6732de78454945cb189f2fee1d8c426afc261` |

## 6. Open items handed to Lane 3

- `config/models.yaml` tuning freeze (D-R32) and the official USA run.
- C-13 ensemble applied once, with the episode-recall guardrail.
- `docs/EXPERIMENTS.md`, headline tables and robustness ablations.
- Combined Day 7 clean clone after the official artefacts exist.
