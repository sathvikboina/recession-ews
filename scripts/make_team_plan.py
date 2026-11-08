#!/usr/bin/env python3
"""Build Team_Plan.xlsx - the plain-English one-week team plan.

The workbook is written for the four project members, not for specialists.
It explains what is done, what comes next, who does what on Days 1-5, how the
four parts are combined on Days 6-7, and what must be reviewed before release.

Run:
    python scripts/make_team_plan.py

The file is generated. Edit this script, not the workbook, when the plan changes.
"""
from __future__ import annotations

import math
from datetime import date
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / "Team_Plan.xlsx"

NAVY = "1F3864"
BLUE = "2E5C8A"
LIGHT = "DCE6F1"
PALE = "F7F9FC"
GREY = "F2F2F2"
GREEN = "E2EFDA"
AMBER = "FFF2CC"
RED = "F8D7DA"
WHITE = "FFFFFF"

TITLE_FONT = Font(bold=True, size=16, color=NAVY)
SUB_FONT = Font(italic=True, size=10, color="595959")
SECTION_FONT = Font(bold=True, size=11, color=NAVY)
HEAD_FONT = Font(bold=True, color=WHITE, size=10)
BODY_FONT = Font(size=10)
BOLD_FONT = Font(bold=True, size=10)
SMALL_FONT = Font(size=9)
HEAD_FILL = PatternFill("solid", fgColor=BLUE)
SECTION_FILL = PatternFill("solid", fgColor=LIGHT)
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)


def set_widths(ws, widths: list[int]) -> None:
    for i, width in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = width


def start_sheet(wb: Workbook, name: str, title: str, subtitle: str, widths: list[int]):
    ws = wb.create_sheet(name)
    ws.sheet_view.showGridLines = False
    set_widths(ws, widths)
    ncols = len(widths)
    ws["A1"] = title
    ws["A1"].font = TITLE_FONT
    ws.row_dimensions[1].height = 27
    ws["A2"] = subtitle
    ws["A2"].font = SUB_FONT
    ws["A2"].alignment = WRAP
    if ncols > 1:
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=ncols)
    ws.row_dimensions[2].height = 34
    ws.freeze_panes = "A5"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    return ws


def section(ws, row: int, text: str, ncols: int) -> int:
    cell = ws.cell(row=row, column=1, value=text)
    cell.font = SECTION_FONT
    cell.fill = SECTION_FILL
    cell.alignment = Alignment(vertical="center")
    if ncols > 1:
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=ncols)
    ws.row_dimensions[row].height = 22
    return row + 1


def note(ws, row: int, text: str, ncols: int, height: int = 32) -> int:
    cell = ws.cell(row=row, column=1, value=text)
    cell.font = SMALL_FONT
    cell.alignment = WRAP
    if ncols > 1:
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=ncols)
    ws.row_dimensions[row].height = height
    return row + 1


def estimate_height(values, widths, minimum: int = 18, maximum: int = 190) -> int:
    lines = 1
    for value, width in zip(values, widths):
        text = "" if value is None else str(value)
        for part in text.split("\n"):
            lines = max(lines, math.ceil(len(part) / max(width * 1.05, 8)))
    return min(maximum, max(minimum, lines * 14 + 6))


def table(
    ws,
    row: int,
    headers: list[str],
    rows: list[tuple],
    widths: list[int],
    *,
    row_fills: dict[int, str] | None = None,
    bold_first: bool = False,
    header_height: int = 32,
) -> int:
    for c, header in enumerate(headers, 1):
        cell = ws.cell(row=row, column=c, value=header)
        cell.font = HEAD_FONT
        cell.fill = HEAD_FILL
        cell.alignment = CENTER
        cell.border = BORDER
    ws.row_dimensions[row].height = header_height
    header_row = row
    row += 1

    for index, values in enumerate(rows):
        fill = None
        if row_fills and index in row_fills:
            fill = row_fills[index]
        elif index % 2 == 1:
            fill = PALE
        for c, value in enumerate(values, 1):
            cell = ws.cell(row=row, column=c, value=value)
            cell.font = BOLD_FONT if (bold_first and c == 1) else BODY_FONT
            cell.alignment = WRAP
            cell.border = BORDER
            if fill:
                cell.fill = PatternFill("solid", fgColor=fill)
        ws.row_dimensions[row].height = estimate_height(values, widths)
        row += 1

    ws.auto_filter.ref = f"A{header_row}:{get_column_letter(len(headers))}{row - 1}"
    return row + 1


def merged_table(
    ws,
    row: int,
    headers: list[str],
    rows: list[tuple],
    spans: list[tuple[int, int]],
    widths: list[int],
    *,
    bold_first: bool = False,
) -> int:
    """A table whose logical columns span several sheet columns."""
    for header, (start, end) in zip(headers, spans):
        for col in range(start, end + 1):
            cell = ws.cell(row=row, column=col)
            cell.fill = HEAD_FILL
            cell.border = BORDER
            cell.alignment = CENTER
        cell = ws.cell(row=row, column=start, value=header)
        cell.font = HEAD_FONT
        if end > start:
            ws.merge_cells(start_row=row, start_column=start, end_row=row, end_column=end)
    ws.row_dimensions[row].height = 32
    row += 1

    for index, values in enumerate(rows):
        fill = PALE if index % 2 == 1 else None
        logical_widths = []
        for value, (start, end) in zip(values, spans):
            logical_widths.append(sum(widths[start - 1:end]))
            for col in range(start, end + 1):
                cell = ws.cell(row=row, column=col)
                cell.border = BORDER
                cell.alignment = WRAP
                if fill:
                    cell.fill = PatternFill("solid", fgColor=fill)
                cell.font = BOLD_FONT if (bold_first and start == 1) else BODY_FONT
            cell = ws.cell(row=row, column=start, value=value)
            if end > start:
                ws.merge_cells(start_row=row, start_column=start, end_row=row, end_column=end)
        ws.row_dimensions[row].height = estimate_height(values, logical_widths)
        row += 1
    return row + 1


def add_legend(ws, row: int, items: list[tuple[str, str]], ncols: int) -> int:
    col = 1
    for label, colour in items:
        cell = ws.cell(row=row, column=col, value=label)
        cell.fill = PatternFill("solid", fgColor=colour)
        cell.font = SMALL_FONT
        cell.alignment = CENTER
        cell.border = BORDER
        col += 1
    if ncols > col - 1:
        ws.merge_cells(start_row=row, start_column=col, end_row=row, end_column=ncols)
    ws.row_dimensions[row].height = 20
    return row + 1


# ---------------------------------------------------------------------------
# Sheet 1 - Start Here
# ---------------------------------------------------------------------------
def sheet_start_here(wb: Workbook) -> None:
    ws = start_sheet(
        wb,
        "Start Here",
        "Recession Early-Warning Project - One-Week Team Plan",
        "One page to understand what is done, what is next, who does what, and how the four parts "
        "are joined. Days 1-5 are individual work; Days 6-7 are combining and review. Plain English first.",
        [32, 55, 78],
    )
    row = 4
    row = section(ws, row, "The project in one sentence", 3)
    row = note(
        ws,
        row,
        "We are building a careful, testable recession 'answer key' from eight measures of economic activity. "
        "The USA data now runs to 2026Q3 (147 quarters) and the label is frozen as labels-v3. "
        "We still do not claim we can predict recessions until the out-of-sample model results exist.",
        3,
        height=42,
    )
    row += 1
    row = section(ws, row, "The one-page summary", 3)
    rows = [
        ("What is this project?",
         "A careful study of recession dates and early-warning tests.",
         "We build a recession answer key from eight activity measures. Then we test whether other economic "
         "data can warn us before a recession starts. The label comes first; predictors stay separate."),
        ("What is already done?",
         "USA label is built, extended to 2026Q3, checked and frozen.",
         "labels-v3 covers 1990Q1-2026Q3 (147 quarters), matches all four US recessions since 1990, and has "
         "no false episodes. labels-v2 and labels-v1 are archived byte-identical. The ensemble rule was "
         "written before any model result. 38 software tests pass."),
        ("What is not done?",
         "Japan, Germany, features, models and the final report.",
         "There is no Japan or Germany label, no predictor table, no model and no out-of-sample result yet. "
         "India cannot get the main label, so it is a case study."),
        ("Who does what?",
         "Four people, four separate jobs.",
         "1) Japan and Germany labels. 2) Predictor table and fair test splits. 3) Six models plus the "
         "pre-registered ensemble. 4) India, integration, writing and final packaging."),
        ("How does the week work?",
         "Days 1-5 individual work; Days 6-7 combine and review.",
         "Each person owns one lane and hands off fixed files. On Day 6 the branches are merged in order "
         "1 -> 2 -> 3 -> 4. On Day 7 the team runs the full review, the clean-clone check and the go/no-go."),
        ("What rules must everyone follow?",
         "No silent label changes, no leakage, no ensemble changes, no overclaiming.",
         "Do not change labels-v3 without a new version. Do not use future data or the answer key as an input. "
         "Do not change the ensemble after seeing scores. Do not relax the 6-of-8 rule. Do not build the "
         "final bundle or tag without approval."),
        ("What does done look like?",
         "Three country labels or a written coverage finding, one India case study, one honest model result, one reproducible package.",
         "USA and Japan have frozen labels with chronology checks. Germany has a label or a complete coverage "
         "note. The feature table and folds pass leakage tests. The ensemble result is reported exactly once. "
         "A clean clone passes all checks."),
        ("What should I read first?",
         "The Team Plan and Task Detail sheets, then the Markdown plan.",
         "Read Team Plan, Task Detail and Parallel Schedule first. Then read docs/TEAM_PLAN.md, "
         "docs/BUILD_CONTRACT.md and docs/PROPOSAL_ADDENDUM.md."),
    ]
    row = table(ws, row, ["Question", "Short answer", "More detail"], rows, [32, 55, 78], bold_first=True)
    row = note(
        ws,
        row,
        "Colour key used later: blue = individual work, green = review or hand-off, amber = milestone or "
        "buffer, red = approval needed, grey = not started. Names are suggested; swap them if the team agrees, "
        "but keep the four lanes separate.",
        3,
        height=38,
    )


# ---------------------------------------------------------------------------
# Sheet 2 - What Happened
# ---------------------------------------------------------------------------
def sheet_what_happened(wb: Workbook) -> None:
    ws = start_sheet(
        wb,
        "What Happened",
        "What has happened so far",
        "A short, honest timeline. The full detailed work log is in EWS_Work_Log.xlsx.",
        [13, 20, 64, 60, 42],
    )
    rows = [
        ("2026-10-24", "Phase 1", "Built the literature matrix v4.",
         "Shows what methods already exist and what is not new. No novelty claim.", "literature_matrix.xlsx"),
        ("2026-10-28", "Phase 2", "Built the 16-sheet data dictionary, the 1,883-row series catalogue and the decision log.",
         "Gives the team one shared definition of indicators, sources, roles and the label firewall.",
         "recession_ews_data_dictionary.xlsx, decisions_log.csv"),
        ("2026-10-29", "Setup", "Made the runtime config, the 68-row collection shortlist, the FRED collector and the harmoniser.",
         "Turns the dictionary into a repeatable data pipeline.", "config/, data/scope.csv, scripts/"),
        ("2026-10-29", "First label", "Built the US BEAI label from eight activity measures and compared it with NBER dates.",
         "Proves the label idea works on the US before any model work.", "outputs/labels/, docs/LABEL_VALIDATION.md"),
        ("2026-11-04", "Data fix", "Replaced broad investment GPDIC1 with constructed real non-residential business fixed investment (equipment + structures + IPP, deflated); replaced PAYEMS with CE16OV; documented HOANBS.",
         "Removes two real data defects and makes the label match its own rules.", "labels-v2, docs/DECISION_NOTE_Q02_Q04_Q05.md"),
        ("2026-11-04", "Freeze v2", "Archived labels-v1 byte-identical and froze labels-v2 with recorded hashes.",
         "Old results stay reproducible; new results are locked.", "outputs/labels/archive/labels-v1/, labels-v2.json"),
        ("2026-11-05", "Review", "Found and fixed 11 issues: stale decision source, forecasting wording, missing ensemble rule, unaudited India and stale test counts.",
         "Prevents a rebuild from reverting decisions and stops unsupported claims.", "docs/REVIEW_2026-11-05.md"),
        ("2026-11-05", "India", "Checked India against the 6-of-8 rule before collection.",
         "Best case is 4 of 8, so India becomes a case study and the story changes early.", "docs/INDIA_COVERAGE_AUDIT.md"),
        ("2026-11-05", "Ensemble", "Wrote the ensemble rule, leakage rules and beat-the-best test before any model result.",
         "Stops anyone from choosing an ensemble after seeing scores.", "docs/PROPOSAL_ADDENDUM.md, BUILD_CONTRACT C-13"),
        ("2026-11-05", "Team plan", "Split the future work into four parallel packages.",
         "Gives each teammate a clear, separate job and a hand-off point.", "docs/TEAM_PLAN.md"),
        ("2026-11-06", "Data extension", "Extended the USA clean panel and label window from 2025Q4 to 2026Q3 using FRED downloads through 2026-09. Archived v2 byte-identical and froze labels-v3.",
         "The project now uses the latest 2025-2026 data, not a panel that stops in 2025. The label still matches 4/4 NBER recessions with no false episodes.", "outputs/labels/labels-v3.json, data/clean/USA_levels.parquet"),
        ("2026-11-06", "One-week plan", "Compressed the four packages into a seven-day sprint: Days 1-5 individual, Days 6-7 combine and review.",
         "The team gets a realistic one-week delivery rhythm with clear hand-offs and a single review gate.", "docs/TEAM_PLAN.md, Team_Plan.xlsx"),
        ("2026-11-06", "This workbook", "Built Team_Plan.xlsx and refreshed EWS_Work_Log.xlsx.",
         "Gives the team one simple plan and one place to see the history.", "Team_Plan.xlsx, EWS_Work_Log.xlsx"),
        ("2026-11-08", "Review fixes", "Reviewed the whole repository: centralised the runtime window, guarded the frozen label against silent overwrite, verified manifest hashes, split NBER into the validation artifact, fixed the annual lag, added real test assertions and CI, and cleaned stale paths, counts and lock files.",
         "The pipeline, docs and workbooks now agree; no frozen hash moved.", "docs/STATE.md, .github/workflows/ci.yml, scripts/make_worklog.py"),
    ]
    table(ws, 4, ["Date", "Stage", "What happened", "Why it matters", "Where to look"], rows, [13, 20, 64, 60, 42])


# ---------------------------------------------------------------------------
# Sheet 3 - What Happens Next
# ---------------------------------------------------------------------------
def sheet_what_next(wb: Workbook) -> None:
    ws = start_sheet(
        wb,
        "What Happens Next",
        "What happens next: the seven-day sprint",
        "Days 1-5: four people work in parallel on separate lanes. Days 6-7: combine, review and decide. "
        "Packaging is a separate approval step after Day 7.",
        [10, 26, 58, 54, 44, 22],
    )
    rows = [
        ("Days 1-5", "Part 1 - Japan + Germany labels",
         "Build the answer key for Japan; resolve and download Germany; build the German label only if the 6-of-8 gate passes.",
         "Japan panel and label, Germany source map and coverage decision.",
         "Nothing; start source resolution on Day 1.", "Days 1-5"),
        ("Days 1-5", "Part 2 - Feature table + harness",
         "Audit the 2026 extension, build the predictor table and make fair 'train on past, test on future' folds.",
         "dataset.parquet, folds.json, leakage tests, feature dictionary.",
         "Can start now; uses the extended USA panel.", "Days 1-5"),
        ("Days 1-5", "Part 3 - Models + ensemble",
         "Run six models and the one pre-registered ensemble on the same folds; report what actually happens.",
         "Model code, headline table, episode table, ablations, results note.",
         "Code starts Day 1 on a fixture; real runs use Part 2's draft folds from Day 3 and final folds from Day 5.", "Days 1-5"),
        ("Days 1-5", "Part 4 - India + integration",
         "Finish India's downloaded-data count, keep the scope honest, and prepare the merge and clean-clone checks.",
         "India coverage table, updated docs, clean-clone evidence, integration checklist.",
         "Runs alongside everyone; leads the merge on Day 6.", "Days 1-5"),
        ("Day 6", "Combine the four lanes",
         "Merge in the fixed order 1 -> 2 -> 3 -> 4 and run the checks after every merge.",
         "Combined main branch with labels, features, folds and model results.",
         "All four lanes have handed off their Day 5 files.", "Day 6"),
        ("Day 7", "Review and go/no-go",
         "Cross-review, run the full clean-clone check, verify hashes and decide whether the package is ready.",
         "Review record and written go/no-go decision.",
         "Day 6 merge is green.", "Day 7"),
        ("After Day 7", "Approval + packaging",
         "Build the bundle, mirror and zip, then tag the release - only after explicit approval.",
         "Final bundle and release tag.",
         "All checks green and the project lead approves.", "After Day 7"),
    ]
    row = table(ws, 4, ["When", "Work package", "Plain-English goal", "Main output", "Depends on", "Window"], rows, [10, 26, 58, 54, 44, 22])

    row = section(ws, row, "Gates - stop and report if one fails", 6)
    gates = [
        ("Gate 1", "Country label gate",
         "A country needs at least 6 of the 8 core indicators at 70% or more coverage of the 147-quarter window (at least 103 quarters), plus a sensible chronology check.",
         "Do not relax the rule. Write the missing indicators and treat it as a finding."),
        ("Gate 2", "Feature gate",
         "No label input, no NBER series, no future data and no country-size or country-id column may enter the predictor table.",
         "Fix the feature builder. Do not train a model on a leaking table."),
        ("Gate 3", "Model gate",
         "Every model uses the same folds and features. The threshold is locked before the test block. The ensemble rule is applied once.",
         "Report the single model as primary and the ensemble as a negative result."),
        ("Gate 4", "Release gate",
         "A clean clone passes the tests, the docs agree, and the project lead approves the final package.",
         "Do not build the bundle, mirror, zip or tag."),
    ]
    table(ws, row, ["Gate", "Name", "Rule in plain English", "What to do if it fails"], gates, [10, 26, 58, 54])


# ---------------------------------------------------------------------------
# Sheet 4 - Team Plan
# ---------------------------------------------------------------------------
def sheet_team_plan(wb: Workbook) -> None:
    ws = start_sheet(
        wb,
        "Team Plan",
        "The four work packages: Days 1-5",
        "One owner per package. Each person works alone on Days 1-5, then joins the merge and review on Days 6-7. "
        "Suggested names can be swapped; keep the four lanes separate.",
        [26, 24, 58, 76, 66, 48],
    )
    rows = [
        (
            "Part 1\nSuggested owner: Shravani Math",
            "Data and label lead",
            "Job: Build Japan's recession label and resolve Germany's data. Japan is the priority; Germany's label is a stretch goal only if the 6-of-8 gate passes by Day 5.\n\n"
            "Why it matters: Everything else needs an answer key. One country and four recessions is too thin for a cross-country project.",
            "Day 1: resolve BOJ/OECD/e-Stat Japan series.\nDay 2: download, harmonise and pass 6/8.\nDay 3: run the frozen label and compare with ESRI.\nDay 4: resolve and download Germany (OECD/Destatis/BIS).\nDay 5: Germany coverage and label decision.",
            "Inputs: data/scope.csv, config/*.yaml, BUILD_CONTRACT, US label code, OECD/BOJ access.\n\n"
            "Outputs: series_resolution rows, raw downloads + manifest, JPN/DEU clean panels, JPN label + chronology note, DEU coverage note.\n\n"
            "Done when: Japan label reproducible; Germany 6/8 decision written; US hashes unchanged; tests green.",
            "Day 6: audit the Japan label and Germany coverage before merge.\nDay 7: sign off the label lane.\n\nMain risk: source keys and Japan hours/employment; Germany may not finish in five days.",
        ),
        (
            "Part 2\nSuggested owner: Arshiya",
            "ML engineering lead",
            "Job: Build the predictor table and the fair time-based test harness on the extended USA panel.\n\n"
            "Why it matters: Models are only as honest as the features and folds. Leakage is the biggest technical risk in the project.",
            "Day 1: feature spec and 2026 data audit.\nDay 2: build the USA feature table.\nDay 3: leakage tests and draft folds.\nDay 4: final walk-forward folds and fold tests.\nDay 5: baselines, freeze dataset/folds and hand off.",
            "Inputs: extended clean panels, series_resolution, C-01/C-05/C-06/C-07/C-08, scope config.\n\n"
            "Outputs: src/ews/features.py, src/ews/harness.py, scripts/05_features.py, scripts/06_folds.py, tests, dataset.parquet, folds.json.\n\n"
            "Done when: make features and make folds run; one country x horizon reproducible; leakage tests pass; a deliberately shuffled pipeline fails; no BEAI/NBER column.",
            "Day 6: audit leakage and fold boundaries before merge.\nDay 7: sign off the feature lane.\n\nMain risk: accidentally including label inputs, future data or unclear lag rules.",
        ),
        (
            "Part 3\nSuggested owner: Palchhin",
            "Modelling lead",
            "Job: Run six single models and the pre-registered ensemble on the same folds and report what actually happens.\n\n"
            "Why it matters: This is the first real test of whether the predictors help. The result may be negative and must be reported honestly.",
            "Day 1: model interfaces and preprocessing.\nDay 2: six singles and baselines on a fixture.\nDay 3: REWI and inner-fold tuning.\nDay 4: real folds, ensemble and headline run.\nDay 5: ablations, robustness and results note.",
            "Inputs: dataset.parquet, folds.json, country labels, C-09/C-10/C-13, docs/PROPOSAL_ADDENDUM.md.\n\n"
            "Outputs: model code, scripts/07_run.py, outputs/runs/*, outputs/results/*, docs/EXPERIMENTS.md.\n\n"
            "Done when: make run reproduces the headline table from a clean clone; every result row has data version, features, folds, parameters, threshold and seed; ensemble rule applied once.",
            "Day 6: reproduce the headline result after merge.\nDay 7: audit the result tables and caveats.\n\nMain risk: optional packages not installed; different tuning budgets; temptation to change the ensemble after scores.",
        ),
        (
            "Part 4\nSuggested owner: Sathvik Boina",
            "Validation, integration and writing lead",
            "Job: Close the India question, keep the scope honest, prepare the merge and run the final review.\n\n"
            "Why it matters: A good project is not just code. It needs a clear story, consistent documents and proof that it reproduces.",
            "Day 1: download India data.\nDay 2: final India count and O-2 decision.\nDay 3: audit the 2026 extension and sync docs.\nDay 4: clean-clone and packaging dry run.\nDay 5: integration rehearsal and plain-English pitch.",
            "Inputs: all outputs from Parts 1-3, docs/INDIA_COVERAGE_AUDIT.md, decisions log, test results.\n\n"
            "Outputs: data/india_core_coverage.csv, updated decisions and docs, final README/pitch, clean-clone evidence, integration checklist.\n\n"
            "Done when: India has a downloaded-data count; docs agree; clean clone passes; no unsupported forecast claim; package ready for approval.",
            "Day 6: lead the merge in the fixed order.\nDay 7: lead the review and go/no-go.\n\nMain risk: waiting for other lanes; document drift; scope creep.",
        ),
    ]
    row = table(
        ws,
        4,
        ["Package and owner", "Role", "Job and why it matters", "Days 1-5 plan", "Inputs, outputs and done test", "Days 6-7 role and main risk"],
        rows,
        [26, 24, 58, 76, 66, 48],
        bold_first=True,
    )
    note(
        ws,
        row,
        "Rule: one lane, one owner. If someone is away, the lane pauses; do not merge two lanes into one person without recording the change.",
        6,
        height=30,
    )


# ---------------------------------------------------------------------------
# Sheet 5 - Task Detail
# ---------------------------------------------------------------------------
def sheet_tasks(wb: Workbook) -> None:
    ws = start_sheet(
        wb,
        "Task Detail",
        "Detailed task list: Days 1-5 individual, Days 6-7 joint",
        "Every task has one owner, one day, one output and one simple 'done' test. Days are a guide, not a promise.",
        [7, 8, 22, 8, 28, 62, 40, 40, 46, 18],
    )
    rows = [
        ("1.1", "Part 1", "Shravani", "Day 1", "Map Japan sources",
         "List every core indicator, the exact BOJ, e-Stat, Cabinet Office or OECD series, frequency, seasonal adjustment and first/last date. Do not guess.",
         "data/scope.csv, country source rules", "series_resolution rows", "21/21 rows have a source or a written reason for pending", "None"),
        ("1.2", "Part 1", "Shravani", "Day 2", "Download and clean Japan",
         "Download the Japan series, record SHA-256 and coverage, harmonise to quarterly with complete quarters only, no interpolation. Check 6/8 at 70% of 147 quarters (>=103).",
         "Japan source map, raw downloads", "JPN clean panel, coverage table", "6/8 passed or failure documented", "1.1"),
        ("1.3", "Part 1", "Shravani", "Day 3", "Build Japan label",
         "Run the frozen DFM -> BBQ -> diffusion pipeline. Compare with ESRI reference dates. Freeze the first Japan label with hashes and write the chronology note.",
         "JPN growth panel, frozen label code", "outputs/labels/JPN/*, validation note", "Label reproducible; 4/4-style chronology comparison written", "1.2"),
        ("1.4", "Part 1", "Shravani", "Day 4", "Map and download Germany",
         "Resolve OECD QNA/STES, Destatis and BIS series. Record the 1990-91 reunification break. Download and harmonise to quarterly; no interpolation.",
         "Germany source rules", "DEU source map, clean panel", "21/21 rows resolved or pending with reason; break documented", "1.1"),
        ("1.5", "Part 1", "Shravani", "Day 5", "Germany coverage and label decision",
         "Compute Germany 6/8 coverage. Build the label only if the gate passes. If it fails, write the missing-indicator finding and hand off a complete coverage note.",
         "DEU clean panel", "DEU coverage note, label if gate passes", "Gate decision recorded; no rule relaxation", "1.4"),
        ("2.1", "Part 2", "Arshiya", "Day 1", "Write feature spec and audit 2026 data",
         "Write the exact predictor list, transforms, lags and missing-data rules. Confirm the 2026Q1-Q3 extension is complete and that no BEAI factor, NBER or label output enters the table.",
         "Scope, C-01/C-05/C-06/C-07, 2026 panel", "Feature spec and column list", "Every column has a source, transform and lag; 2026 audit written", "None"),
        ("2.2", "Part 2", "Arshiya", "Day 2", "Build the USA feature table",
         "Build one row per country-quarter, 1990Q1-2026Q3. Store unscaled values only. Missing stays missing. Include separate predictor copies of BEAI rows.",
         "Clean panels, feature spec", "src/ews/features.py, scripts/05_features.py, dataset.parquet", "make features runs; row count and keys check out", "2.1"),
        ("2.3", "Part 2", "Arshiya", "Day 3", "Add leakage tests and draft folds",
         "Test that no BEAI factor, NBER column, future observation, country id or country-size level enters the table. Build a draft expanding-window fold file for Part 3.",
         "Feature table", "tests/test_features.py, draft folds.json", "All leakage tests pass; a deliberately leaking table fails", "2.2"),
        ("2.4", "Part 2", "Arshiya", "Day 4", "Build final walk-forward folds",
         "Expanding-window walk-forward. Inner folds are time-ordered. y(t,H)=1 if a recession starts in t+1 to t+H. Horizons 1, 2 and 4 quarters; 2 is primary.",
         "Labels, feature table, C-08", "src/ews/harness.py, scripts/06_folds.py, folds.json", "make folds runs; boundaries written to JSON; no test row in training", "2.3"),
        ("2.5", "Part 2", "Arshiya", "Day 5", "Add baselines and freeze handoff",
         "Add majority class, term-spread probit/logit and plain logistic. Freeze dataset.parquet and folds.json. Write the feature dictionary and exact build commands.",
         "All Part 2 outputs", "Feature dictionary, handoff note", "Part 3 can run from the handed files and a seed", "2.2, 2.4"),
        ("3.1", "Part 3", "Palchhin", "Day 1", "Build model interfaces",
         "Wrap logistic, elastic net, random forest, XGBoost, SVM and MLP behind one interface. Freeze the tuning budget, class weights and MLP seed rule before scoring.",
         "Feature spec, C-09", "Model code skeleton", "Every model accepts the same table and fold object", "None"),
        ("3.2", "Part 3", "Palchhin", "Day 2", "Run six singles on a fixture",
         "Run the six singles and the baselines on a small fixture fold. Check shapes, probabilities, class weights and that no preprocessing is fitted outside the training fold.",
         "Model interfaces, fixture folds", "results table v0", "All models run on the fixture; leakage checks pass", "3.1"),
        ("3.3", "Part 3", "Palchhin", "Day 3", "Implement REWI and inner-fold tuning",
         "Build the weighted index from training-fold coefficients only. Exclude the intercept. Report selected features and stability. Tune only inside the training folds.",
         "Feature table, draft folds", "REWI results, stability table", "No full-sample weights; stability table produced", "3.2"),
        ("3.4", "Part 3", "Palchhin", "Day 4", "Implement ensemble and headline run",
         "Equal-weight probability average of the top-3 models by inner-fold pooled PR-AUC. Same folds, same features, threshold locked. Apply the C-13 test exactly.",
         "Single-model inner-fold scores, final folds", "Ensemble code, headline.md, episodes.md", "Rule matches docs/PROPOSAL_ADDENDUM.md exactly; every row has metadata", "3.3"),
        ("3.5", "Part 3", "Palchhin", "Day 5", "Run ablations, robustness and write the results note",
         "Track 1 categories; Track 2 I/II/III. COVID with and without 2020. Report a negative ensemble honestly. Write the headline, caveats and ensemble decision.",
         "Headline pipeline", "ablations.md, robustness.md, docs/EXPERIMENTS.md", "Claims match out-of-sample numbers; negative result kept", "3.4"),
        ("4.1", "Part 4", "Sathvik", "Day 1", "Download India data",
         "Download the candidate MoSPI and RBI series. Fill actual first/last date, frequency, coverage and status in a coverage table. Do not substitute a proxy.",
         "India source notes", "data/india_core_coverage.csv", "Every India core row has a downloaded-data status", "None"),
        ("4.2", "Part 4", "Sathvik", "Day 2", "Close the India verdict",
         "Confirm whether a quarterly business/non-residential GFCF split exists and whether an official monthly retail series covers the window. Recompute 6/8.",
         "India coverage table", "Final India count and note", "Final count recorded; O-2 stays Label-B-only", "4.1"),
        ("4.3", "Part 4", "Sathvik", "Day 3", "Audit the 2026 extension and sync docs",
         "Verify labels-v3, the 147-quarter window, v1/v2 archives and every hash. Update README, STATE, VERIFICATION and the claim wording. No unsupported forecast.",
         "v3 outputs, docs", "Updated docs", "Docs agree with v3; no unsupported forecast claim", "1.3, 2.2"),
        ("4.4", "Part 4", "Sathvik", "Day 4", "Clean-clone and packaging dry run",
         "Clone the repository into a fresh directory. Run make check, make test and the label hash check. Confirm the packaging checklist; do not create a bundle, mirror, zip or release tag.",
         "All outputs", "Clean-clone evidence, packaging checklist", "Fresh clone passes; nothing packaged or tagged", "4.3"),
        ("4.5", "Part 4", "Sathvik", "Day 5", "Integration rehearsal and plain-English pitch",
         "Do a dry-run merge in the fixed order. Write the one-page story: what was built, what the label proves, what the model result does not prove, and what is next.",
         "Outputs from Parts 1-3", "Rehearsal notes, pitch", "Merge order works; pitch is accurate and plain", "4.3, 2.5, 3.5"),
        ("6.1", "Day 6", "Sathvik + Shravani", "Day 6", "Merge Part 1 labels first",
         "Merge the label branch. Run the label hash checks and the chronology notes. Do not merge if a frozen hash moves or a country gate is undocumented.",
         "Part 1 outputs, main branch", "Labels on main", "All label checks green", "1.5"),
        ("6.2", "Day 6", "Sathvik + Arshiya", "Day 6", "Merge Part 2 features and folds",
         "Merge the feature/fold branch. Re-run leakage tests and check that the folds match the labels now on main.",
         "Part 2 outputs", "Features and folds on main", "Leakage tests green; fold boundaries unchanged", "6.1"),
        ("6.3", "Day 6", "Sathvik + Palchhin", "Day 6", "Merge Part 3 models",
         "Merge the model branch. Reproduce the headline table from the merged files and a seed. Do not change the ensemble rule to improve the result.",
         "Part 3 outputs", "Models and results on main", "Headline reproduces; C-13 applied once", "6.2"),
        ("6.4", "Day 6", "Sathvik + all", "Day 6", "Merge Part 4 docs and run full check",
         "Merge the docs/integration branch. Run make check, make test and the label hash check on the combined tree.",
         "All branches", "Combined main branch", "All checks green; no red merge", "6.3"),
        ("7.1", "Day 7", "All four", "Day 7", "Cross-review each other's lane",
         "Shravani reviews features/folds; Arshiya reviews labels; Palchhin reviews docs/India; Sathvik reviews models. Write findings, not verbal comments.",
         "Combined main branch", "Review notes", "Every lane has one named reviewer and written findings", "6.4"),
        ("7.2", "Day 7", "Sathvik + Arshiya", "Day 7", "Run the full clean-clone check",
         "Clone the combined repository into a fresh directory. Run make check, make test and verify all label hashes. Record the exact commands and output.",
         "Combined main branch", "Clean-clone evidence", "Fresh clone passes; hashes match", "7.1"),
        ("7.3", "Day 7", "All four", "Day 7", "Go/no-go review",
         "Review the four gates: label, features, models and release. Record a clear go or no-go with the reasons and the owner of each follow-up.",
         "Review notes, clean-clone evidence", "Written go/no-go decision", "Decision recorded; no silent exceptions", "7.2"),
        ("7.4", "Day 7", "Sathvik", "Day 7", "Package only if approved",
         "If the decision is go and the lead approves, build the bundle, mirror and zip and tag the release. If not, write the findings and next actions instead.",
         "Approval, combined tree", "Final package or findings note", "Approval recorded before any tag", "7.3"),
    ]
    table(
        ws,
        4,
        ["ID", "Part", "Owner", "Day", "Task", "What to do in plain English", "Inputs", "Outputs", "Done when", "Depends on"],
        rows,
        [7, 8, 22, 8, 28, 62, 40, 40, 46, 18],
        bold_first=True,
    )


# ---------------------------------------------------------------------------
# Sheet 6 - Parallel Schedule
# ---------------------------------------------------------------------------
def sheet_schedule(wb: Workbook) -> None:
    ws = start_sheet(
        wb,
        "Parallel Schedule",
        "Seven-day parallel schedule",
        "Days 1-5: four people work in parallel on separate lanes. Day 6: merge. Day 7: review and sign off.",
        [38, 17, 17, 17, 17, 17, 17, 17],
    )
    rows = [
        ("Part 1 - Japan (Shravani)", "Sources", "Data", "Label\nM1", "", "", "Audit", "Sign-off"),
        ("Part 1 - Germany (Shravani)", "", "", "", "Sources", "Coverage\nM2", "Audit", "Sign-off"),
        ("Part 2 - Features/folds (Arshiya)", "Spec", "Table", "Draft folds", "Folds", "Freeze\nM3", "Leak audit", "Sign-off"),
        ("Part 3 - Models (Palchhin)", "Interfaces", "Singles", "REWI", "Ensemble", "Results\nM4", "Reproduce", "Audit"),
        ("Part 4 - India/integration (Sathvik)", "India data", "India count", "Docs", "Clean clone", "Rehearsal", "Merge lead", "Review lead\nM5"),
        ("Joint - all four", "Individual", "Individual", "Individual", "Individual", "Individual", "Merge", "Review"),
        ("Release", "", "", "", "", "", "", "Approval"),
    ]
    row = table(
        ws,
        4,
        ["Work stream", "Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"],
        rows,
        [38, 17, 17, 17, 17, 17, 17, 17],
        bold_first=True,
        header_height=30,
    )
    for r in range(5, 5 + len(rows)):
        for c in range(2, 9):
            cell = ws.cell(row=r, column=c)
            cell.alignment = CENTER
            text = str(cell.value or "")
            if text == "Approval":
                cell.fill = PatternFill("solid", fgColor=RED)
            elif "M1" in text or "M2" in text or "M3" in text or "M4" in text or "M5" in text:
                cell.fill = PatternFill("solid", fgColor=AMBER)
            elif text in {"Merge", "Review", "Audit", "Sign-off", "Leak audit", "Reproduce", "Merge lead", "Review lead"} or "Review" in text:
                cell.fill = PatternFill("solid", fgColor=GREEN)
            elif text and text != "Individual":
                cell.fill = PatternFill("solid", fgColor=LIGHT)
    add_legend(ws, row, [("Individual work", LIGHT), ("Review / merge", GREEN), ("Milestone", AMBER), ("Approval needed", RED)], 8)
    note(
        ws,
        row + 1,
        "Parallel rule: all four lanes start on Day 1. Part 3 may use a fixture until Part 2 hands over draft folds on Day 3. "
        "No lane waits for another lane to finish before starting. Days 6-7 are shared work, not individual work.",
        8,
        height=44,
    )


# ---------------------------------------------------------------------------
# Sheet 7 - Handoffs
# ---------------------------------------------------------------------------
def sheet_handoffs(wb: Workbook) -> None:
    ws = start_sheet(
        wb,
        "Handoffs",
        "How the work moves between people",
        "A hand-off is only complete when the receiving person can run the output without asking for an explanation.",
        [7, 22, 24, 24, 50, 48, 44, 16],
    )
    rows = [
        ("H1", "Sathvik -> all", "Sprint start",
         "Read the v3 label, the 2026 data extension and the 7-day plan.",
         "docs/STATE.md, docs/TEAM_PLAN.md, Team_Plan.xlsx", "Everyone can state their Day 1 task", "Day 1 morning"),
        ("H2", "Arshiya -> Palchhin", "Draft folds",
         "A draft fold file with the same row keys and horizons as the final file.",
         "outputs/folds/folds.json (draft)", "Part 3 can run a fixture and a first real pass", "Day 3 end"),
        ("H3", "Shravani -> Sathvik", "Japan label and Germany coverage",
         "Japan label, chronology note and the German 6/8 decision.",
         "outputs/labels/JPN/*, DEU coverage note", "Hash recorded; chronology compared; gate decision written", "Day 5 end"),
        ("H4", "Arshiya -> Palchhin + Sathvik", "Final features and folds",
         "One predictor table and one fold file used by every model.",
         "data/clean/dataset.parquet, outputs/folds/folds.json", "Leakage tests pass; no BEAI/NBER; boundaries frozen", "Day 5 end"),
        ("H5", "Palchhin -> Sathvik", "Model results",
         "Headline, episode, ablation and ensemble tables.",
         "outputs/results/*", "Same folds and features; C-13 applied once", "Day 5 end"),
        ("H6", "All -> Sathvik", "Merge inputs",
         "One branch per lane, green checks and a short hand-off note.",
         "Four lane branches", "Each branch passes its own checks before merge", "Day 6 morning"),
        ("H7", "Sathvik -> all", "Review pack",
         "Clean-clone evidence, hash table and the written go/no-go draft.",
         "Combined main branch", "All four gates answered in writing", "Day 7 morning"),
    ]
    row = table(ws, 4, ["ID", "From -> to", "Hand-off", "What is passed", "Where it lives", "Check before passing", "When"], rows, [7, 22, 24, 24, 50, 48, 44, 16], bold_first=True)

    row = section(ws, row, "Merge order - do not change this order", 8)
    merge_rows = [
        ("1", "Merge the Part 1 label branch first.", "Labels are the foundation. No model result is meaningful before the answer key is frozen."),
        ("2", "Merge the Part 2 feature and fold branch.", "The feature table and folds must match the labels that are now on main."),
        ("3", "Merge the Part 3 model branch.", "Models run only after the folds and labels are on main."),
        ("4", "Merge the Part 4 docs and integration branch.", "The final story is written after the results are known."),
        ("5", "Run a full clean-clone check.", "Proves the combined project reproduces on a fresh machine."),
        ("6", "Build the final bundle and tag only after approval.", "Packaging is a release step, not a development step."),
    ]
    merged_table(ws, row, ["Order", "Merge step", "Why"], merge_rows, [(1, 1), (2, 4), (5, 8)], [7, 22, 24, 24, 50, 48, 44, 16], bold_first=True)


# ---------------------------------------------------------------------------
# Sheet 8 - How We Combine
# ---------------------------------------------------------------------------
def sheet_combine(wb: Workbook) -> None:
    ws = start_sheet(
        wb,
        "How We Combine",
        "How the four parts become one project",
        "Think of the project as a small factory with four stations. Each station has one output that the next station needs. Days 1-5 build the stations; Days 6-7 join them.",
        [16, 20, 40, 46, 50],
    )
    row = 4
    row = section(ws, row, "The four stations", 5)
    stations = [
        ("Station 1", "Part 1 - Data and labels",
         "Raw official data from Japan and Germany.",
         "Clean panels plus frozen recession labels.",
         "Part 2 needs clean activity data; Part 3 needs the labels as the target."),
        ("Station 2", "Part 2 - Features and folds",
         "Clean panels, predictor data and labels.",
         "One predictor table plus one set of time folds.",
         "Part 3 cannot train or test without a fixed table and fixed splits."),
        ("Station 3", "Part 3 - Models and ensemble",
         "Feature table, folds and labels.",
         "Scores, episode tables and one ensemble decision.",
         "Part 4 needs the numbers and the caveats to write the final story."),
        ("Station 4", "Part 4 - India and integration",
         "India downloads plus all outputs from Stations 1-3.",
         "India verdict, consistent docs, clean clone and final package.",
         "This is the assembled project that the team presents."),
    ]
    row = table(ws, row, ["Station", "Who", "What goes in", "What comes out", "Why the next station needs it"], stations, [16, 20, 40, 46, 50], bold_first=True)

    row = section(ws, row, "What the final project will contain", 5)
    contents = [
        ("Three country labels", "The answer key for the US, Japan and Germany, or a written coverage finding where a country fails.", "outputs/labels/"),
        ("India case study", "A downloaded-data verdict showing why India does or does not pass the 6-of-8 rule.", "data/india_core_coverage.csv, docs/INDIA_COVERAGE_AUDIT.md"),
        ("2025-2026 extension", "The USA panel and label extended to 2026Q3, with v2 archived byte-identical.", "labels-v3.json, outputs/labels/archive/labels-v2/"),
        ("Predictor table", "A clean table with no label inputs and no future information.", "data/clean/dataset.parquet"),
        ("Time folds", "The same train/test splits used by every model.", "outputs/folds/folds.json"),
        ("Model results", "Six single models, baselines and episode tables.", "outputs/results/"),
        ("Ensemble result", "One pre-registered ensemble result, positive or negative.", "outputs/results/headline.md"),
        ("Honest report", "A short write-up that states the data limits and does not overclaim.", "README.md, docs/EXPERIMENTS.md"),
        ("Reproducible package", "A clean clone that passes the tests and reproduces the label hashes.", "Repository, final bundle after approval"),
    ]
    row = merged_table(ws, row, ["Item", "What it proves", "Where it lives"], contents, [(1, 1), (2, 4), (5, 5)], [16, 20, 40, 46, 50], bold_first=True)

    row = section(ws, row, "Combining rules", 5)
    rules = [
        ("One branch per lane.", "Do not mix two lanes in one branch. It makes review and rollback impossible."),
        ("Fixed output paths.", "Each lane writes to the paths in the Handoffs sheet. Do not move another lane's files."),
        ("No hand-editing another lane's output.", "If a number is wrong, fix the generator and rerun it."),
        ("Merge in the stated order.", "Part 1 -> Part 2 -> Part 3 -> Part 4. The integration owner runs the checks after each merge."),
        ("Run the checks after every merge.", "make check test plus the label hash check. Do not merge a red branch."),
        ("Fix at the source, not in the report.", "Never patch a result table by hand to make the story look better."),
        ("Release only after approval.", "The final bundle, mirror, zip and tag are a separate approved step."),
    ]
    merged_table(ws, row, ["Rule", "What it means in practice"], rules, [(1, 2), (3, 5)], [16, 20, 40, 46, 50], bold_first=True)


# ---------------------------------------------------------------------------
# Sheet 9 - Rules and Risks
# ---------------------------------------------------------------------------
def sheet_rules(wb: Workbook) -> None:
    ws = start_sheet(
        wb,
        "Rules and Risks",
        "Rules everyone follows, and the risks to watch",
        "The rules protect the project from the mistakes that are easiest to make: leakage, silent changes and overclaiming.",
        [8, 30, 70, 40],
    )
    row = 4
    row = section(ws, row, "Non-negotiable rules", 4)
    rules = [
        ("R1", "Label first, predictors separate.", "The eight activity measures build the label. Predictors live in a different pipeline and never enter the label.", "C-01"),
        ("R2", "No label change without a new version.", "Archive the old files, record hashes, re-validate the chronology and write a decision.", "D-R26 to D-R31"),
        ("R3", "No leakage.", "Every scaler, selector, model parameter, ensemble member, weight and threshold is fitted inside the training fold. No future data.", "C-08, C-13"),
        ("R4", "No ensemble change after scores.", "The equal-weight top-3 rule and the beat-the-best test are fixed before the first result.", "C-13"),
        ("R5", "Missing stays missing.", "No interpolation, no forward fill, no partial-quarter imputation.", "C-03, C-06"),
        ("R6", "No relaxation of 6-of-8.", "A country that fails is a finding, not an exception. India is already handled this way.", "Q-06, D-R30"),
        ("R7", "No forecasting claim before results.", "Say 'we built and validated a recession label', not 'we predict recessions'.", "Proposal addendum"),
        ("R8", "One active source per series.", "Raw downloads are immutable. Retirements go in data/superseded_series.csv.", "D-R15, D-R16"),
        ("R9", "Regenerate, do not hand-edit.", "Config, scope, workbook and decision CSVs come from scripts.", "Makefile, scripts/"),
        ("R10", "No bundle or tag without approval.", "Packaging is a release decision, not a development step.", "Project lead"),
    ]
    row = table(ws, row, ["ID", "Rule", "What it means in practice", "Basis"], rules, [8, 30, 70, 40], bold_first=True)

    row = section(ws, row, "Risks to watch", 4)
    risks = [
        ("RK1", "Japan or Germany data access is unresolved.",
         "Warning: Part 1 spends the week guessing source keys.\nAction: resolve the dataflow and series keys first. Do not guess. Ask for help early.",
         "Part 1"),
        ("RK2", "Germany may not finish a label in five days.",
         "Warning: the week ends with a panel but no German label.\nAction: that is an acceptable deliverable if the coverage note and gate decision are complete. Do not fake a label.",
         "Part 1"),
        ("RK3", "Japan or Germany may fail 6/8.",
         "Warning: a country cannot produce a label.\nAction: write the missing indicators, report the finding and move on. Do not relax the rule.",
         "Part 1"),
        ("RK4", "Germany's 1990-91 reunification break.",
         "Warning: the long history has a structural break.\nAction: use the source as published, record the break and let the audit choose the usable start.",
         "Part 1"),
        ("RK5", "2026 data revisions.",
         "Warning: v3 is built on revised data, not real-time vintages.\nAction: say so in every report. Do not call it a real-time forecast.",
         "Part 4"),
        ("RK6", "Leakage in the feature table.",
         "Warning: scores look too good and are meaningless.\nAction: run the leakage tests. A deliberately shuffled pipeline must fail.",
         "Part 2"),
        ("RK7", "Different tuning budgets across models.",
         "Warning: the comparison is unfair.\nAction: freeze the budget and class weights before the run. Record them.",
         "Part 3"),
        ("RK8", "The ensemble may fail.",
         "Warning: the headline result is a single model.\nAction: that is an acceptable negative result. Report it with the same prominence.",
         "Part 3"),
        ("RK9", "Optional model packages are not installed.",
         "Warning: Part 3 cannot run XGBoost or SHAP.\nAction: install the full development environment before Day 3.",
         "Part 3"),
        ("RK10", "Four people working in parallel for one week.",
         "Warning: files collide, docs drift and the merge becomes a rescue.\nAction: one branch per lane, fixed output paths, daily stand-up and the Day 6 merge order.",
         "All"),
    ]
    table(ws, row, ["ID", "Risk", "Early warning and what to do", "Owner"], risks, [8, 30, 70, 40], bold_first=True)


# ---------------------------------------------------------------------------
# Sheet 10 - Final Review
# ---------------------------------------------------------------------------
def sheet_review(wb: Workbook) -> None:
    ws = start_sheet(
        wb,
        "Final Review",
        "Final review of the project so far",
        "A short, plain-English audit of what is solid, what is missing, and what the next person should trust.",
        [34, 14, 90],
    )
    row = 4
    row = section(ws, row, "Review summary", 3)
    rows = [
        ("US recession label", "Solid", "labels-v3 covers 1990Q1-2026Q3 (147 quarters), matches 4/4 NBER recessions and has 0 false episodes. labels-v2 and labels-v1 are archived byte-identical."),
        ("2025-2026 data", "Solid", "The USA panel now uses FRED observations through 2026Q3. The extension did not create a new false recession episode."),
        ("Two data defects", "Solid", "GPDIC1 (housing and inventories) and PAYEMS (establishment survey) are replaced and explicitly signed off for the USA. HOANBS coverage is documented."),
        ("Decision source", "Solid", "spec.py and decisions_log.csv now agree. A regression test fails if they drift, so a rebuild cannot silently revert the decisions."),
        ("India", "Watch", "Pre-audit best case is 4/8. India is Label-B-only under O-2. The final downloaded-data count is still owed by Part 4."),
        ("Ensemble rule", "Solid", "Pre-registered before any model result: equal-weight top-3, at least +0.01 pooled PR-AUC, bootstrap interval excluding zero, no episode-recall loss."),
        ("Wording", "Solid", "The README and validation note say the current deliverable is a validated label, not a forecasting system."),
        ("Software checks", "Solid", "38 tests pass. make check gives 33 ok, 3 warnings for optional model packages, 0 failures."),
        ("Frozen artefacts", "Solid", "labels-v1 and labels-v2 archive hashes match. labels-v3 is the active label. A fresh clone reproduces the same hashes."),
        ("Japan and Germany labels", "Gap", "Not started. Part 1 starts with Japan source resolution on Day 1; Germany is a stretch goal."),
        ("Features, folds and models", "Gap", "Not started. Parts 2 and 3 build them during Days 1-5. No out-of-sample score exists yet."),
        ("Final bundle and tag", "Waiting", "Deliberately not built. It waits for explicit approval after the combined project passes its checks."),
    ]
    fills = []
    for _, status, _ in rows:
        fills.append(GREEN if status == "Solid" else AMBER if status == "Watch" else RED if status == "Gap" else GREY)
    row = table(ws, row, ["Area", "Status", "What the review found"], rows, [34, 14, 90], row_fills={i: c for i, c in enumerate(fills)}, bold_first=True)

    row = section(ws, row, "Verification results", 3)
    verify = [
        ("Tests", "38 passed", "pytest, 2026-11-08"),
        ("Config check", "33 ok, 3 warnings, 0 failures", "make check"),
        ("labels-v3 label hash", "2379fd53...ed19daa", "SHA-256, active"),
        ("labels-v3 metadata hash", "6f1aa665...402c0a50", "SHA-256, active"),
        ("labels-v2 label hash", "f5ed42a6...16dc8e", "SHA-256, archive"),
        ("labels-v2 metadata hash", "1fb38a76...09e74", "SHA-256, archive"),
        ("labels-v1 label hash", "1a1b1f6a...b749e29a", "SHA-256, archive"),
        ("labels-v1 metadata hash", "954565d2...991834", "SHA-256, archive"),
        ("Fresh clone", "36 pass, 2 explicit skips; same hashes", "git clone + pytest (rebuild git-ignored data/clean to run all 38)"),
        ("Working tree", "Clean after the review commit; no tags; not pushed", "git status, git tag"),
    ]
    row = table(ws, row, ["Check", "Result", "How / when"], verify, [34, 14, 90], bold_first=True)

    row = section(ws, row, "Open decisions", 3)
    decisions = [
        ("O-1", "Use pre-1990 history for long-series countries?", "No, 1990-2026Q3 for now", "Before the next label report"),
        ("O-2", "India fallback if 6/8 fails?", "Label-B-only case study", "Already applied provisionally; final count pending"),
        ("O-3", "Threshold objective: max F1 or recall at a precision floor?", "Max F1", "Before the harness"),
        ("O-4", "Widen scope from P0-P1 to P0-P2?", "Defer until the label gate passes", "After the country labels"),
        ("O-5", "COVID treatment and with/without evaluation?", "Keep, document, evaluate", "Before experiments"),
        ("Release", "Build the final bundle and tag?", "Not yet", "After Day 7 approval"),
    ]
    row = table(ws, row, ["ID", "Question", "Current default", "Needed by"], decisions, [34, 14, 90, 30], bold_first=True)

    row = section(ws, row, "Review verdict", 3)
    note(
        ws,
        row,
        "The project is in a good, honest state for the one-week sprint. The USA label is solid, now extended to 2026Q3 and reproducible, the two data defects are closed, India has been checked before collection, and the ensemble rule is frozen before results. "
        "The main gap is country coverage, not model code. That is why the sprint starts with Japan and Germany. Nothing in this review changed the archived labels-v1 or labels-v2.",
        3,
        height=78,
    )


# ---------------------------------------------------------------------------
# Sheet 11 - Work Log
# ---------------------------------------------------------------------------
def sheet_worklog(wb: Workbook) -> None:
    ws = start_sheet(
        wb,
        "Work Log",
        "Simple work log",
        "The full detailed log is EWS_Work_Log.xlsx. This is the team-facing version.",
        [13, 24, 76, 60],
    )
    rows = [
        ("2026-10-24", "Project", "Built the literature matrix v4.", "Methods and gaps documented; no novelty claim."),
        ("2026-10-28", "Project", "Built the 16-sheet data dictionary and the 1,883-row series catalogue.", "Shared definitions for indicators, sources, roles and the firewall."),
        ("2026-10-29", "Project", "Built the runtime config, the 68-row shortlist and the FRED collector.", "The dictionary became a working data pipeline."),
        ("2026-10-29", "Project", "Built and validated the first US BEAI label.", "The label matched the NBER chronology."),
        ("2026-11-04", "Project", "Fixed the investment and employment inputs; froze labels-v2; archived labels-v1.", "The label now follows its own Q-02 and Q-04 rules."),
        ("2026-11-05", "Review", "Audited the repo; fixed the stale decision source, wording, download count and build contract.", "A rebuild cannot silently revert decisions; no forecasting claim."),
        ("2026-11-05", "Review", "Audited India against 6/8.", "Best case 4/8; India becomes a Label-B case study."),
        ("2026-11-05", "Review", "Pre-registered the ensemble and leakage rules.", "The rule is frozen before any model result."),
        ("2026-11-05", "Review", "Added two regression tests and updated the docs.", "32 tests pass; docs and decision source agree."),
        ("2026-11-05", "Team plan", "Wrote the four-package team plan.", "Each teammate has a separate job, output and done test."),
        ("2026-11-06", "Data extension", "Extended the USA panel and label window to 2026Q3; archived labels-v2 and froze labels-v3.", "2025-2026 data added; 4/4 NBER episodes still match; 32 tests pass."),
        ("2026-11-06", "One-week plan", "Compressed the four packages into a 7-day sprint: Days 1-5 individual, Days 6-7 combine and review.", "The team has a day-level plan with hand-offs and one review gate."),
        ("2026-11-06", "This workbook", "Built Team_Plan.xlsx with the 7-day plan and the review.", "One place for the team to see what happened, what is next and how the work combines."),
        ("2026-11-06", "This workbook", "Updated EWS_Work_Log.xlsx with the v3 extension and the sprint plan.", "The detailed work log stays current."),
        ("2026-11-08", "Review fixes", "Reviewed the whole repository and fixed the stale window text, runtime source, frozen-label guard, manifest checks, NBER split, annual lag, test skips, CI and stale paths/counts; removed old lock files and regenerated both workbooks.", "38 tests pass; labels-v3 and archive hashes are unchanged; the docs and workbooks agree."),
    ]
    table(ws, 4, ["Date", "Part / person", "What was done", "Result in plain English"], rows, [13, 24, 76, 60], bold_first=True)
    note(
        ws,
        4 + len(rows) + 2,
        "Rule: add one row whenever a lane reaches a milestone or a decision is made. Do not rewrite old rows. If a decision changes, add a new row with the new date.",
        4,
        height=30,
    )


# ---------------------------------------------------------------------------
# Sheet 12 - Glossary
# ---------------------------------------------------------------------------
def sheet_glossary(wb: Workbook) -> None:
    ws = start_sheet(
        wb,
        "Glossary",
        "Plain-English glossary",
        "If a term in this workbook or in the repo is unclear, start here.",
        [30, 100],
    )
    rows = [
        ("Label", "The answer key. Here it is a quarterly yes/no recession marker built from eight activity measures."),
        ("BEAI", "The eight core activity measures used to build the label: GDP, industrial production, employment, hours, income, consumption, retail and investment."),
        ("Predictor", "Data used to guess the label. Predictors are kept separate from the label inputs."),
        ("Leakage", "Accidentally using future information, the answer key, or the held-out country while training. It makes scores look good but meaningless."),
        ("Walk-forward", "Train on past data, test on the next block of time, then move the window forward. No random split."),
        ("Fold", "One train/test split in the walk-forward schedule."),
        ("PR-AUC", "A score for ranking rare events such as recessions. Higher is better. It is the primary metric."),
        ("Ensemble", "A combination of several models. Here it is the equal-weight average of the top three models."),
        ("Pre-registered", "The rule is written down before the scores are seen. Changing it after scores makes the test invalid."),
        ("Frozen", "The file is saved and hash-locked. Any change needs a new version and a new decision."),
        ("Coverage gate", "A country needs at least 6 of the 8 core indicators, each covering at least 70% of the 147 quarters (at least 103)."),
        ("Label B", "A simpler fallback label for a country that cannot build the main BEAI label."),
        ("labels-v3", "The active USA label. It extends the window to 2026Q3. labels-v1 and labels-v2 are archived byte-identical."),
        ("2026Q3", "The third quarter of 2026, the latest complete quarter in the extended USA panel."),
        ("Sprint", "A fixed, short delivery period. Here it is seven days: five individual days plus two combine/review days."),
        ("Seasonal adjustment (SA)", "Removing normal seasonal patterns so quarter-to-quarter changes are comparable."),
        ("Clean clone", "A fresh copy of the repository used to prove the project reproduces from scratch."),
        ("Out-of-sample", "A test on data the model did not see during training."),
    ]
    table(ws, 4, ["Word", "Plain meaning"], rows, [30, 100], bold_first=True)


def main() -> int:
    wb = Workbook()
    wb.remove(wb.active)
    wb.properties.title = "Recession Early-Warning - One-Week Team Plan"
    wb.properties.subject = "Plain-English 7-day plan for four parallel work packages"
    wb.properties.creator = "Recession EWS project"
    wb.properties.description = f"Generated {date.today().isoformat()} from scripts/make_team_plan.py"

    sheet_start_here(wb)
    sheet_what_happened(wb)
    sheet_what_next(wb)
    sheet_team_plan(wb)
    sheet_tasks(wb)
    sheet_schedule(wb)
    sheet_handoffs(wb)
    sheet_combine(wb)
    sheet_rules(wb)
    sheet_review(wb)
    sheet_worklog(wb)
    sheet_glossary(wb)

    wb.save(OUT)
    print(f"written {OUT}")
    print(f"sheets: {', '.join(wb.sheetnames)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
