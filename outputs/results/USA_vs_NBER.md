# USA BEAI label vs NBER chronology

Window 1990Q1–2025Q4 (144 quarters).
NBER = `USRECQ` (period after peak through trough). Label = DFM factor -> BBQ -> diffusion >= 0.50.

## Quarter-level agreement

| | NBER 1 | NBER 0 |
|---|---:|---:|
| label 1 | 13 | 1 |
| label 0 | 0 | 130 |

- accuracy 0.993 · precision 0.929 · recall 1.000 · F1 0.963
- USRECQ quarters: NBER 13, label 14

## Episode matching

| NBER peak–trough | USRECQ quarters | label peak–trough | overlap | peak diff | trough diff |
|---|---:|---|---:|---:|---:|
| 1990Q3–1991Q1 | 2 | 1990Q2–1991Q1 | 2 | -1 | 0 |
| 2001Q1–2001Q4 | 3 | 2001Q1–2001Q4 | 3 | 0 | 0 |
| 2007Q4–2009Q2 | 6 | 2007Q4–2009Q2 | 6 | 0 | 0 |
| 2019Q4–2020Q2 | 2 | 2019Q4–2020Q2 | 2 | 0 | 0 |

Matched 4/4 NBER episodes; 0 label episode(s) with no NBER counterpart.

## Retained label episodes

| peak | trough | duration | depth (SD) | diffusion | review flag |
|---|---|---:|---:|---:|---|
| 1990Q2 | 1991Q1 | 3 | 1.447 | 0.810 | no |
| 2001Q1 | 2001Q4 | 3 | 0.679 | 0.708 | no |
| 2007Q4 | 2009Q2 | 6 | 6.211 | 0.875 | no |
| 2019Q4 | 2020Q2 | 2 | 10.919 | 0.938 | no |

## Rejected candidate episodes

| peak | trough | duration | depth (SD) | diffusion | reason |
|---|---|---:|---:|---:|---|

## Robustness

| variant | candidates | kept | kept dates |
|---|---:|---:|---|
| baseline | 4 | 4 | 1990Q2->1991Q1; 2001Q1->2001Q4; 2007Q4->2009Q2; 2019Q4->2020Q2 |
| min_phase=3 | 3 | 3 | 1990Q2->1991Q1; 2001Q1->2001Q4; 2007Q4->2009Q2 |
| diffusion=0.60 | 4 | 4 | 1990Q2->1991Q1; 2001Q1->2001Q4; 2007Q4->2009Q2; 2019Q4->2020Q2 |
| sample ends 2019Q4 | 7 | 3 | 1990Q2->1991Q1; 2000Q4->2002Q1; 2007Q4->2009Q3 |

## Label B (technical GDP) cross-check

Two consecutive quarters of negative real GDP growth, no factor, no gate:

- episodes: 1990Q4–1991Q1, 2008Q3–2009Q2, 2020Q1–2020Q2
- NBER episodes caught: 3/4
- Label B is deliberately crude; it is a robustness label, not the primary target.

## Reading the discrepancies

- A label peak one quarter before the NBER peak is a boundary convention: the NBER date is the
  last quarter of expansion, and a quarterly factor can turn down inside that quarter.
- A label trough one quarter after the NBER trough means the factor stayed below its previous
  peak for one extra quarter; the contraction end is still inside the same episode.
- Episodes rejected by the diffusion gate are listed above with their diffusion value, not hidden.
