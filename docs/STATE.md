# Build State

Last updated: **2026-10-29**. One page of truth for the next session.

## Where we are

Phase 2 (dictionary + design) is complete. The build scaffolding is in place and validated.
**No data has been collected and no model code exists yet.**

| Item | Value |
|---|---|
| Countries enabled | USA, JPN, DEU (+ GLOBAL predictors) |
| Indicators in scope | 21 (P0: 8 core, P1: 13 predictors) |
| Series shortlist | 68 rows (30 BEAI-eligible; 65 download, 3 derived) |
| Window / horizons | 1990Q1–2025Q4 / 1Q, 2Q, 4Q (2Q primary) |
| Verified series | **0 of 68** |
| Label version | none yet |
| Config check | `make check` → 26 ok, 10 warnings (missing model deps), 0 failures |
| Tests | 12 passing (config + scope) |

## Fingerprints (2026-10-29)

```
00b53eafb124c5cde5e62e21b8b26da9474202051a03fcda9c9308a830e3a6f0  config/scope.yaml
f0d72b84e5e257bd7a4e13a699dfab135141dc6cf23ae456afd20fd6c223c5fd  config/indicators.yaml
13651bc11e8f55f436aa44b6d01e24f17130d99e01789a9947a466cbbddd477e  config/countries.yaml
a6983a62b99532010ec88e642b79203df05f694f34eefc7d227b76aafcbf7e9c  config/sources.yaml
b10bff4dc6bd01d36bfc4da565647f0afe9005ddcc2b1311674f5e50b5244f6a  data/scope.csv
e6a5ca4c7c8e270a3862684f3cfaaa989fb58d132771cb01b1c97cf1cba8bc90  data/scope_coverage.csv
```

If a hash changes, re-run `make check test` before trusting any downstream result.

## Done in this session

- Fixed `build.py`: portable paths, `EWS_OUT` output root (default `build/`), removed a
  non-existent width key, rewrote the V-16 verification note.
- Rewrote `README.md` for the real (flat) repository layout and current status.
- Added the build skeleton: `config/`, `src/ews/`, `scripts/`, `tests/`, `docs/`, `outputs/`.
- Added `pyproject.toml`, `Makefile`, `.gitignore`, `src/ews/__init__.py`.
- `scripts/export_spec.py` → deterministic `config/indicators.yaml`, `countries.yaml`, `sources.yaml`.
- `scripts/scope_catalog.py` → `data/scope.csv` (68 rows) + `data/scope_coverage.csv` + summary.
- `scripts/00_env.py` → 26 assertions incl. firewall and key-format checks.
- `tests/test_config.py`, `tests/test_scope.py` → 12 tests, runnable with or without pytest.
- `docs/BUILD_CONTRACT.md` (rules C-01…C-12), `docs/DECISIONS.md` (D-R01…D-R21),
  `docs/VERIFICATION.md` (scoped pass + progress table).
- Marked `spec.py` as documentation-only; runtime reads `config/*.yaml`.
- Initialised git history with one baseline commit (Phase 2 deliverable + build scaffold).

## Next five actions

1. **Verify FRED rows** (25). Use the API metadata endpoint; write results into
   `docs/VERIFICATION.md` and the manifest. Acceptance: 25/25 have ID, frequency,
   start, end, units, SA status or a recorded reason for failure.
2. **Resolve OECD dataflows** for the 22 OECD rows. Cache one structure response per
   family; stay under 60 requests/hour. Acceptance: each row has a dataflow + key
   pattern or is marked unavailable.
3. **Resolve BOJ series keys** for the 18 Japanese rows. Acceptance as above.
4. **Write `fetch_fred.py` + manifest schema** (`series_key, source, source_id, url,
   retrieved_at, sha256, n_rows, start, end, status`). Acceptance: `make fetch` is
   idempotent and manifest rows equal scope rows.
5. **Build the USA BEAI label** (DFM + BBQ + diffusion) and compare with NBER
   1990, 2001, 2008 (and document 2020). This is the stop/go gate for the whole design.

## Open decisions (block their step, not this one)

| ID | Question | Default | Needed by |
|---|---|---|---|
| O-1 | Use pre-1990 history for long-series countries? | no | Step 6 (harmonise) |
| O-2 | India fallback if §19 fails? | Label B only, reported | Step 8 (labels) |
| O-3 | Threshold objective? | max F1 | Step 10 (harness) |
| O-4 | Widen scope to P0–P2 (68 → 140 rows)? | P0–P1 first | Step 4 (verification) |
| O-5 | COVID 2020 treatment + with/without evaluation? | keep, document, evaluate | Step 11 (experiments) |

## Session hand-off rule

Start a session by reading **this file + `docs/BUILD_CONTRACT.md` only**. Do not re-read
`spec.py`, `build.py` or `series_catalogue.csv`; they are large and already summarised here.
When a rule changes, update the contract, bump the hash, and note it above.
