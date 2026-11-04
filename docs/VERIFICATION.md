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
6. The manifest (`data/manifest.csv`) records provenance; the source CSV is not edited.

## Progress

| Source | Rows in scope | Verified | Notes |
|---|---:|---:|---|
| FRED | 25 | 22 | 1 insufficient history (`PCEC96`, 52.8%), 2 derived; 23 scope downloads + 1 auxiliary chronology |
| OECD | 22 | 0 | dataflow IDs unresolved (Q-15) |
| BOJ / Japanese official | 18 | 0 | API exists; series keys unresolved |
| DERIVED | 3 | n/a | 3 defined, 0 built: `harmonize.py` consumes `VERIFIED` downloads only, and the JPN/DEU inputs are still pending |
| **Total** | **68** | **22** | USA complete except one rejected variant |

Run date: **2026-10-29**. Verification facts refreshed **2026-11-04** (stale `DPIC96`
row removed; see `data/superseded_series.csv`). Downloads:
`data/raw/fred/2026-10-29/`.
Verification facts: `data/fred_verification.csv`. Resolution table:
`data/series_resolution.csv`. Hashes: `data/manifest.csv`.

## FRED verification (USA)

Coverage is the share of the 144 quarters in 1990Q1–2025Q4 for which the series has
a complete observation at native frequency (a monthly quarter needs all three months).

| scope key | FRED id | freq | SA | first | last | window | status |
|---|---|---|---|---|---|---|---|
| `USA.ACT_GDP_REAL.Q.NA` | `GDPC1` | Q | SA | 1947-01-01 | 2026-04-01 | 100.0% | VERIFIED |
| `USA.ACT_IP.M.STD` | `INDPRO` | M | SA | 1919-01-01 | 2026-09-01 | 100.0% | VERIFIED |
| `USA.ACT_EMP.Q.NA` | `PAYEMS` | M | SA | 1939-01-01 | 2026-09-01 | 100.0% | VERIFIED |
| `USA.ACT_HOURS.Q.STD` | `HOANBS` | Q | SA | 1947-01-01 | 2026-04-01 | 100.0% | VERIFIED |
| `USA.ACT_RINC.Q.STD` | `W875RX1` | M | SA | 1959-01-01 | 2026-08-01 | 100.0% | VERIFIED |
| `USA.ACT_CONS.Q.NA` | `PCECC96` | Q | SA | 1947-01-01 | 2026-04-01 | 100.0% | VERIFIED |
| `USA.ACT_RETAIL.M.STD` | `RRSFS` | M | SA | 1992-01-01 | 2026-09-01 | 93.8% | VERIFIED |
| `USA.ACT_INV.Q.STD` | `GPDIC1` | Q | SA | 1947-01-01 | 2026-04-01 | 100.0% | VERIFIED |
| `USA.ACT_CONS.M.US` | `PCEC96` | M | SA | 2007-01-01 | 2026-08-01 | 52.8% | LOW_COVERAGE |
| `USA.ACT_EMP.M.ESTAB` | `PAYEMS` | M | SA | 1939-01-01 | 2026-09-01 | 100.0% | VERIFIED |
| `USA.ACT_EMP.M.LFS` | `CE16OV` | M | SA | 1948-01-01 | 2026-09-01 | 99.3% | VERIFIED |
| `USA.ACT_RINC.M.US` | `DSPIC96` | M | SA | 1959-01-01 | 2026-08-01 | 100.0% | VERIFIED |
| `USA.FIN_CREDIT_GDP.Q.STD` | `QUSPAM770A` | Q | NSA | 1947-10-01 | 2025-10-01 | 100.0% | VERIFIED |
| `USA.FIN_CREDIT_GAP.Q.STD` | derived from `QUSPAM770A` | Q | — | — | — | — | DERIVED |
| `USA.FIN_EQUITY.M.STD` | `NASDAQCOM` | D | NSA | 1971-02-05 | 2026-10-27 | 100.0% | VERIFIED |
| `USA.FIN_HOUSEPRICE.M.US_CS` | `CSUSHPISA` | M | SA | 1987-01-01 | 2026-08-01 | 100.0% | VERIFIED |
| `USA.FIN_HOUSEPRICE.Q.OECD_BIS` | `USSTHPI` | Q | NSA | 1975-01-01 | 2026-04-01 | 100.0% | VERIFIED |
| `USA.FIN_LONG.M.STD` | `GS10` | M | NSA | 1953-04-01 | 2026-09-01 | 100.0% | VERIFIED |
| `USA.FIN_POLICY.M.STD` | `FEDFUNDS` | M | NSA | 1954-07-01 | 2026-09-01 | 100.0% | VERIFIED |
| `USA.FIN_SHORT.M.STD` | `TB3MS` | M | NSA | 1934-01-01 | 2026-09-01 | 100.0% | VERIFIED |
| `USA.FIN_SLOPE.M.DERIVED` | `GS10 - TB3MS` | M | — | — | — | — | DERIVED |
| `USA.LAB_UNEMP.M.STD` | `UNRATE` | M | SA | 1948-01-01 | 2026-09-01 | 99.3% | VERIFIED |
| `USA.PRC_CPI.M.STD` | `CPIAUCSL` | M | SA | 1947-01-01 | 2026-09-01 | 99.3% | VERIFIED |
| `USA.SEN_BCI.M.STD` | `BSCICP03USM665S` | M | SA | 1950-01-01 | 2024-01-01 | 94.4% | VERIFIED |
| `USA.SEN_CCI.M.STD` | `UMCSENT` | M | NSA | 1952-11-01 | 2026-09-01 | 100.0% | VERIFIED |
| `USA.NBER.Q` (aux) | `USRECQ` | Q | NSA | 1854-10-01 | 2026-07-01 | 100.0% | VERIFIED |

## Rejections and substitutions (recorded, not hidden)

| Item | Decision | Reason |
|---|---|---|
| `PCEC96` (`ACT_CONS.M.US`) | rejected: 52.8% coverage | FRED monthly real PCE starts 2007. The quarterly variant `PCECC96` covers the label; the monthly predictor copy is dropped. |
| `DPIC96` for `ACT_RINC.Q.STD` | replaced by `W875RX1` | `DPIC96` is monthly (frequency mismatch) and real DPI including transfers is counter-cyclical (COVID stimulus). Coincident indices use income excluding transfers. See D-R23; the retired row is retained in `data/superseded_series.csv`. |
| `PNFIC1` for `ACT_INV.Q.STD` | replaced by `GPDIC1` | `PNFIC1` (real nonresidential fixed investment) only starts 2007 in the current FRED vintage; `PNFIC1` discontinued (`PNFIC96`) ends 2017. `GPDIC1` (real gross private domestic investment) is complete from 1947. Broad proxy, documented. |
| `WILL5000IND` for `FIN_EQUITY` | replaced by `NASDAQCOM` | `WILL5000IND` returns 301/404 (moved). `SP500` has only 10 years. `NASDAQCOM` starts 1971. |
| OECD/BIS house price for `FIN_HOUSEPRICE.Q.OECD_BIS` | substituted `USSTHPI` | No OECD/BIS series resolved in the FRED chain; FHFA all-transactions HPI is the official US quarterly index from 1975. |
| `HOANBS` for `ACT_HOURS.Q.STD` | accepted | Nonfarm business hours, index 2017=100, SA, quarterly from 1947. |
| `RRSFS` for `ACT_RETAIL.M.STD` | accepted with caveat | Real retail and food services sales from 1992 → 93.8% of the window, above the 70% gate but the first eight quarters are missing and stay missing. |
| `BSCICP03USM665S` for `SEN_BCI` | accepted with caveat | OECD business confidence ends 2024-01 in FRED; 94.4% coverage, last year stale. Acceptable as a predictor; refresh from OECD direct later. |

## Log

| Date | Source | Rows checked | Result | Checked by |
|---|---|---|---|---|
| 2026-10-29 | FRED | 24 downloads + 2 derived | 22 verified, 1 low coverage, 2 derived | automated (`scripts/fetch_fred.py`) |
| 2026-11-04 | FRED | provenance maintenance | removed stale `DPIC96` duplicate; one active row per scope key | review fix |
| 2026-10-29 | — | JPN, DEU, OECD, BOJ | not started | — |

## Commands

```bash
python scripts/fetch_fred.py            # verify + download USA FRED series
python scripts/harmonize.py             # quarterly panel + growth matrix
python scripts/03_labels.py             # DFM -> BBQ -> diffusion label
python scripts/04_compare_nber.py       # NBER agreement report
```

Authentication: none required. The FRED CSV endpoint
(`https://fred.stlouisfed.org/graph/fredgraph.csv?id=<ID>`) is public. Metadata is
read from the series page. Requests go through `curl` because outbound
`urllib`/`requests` reads stall in this environment (see `scripts/fetch_fred.py`).
