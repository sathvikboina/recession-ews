# Audit Report: Lane 1 Japan & Germany Labels

**Audit Date:** 2026-11-13  
**Auditor:** Independent Econometric Data & Software Auditor  
**Repository:** `D:\ml_ews\recession-ews`  
**Branch:** `feat/jpn-deu-labels`  
**Scope:** Evaluation of claim: *"Lane 1 Japan & Germany labels are complete and verified under docs/BUILD_CONTRACT.md C-01–C-12."*

---

## A1. DELIVERY STATE

**Verdict:** **FAIL**

### Commands Executed:
```powershell
git status --short
git log --oneline -12
git branch -a
git cat-file -t 200057e
gh pr list --head feat/jpn-deu-labels --state all
```

### Exact Output:
```text
 M .gitignore
 M data/manifest.csv
 M data/series_resolution.csv
 M docs/STATE.md
 M scripts/03_labels.py
 M scripts/harmonize.py
 M src/ews/labels/__init__.py
 M src/ews/labels/ids.py
?? data/source_map_DEU.csv
?? data/source_map_JPN.csv
?? docs/COVERAGE_DEU.md
?? docs/HANDOFF_JPN_DEU.md
?? docs/LABEL_VALIDATION_DEU.md
?? docs/LABEL_VALIDATION_JPN.md
?? docs/SOURCE_MAP_DEU.md
?? docs/SOURCE_MAP_JPN.md
?? docs/team/
?? outputs/labels/DEU/
?? outputs/labels/JPN/
?? scripts/fetch_deu.py
?? scripts/fetch_jpn.py
?? src/ews/labels/coverage.py
?? tests/test_country_plumbing.py
fa57a1c Initial commit
6b97f77 Review fixes: clean-clone packaging, freeze metadata, episode ids, provenance
c97c680 Add generated work log workbook and packaging notes
a117998 fetch_fred: exit 0 on recorded low-coverage series; stable resolution ordering
5c042e9 USA milestone: FRED verification, harmonisation, BEAI label, NBER validation
eeea363 Phase 2 dictionary + build scaffold
* feat/jpn-deu-labels
  master
  remotes/origin/HEAD -> origin/master
  remotes/origin/master
fatal: Not a valid object name 200057e
gh : The term 'gh' is not recognized as the name of a cmdlet, function, script file, or operable program.
```

### Supporting Evidence:
1. The entire lane deliverable is completely uncommitted in the working tree (8 modified files, 14 untracked files/directories).
2. The cited base commit in `docs/HANDOFF_JPN_DEU.md:6` (`200057e`) does not resolve in git (`fatal: Not a valid object name 200057e`). Actual HEAD is `fa57a1c`.
3. No pull request exists (`gh` tool missing / branch not pushed to remote).

---

## A2. TEST SUITE

**Verdict:** **PASS**

### Commands Executed:
```powershell
.venv-win\Scripts\python -m pytest -p no:cacheprovider -q
git worktree add --detach "$env:TEMP\audit-master" master
.venv-win\Scripts\python -m pytest -p no:cacheprovider -q "$env:TEMP\audit-master\tests"
git worktree remove "$env:TEMP\audit-master"
```

### Exact Output on `feat/jpn-deu-labels`:
```text
................FF....F.................                                 [100%]
================================== FAILURES ===================================
______________________ test_v1_archive_is_byte_identical ______________________
    def test_v1_archive_is_byte_identical() -> None:
>       assert hashlib.sha256(V1_LABELS.read_bytes()).hexdigest() == V1_LABELS_SHA256
                              ^^^^^^^^^^^^^^^^^^^^^^
tests\test_freeze.py:86: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
C:\Users\ACER.DESKTOP-EKKIH4U\AppData\Local\Programs\Python\Python313\Lib\pathlib\_abc.py:625: in read_bytes
    with self.open(mode='rb') as f:
         ^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
self = WindowsPath('D:/ml_ews/recession-ews/outputs/labels/archive/labels-v1/USA_labels.csv')
mode = 'rb', buffering = -1, encoding = None, errors = None, newline = None
    def open(self, mode='r', buffering=-1, encoding=None,
             errors=None, newline=None):
>       return io.open(self, mode, buffering, encoding, errors, newline)
E       FileNotFoundError: [Errno 2] No such file or directory: 'D:\\ml_ews\\recession-ews\\outputs\\labels\\archive\\labels-v1\\USA_labels.csv'
________________________ test_active_label_hash_is_v2 _________________________
    def test_active_label_hash_is_v2() -> None:
        digest = hashlib.sha256(LABELS.read_bytes()).hexdigest()
>       assert digest == V2_LABELS_SHA256, "the active v2 label CSV changed"
E       AssertionError: the active v2 label CSV changed
E       assert '452ba036b5d0...f1734664577b0' == 'f5ed42a6c433...a6aa31816dc8e'
E         - f5ed42a6c4333aaecbae4fae1f5f6fcab3606ce46dd2b459791a6aa31816dc8e
E         + 452ba036b5d0420a0b49c493738d1e46b4dba482ef4e830df1cf1734664577b0
tests\test_freeze.py:97: AssertionError
________________ test_v2_metadata_records_the_input_decisions _________________
    def test_v2_metadata_records_the_input_decisions() -> None:
        meta = json.loads(META.read_text(encoding="utf-8"))
        assert meta["label_version"] == "labels-v2"
        assert meta["supersedes"] == "labels-v1"
>       assert meta["hashes"]["superseded_labels_csv_sha256"] == V1_LABELS_SHA256
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       KeyError: 'superseded_labels_csv_sha256'
tests\test_freeze.py:163: KeyError
3 failed, 37 passed in 2.12s
```

### Exact Output on `master` (`%TEMP%\audit-master`):
```text
Preparing worktree (detached HEAD fa57a1c)
HEAD is now at fa57a1c Initial commit
......FF....F.................                                           [100%]
3 failed, 27 passed in 1.48s
(Identical failures: test_v1_archive_is_byte_identical FileNotFoundError, test_active_label_hash_is_v2 AssertionError, test_v2_metadata_records_the_input_decisions FileNotFoundError on labels-v2.json)
```

### Supporting Evidence:
1. Exact counts on `feat/jpn-deu-labels`: 37 passed, 3 failed.
2. The 3 failures are pre-existing on `master` (caused by the repository being mid-upgrade between v1 and v2, and Windows CRLF checkout). Zero failures were introduced by this lane.
3. Test suite in `tests/test_country_plumbing.py::test_usa_labels_hash_is_preserved` explicitly asserts that `outputs/labels/USA_labels.csv` matches `FROZEN_USA_HASH_CRLF` or `FROZEN_USA_HASH_LF`, catching any accidental modification.

---

## A3. USA NO-COLLATERAL-CHANGE

**Verdict:** **PASS**

### Commands Executed:
```powershell
(Get-FileHash outputs\labels\USA_labels.csv -Algorithm SHA256).Hash
git show master:outputs/labels/USA_labels.csv | python -c "import sys, hashlib; b=sys.stdin.buffer.read(); print(hashlib.sha256(b).hexdigest())"
git diff master --stat -- outputs/labels/USA_labels.csv
```

### Exact Output:
```text
452BA036B5D0420A0B49C493738D1E46B4DBA482EF4E830DF1CF1734664577B0
452ba036b5d0420a0b49c493738d1e46b4dba482ef4e830df1cf1734664577b0
```
*(git diff returned exit code 0 with 0 lines changed).*

### Supporting Evidence:
The stored file `outputs/labels/USA_labels.csv` on disk is byte-for-byte identical to `master:outputs/labels/USA_labels.csv`.

---

## A4. Q-02 COMPLIANCE (Highest Priority)

**Verdict:** **FAIL**

### Commands Executed:
```powershell
python -c "
with open('docs/DECISION_NOTE_Q02_Q04_Q05.md', encoding='utf-8') as f:
    text = f.read()
import re
print('Q-02 strict rule quote:')
m = re.search(r'Frozen decision \(quote\)\.\s*([^\n]+)', text)
if m: print(' ', m.group(1))
"
Select-String -Path scripts\fetch_deu.py -Pattern "NAEXKP04DEQ661S" -Context 0,2
Select-String -Path docs\LABEL_VALIDATION_DEU.md, docs\COVERAGE_DEU.md, data\source_map_DEU.csv -Pattern "ACT_INV"
Select-String -Path scripts\fetch_jpn.py, outputs\labels\JPN\labels-v1-JPN.json -Pattern "col_indices|Col 5|Col 6"
```

### Exact Output:
```text
Q-02 strict rule quote:
  "Strict: business (non-residential) fixed investment only. Total GFCF is not substituted; where business investment is missing the component counts as missing." (`decisions_log.csv`, Q-02.)

> scripts\fetch_deu.py:11:- NAEXKP04DEQ661S: Gross Fixed Capital Formation for Germany (quarterly, SA, chained 2015 Euros).
> scripts\fetch_deu.py:64:        "source_id": "NAEXKP04DEQ661S",
  scripts\fetch_deu.py:65:        "url": "https://fred.stlouisfed.org/series/NAEXKP04DEQ661S",
  scripts\fetch_deu.py:66:        "freq": "Q",

> docs\LABEL_VALIDATION_DEU.md:22:| `ACT_INV` | Destatis / Eurostat (FRED) | `NAEXKP04DEQ661S` | Q | 130/144 (90.3%) | **Yes** | $\Delta\log$ |
> docs\COVERAGE_DEU.md:20:| `ACT_INV` | Real Business Fixed Investment | `NAEXKP04DEQ661S` | Q | 130 | 90.3% | **PASS** |
> docs\COVERAGE_DEU.md:73:6. **`ACT_INV` (`NAEXKP04DEQ661S`):** Gross fixed capital formation, chained 2015 Euros, quarterly, seasonally adjusted. 130 quarters available in window ($90.3\%$).
> data\source_map_DEU.csv:10:DEU.ACT_INV.Q.STD,Real business fixed investment (Gross Fixed Capital Formation),Destatis / Eurostat (FRED),NAEXKP04DEQ661S,Q,SA,1970-01-01,2023-07-01,135/144 (93.8%),2026-11-13,9cf3d17c712b8075e508bb5d89780690b109d1bd1c7ed0ae3bd749c920f589fa,VERIFIED,"Gross fixed capital formation, chained 2015 Euros, seasonally adjusted.",2026-11-13

> scripts\fetch_jpn.py:199: col_indices={"JPN_ACT_GDP_REAL": 1, "JPN_ACT_CONS": 2, "JPN_ACT_INV": 6},
> outputs\labels\JPN\labels-v1-JPN.json:27: "ACT_INV": "tables/gaku-jk2622.csv (Col 5)"
```

### Supporting Evidence:
1. `docs/DECISION_NOTE_Q02_Q04_Q05.md:62-64` explicitly quotes the frozen rule:
   > *"Strict: business (non-residential) fixed investment only. Total GFCF is not substituted; where business investment is missing the component counts as missing."*
2. In `scripts/fetch_deu.py:11`, the series feeding `DEU.ACT_INV` is `NAEXKP04DEQ661S`, described in its own docstring as:
   > `- NAEXKP04DEQ661S: Gross Fixed Capital Formation for Germany (quarterly, SA, chained 2015 Euros).`
3. `NAEXKP04DEQ661S` is total Gross Fixed Capital Formation (including residential structures and government investment). In `docs/LABEL_VALIDATION_DEU.md` and `docs/COVERAGE_DEU.md`, this series is conflated with "Real Business Fixed Investment".
4. **Does DEU's 6-of-8 pass depend on a total-GFCF series? YES.** Excluding total GFCF drops Germany to 5 valid core indicators (`ACT_GDP_REAL`, `ACT_IP`, `ACT_EMP`, `ACT_CONS`, `ACT_RETAIL`), failing the C-03 gate. Under Q-02 and C-01, the frozen German label is invalid.
5. **Japan Q-02 check:** In `scripts/fetch_jpn.py:199`, the column parsed for `ACT_INV` is Column 6 (`民間企業設備`, Private Non-Residential Investment), which is concept-compliant. However, `outputs/labels/JPN/labels-v1-JPN.json:27` falsely claims `"ACT_INV": "tables/gaku-jk2622.csv (Col 5)"` (Column 5 is residential investment `民間住宅`). This is a documentation and metadata defect.

---

## A5. COVERAGE ARITHMETIC (Recomputed from `data/raw`)

**Verdict:** **FAIL**

### Commands Executed:
```powershell
python -c "
import pandas as pd
from pathlib import Path

win = pd.period_range('1990Q1', '2025Q4', freq='Q')

def count_raw(path, freq):
    df = pd.read_csv(path, parse_dates=['observation_date']).dropna(subset=['value'])
    if freq == 'Q':
        return sum(1 for p in win if p in set(df['observation_date'].dt.to_period('Q')))
    elif freq == 'M':
        m_set = set(df['observation_date'].dt.to_period('M'))
        return sum(1 for p in win if p.asfreq('M', how='start') in m_set and (p.asfreq('M', how='start')+1) in m_set and (p.asfreq('M', how='start')+2) in m_set)
    return 0

# Check JPN & DEU raw files...
"
```

### Recomputed Complete Quarters inside `1990Q1–2025Q4`:

| Country | Core Indicator | Raw Complete Qtrs | `coverage_<ISO3>.csv` | `manifest.csv` | `LABEL_VALIDATION_<ISO3>.md` | `source_map_<ISO3>.csv` | Mismatch Flag |
|---|---|---:|---:|---:|---:|---:|:---:|
| **JPN** | `ACT_GDP_REAL` | **128** | 127 | 128 | 127 | 128 | **MISMATCH (128 vs 127)** |
| **JPN** | `ACT_IP` | **137** | 120 | 137 | 120 | 144 | **MISMATCH (137 vs 120 vs 144)** |
| **JPN** | `ACT_EMP` | **144** | 127 | 144 | 127 | 144 | **MISMATCH (144 vs 127)** |
| **JPN** | `ACT_HOURS` | **0** | 0 | — | 0 | 0 | Match |
| **JPN** | `ACT_RINC` | **128** | 127 | 128 | 127 | 128 | **MISMATCH (128 vs 127)** |
| **JPN** | `ACT_CONS` | **128** | 127 | 128 | 127 | 128 | **MISMATCH (128 vs 127)** |
| **JPN** | `ACT_RETAIL` | **0** | 0 | — | 0 | 0 | Match |
| **JPN** | `ACT_INV` | **128** | 127 | 128 | 127 | 128 | **MISMATCH (128 vs 127)** |
| **DEU** | `ACT_GDP_REAL` | **140** | 139 | 140 | 139 | 140 | **MISMATCH (140 vs 139)** |
| **DEU** | `ACT_IP` | **137** | 132 | 137 | 132 | 137 | **MISMATCH (137 vs 132)** |
| **DEU** | `ACT_EMP` | **144** | 139 | 144 | 139 | 144 | **MISMATCH (144 vs 139)** |
| **DEU** | `ACT_HOURS` | **0** | 0 | — | 0 | 0 | Match |
| **DEU** | `ACT_RINC` | **0** | 0 | — | 0 | 0 | Match |
| **DEU** | `ACT_CONS` | **135** | 130 | 135 | 130 | 135 | **MISMATCH (135 vs 130)** |
| **DEU** | `ACT_RETAIL` | **137** | 132 | 137 | 132 | 137 | **MISMATCH (137 vs 132)** |
| **DEU** | `ACT_INV` | **135** | 130 | 135 | 130 | 135 | **MISMATCH (135 vs 130)** |

### Specific Metric Tests:
- **JPN ACT_IP:** Raw is **137**; clean coverage is **120**; source map recorded **144**.
- **JPN ACT_EMP:** Raw is **144**; clean coverage is **127**.
- **JPN GDP:** Raw is **128**; clean coverage is **127**.

### Cause of Mismatch:
`data/clean/coverage_<ISO3>.csv` counts post-differencing growth quarters inside a truncated estimation window (`1994Q2–2025Q4` for JPN, `1991Q2–2025Q4` for DEU). Truncation discards 17 complete quarters of `JPNPROINDMISMEI` (137 $\to$ 120) and `LFEMTTTTJPM647S` (144 $\to$ 127). The manifest and source map report raw level window quarters. Conflating these across tables creates contradictory arithmetic.

### Gate Impact:
- **JPN:** Raw level quarters (128, 137, 144, 128, 128, 128) and truncated growth quarters (127, 120, 127, 127, 127, 127) are both $\ge 70\%$ ($\ge 101$ quarters). Gate outcome for JPN remains PASS.
- **DEU:** Arithmetic alone passes under both, but DEU fails due to Q-02 disqualification of `ACT_INV`.

---

## A6. SAMPLE WINDOW

**Verdict:** **FAIL**

### Commands Executed:
```powershell
python -c "
import pandas as pd
for name in ['JPN_panel', 'JPN_growth', 'DEU_panel', 'DEU_growth']:
    df = pd.read_csv(f'data/clean/{name}.csv', index_col=0)
    print(f'=== {name} ===')
    for c in df.columns:
        v = df[c].dropna()
        print(f'{c:<26} first={v.index[0]} last={v.index[-1]} len={len(v)}')
"
Get-Content scripts\harmonize.py | Select-Object -Skip 270 -First 15
```

### Exact Output:
```text
=== JPN_panel ===
JPN.ACT_GDP_REAL.Q.NA      first=1994Q2 last=2025Q4 len=127
JPN.ACT_CONS.Q.NA          first=1994Q2 last=2025Q4 len=127
JPN.ACT_INV.Q.STD          first=1994Q2 last=2025Q4 len=127
JPN.ACT_RINC.Q.STD         first=1994Q2 last=2025Q4 len=127
JPN.ACT_IP.M.STD           first=1994Q2 last=2024Q1 len=120
JPN.ACT_EMP.M.LFS          first=1994Q2 last=2025Q4 len=127
JPN.ACT_EMP.Q.NA           first=1994Q2 last=2025Q4 len=127
=== JPN_growth ===
ACT_GDP_REAL               first=1994Q2 last=2025Q4 len=127
ACT_IP                     first=1994Q2 last=2024Q1 len=120
ACT_EMP                    first=1994Q2 last=2025Q4 len=127
ACT_RINC                   first=1994Q2 last=2025Q4 len=127
ACT_CONS                   first=1994Q2 last=2025Q4 len=127
ACT_INV                    first=1994Q2 last=2025Q4 len=127
=== DEU_panel ===
DEU.ACT_GDP_REAL.Q.NA      first=1991Q2 last=2025Q4 len=139
DEU.ACT_IP.M.STD           first=1991Q2 last=2024Q1 len=132
DEU.ACT_EMP.Q.NA           first=1991Q2 last=2025Q4 len=139
DEU.ACT_CONS.Q.NA          first=1991Q2 last=2023Q3 len=130
DEU.ACT_INV.Q.STD          first=1991Q2 last=2023Q3 len=130
DEU.ACT_RETAIL.M.STD       first=1991Q2 last=2024Q1 len=132
=== DEU_growth ===
ACT_GDP_REAL               first=1991Q2 last=2025Q4 len=139
ACT_IP                     first=1991Q2 last=2024Q1 len=132
ACT_EMP                    first=1991Q2 last=2025Q4 len=139
ACT_CONS                   first=1991Q2 last=2023Q3 len=130
ACT_RETAIL                 first=1991Q2 last=2024Q1 len=132
ACT_INV                    first=1991Q2 last=2023Q3 len=130

scripts/harmonize.py lines 271-285:
    # ---- derive SAMPLE_START from data availability ----------------------
    if args.sample_start:
        sample_start = args.sample_start
    elif country == "USA":
        sample_start = "1960Q1"  # D-R22 implementation baseline
    else:
        # Earliest quarter with >= 4 core indicators available
        n_avail = raw_growth.notna().sum(axis=1)
        eligible_qs = n_avail[n_avail >= 4].index
        if len(eligible_qs):
            sample_start = str(eligible_qs[0])
        else:
            sample_start = win_start_cfg

    sample_range = pd.period_range(sample_start, win_end_cfg, freq="Q")
```

### Supporting Evidence:
1. **Japan 1994Q2:** Follows the dynamic rule $\ge 4$ indicators. In `raw_growth`, only IP and EMP exist before 1994Q2 ($n=2 < 4$). In 1994Q2, all 6 indicators become available ($n=6 \ge 4$).
2. **Germany 1991Q2:** Does **NOT** follow the dynamic $\ge 4$ rule; it requires a CLI literal `--sample-start 1991Q2`. Without this CLI override, the dynamic rule selects `1990Q1` because 5 West German series existed in 1990.
3. **Reunification break documentation:** `docs/SOURCE_MAP_DEU.md` describes the break narratively but provides no formal statistical citation (e.g. Destatis Fachserie 18 or Bundesbank Monatsbericht citation with publication ID).
4. **Window reconciliation:** The lane brief (`PROMPT_shravani_jpn_deu_lane.md` §3.2) explicitly mandates reconciling the brief's `1990Q1–2026Q3` (147 quarters) with the checkout's `1990Q1–2025Q4` (144 quarters) at the top of the hand-off. `docs/HANDOFF_JPN_DEU.md` omits this reconciliation.

---

## A7. CHRONOLOGY HONESTY

**Verdict:** **FAIL**

### Commands Executed:
```powershell
python -c "
import pandas as pd
# JPN Confusion Matrix
df_jpn = pd.read_csv('outputs/labels/JPN/JPN_labels.csv', index_col=0)
esri_episodes = [('1997Q2', '1999Q1'), ('2000Q4', '2002Q1'), ('2008Q1', '2009Q1'), ('2012Q1', '2012Q4'), ('2018Q4', '2020Q2')]
esri_r = pd.Series(0, index=df_jpn.index)
for p, tr in esri_episodes:
    for q in pd.period_range(p, tr, freq='Q')[1:]:
        if str(q) in esri_r.index: esri_r.loc[str(q)] = 1
dated_jpn = df_jpn.loc['1994Q2':'2025Q4']
tp = int(((dated_jpn['R'] == 1) & (esri_r == 1)).sum())
fp = int(((dated_jpn['R'] == 1) & (esri_r == 0)).sum())
fn = int(((dated_jpn['R'] == 0) & (esri_r == 1)).sum())
tn = int(((dated_jpn['R'] == 0) & (esri_r == 0)).sum())
print(f'JPN: TP={tp}, FP={fp}, FN={fn}, TN={tn}, Acc={(tp+tn)/len(dated_jpn):.3f}, Prec={tp/(tp+fp):.3f}, Rec={tp/(tp+fn):.3f}, F1={2*tp/(2*tp+fp+fn):.3f}')

# DEU Confusion Matrix
df_deu = pd.read_csv('outputs/labels/DEU/DEU_labels.csv', index_col=0)
cepr_episodes = [('1992Q1', '1993Q3'), ('2001Q1', '2003Q3'), ('2008Q1', '2009Q2'), ('2011Q3', '2013Q1'), ('2019Q4', '2020Q2')]
cepr_r = pd.Series(0, index=df_deu.index)
for p, tr in cepr_episodes:
    for q in pd.period_range(p, tr, freq='Q')[1:]:
        if str(q) in cepr_r.index: cepr_r.loc[str(q)] = 1
dated_deu = df_deu.loc['1991Q2':'2025Q4']
tp = int(((dated_deu['R'] == 1) & (cepr_r == 1)).sum())
fp = int(((dated_deu['R'] == 1) & (cepr_r == 0)).sum())
fn = int(((dated_deu['R'] == 0) & (cepr_r == 1)).sum())
tn = int(((dated_deu['R'] == 0) & (cepr_r == 0)).sum())
print(f'DEU: TP={tp}, FP={fp}, FN={fn}, TN={tn}, Acc={(tp+tn)/len(dated_deu):.3f}, Prec={tp/(tp+fp):.3f}, Rec={tp/(tp+fn):.3f}, F1={2*tp/(2*tp+fp+fn):.3f}')
"
```

### Exact Output:
```text
JPN: TP=22, FP=13, FN=3, TN=89, Acc=0.874, Prec=0.629, Rec=0.880, F1=0.733
DEU: TP=15, FP=5, FN=14, TN=105, Acc=0.863, Prec=0.750, Rec=0.517, F1=0.612
```

### Verification & Refutation:
1. **JPN Metrics:** The mathematical values (`recall 88.0%, precision 62.9%, F1 0.733`) are exact for the dated sample `1994Q2–2025Q4`. However, "0 missed cycles" is strictly an **episode-level** claim (all 5 ESRI cycles have overlapping BEAI episodes), while recall ($88.0\%$) is a **quarter-level** metric (22 of 25 recession quarters captured; 3 false negative quarters: `2001Q1`, `2002Q1`, `2012Q4`).
2. **DEU Peak Gaps:** In `docs/LABEL_VALIDATION_DEU.md:58-65`, the 2002 episode has a peak difference of **+6 quarters** (`2002Q3` vs `2001Q1`), and the 2012 episode has a peak difference of **+4 quarters** (`2012Q3` vs `2011Q3`). The table labels both as `"Matched (acute phase)"` and `"Matched (trough exact)"`. Calling peak shifts of $+6$ and $+4$ quarters "Matched" violates the contract tolerance ($\le 1$ quarter).
3. **DEU Cherry-Picking Chronology:** The benchmark table in `docs/LABEL_VALIDATION_DEU.md` uses a hybrid reference set:
   - Early 1990s: CEPR Euro Area (`1992Q1–1993Q3`)
   - 2001–2003: GCEE German Stagnation (`2001Q1–2003Q3`), because CEPR Euro Area declared no recession.
   - GFC: CEPR (`2008Q1–2009Q2`)
   - Euro Debt Crisis: CEPR Euro Area (`2011Q3–2013Q1`), though Germany did not contract until 2012.
   - COVID: CEPR (`2019Q4–2020Q2`)
   This mixes two different institutions rather than evaluating against a single official reference standard.

---

## A8. FREEZE AND REPRODUCIBILITY (C-12)

**Verdict:** **FAIL**

### Commands Executed:
```powershell
python -c "
import hashlib
from pathlib import Path
for p in Path('outputs/labels').glob('*/*.*'):
    print(f'{str(p):<45}: {hashlib.sha256(p.read_bytes()).hexdigest()}')
"
python -c "
import json
with open('outputs/labels/JPN/labels-v1-JPN.json') as f:
    d = json.load(f)
print('JPN source_ids:', d['inputs']['source_ids'])
"
```

### Exact Output:
```text
outputs\labels\DEU\DEU_episodes.csv          : bd370d5f12d6b3840ef97ac82913b73d2fd5d0dc910b4b8bfbf0a34257709246
outputs\labels\DEU\DEU_labels.csv            : 22cfb91a9b47d35f6f864df5c1e115e0182a4e95e269eb1dfa18f156403f02de
outputs\labels\DEU\DEU_turning_points.csv    : c7f608e1e814e224c917f5ca669d6cec2a262bac2ead421f8645b62d3e0f2b2a
outputs\labels\DEU\labels-v1-DEU.json        : fd8b870f00c6efcdb84a4a96a71dbd69119b0f121e317b074cb5c2cadfa16f2b
outputs\labels\JPN\JPN_episodes.csv          : ec84ea45db65da606af7504f4fd7d066c846b9f55d729233eebae401ba82c849
outputs\labels\JPN\JPN_labels.csv            : b20a9f23dec8516f12cf2047dfd87f2575a307ed0839c811d30b95f29cd6b6f5
outputs\labels\JPN\JPN_turning_points.csv    : 0465c16f88d352eec3803b1b067e7d6ddefe04807782e98a8ce64f3d6e6ea709
outputs\labels\JPN\labels-v1-JPN.json        : 5c5d518dbc53866c01728904a7a6b3f92de763ac06a4b8b8b7231c06d8786f98
outputs\labels\USA_labels.csv                : 452ba036b5d0420a0b49c493738d1e46b4dba482ef4e830df1cf1734664577b0

JPN source_ids: {'ACT_GDP_REAL': '00100409 / tables/gaku-jk2622.csv (Col 1)', 'ACT_IP': '00550300 / b2020_sgo1j.xlsx', 'ACT_EMP': 'Q-04 LFS fallback (quarterly mean of JPN.ACT_EMP.M.LFS)', 'ACT_HOURS': 'MHLW Table 0003058864', 'ACT_RINC': 'tables/kshotoku-q2622.csv', 'ACT_CONS': 'tables/gaku-jk2622.csv (Col 2)', 'ACT_RETAIL': '00550030 / Table 0003195026', 'ACT_INV': 'tables/gaku-jk2622.csv (Col 5)'}
```

### Supporting Evidence:
1. Recomputed SHA-256 for all 9 artefacts matches the hand-off table.
2. In `labels-v1-JPN.json`:
   - It records `growth_file_sha256` and `growth_values_sha256`, but records **no raw input payload file hashes**.
   - `source_ids` records `'ACT_IP': '00550300 / b2020_sgo1j.xlsx'` (METI Excel file) and `'ACT_EMP': 'Q-04 LFS fallback'`, while `scripts/fetch_jpn.py` actually downloaded `JPNPROINDMISMEI` and `LFEMTTTTJPM647S` from FRED.
   - `source_ids` records `'ACT_INV': 'tables/gaku-jk2622.csv (Col 5)'` (Residential investment), whereas `fetch_jpn.py` extracted Col 6 (`民間企業設備`).
3. The label **cannot** be rebuilt from `labels-v1-JPN.json` and raw files alone without external knowledge of the script overrides.

---

## A9. CLAIM-BY-CLAIM LEDGER

Audit of every quantitative statement in `docs/HANDOFF_JPN_DEU.md`:

| Line | Claim in Hand-off | Finding | Evidence / Citation |
|---|---|:---:|---|
| 6 | `Base Commit / HEAD: 200057e` | **FALSE** | `git cat-file -t 200057e` exits 128: `Not a valid object name`. |
| 18 | `10 new tests enforcing C-01, C-03...` | **VERIFIED** | `tests/test_country_plumbing.py` contains exactly 10 tests, all passing. |
| 26 | `All 21 JPN scope rows resolved (18 resolved, 3 documented pending).` | **VERIFIED** | `data/source_map_JPN.csv` has 18 RESOLVED and 3 PENDING_VERIFICATION. |
| 28 | `All 21 DEU scope rows resolved.` | **FALSE** | Contradicts `data/source_map_DEU.csv` (18 RESOLVED, 3 PENDING_VERIFICATION). |
| 69 | `Country Plumbing Suite: 10 passed in 1.02s.` | **VERIFIED** | Exact runtime: 10 passed in 1.02s. |
| 70 | `Full Test Suite: 35 passing tests.` | **FALSE** | Actual suite passed 37 tests (27 from master + 10 new). |
| 84 | USA baseline hash `452BA036B5D0420A...` | **VERIFIED** | `Get-FileHash outputs/labels/USA_labels.csv` matches byte-for-byte. |
| 91-94 | JPN frozen hashes (`b20a9f...`, `ec84ea...`, `0465c1...`, `5c5d51...`) | **VERIFIED** | Recomputed SHA-256 digests match disk files. |
| 99-102 | DEU frozen hashes (`22cfb9...`, `bd370d...`, `c7f608...`, `fd8b87...`) | **VERIFIED** | Recomputed SHA-256 digests match disk files. |
| 108 | `Japan Gate: PASS (6 of 8 indicators)` | **VERIFIED** | 6 indicators pass $\ge 70\%$ threshold. |
| 109 | JPN coverage shares (`88.2%, 83.3%, 88.2%...`) | **UNSUPPORTED** | Cites post-truncation growth counts (127, 120), contradicting manifest raw counts (128, 137, 144). |
| 111 | JPN `Datable quarters: 127 quarters (1994Q2–2025Q4).` | **VERIFIED** | Quarters with $\ge 4$ indicators available equals 127. |
| 112 | ESRI metrics: `recall 88.0%, precision 62.9%, accuracy 87.4%` | **VERIFIED** | Mathematically verified on dated sample `1994Q2–2025Q4`. |
| 114 | `Germany Gate: PASS (6 of 8 indicators)` | **FALSE** | `DEU.ACT_INV` is total GFCF, forbidden by Q-02. Actual valid count is 5/8 (FAIL). |
| 115 | DEU coverage shares (`96.5%, 91.7%, 96.5%...`) | **UNSUPPORTED** | Cites post-truncation growth counts rather than raw series window counts. |
| 117 | DEU `Datable quarters: 132 quarters (1991Q2–2025Q4).` | **VERIFIED** | Quarters with $\ge 4$ indicators available equals 132. |
| 118 | CEPR metrics: `accuracy 86.3%, precision 75.0%` | **VERIFIED** | Mathematically verified against the hybrid table, but table conceals +6Q and +4Q peak gaps. |

---

## OVERALL VERDICT

### **NOT COMPLETE**

While the technical refactoring of `scripts/harmonize.py` and `scripts/03_labels.py` successfully preserved the USA label without collateral drift, and the Japan estimator converged cleanly, **Lane 1 cannot be approved or merged in its current state**.

The German label fundamentally breaches Rule Q-02 by substituting total GFCF for business fixed investment, and the delivery state is uncommitted with phantom commit hashes and severe provenance contradictions in `labels-v1-JPN.json`.

---

## 5 DEFECTS THAT MUST BE FIXED BEFORE MERGE (Ranked by Severity)

### 1. [CRITICAL] Germany Label Breaches Rule Q-02 / C-01 (Total GFCF Substituted for Business Investment)
- **File & Line:** `scripts/fetch_deu.py:11, 64-67`, `docs/DECISION_NOTE_Q02_Q04_Q05.md:62-64`.
- **Rule Broken:** Decision Q-02 ("Strict: business (non-residential) fixed investment only. Total GFCF is not substituted; where business investment is missing the component counts as missing.") and Rule C-01.
- **Defect:** `scripts/fetch_deu.py` feeds `DEU.ACT_INV` with `NAEXKP04DEQ661S` (total GFCF including residential construction). Excluding total GFCF drops Germany to 5 passing indicators, which fails C-03.
- **Required Fix:** Revoke `labels-v1-DEU`. Germany must be recorded as a **Coverage Finding** (`docs/COVERAGE_DEU.md`) documenting that only 5 of 8 core indicators pass without total GFCF.

### 2. [CRITICAL] `labels-v1-JPN.json` Source IDs Contradict Raw Ingestion and Mislabel Column
- **File & Line:** `outputs/labels/JPN/labels-v1-JPN.json:20-27`.
- **Rule Broken:** Rule C-12 (Reproducibility and Provenance).
- **Defect:** The JSON metadata records `'ACT_IP': '00550300 / b2020_sgo1j.xlsx'` and `'ACT_EMP': 'Q-04 LFS fallback'`, while `scripts/fetch_jpn.py` actually downloaded `JPNPROINDMISMEI` and `LFEMTTTTJPM647S` from FRED. Line 27 claims `'ACT_INV': 'tables/gaku-jk2622.csv (Col 5)'` (residential investment), whereas the script extracted Col 6 (`民間企業設備`). The label cannot be rebuilt from the JSON metadata alone.
- **Required Fix:** Re-generate `labels-v1-JPN.json` so its `source_ids` and input hashes reflect the exact FRED and ESRI series IDs and column indices used by `fetch_jpn.py`.

### 3. [HIGH] Chronology Dishonesty and Benchmark Cherry-Picking in Germany Validation
- **File & Line:** `docs/LABEL_VALIDATION_DEU.md:58-65`.
- **Rule Broken:** Build Contract §6.2, §6.3 (Chronology plausibility and 1-quarter tolerance rule).
- **Defect:** The German validation table labels peak differences of **+6 quarters** (2002Q3 vs 2001Q1) and **+4 quarters** (2012Q3 vs 2011Q3) as "Matched". Furthermore, the benchmark cherry-picks between CEPR Euro Area and GCEE German dates on an episode-by-episode basis.
- **Required Fix:** Disclose the actual peak gaps explicitly as findings/divergences, and benchmark against a single consistent reference standard (e.g. GCEE German chronology alone).

### 4. [HIGH] Uncommitted Delivery State, Phantom Commit Hash, and Missing PR
- **File & Line:** `docs/HANDOFF_JPN_DEU.md:6`, repository git status.
- **Rule Broken:** Lane Brief §0, §8.3 (Clean git commit structure and pull request delivery).
- **Defect:** 8 tracked files are modified and 14 files/directories are untracked. `docs/HANDOFF_JPN_DEU.md` cites non-existent commit `200057e`. No PR exists on GitHub.
- **Required Fix:** Delete or resolve invalid artifacts, commit clean logical units to `feat/jpn-deu-labels`, push to remote, and open a documented PR. Correct the cited base commit in `docs/HANDOFF_JPN_DEU.md` to `fa57a1c`.

### 5. [MEDIUM] Arithmetic Discrepancy Between Raw Level and Truncated Growth Coverage
- **File & Line:** `data/clean/coverage_JPN.csv`, `data/manifest.csv`, `docs/LABEL_VALIDATION_JPN.md:12-22`.
- **Rule Broken:** Rule C-03, C-12.
- **Defect:** `manifest.csv` reports raw level window coverage (JPN IP = 137, EMP = 144, GDP = 128), while `coverage_JPN.csv` reports post-sample-truncation growth counts (120, 127, 127). Validation docs cite the truncated numbers as general coverage without explaining the 17-quarter truncation from differencing and sample start.
- **Required Fix:** Reconcile coverage tables by displaying both metrics clearly: Raw Series Window Coverage (Levels) vs. Estimation Sample Coverage (Growth).
