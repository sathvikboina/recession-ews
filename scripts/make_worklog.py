#!/usr/bin/env python3
"""Generate EWS_Work_Log.xlsx: everything done on the project, in one workbook.

The workbook is a record of work, not an input to the pipeline. It is regenerated
from the repository state (scope, verification, labels, tests) so the numbers stay
consistent with the code.

Run:
    python scripts/make_worklog.py
"""
from __future__ import annotations

import csv
import json
import subprocess
from datetime import date
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / "EWS_Work_Log.xlsx"

NAVY = "1F3864"
BLUE = "2E5C8A"
LIGHT = "DCE6F1"
GREY = "F2F2F2"
GREEN = "E2EFDA"
AMBER = "FFF2CC"
RED = "F8D7DA"

TITLE_FONT = Font(bold=True, size=15, color=NAVY)
SUB_FONT = Font(italic=True, size=9, color="595959")
HEAD_FONT = Font(bold=True, color="FFFFFF", size=10)
HEAD_FILL = PatternFill("solid", fgColor=BLUE)
BODY_FONT = Font(size=10)
MONO = Font(name="Consolas", size=9)
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")
CENTER = Alignment(horizontal="center", vertical="top", wrap_text=True)


def sheet(wb, name, title, subtitle, headers, rows, widths, *, wrap=True, freeze="A4",
          number_formats=None, row_fills=None, autofilter=True):
    ws = wb.create_sheet(name)
    ws["A1"] = title
    ws["A1"].font = TITLE_FONT
    ws["A2"] = subtitle
    ws["A2"].font = SUB_FONT
    ws.append([])
    ws.append(headers)
    head_row = 4
    for c, _ in enumerate(headers, 1):
        cell = ws.cell(row=head_row, column=c)
        cell.font = HEAD_FONT
        cell.fill = HEAD_FILL
        cell.alignment = CENTER
        cell.border = BORDER
    for r_i, row in enumerate(rows, head_row + 1):
        ws.append(list(row))
        for c in range(1, len(headers) + 1):
            cell = ws.cell(row=r_i, column=c)
            cell.font = BODY_FONT
            cell.border = BORDER
            cell.alignment = WRAP if wrap else CENTER
            if number_formats and c in number_formats:
                cell.number_format = number_formats[c]
            if row_fills and (r_i - head_row - 1) in row_fills:
                cell.fill = PatternFill("solid", fgColor=row_fills[r_i - head_row - 1])
    for c, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(c)].width = w
    if freeze:
        ws.freeze_panes = freeze
    if autofilter and rows:
        ws.auto_filter.ref = f"A{head_row}:{get_column_letter(len(headers))}{head_row + len(rows)}"
    ws.sheet_view.showGridLines = False
    return ws


def kpi_block(ws, start_row: int, items: list[tuple[str, str]]) -> int:
    r = start_row
    for label, value in items:
        a = ws.cell(row=r, column=1, value=label)
        a.font = Font(bold=True, size=10, color=NAVY)
        a.fill = PatternFill("solid", fgColor=LIGHT)
        a.border = BORDER
        b = ws.cell(row=r, column=2, value=value)
        b.font = BODY_FONT
        b.alignment = WRAP
        b.border = BORDER
        r += 1
    return r


def git_state() -> tuple[list[dict], str]:
    """Return the commit list and a human-readable working-tree state."""
    try:
        out = subprocess.run(
            ["git", "log", "--pretty=%h|%ad|%s", "--date=short"],
            cwd=PROJECT, capture_output=True, text=True, check=True,
        ).stdout.strip().splitlines()
        dirty = subprocess.run(
            ["git", "status", "--porcelain"], cwd=PROJECT,
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except Exception:
        return [], "unknown"
    rows = []
    for line in out:
        parts = line.split("|", 2)
        if len(parts) == 3:
            rows.append({"commit": parts[0], "date": parts[1], "subject": parts[2]})
    return rows, ("clean" if not dirty else f"{len(dirty.splitlines())} uncommitted path(s)")


def compute_confusion(nber: pd.DataFrame) -> dict:
    """Quarter-level agreement between the frozen label and the NBER flag."""
    tp = int(((nber["R"] == 1) & (nber["NBER"] == 1)).sum())
    fp = int(((nber["R"] == 1) & (nber["NBER"] == 0)).sum())
    fn = int(((nber["R"] == 0) & (nber["NBER"] == 1)).sum())
    tn = int(((nber["R"] == 0) & (nber["NBER"] == 0)).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "accuracy": (tp + tn) / len(nber),
        "precision": precision, "recall": recall, "f1": f1,
        "nber_quarters": tp + fn, "label_quarters": tp + fp,
    }




WORK_LOG = [
    ("2026-10-29", "1", "Audit", "Read every Phase 2 artefact: README, 16 CSVs, spec.py, build.py, plan_ML.docx, literature_matrix.xlsx", "—", "Understood the dictionary, the firewall and the 1,883-row catalogue"),
    ("2026-10-29", "1", "Fix", "Made build.py portable: removed /home/claude and /mnt/user-data paths, added EWS_OUT, fixed a bad width key, rewrote the V-16 note", "build.py, verification_log.csv", "build.py parses and writes to build/ without clobbering root deliverables"),
    ("2026-10-29", "1", "Scaffold", "Created config/, src/ews/, scripts/, tests/, docs/, data/{raw,interim,clean}, outputs/*", "directory tree", "Project layout in place"),
    ("2026-10-29", "1", "Config", "Wrote scripts/export_spec.py to freeze the machine-readable spec", "config/indicators.yaml (68), countries.yaml (41), sources.yaml (9)", "Runtime config separated from spec.py"),
    ("2026-10-29", "1", "Scope", "Wrote scripts/scope_catalog.py to reduce 1,883 catalogue rows to the rows this build will collect", "data/scope.csv (68), scope_coverage.csv, scope_summary.txt", "USA 25, JPN 21, DEU 21, GLOBAL 1; 30 BEAI-eligible"),
    ("2026-10-29", "1", "Gate", "Wrote scripts/00_env.py: environment, firewall and key-format checks", "scripts/00_env.py", "26 checks pass, 0 failures"),
    ("2026-10-29", "1", "Tests", "Wrote tests/test_config.py and tests/test_scope.py", "12 tests", "Firewall, BEAI set, vocab, scope membership all enforced"),
    ("2026-10-29", "1", "Docs", "Wrote BUILD_CONTRACT (C-01..C-12), DECISIONS (D-R01..D-R21), VERIFICATION, STATE; rewrote README", "docs/*.md", "One-page hand-off + frozen runtime rules"),
    ("2026-10-29", "1", "Repo", "Added pyproject.toml, Makefile, .gitignore, .env.example, src/ews/__init__.py; initialised git", "commit eeea363", "48 tracked files, clean tree"),
    ("2026-10-29", "2", "Diagnose", "FRED connectivity: urllib/requests stall, system curl works; metadata readable from the series page HTML", "—", "Switched the fetcher to curl via subprocess"),
    ("2026-10-29", "2", "Verify", "Wrote scripts/fetch_fred.py: metadata + history + coverage + SHA-256 manifest for 24 candidate series", "data/manifest.csv, data/fred_verification.csv, data/series_resolution.csv, data/raw/fred/2026-10-29/*.csv", "22 verified, 1 insufficient history, 2 derived"),
    ("2026-10-29", "2", "Data fix", "PNFIC1 only starts 2007 -> replaced by GPDIC1 for ACT_INV", "resolution table, scope.csv", "Recorded as a substitution, not hidden"),
    ("2026-10-29", "2", "Data fix", "PCEC96 (monthly real PCE) starts 2007 -> 52.8% coverage, rejected", "resolution table", "Quarterly PCECC96 carries the label"),
    ("2026-10-29", "2", "Data fix", "WILL5000IND dead (301/404), SP500 only 10 years -> NASDAQCOM from 1971", "resolution table", "Equity predictor usable"),
    ("2026-10-29", "2", "Data fix", "Real income: DPIC96 is monthly and counter-cyclical (transfers) -> W875RX1, income excluding transfers", "resolution table, D-R23", "Factor loading on income turns positive (+0.72 vs -0.25)"),
    ("2026-10-29", "2", "Harmonise", "Wrote scripts/harmonize.py: monthly/daily -> quarterly mean with complete-quarter rule, dlog, sign alignment, no imputation", "data/clean/USA_levels.parquet, USA_growth.parquet, coverage.csv", "All 8 core indicators >= 93% of the window"),
    ("2026-10-29", "2", "Label", "Implemented DFM, BBQ and diffusion gate", "src/ews/labels/{dfm,bbq,diffusion,build}.py", "One-factor DynamicFactorMQ, min phase 2, min cycle 5, censor 2, gate 0.50"),
    ("2026-10-29", "2", "Bug fix", "Factor rescaled with mean(sigma) instead of mean(sigma*|lambda|): common component overstated ~3x", "src/ews/labels/dfm.py", "Before: 1990-91 and 2001 missed. After: 4/4 NBER episodes"),
    ("2026-10-29", "2", "Bug fix", "Dropping the leading all-NaN row shifted the factor index by one quarter, moving every turning point", "src/ews/labels/dfm.py", "Reindexed the factor back to the caller's index"),
    ("2026-10-29", "2", "Method", "Switched to the smoothed factor (ex-post label, no availability lag)", "dfm.py, D-R24", "2001 and 2020 peak dates align exactly with NBER"),
    ("2026-10-29", "2", "Validate", "Wrote scripts/03_labels.py and scripts/04_compare_nber.py; ran NBER comparison and robustness variants", "outputs/labels/*, outputs/results/*", "4/4 episodes, 0 false, accuracy 0.986, recall 1.000"),
    ("2026-10-29", "2", "Tests", "Wrote tests/test_labels.py: BBQ on a known cycle, flag semantics, diffusion gate, frozen-file invariants, no-NBER test", "9 tests", "21 tests total passing"),
    ("2026-10-29", "2", "Docs", "Wrote docs/LABEL_VALIDATION.md; updated VERIFICATION, DECISIONS (D-R22..D-R25), BUILD_CONTRACT C-02, STATE, README", "docs/*.md", "Method, discrepancies, falsification checks documented"),
    ("2026-10-29", "2", "Repo", "Committed the USA milestone and the fetch exit-code fix", "commits 5c042e9, a117998", "Clean tree, labels reproducible byte-for-byte"),
    ("2026-11-04", "3", "Packaging", "Generated this workbook and a portable repository (bare mirror + bundle)", "EWS_Work_Log.xlsx, recession-ews.git, recession-ews.bundle", "Shareable without GitHub credentials"),
    ("2026-11-04", "4", "Maintenance", "Applied review fixes without touching the frozen label: window episode ids, in_window turning points, stale DPIC96 removal, preserved freeze date, canonical growth digest, committed result CSVs, $(PY) Makefile fix, docs corrections", "USA_episodes.csv, USA_turning_points.csv, labels-v1.json, data/superseded_series.csv, tests/test_freeze.py", "Frozen labels CSV byte-identical; clean clone matches"),
    ("2026-11-04", "5", "Decision", "Resolved Q-02/Q-04/Q-05. Q-02 B: constructed real non-residential business fixed investment from four BEA components; Q-04 B: CE16OV LFS fallback; Q-05 A: keep HOANBS with sector limitation documented", "scripts/fetch_fred.py, scripts/harmonize.py, data/series_resolution.csv, data/superseded_series.csv, docs/DECISION_NOTE_Q02_Q04_Q05.md", "All four NBER episodes matched; 2009 trough now exact; F1 0.929 -> 0.963"),
    ("2026-11-04", "5", "Freeze", "Archived labels-v1 byte-identical and issued labels-v2 with Q-02/Q-04 provenance and the archived v1 hash; rewrote freeze tests", "outputs/labels/archive/labels-v1/*, outputs/labels/labels-v2.json, tests/test_freeze.py", "v1 hash unchanged; v2 label hash f5ed42a6...; 30 tests"),
    ("2026-11-05", "5", "Verify", "Repaired a failed-retry provenance overwrite with a full FRED re-fetch (30 registry entries = 27 downloads + 3 derived), re-ran harmonize/labels/validate, and confirmed the v2 hashes reproduce", "data/manifest.csv, data/fred_verification.csv, data/series_resolution.csv, data/raw/fred/2026-11-05/*", "26 verified + 1 low coverage; labels-v2 byte-identical"),
    ("2026-11-05", "6", "Review", "Audited the labels-v2 work: fixed the stale spec.py decision source, removed the unsupported forecasting claim, added the India coverage pre-audit, pre-registered the ensemble and leakage rules, fixed the 27-download/3-derived wording, split the work into four packages, and added 2 regression tests", "spec.py, decisions_log.csv, unresolved_questions.csv, README.md, docs/{STATE,BUILD_CONTRACT,VERIFICATION,DECISIONS,DECISION_NOTE_Q02_Q04_Q05,LABEL_VALIDATION,PROPOSAL_ADDENDUM,INDIA_COVERAGE_AUDIT,TEAM_PLAN,REVIEW_2026-11-05}.md, tests/test_review_invariants.py", "32 tests pass; make check 26 ok / 3 warnings / 0 failures; v1 and v2 hashes unchanged"),
    ("2026-11-05", "7", "Team plan", "Wrote docs/TEAM_PLAN.md: four parallel work packages with owners, outputs, dependencies and acceptance gates", "docs/TEAM_PLAN.md", "JPN/DEU labels, features/folds, models/ensemble and India/integration can run at the same time"),
    ("2026-11-06", "7", "Workbook", "Built Team_Plan.xlsx (12 sheets) and scripts/make_team_plan.py: plain-English plan, task detail, parallel schedule, hand-offs, combination rules, risks, final review and glossary", "Team_Plan.xlsx, scripts/make_team_plan.py", "One simple plan for four teammates; regenerated from a script, not hand-edited"),
    ("2026-11-06", "7", "Work log", "Added the Team Plan summary and the 2026-11-05/06 plan rows to this workbook", "EWS_Work_Log.xlsx, scripts/make_worklog.py", "The detailed log and the simple plan agree"),
    ("2026-11-06", "7", "Verify", "Re-ran pytest and make check; confirmed v1/v2 label hashes and docs consistency after the plan changes", "pytest, make check, SHA-256 checks", "32 tests pass; 26 ok / 3 warnings / 0 failures; frozen hashes unchanged"),
    ("2026-11-06", "8", "Data extension", "Fetched FRED through 2026-09, extended the USA clean panel and reporting window from 2025Q4 to 2026Q3 (147 quarters), archived labels-v2 byte-identically and froze labels-v3", "data/raw/fred/2026-11-06/*, data/manifest.csv, data/clean/*, outputs/labels/labels-v3.json, outputs/labels/archive/labels-v2/*", "2025-2026 data added; 4/4 NBER episodes still match; no false episodes; v2 hashes unchanged"),
    ("2026-11-06", "8", "One-week plan", "Replaced the five-week plan with a seven-day sprint: Days 1-5 individual work in four lanes, Days 6-7 merge, cross-review and go/no-go", "docs/TEAM_PLAN.md, scripts/make_team_plan.py", "Four balanced lanes, day-level tasks, fixed hand-offs and one review gate"),
    ("2026-11-06", "8", "Workbook", "Rebuilt Team_Plan.xlsx for the 7-day sprint and refreshed this work log with the v3 extension", "Team_Plan.xlsx, EWS_Work_Log.xlsx", "The simple plan and the detailed log agree; no pipeline artefact was changed by the plan work"),
    ("2026-11-06", "8", "Verify", "Ran the full suite and config gate on the extended window; checked v1 and v2 archive hashes and the v3 active hashes", "pytest, make check, SHA-256 checks", "32 tests pass; 26 ok / 3 warnings / 0 failures; all frozen hashes match"),
]

DATA_NOTES = {
    "USA.ACT_GDP_REAL.Q.NA": "Core BEAI input",
    "USA.ACT_IP.M.STD": "Core BEAI input",
    "USA.ACT_EMP.Q.NA": "Core BEAI input; CE16OV LFS fallback (Q-04)",
    "USA.ACT_EMP.M.ESTAB": "Predictor; establishment survey",
    "USA.ACT_EMP.M.LFS": "Predictor; household survey",
    "USA.ACT_RINC.M.US": "Predictor; monthly real disposable income",
    "USA.ACT_HOURS.Q.STD": "Core BEAI input; HOANBS, nonfarm business (Q-05)",
    "USA.ACT_RINC.Q.STD": "Core BEAI input; replaced DPIC96 (D-R23)",
    "USA.ACT_CONS.Q.NA": "Core BEAI input",
    "USA.ACT_RETAIL.M.STD": "Core BEAI input; starts 1992",
    "USA.ACT_INV_EQ.Q.STD": "Q-02 component; non-residential equipment (nominal)",
    "USA.ACT_INV_STRUCT.Q.STD": "Q-02 component; non-residential structures (nominal)",
    "USA.ACT_INV_IPP.Q.STD": "Q-02 component; intellectual property products (nominal)",
    "USA.ACT_INV_DEFL.Q.STD": "Q-02 component; non-residential implicit price deflator",
    "USA.ACT_INV.Q.STD": "Core BEAI input; constructed real non-residential (Q-02)",
    "USA.ACT_CONS.M.US": "Rejected: 52.8% coverage",
    "USA.FIN_EQUITY.M.STD": "Replaced WILL5000IND",
    "USA.FIN_HOUSEPRICE.M.US_CS": "Predictor; Case-Shiller national",
    "USA.FIN_HOUSEPRICE.Q.OECD_BIS": "Substituted USSTHPI for OECD/BIS",
    "USA.FIN_CREDIT_GAP.Q.STD": "Derived: one-sided HP filter of credit/GDP",
    "USA.FIN_CREDIT_GDP.Q.STD": "Predictor; credit-to-GDP input to the gap",
    "USA.FIN_SLOPE.M.DERIVED": "Derived: GS10 - TB3MS",
    "USA.FIN_LONG.M.STD": "Predictor; 10-year Treasury yield",
    "USA.FIN_POLICY.M.STD": "Predictor; effective fed funds rate",
    "USA.FIN_SHORT.M.STD": "Predictor; 3-month T-bill rate",
    "USA.LAB_UNEMP.M.STD": "Predictor only (Q-01)",
    "USA.PRC_CPI.M.STD": "Predictor; headline inflation",
    "USA.SEN_BCI.M.STD": "Predictor; OECD business confidence",
    "USA.SEN_CCI.M.STD": "Predictor; U. Michigan consumer sentiment",
    "USA.NBER.Q": "External chronology, robustness only",
}

TESTS = [
    ("test_config.py", "test_beai_set_is_exact", "BEAI-eligible set equals the eight §11 core indicators"),
    ("test_config.py", "test_unemployment_is_predictor_only", "Unemployment is not a label input (Q-01)"),
    ("test_config.py", "test_indicator_identifiers_unique", "No duplicate indicator ids"),
    ("test_config.py", "test_indicator_semantics_in_vocabulary", "Form, lag class, frequency and priority are valid"),
    ("test_config.py", "test_countries_and_scope", "40 countries + GLOBAL, horizon and window consistency"),
    ("test_config.py", "test_scope_priorities_are_valid", "Priorities and core set match scope.yaml"),
    ("test_scope.py", "test_scope_exists_and_nonempty", "Shortlist exists"),
    ("test_scope.py", "test_columns_present", "Required columns present"),
    ("test_scope.py", "test_keys_unique_and_well_formed", "series_key unique and regex-valid"),
    ("test_scope.py", "test_every_key_is_in_the_catalogue", "Every scope row traces to the catalogue"),
    ("test_scope.py", "test_scope_respects_config", "Scope obeys enabled countries, priorities and firewall"),
    ("test_scope.py", "test_scope_excludes_decision_rows", "No excluded/not-applicable rows leak in"),
    ("test_labels.py", "test_bbq_finds_known_cycle", "BBQ recovers turning points on a synthetic cycle"),
    ("test_labels.py", "test_bbq_respects_min_phase_and_cycle", "Min phase 2 and min cycle 5 enforced"),
    ("test_labels.py", "test_bbq_censors_endpoints", "No turning point in the last/first 2 quarters"),
    ("test_labels.py", "test_recession_flag_is_peak_plus_one_through_trough", "R=1 only from peak+1 to trough"),
    ("test_labels.py", "test_diffusion_share_ignores_missing", "Diffusion uses available indicators only"),
    ("test_labels.py", "test_diffusion_gate_drops_weak_episode", "A 1/8 diffusion episode would be rejected"),
    ("test_labels.py", "test_frozen_labels_present_and_sane", "Frozen label has 147 rows, contiguous episodes"),
    ("test_labels.py", "test_label_pipeline_does_not_use_nber", "No external chronology reaches the label"),
    ("test_labels.py", "test_episode_peak_is_before_trough", "Every episode has duration >= 2"),
    ("test_freeze.py", "test_v1_and_v2_archives_are_byte_identical", "labels-v1, labels-v2 and their metadata stay byte-identical"),
    ("test_freeze.py", "test_active_label_hash_is_v3", "active labels-v3 CSV stays byte-identical"),
    ("test_freeze.py", "test_v3_label_dates_and_factor_values", "D-R25 factor/level values and v3 episode dates"),
    ("test_freeze.py", "test_episode_ids_join_across_frozen_artefacts", "label and episode ids share one window numbering"),
    ("test_freeze.py", "test_turning_points_carry_in_window_flag", "pre-1990 points are flagged, not hidden"),
    ("test_freeze.py", "test_one_active_source_per_scope_key", "one active provenance row per scope key"),
    ("test_freeze.py", "test_v3_metadata_records_the_input_decisions", "labels-v3 records Q-02/Q-04/Q-05 and the 2026Q3 window"),
    ("test_freeze.py", "test_created_date_is_preserved", "re-running the builder does not rewrite the freeze date"),
    ("test_freeze.py", "test_canonical_digest_tracks_values_not_parquet_bytes", "freeze digest is environment-independent"),
    ("test_review_invariants.py", "test_spec_matches_active_decision_log", "spec.py and decisions_log.csv cannot drift; Q-02/Q-04/Q-05 sign-offs and the India finding are present"),
    ("test_review_invariants.py", "test_ensemble_preregistration_is_present_and_specific", "the pre-registered ensemble, beat-the-best test and leakage conditions stay in the docs"),
]

REPO_MAP = [
    ("README.md", "Project overview, status, quickstart, USA result", "entry point"),
    ("docs/BUILD_CONTRACT.md", "Frozen runtime rules C-01..C-13", "read before writing pipeline code"),
    ("docs/DECISIONS.md", "D-R01..D-R30 and open items O-1..O-5", "decision record"),
    ("docs/VERIFICATION.md", "FRED verification table, substitutions, India pre-audit, sign-offs", "data provenance"),
    ("docs/LABEL_VALIDATION.md", "Method, NBER agreement, discrepancies, falsification checks, claim scope", "label evidence"),
    ("docs/STATE.md", "One-page hand-off with hashes and next actions", "start here each session"),
    ("docs/DECISION_NOTE_Q02_Q04_Q05.md", "Q-02/Q-04/Q-05 comparison, selected options and 2026-11-05 sign-off", "decision support"),
    ("docs/PROPOSAL_ADDENDUM.md", "Pre-registered ensemble, leakage rules, beat-the-best test, claim wording", "pre-registration"),
    ("docs/INDIA_COVERAGE_AUDIT.md", "India 4/8 best-case finding; Label-B-only under O-2", "coverage finding"),
    ("docs/TEAM_PLAN.md", "Four work packages, owners, acceptance criteria, integration rules", "team plan"),
    ("Team_Plan.xlsx", "Generated 12-sheet plain-English team plan (what happened, what is next, tasks, schedule, hand-offs, risks, review)", "deliverable"),
    ("scripts/make_team_plan.py", "Builds Team_Plan.xlsx from the repository state", "reporting"),
    ("docs/REVIEW_2026-11-05.md", "Review discrepancies, fixes, data sign-offs, remaining gaps", "review record"),
    ("config/scope.yaml", "Countries, window, horizons, coverage, firewall", "runtime config"),
    ("config/indicators.yaml", "68 indicators, roles, forms, lag classes, variants", "generated from spec.py"),
    ("config/countries.yaml", "40 countries + GLOBAL with source chains", "generated"),
    ("config/sources.yaml", "9 sources with access method and caveats", "generated"),
    ("data/scope.csv", "68-row collection shortlist with resolved ids", "collection plan"),
    ("data/manifest.csv", "One active row per scope key with SHA-256 and coverage", "provenance"),
    ("data/fred_verification.csv", "Title, units, frequency, SA, first/last, coverage", "verification facts"),
    ("data/superseded_series.csv", "Retired source ids replaced by a new active source", "provenance history"),
    ("data/series_resolution.csv", "scope_key -> concrete source id / derivation", "join table"),
    ("data/raw/fred/<date>/", "Immutable downloads (git-ignored)", "raw layer"),
    ("data/clean/", "Quarterly panel and growth matrix (git-ignored)", "clean layer"),
    ("src/ews/labels/dfm.py", "One-factor DFM, loading-based scale, cumulated level", "label estimator"),
    ("src/ews/labels/bbq.py", "Turning points, episodes, recession flag", "dating"),
    ("src/ews/labels/diffusion.py", "Deterioration share and episode gate", "label gate"),
    ("src/ews/labels/build.py", "Orchestrates DFM -> BBQ -> diffusion", "label pipeline"),
    ("src/ews/labels/freeze.py", "Preserves the freeze date and hashes values, not parquet bytes", "freeze helpers"),
    ("src/ews/labels/ids.py", "Renumbers window episodes for label/episode joins", "freeze helpers"),
    ("scripts/00_env.py", "Environment and configuration gate", "CI entry"),
    ("scripts/export_spec.py", "spec.py -> config/*.yaml", "config build"),
    ("scripts/scope_catalog.py", "Catalogue -> 68-row shortlist + resolutions", "scope build"),
    ("scripts/fetch_fred.py", "Verify + download FRED, write manifest", "collection"),
    ("scripts/harmonize.py", "Quarterly panel, dlog, sign alignment", "clean data"),
    ("scripts/03_labels.py", "Build and freeze the label", "labels"),
    ("scripts/04_compare_nber.py", "NBER comparison + robustness", "validation"),
    ("scripts/make_worklog.py", "This workbook", "reporting"),
    ("EWS_Work_Log.xlsx", "Generated work log (this file)", "deliverable"),
    ("tests/", "32 invariants (config, scope, labels, freeze, review)", "software checks"),
    ("outputs/labels/USA_labels.csv", "Frozen label: factor, level, diffusion, R", "deliverable"),
    ("outputs/labels/labels-v3.json", "Parameters, loadings, decisions, hashes", "freeze record"),
    ("outputs/labels/archive/labels-v2/", "Byte-identical v2 label, metadata and SHA-256 sums", "archive"),
    ("outputs/labels/archive/labels-v1/", "Byte-identical v1 label, metadata and SHA-256 sums", "archive"),
    ("outputs/results/USA_vs_NBER.md", "Episode matching, confusion matrix, robustness", "validation report"),
]

DECISIONS = [
    ("D-R01", "Unemployment is predictor-only; BEAI is exactly the eight §11 indicators", "FROZEN"),
    ("D-R02", "Study window 1990Q1-2026Q3 (147 quarters); 70% = 103 quarters", "FROZEN"),
    ("D-R03", "Horizons 1Q/2Q/4Q, 2Q primary", "FROZEN"),
    ("D-R04", "Coverage gate: 6/8 core at >=70%; >=4 indicators to date a quarter", "FROZEN"),
    ("D-R05", "Availability lags by data class", "FROZEN"),
    ("D-R06", "Monthly -> quarterly mean, no partial-quarter imputation", "FROZEN"),
    ("D-R07", "SA: official SA preferred; NSA BEAI inputs X-13 up to the cutoff", "FROZEN"),
    ("D-R08", "Annual series: carry last value with 1-year lag", "FROZEN"),
    ("D-R11", "Walk-forward only; threshold locked before test", "FROZEN"),
    ("D-R14", "Revised data with simulated lags, not a real-time vintage study", "FROZEN"),
    ("D-R16", "Verify only the 68 scope rows, not the 1,883 catalogue", "FROZEN"),
    ("D-R19", "Threshold objective: max F1 vs recall-at-precision", "OPEN"),
    ("D-R20", "P0-P1 first (68 rows); widen to P0-P2 after the label gate", "CONFIRM"),
    ("D-R21", "COVID kept; document BBQ treatment; with/without evaluation", "CONFIRM"),
    ("D-R22", "Estimate the factor on 1960Q1-2026Q3; report labels 1990Q1-2026Q3", "FROZEN"),
    ("D-R23", "US income uses W875RX1 (excluding transfers), not DPIC96", "FROZEN"),
    ("D-R24", "Label uses the smoothed factor (ex-post, no availability lag)", "FROZEN"),
    ("D-R25", "Convert factor with scale = mean(sigma*|lambda|)", "FROZEN"),
    ("D-R26", "Q-02 B: constructed real non-residential business fixed investment", "FROZEN"),
    ("D-R27", "Q-04 B: USA employment uses CE16OV (LFS fallback)", "FROZEN"),
    ("D-R28", "Q-05 A: keep HOANBS; document nonfarm-business coverage", "FROZEN"),
    ("D-R29", "Ensemble pre-registered: equal-weight top-3 by inner-fold PR-AUC; must beat best single by >=0.01 pooled PR-AUC with bootstrap CI excluding 0 and no recall loss", "FROZEN"),
    ("D-R30", "India best case 4/8 under §19; Label-B-only case study under O-2; no relaxation", "CONFIRM"),
    ("D-R31", "2026 data extension: reporting window 1990Q1-2026Q3 (147 quarters); estimator, BBQ, diffusion gate and eight-indicator structure unchanged; labels-v2 archived; labels-v3 active", "FROZEN"),
]

OPEN_ITEMS = [
    ("O-1", "Report pre-1990 labels now that estimation runs from 1960?", "No, 1990-2026Q3", "Next labels"),
    ("O-2", "If India/Japan fail §19, Label-B-only or drop?", "Label B only, reported (India pre-audit 4/8)", "JPN/DEU/IND"),
    ("O-3", "Threshold rule: max F1 or recall at a precision floor?", "Max F1", "Harness"),
    ("O-4", "Widen P0-P1 to P0-P2 (68 -> 140 rows)?", "After the label gate", "Collection"),
    ("O-5", "COVID with/without evaluation?", "Keep, document, evaluate", "Experiments"),
]

PHASES = [
    ("1", "Literature matrix", "Done", "literature_matrix.xlsx v4", ""),
    ("2", "Data dictionary", "Done", "16-sheet workbook, 1,883-row catalogue", ""),
    ("3", "Scoped verification", "USA done; JPN/DEU pending", "21 verified, 1 low coverage, 3 derived", "JPN 21 + DEU 21 rows"),
    ("4", "Collect + harmonise", "USA done; JPN/DEU pending", "267-quarter panel (1960Q1-2026Q3), 8 core indicators", "BOJ/OECD access"),
    ("5", "BEAI label", "USA done, extended to 2026Q3, frozen, signed off", "4/4 NBER, accuracy 0.993, F1 0.963; labels-v3", "JPN/DEU labels"),
    ("6", "JPN + DEU labels", "Not started", "-", "Phase 3/4 for those countries"),
    ("7", "Feature table", "Not started", "-", "O-4, firewall tests"),
    ("8", "Walk-forward harness", "Not started", "-", "O-3, folds"),
    ("9", "Experiments + metrics", "Not started", "-", "Harness; ensemble C-13 pre-registered"),
    ("10", "Cross-country (LOCO)", "Not started, conditional", "-", ">=6 countries, >=20 episodes"),
    ("11", "Interpretation", "Not started", "-", "Experiments"),
    ("12", "Dashboard + write-up", "Not started", "-", "Interpretation"),
]

RUNBOOK = [
    ("Setup", "python3 -m venv .venv && .venv/bin/pip install -e \".[dev]\"", "once"),
    ("Config", "make config", "regenerate config/*.yaml from spec.py"),
    ("Scope", "make scope", "rebuild the 68-row shortlist"),
    ("Fetch", "make fetch", "verify + download FRED, write manifest"),
    ("Harmonise", "make harmonize", "quarterly panel + growth matrix"),
    ("Label", "make labels", "DFM -> BBQ -> diffusion, freeze labels-v3"),
    ("Validate", "make validate", "NBER comparison + robustness"),
    ("All", "make pipeline", "fetch + harmonize + labels + validate"),
    ("Checks", "make check && make test", "26 config checks + 32 tests"),
    ("Team plan", "make team-plan", "rebuild Team_Plan.xlsx (12 sheets)"),
    ("Workbook", "python scripts/make_worklog.py", "regenerate this file"),
]


def main() -> int:
    wb = Workbook()
    wb.remove(wb.active)

    commits, _ = git_state()
    scope = pd.read_csv(PROJECT / "data" / "scope.csv")
    ver = pd.read_csv(PROJECT / "data" / "fred_verification.csv")
    res = pd.read_csv(PROJECT / "data" / "series_resolution.csv")
    eps = pd.read_csv(PROJECT / "outputs" / "labels" / "USA_episodes.csv")
    rob = pd.read_csv(PROJECT / "outputs" / "results" / "USA_robustness.csv")
    false_eps = pd.read_csv(PROJECT / "outputs" / "results" / "USA_false_episodes.csv")
    meta = json.loads((PROJECT / "outputs" / "labels" / "labels-v3.json").read_text())
    vs_nber = pd.read_csv(PROJECT / "outputs" / "results" / "USA_vs_NBER.csv")
    match = pd.read_csv(PROJECT / "outputs" / "results" / "USA_episode_match.csv")
    cm = compute_confusion(vs_nber)
    episodes_matched = int(match["matched"].sum())

    # 1. Summary -----------------------------------------------------------
    ws = wb.create_sheet("Summary")
    ws.sheet_view.showGridLines = False
    ws["A1"] = "Recession Early-Warning - Work Log"
    ws["A1"].font = Font(bold=True, size=18, color=NAVY)
    ws["A2"] = (f"Generated {date.today().isoformat()} from the repository state at "
                f"{commits[0]['commit'] if commits else 'unknown'}. Cross-country recession EWS: USA label extended "
                f"to 2026Q3, 2026-11-06 data freeze and the one-week four-lane sprint.")
    ws["A2"].font = SUB_FONT
    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["B"].width = 92
    r = kpi_block(ws, 4, [
        ("Project", "Cross-country recession early-warning (BEAI label, REWI, walk-forward evaluation)"),
        ("Team", "Sathvik Boina, Shravani Math, Arshiya, Palchhin"),
        ("Repository", str(PROJECT)),
        ("Commits covered", f"{len(commits)}  ({', '.join(c['commit'] for c in commits)})"),
        ("", ""),
        ("Scope", "68 series rows: USA 25, JPN 21, DEU 21, GLOBAL 1; 30 BEAI-eligible"),
        ("Window", "1990Q1-2026Q3 (147 quarters); horizons 1Q/2Q/4Q, 2Q primary"),
        ("USA data", "30 FRED registry entries = 27 downloads + 3 derived (26 verified + 1 low coverage); 4 Q-02 components, 1 auxiliary chronology; observations through 2026-09"),
        ("USA label", f"labels-v3 frozen: {int(eps['kept'].sum())} episodes, "
                      f"{len(false_eps)} false positives; labels-v2 and labels-v1 archived byte-identically"),
        ("NBER agreement", f"{episodes_matched}/{len(match)} episodes, accuracy {cm['accuracy']:.3f}, "
                           f"recall {cm['recall']:.3f}, precision {cm['precision']:.3f}, F1 {cm['f1']:.3f}"),
        ("Tests", "32 passing (config 6, scope 6, labels 9, freeze 9, review invariants 2)"),
        ("Config gate", "26 ok, 3 warnings (optional model packages), 0 failures"),
        ("Not started", "JPN/DEU labels (Days 1-5), feature table, harness, experiments, dashboard"),
        ("Pre-registered", "Equal-weight top-3 ensemble, C-13 (docs/PROPOSAL_ADDENDUM.md); no model result yet"),
        ("India", "Pre-audit best case 4/8; Label-B-only under O-2 pending final downloads"),
        ("Team plan", "One-week sprint: Days 1-5 individual, Days 6-7 combine/review; Team_Plan.xlsx (12 sheets) and docs/TEAM_PLAN.md"),
        ("", ""),
        ("How to read", "Team Plan = four lanes and the 7-day shape. Status = phase state. Work Log = chronological actions. "
                        "Data Sources = verified series. Labels = result. Tests = software invariants. "
                        "Decisions = frozen/open choices. Next Phases = roadmap."),
        ("Caveat", "The label is built on revised historical data with no real-time vintages. Results are not a "
                   "real-time forecasting claim (D-R14)."),
    ])
    ws.cell(row=r + 1, column=1, value="Commit history").font = Font(bold=True, size=11, color=NAVY)
    r += 2
    ws.cell(row=r, column=1, value="Commit").font = HEAD_FONT
    ws.cell(row=r, column=1).fill = HEAD_FILL
    ws.cell(row=r, column=2, value="Date | Subject").font = HEAD_FONT
    ws.cell(row=r, column=2).fill = HEAD_FILL
    for c in commits:
        r += 1
        ws.cell(row=r, column=1, value=c["commit"]).font = MONO
        ws.cell(row=r, column=2, value=f"{c['date']}  {c['subject']}").font = BODY_FONT

    # 2. Team plan ---------------------------------------------------------
    team_rows = [
        ("Part 1", "Shravani Math", "Data and label lead",
         "Build Japan's BEAI label and resolve Germany far enough to build it or record a complete 6/8 finding.",
         "Day 1 sources, Day 2 Japan data, Day 3 Japan label, Day 4 Germany data, Day 5 Germany verdict",
         "JPN/DEU clean panels, frozen labels, chronology notes, source resolutions",
         "Nothing; start source resolution on Day 1",
         "Day 6 label audit, Day 7 sign-off"),
        ("Part 2", "Arshiya", "ML engineering lead",
         "Build the predictor table and the fair walk-forward splits on the extended 2026Q3 panel.",
         "Day 1 spec, Day 2 table, Day 3 draft folds, Day 4 final folds, Day 5 freeze hand-off",
         "dataset.parquet, folds.json, leakage tests, feature dictionary",
         "Can start now on the USA; no dependency on Part 1",
         "Day 6 leakage audit, Day 7 sign-off"),
        ("Part 3", "Palchhin", "Modelling lead",
         "Run six single models, baselines and the pre-registered ensemble on the same folds.",
         "Day 1 interfaces, Day 2 fixture run, Day 3 REWI, Day 4 ensemble/headline, Day 5 ablations",
         "Model code, headline/episode/ablation tables, results note",
         "Starts Day 1; uses draft folds from Day 3 and final folds from Day 5",
         "Day 6 reproduce result, Day 7 audit"),
        ("Part 4", "Sathvik Boina", "Validation, integration and writing lead",
         "Finish India, keep the scope honest, and combine the four lanes into one reproducible project.",
         "Day 1 India data, Day 2 India verdict, Day 3 docs, Day 4 clean clone, Day 5 rehearsal",
         "India coverage table, updated docs, clean-clone evidence, final package after approval",
         "Runs in parallel; leads the merge on Day 6",
         "Day 6 merge lead, Day 7 review lead"),
    ]
    sheet(wb, "Team Plan", "Four lanes in a one-week sprint",
          "Days 1-5 are individual work; Days 6-7 are combining, cross-review and sign-off. Detailed tasks are in Team_Plan.xlsx.",
          ["Package", "Suggested owner", "Role", "Job", "Days 1-5", "Main outputs", "Depends on", "Days 6-7"],
          team_rows, [10, 20, 26, 58, 48, 52, 42, 30],
          row_fills={0: LIGHT, 1: GREEN, 2: AMBER, 3: GREY})

    # 3. Status ------------------------------------------------------------
    sheet(wb, "Status", "Phase status",
          "Phases 1-5 are complete for the USA. Everything after Phase 5 is unstarted.",
          ["Phase", "Name", "State", "Evidence", "Next action"],
          PHASES, [8, 28, 28, 46, 34],
          row_fills={2: AMBER, 3: AMBER})

    # 4. Work log ----------------------------------------------------------
    fills = {}
    for i, row in enumerate(WORK_LOG):
        if "Bug fix" in row[3]:
            fills[i] = AMBER
    sheet(wb, "Work Log", "Chronological work log",
          "Every substantive action taken since the first session, with the artefact it produced.",
          ["Date", "Session", "Phase", "Action", "Artefact / output", "Outcome"],
          WORK_LOG, [12, 9, 14, 76, 48, 46], row_fills=fills)

    # 5. Data sources ------------------------------------------------------
    rows = []
    vmap = {r["series_key"]: r for _, r in ver.iterrows()}
    rmap = {r["series_key"]: r for _, r in res.iterrows()}
    for _, s in scope[scope["country_iso3"] == "USA"].iterrows():
        key = s["series_key"]
        v = vmap.get(key, {})
        rr = rmap.get(key, {})
        rows.append((
            key,
            rr.get("source_id", s["preferred_source_series_id"]),
            s["priority_class"],
            s["beai_eligible"],
            v.get("native_freq", rr.get("native_freq", "")),
            v.get("seasonal", ""),
            v.get("first_obs", ""),
            v.get("last_obs", ""),
            float(v["coverage_pct"]) if v.get("coverage_pct") not in (None, "") and pd.notna(v.get("coverage_pct")) else None,
            rr.get("status", s["id_status"]),
            DATA_NOTES.get(key, ""),
        ))
    nber = vmap.get("USA.NBER.Q", {})
    rows.append(("USA.NBER.Q (aux)", "USRECQ", "aux", "N", nber.get("native_freq", "Q"), nber.get("seasonal", ""),
                 nber.get("first_obs", ""), nber.get("last_obs", ""), float(nber["coverage_pct"]),
                 "VERIFIED", DATA_NOTES["USA.NBER.Q"]))
    df = pd.DataFrame(rows, columns=["scope key", "source id", "priority", "BEAI", "freq", "SA",
                                     "first", "last", "coverage", "status", "note"])
    df = df.sort_values(["BEAI", "priority", "scope key"], ascending=[False, True, True])
    sheet(wb, "Data Sources", "USA series: verification and resolution",
          "Coverage = share of the 147 window quarters with a complete observation at native frequency.",
          list(df.columns), df.values.tolist(),
          [30, 34, 9, 8, 8, 8, 12, 12, 10, 22, 44],
          number_formats={9: "0.0%"})

    # 6. Labels ------------------------------------------------------------
    ws = wb.create_sheet("Labels")
    ws.sheet_view.showGridLines = False
    ws["A1"] = "USA BEAI label (labels-v3)"
    ws["A1"].font = TITLE_FONT
    ws["A2"] = "DFM on eight core indicators -> cumulated level -> BBQ -> diffusion gate >= 0.50"
    ws["A2"].font = SUB_FONT
    for col, w in zip("ABCDEF", [20, 16, 12, 14, 12, 14]):
        ws.column_dimensions[col].width = w

    r = 4
    ws.cell(row=r, column=1, value="Retained episodes").font = Font(bold=True, size=11, color=NAVY)
    r += 1
    heads = ["Peak", "Trough", "Duration (Q)", "Depth (SD)", "Diffusion", "Kept"]
    for c, h in enumerate(heads, 1):
        cell = ws.cell(row=r, column=c, value=h)
        cell.font = HEAD_FONT
        cell.fill = HEAD_FILL
        cell.alignment = CENTER
    for _, e in eps.iterrows():
        r += 1
        vals = [e["peak"], e["trough"], int(e["duration"]), round(float(e["depth_sd"]), 3),
                round(float(e["diffusion"]), 3), "yes" if e["kept"] else "no"]
        for c, v in enumerate(vals, 1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.font = BODY_FONT
            cell.border = BORDER
            cell.alignment = CENTER

    r += 2
    ws.cell(row=r, column=1, value="NBER comparison").font = Font(bold=True, size=11, color=NAVY)
    r += 1
    heads = ["NBER peak-trough", "Label peak-trough", "Peak diff", "Trough diff", "Overlap (Q)"]
    for c, h in enumerate(heads, 1):
        cell = ws.cell(row=r, column=c, value=h)
        cell.font = HEAD_FONT
        cell.fill = HEAD_FILL
        cell.alignment = CENTER
    compare = [
        (f"{m.nber_peak}-{m.nber_trough}", f"{m.label_peak}-{m.label_trough}",
         int(m.peak_diff_q), int(m.trough_diff_q), int(m.overlap_quarters))
        for m in match.itertuples(index=False)
    ]
    for row in compare:
        r += 1
        for c, v in enumerate(row, 1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.font = BODY_FONT
            cell.border = BORDER
            cell.alignment = CENTER

    r += 2
    ws.cell(row=r, column=1, value="Quarter-level confusion matrix").font = Font(bold=True, size=11, color=NAVY)
    r += 1
    matrix = [("", "NBER 1", "NBER 0"), ("label 1", cm["tp"], cm["fp"]), ("label 0", cm["fn"], cm["tn"])]
    for row in matrix:
        for c, v in enumerate(row, 1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.font = HEAD_FONT if row is matrix[0] or c == 1 else BODY_FONT
            cell.fill = HEAD_FILL if row is matrix[0] or c == 1 else PatternFill("solid", fgColor=GREY)
            cell.border = BORDER
            cell.alignment = CENTER
        r += 1

    r += 1
    metrics = [("Accuracy", round(cm["accuracy"], 3)), ("Precision", round(cm["precision"], 3)),
               ("Recall", round(cm["recall"], 3)), ("F1", round(cm["f1"], 3)),
               ("Recession quarters: NBER", cm["nber_quarters"]),
               ("Recession quarters: label", cm["label_quarters"])]
    ws.cell(row=r, column=1, value="Metrics").font = Font(bold=True, size=11, color=NAVY)
    r += 1
    for k, v in metrics:
        ws.cell(row=r, column=1, value=k).font = Font(bold=True, size=10)
        cell = ws.cell(row=r, column=2, value=v)
        cell.font = BODY_FONT
        cell.alignment = CENTER
        r += 1

    r += 1
    ws.cell(row=r, column=1, value="Frozen parameters").font = Font(bold=True, size=11, color=NAVY)
    r += 1
    params = [
        ("Estimator", f"{meta['method']['estimator']} (converged={meta['method']['converged']})"),
        ("Factor order", "1 factor, AR(1), idio AR(1)"),
        ("Estimation sample", "1960Q1-2026Q3"),
        ("Reporting window", "1990Q1-2026Q3 (147 quarters)"),
        ("Min phase / cycle", "2 / 5 quarters"),
        ("Endpoint censoring", "2 quarters"),
        ("Diffusion gate", "0.50"),
        ("Labels hash", meta["hashes"]["labels_csv_sha256"][:32] + "..."),
    ]
    for k, v in params:
        ws.cell(row=r, column=1, value=k).font = Font(bold=True, size=10)
        c = ws.cell(row=r, column=2, value=v)
        c.font = BODY_FONT
        c.alignment = WRAP
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
        r += 1

    r += 1
    ws.cell(row=r, column=1, value="Selected label decisions").font = Font(bold=True, size=11, color=NAVY)
    r += 1
    decision_rows = [
        ("Q-02", "B: constructed real non-residential business fixed investment (4 BEA components); GPDIC1 retired"),
        ("Q-04", "B: CE16OV household/LFS employment, quarterly mean; PAYEMS retired from the label"),
        ("Q-05", "A: keep HOANBS; nonfarm-business sector coverage documented"),
    ]
    for qid, text in decision_rows:
        ws.cell(row=r, column=1, value=qid).font = MONO
        c = ws.cell(row=r, column=2, value=text)
        c.font = BODY_FONT
        c.alignment = WRAP
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
        r += 1

    # 7. Robustness --------------------------------------------------------
    sheet(wb, "Robustness", "Label robustness",
          "Dates must not move by more than one quarter when the specification changes.",
          ["Variant", "Candidates", "Kept", "Kept dates"],
          [(r[0], int(r[1]), int(r[2]), r[3]) for r in rob.itertuples(index=False)],
          [26, 12, 10, 82],
          number_formats={2: "0", 3: "0"})

    # 8. Tests -------------------------------------------------------------
    sheet(wb, "Tests", "Test suite (32 invariants)",
          "These establish software correctness only; economic credibility comes from the NBER comparison.",
          ["Module", "Test", "What it protects"],
          TESTS, [18, 58, 70])

    # 9. Repo map ----------------------------------------------------------
    sheet(wb, "Repo Map", "Repository contents",
          "What each path is for. Generated files are marked in their description.",
          ["Path", "Purpose", "Role"], REPO_MAP, [44, 76, 30])

    # 10. Decisions ---------------------------------------------------------
    ws = wb.create_sheet("Decisions")
    ws.sheet_view.showGridLines = False
    ws["A1"] = "Decisions and open items"
    ws["A1"].font = TITLE_FONT
    ws["A2"] = "Full text in docs/DECISIONS.md; Phase 2 log in decisions_log.csv."
    ws["A2"].font = SUB_FONT
    for col, w in zip("ABCD", [10, 96, 16, 22]):
        ws.column_dimensions[col].width = w

    r = 4
    for c, h in enumerate(["ID", "Decision", "Status"], 1):
        cell = ws.cell(row=r, column=c, value=h)
        cell.font = HEAD_FONT
        cell.fill = HEAD_FILL
        cell.alignment = CENTER
    for did, text, status in DECISIONS:
        r += 1
        ws.cell(row=r, column=1, value=did).font = MONO
        ws.cell(row=r, column=2, value=text).font = BODY_FONT
        ws.cell(row=r, column=2).alignment = WRAP
        cell = ws.cell(row=r, column=3, value=status)
        cell.font = BODY_FONT
        cell.alignment = CENTER
        cell.fill = PatternFill("solid", fgColor=GREEN if status == "FROZEN" else AMBER)
        for c in range(1, 4):
            ws.cell(row=r, column=c).border = BORDER

    r += 2
    for c, h in enumerate(["ID", "Open question", "Default", "Needed by"], 1):
        cell = ws.cell(row=r, column=c, value=h)
        cell.font = HEAD_FONT
        cell.fill = HEAD_FILL
        cell.alignment = CENTER
    for oid, q, default, needs in OPEN_ITEMS:
        r += 1
        ws.cell(row=r, column=1, value=oid).font = MONO
        ws.cell(row=r, column=2, value=q).font = BODY_FONT
        ws.cell(row=r, column=2).alignment = WRAP
        ws.cell(row=r, column=3, value=default).font = BODY_FONT
        ws.cell(row=r, column=4, value=needs).font = BODY_FONT
        for c in range(1, 5):
            ws.cell(row=r, column=c).border = BORDER

    # 11. Next phases ------------------------------------------------------
    sheet(wb, "Next Phases", "Roadmap",
          "Dependency order. Two gates: per-country label validation, and the LOCO eligibility gate.",
          ["Phase", "Work", "Gate / done when", "Decisions"],
          [
              ("6a", "Japan: 21 rows, BOJ + OECD", "6/8 core at >=70%; label matches ESRI within ~1 quarter", "O-1, O-2"),
              ("6b", "Germany: 21 rows, OECD/Bundesbank", "6/8 core at >=70%; label matches official chronology", "O-2"),
              ("6c", "India coverage case study", "Downloaded-data 6/8 count; Label-B-only if it fails (best case 4/8)", "O-2"),
              ("7", "Predictor feature table", "dataset.parquet; leakage test passes; no BEAI column", "O-4"),
              ("8", "Walk-forward harness", "One country x horizon x 6 models reproducible from a seed", "O-3"),
              ("9", "Experiments and metrics", "PR-AUC pooled, episode tables, false-warning counts, pre-registered ensemble result", "O-5, C-13"),
              ("10", "Cross-country LOCO", "Only headline if >=6 countries and >=20 episodes", "-"),
              ("11", "Interpretation", "REWI/SHAP stability per horizon", "-"),
              ("12", "Dashboard and write-up", "Reproducible from a clean clone", "-"),
          ],
          [8, 44, 70, 18])

    # 12. Run book ---------------------------------------------------------
    sheet(wb, "Run Book", "Commands",
          "Everything runs from the project root. No FRED API key is required.",
          ["Step", "Command", "What it does"], RUNBOOK, [16, 52, 60])

    wb.save(OUT)
    print(f"written {OUT}")
    print(f"sheets: {', '.join(wb.sheetnames)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
