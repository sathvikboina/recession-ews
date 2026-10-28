# Scoped Verification Pass

Phase 2 left every series ID, date, unit, SA status and coverage figure as
`PENDING_VERIFICATION`. This file records the facts as they are checked, for the
**68 rows in `data/scope.csv` only** — not the 1,883-row catalogue (D-R16).

## Rules

1. Verify only rows in `data/scope.csv`. Do not fill the catalogue.
2. Never guess an ID, date or unit. If it cannot be confirmed, leave
   `PENDING_VERIFICATION` and record why.
3. Prefer the country's §7 chain order. A fact from a secondary source is recorded as
   secondary and does not close the item.
4. Record the retrieval date and the exact query used (URL or API call) for every fact.
5. Raw payloads go to `data/raw/<source>/<retrieved_at>/` and are never edited.
6. Update `data/manifest.parquet` (Step 5), not the source CSV, when collection starts.

## Fields to close per series

| Field | Acceptable evidence |
|---|---|
| source series ID | the series page or API metadata response |
| native frequency | API metadata / dataset definition |
| available start / end | first and last observation returned |
| units | metadata title or unit field |
| SA status | metadata (`SA`, `NSA`, `SCA`) |
| coverage of 1990Q1–2025Q4 | computed from the returned observations |
| revision class | provider documentation; else keep the class prior |

## Order of work

1. **FRED** (USA, and global series hosted there) — API metadata endpoint, scriptable.
2. **BIS** — bulk download; confirm series keys against the dataset listing.
3. **OECD** — SDMX; resolve one dataflow per family, cache the structure response,
   stay under 60 requests/hour.
4. **BOJ** — Time-Series Data Search API.
5. **RBI / MoSPI / NBS** — manual download, recorded file path + retrieval date.

## Progress

| Source | Rows in scope | Verified | Notes |
|---|---:|---:|---|
| FRED | 25 | 0 | 15 recalled IDs (not re-checked); 10 still unidentified |
| OECD | 22 | 0 | dataflow IDs unresolved (Q-15) |
| BOJ / Japanese official | 18 | 0 | API exists; series keys unresolved |
| DERIVED | 3 | n/a | no download; inputs must be verified |
| **Total** | **68** | **0** | |

## Log

Add one row per verification session. Do not delete rows; supersede them.

| Date | Source | Rows checked | Result | Checked by |
|---|---|---|---|---|
| 2026-10-29 | — | 0 | scaffolding only; no facts verified | — |

## Commands (Step 5 onward)

```bash
export FRED_API_KEY=...            # never commit
python scripts/fetch_fred.py --scope data/scope.csv --out data/raw/fred
python scripts/harmonize.py --in data/raw --out data/clean
```
