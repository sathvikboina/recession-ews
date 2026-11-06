#!/usr/bin/env python3
"""Build Team_Plan.xlsx - the plain-English team plan.

The workbook is written for the four project members, not for specialists.
It explains what is done, what comes next, who does what, how the four parts
run in parallel, and how the pieces are joined at the end.

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
    """A table whose columns can span several sheet columns.

    ``spans`` gives (start_column, end_column) for each logical column.
    The text is written in the first cell and the cells are merged.
    """
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
    header_row = row
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
                if bold_first and start == 1:
                    cell.font = BOLD_FONT
                elif start == 1:
                    cell.font = BODY_FONT
                else:
                    cell.font = BODY_FONT
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
        "Recession Early-Warning Project - Simple Team Plan",
        "One page to understand what is done, what is next, who does what, and how the four parts fit together. "
        "Plain English first; technical detail is in the other sheets and in docs/TEAM_PLAN.md.",
        [32, 55, 78],
    )
    row = 4
    row = section(ws, row, "The project in one sentence", 3)
    row = note(
        ws,
        row,
        "We are building a careful, testable recession 'answer key' from eight measures of economic activity. "
        "Later we will test whether other economic data can warn us before a recession starts. "
        "We do not claim we can predict recessions yet.",
        3,
        height=36,
    )
    row += 1
    row = section(ws, row, "The one-page summary", 3)
    rows = [
        (
            "What is this project?",
            "A careful study of recession dates and early-warning tests.",
            "We build a recession answer key from eight activity measures. Then we test whether other data can warn us "
            "before a recession starts. The label comes first; the predictors are kept separate.",
        ),
        (
            "What is already done?",
            "The US label is built, checked and frozen.",
            "It matches all four US recessions since 1990. The old version is archived unchanged. Two data problems "
            "were fixed and signed off. The ensemble rule was written down before any model was run. 32 software "
            "tests pass.",
        ),
        (
            "What is not done?",
            "Japan, Germany, features, models and the final report.",
            "There is no Japan or Germany label, no predictor table, no model and no out-of-sample result yet. "
            "India cannot get the main label, so it becomes a case study.",
        ),
        (
            "Who does what?",
            "Four people, four separate jobs.",
            "1) Japan and Germany labels. 2) Predictor table and fair test splits. 3) Six models plus the "
            "pre-registered ensemble. 4) India, integration, writing and final packaging.",
        ),
        (
            "How does the work fit together?",
            "Answer key first, then inputs and test splits, then models, then the story.",
            "Part 1 makes the labels. Part 2 makes the predictor table and the time folds. Part 3 trains and tests "
            "models on those folds. Part 4 checks India, keeps the documents honest and assembles the final project.",
        ),
        (
            "What rules must everyone follow?",
            "No label changes, no leakage, no ensemble changes, no overclaiming.",
            "Do not change the US label without a new version. Do not use future data or the answer key as an input. "
            "Do not change the ensemble after seeing scores. Do not relax the 6-of-8 rule. Do not claim prediction "
            "before out-of-sample results. Do not build the final bundle or tag without approval.",
        ),
        (
            "What does done look like?",
            "Three country labels, one India case study, one honest model result, one reproducible package.",
            "USA, Japan and Germany have frozen labels with chronology checks. India has a downloaded-data verdict. "
            "The feature table and folds pass leakage tests. The ensemble result is reported exactly once. A clean "
            "clone passes all checks.",
        ),
        (
            "What should I read first?",
            "This workbook, then the team plan and build contract.",
            "Start with the Team Plan and Task Detail sheets. Then read docs/TEAM_PLAN.md, docs/BUILD_CONTRACT.md and "
            "docs/PROPOSAL_ADDENDUM.md.",
        ),
    ]
    row = table(ws, row, ["Question", "Short answer", "More detail"], rows, [32, 55, 78], bold_first=True)
    row = note(
        ws,
        row,
        "Colour key used later: blue = planned work, green = review or done, amber = decision or buffer, "
        "grey = not started. Names in the Team Plan are suggested. Swap them if the team agrees; keep the four "
        "roles separate.",
        3,
        height=32,
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
        [13, 18, 62, 62, 42],
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
        ("2026-11-04", "Data fix", "Replaced broad investment GPDIC1 with a non-residential construction; replaced PAYEMS with CE16OV; documented HOANBS.",
         "Removes two real data defects and makes the label match its own rules.", "labels-v2, docs/DECISION_NOTE_Q02_Q04_Q05.md"),
        ("2026-11-04", "Freeze", "Archived labels-v1 byte-identical and froze labels-v2 with recorded hashes.",
         "Old results stay reproducible; new results are locked.", "outputs/labels/archive/labels-v1/, labels-v2.json"),
        ("2026-11-05", "Review", "Found and fixed 11 issues: stale decision source, forecasting wording, missing ensemble rule, unaudited India, ambiguous download count and stale test counts.",
         "Prevents a rebuild from reverting decisions and stops unsupported claims.", "docs/REVIEW_2026-11-05.md"),
        ("2026-11-05", "India", "Checked India against the 6-of-8 rule before collection.",
         "Best case is 4 of 8, so India becomes a case study and the story changes early.", "docs/INDIA_COVERAGE_AUDIT.md"),
        ("2026-11-05", "Ensemble", "Wrote the ensemble rule, leakage rules and beat-the-best test before any model result.",
         "Stops anyone from choosing an ensemble after seeing scores.", "docs/PROPOSAL_ADDENDUM.md, BUILD_CONTRACT C-13"),
        ("2026-11-05", "Team plan", "Split the future work into four parallel packages.",
         "Gives each teammate a clear, separate job and a hand-off point.", "docs/TEAM_PLAN.md"),
        ("2026-11-05", "Verification", "Ran the 32 tests and the config check; confirmed the frozen hashes.",
         "Proves the current state is reproducible.", "pytest, make check, SHA-256 hashes"),
        ("2026-11-06", "This workbook", "Built Team_Plan.xlsx and updated the work log.",
         "Gives the team one simple plan and one place to see the history.", "Team_Plan.xlsx, EWS_Work_Log.xlsx"),
    ]
    table(ws, 4, ["Date", "Stage", "What happened", "Why it matters", "Where to look"], rows, [13, 18, 62, 62, 42])


# ---------------------------------------------------------------------------
# Sheet 3 - What Happens Next
# ---------------------------------------------------------------------------
def sheet_what_next(wb: Workbook) -> None:
    ws = start_sheet(
        wb,
        "What Happens Next",
        "What happens next",
        "Four work packages run in parallel. The final bundle is a separate approval step.",
        [8, 24, 55, 52, 42, 20],
    )
    rows = [
        ("1", "Japan + Germany labels",
         "Build the answer key for two more countries with the same frozen method used for the US.",
         "JPN and DEU labels, clean data, two validation notes.",
         "Nothing. Start source resolution now.", "Week 1"),
        ("2", "Feature table + harness",
         "Turn predictor data into a clean table and make fair 'train on past, test on future' splits.",
         "dataset.parquet, folds.json, leakage tests, feature dictionary.",
         "Can start now. Only the final run needs the new country labels.", "Week 1"),
        ("3", "Models + ensemble",
         "Run six models and the one pre-registered ensemble on the same folds; report what actually happens.",
         "Model code, headline table, episode table, ablations, results note.",
         "Code can start Week 1 against fake folds. Real runs need Part 2 folded output.", "Week 1 / Week 3"),
        ("4", "India + integration",
         "Finish India's downloaded-data count, keep the scope honest, and combine the four parts into one story.",
         "India coverage table, updated docs, plain-English pitch, clean-clone proof.",
         "Runs alongside everyone. Final assembly comes after Parts 1-3.", "Week 1"),
        ("Final", "Approval + packaging",
         "Rebuild the bundle, mirror and zip, then tag the release - only after explicit approval.",
         "Final bundle and release tag.",
         "All checks green and the project lead approves.", "After Week 5"),
    ]
    row = table(ws, 4, ["Step", "Work package", "Plain-English goal", "Main output", "Depends on", "Start"], rows, [8, 24, 55, 52, 42, 20])
    row = section(ws, row, "Decision gates - stop and report if one fails", 6)
    gates = [
        ("Gate 1", "Country label gate",
         "A country needs at least 6 of the 8 core indicators at 70% or more coverage, and a sensible chronology check.",
         "Do not relax the rule. Write the missing indicators and treat it as a finding."),
        ("Gate 2", "Feature gate",
         "No label input, no NBER series, no future data, and no country-size or country-id column may enter the predictor table.",
         "Fix the feature builder. Do not train a model on a leaking table."),
        ("Gate 3", "Model gate",
         "Every model uses the same folds and features. The threshold is locked before the test block. The ensemble rule is applied once.",
         "Report the single model as primary and the ensemble as a negative result."),
        ("Gate 4", "Release gate",
         "A clean clone passes the tests, the docs agree, and the project lead approves the final package.",
         "Do not build the bundle, mirror, zip or tag."),
    ]
    table(ws, row, ["Gate", "Name", "Rule in plain English", "What to do if it fails"], gates, [8, 24, 55, 52, 42, 20])


# ---------------------------------------------------------------------------
# Sheet 4 - Team Plan
# ---------------------------------------------------------------------------
def sheet_team_plan(wb: Workbook) -> None:
    ws = start_sheet(
        wb,
        "Team Plan",
        "The four work packages",
        "One owner per package. Suggested names follow the order the team is listed; swap names if you agree, "
        "but keep the four roles separate.",
        [26, 24, 58, 76, 66, 48],
    )
    rows = [
        (
            "Part 1\nSuggested owner: Shravani Math",
            "Data and label lead",
            "Job: Build Japan and Germany recession labels with the same frozen method used for the US.\n\n"
            "Why it matters: Everything else needs an answer key. One country and four recessions is too thin for a cross-country project.",
            "1) Resolve BOJ/OECD/BIS series.\n2) Download raw data with hashes.\n3) Harmonise to quarterly.\n4) Check 6 of 8 at 70%.\n5) Run the frozen label.\n6) Compare with ESRI and the German chronology.\n7) Freeze labels and write notes.",
            "Inputs: data/scope.csv, config/*.yaml, docs/BUILD_CONTRACT.md, US label code, OECD/BOJ access.\n\n"
            "Outputs: series_resolution rows, raw downloads + manifest, JPN/DEU clean panels, outputs/labels/JPN/* and DEU/*, validation notes.\n\n"
            "Done when: 21/21 rows resolved per country; 6/8 passed or documented; label reproducible; chronology compared; US hashes unchanged; tests green.",
            "Works with: Part 2 from day 1. Part 3 waits for the labels.\n\nMain risk: OECD/BOJ series IDs, Japan employment and hours availability, Germany's 1990-91 break.",
        ),
        (
            "Part 2\nSuggested owner: Arshiya",
            "ML engineering lead",
            "Job: Build the predictor table and the fair time-based test harness.\n\n"
            "Why it matters: Models are only as honest as the features and folds. Leakage is the biggest technical risk in the project.",
            "1) Write the feature spec.\n2) Build the table.\n3) Add leakage tests.\n4) Build expanding-window folds.\n5) Test fold boundaries and threshold locking.\n6) Add baselines.\n7) Write the feature dictionary and hand off.",
            "Inputs: clean country panels, series_resolution, C-01/C-05/C-06/C-07/C-08, scope config.\n\n"
            "Outputs: src/ews/features.py, src/ews/harness.py, scripts/05_features.py, scripts/06_folds.py, tests, dataset.parquet, folds.json.\n\n"
            "Done when: make features and make folds run; one country x horizon reproducible; leakage tests pass; a deliberately shuffled pipeline fails; no BEAI/NBER column.",
            "Works with: Part 1 from day 1. Part 3 uses the outputs.\n\nMain risk: accidentally including label inputs or future data; unclear lag rules.",
        ),
        (
            "Part 3\nSuggested owner: Palchhin",
            "Modelling lead",
            "Job: Run six single models and the pre-registered ensemble on the same folds and report what actually happens.\n\n"
            "Why it matters: This is the first real test of whether the predictors help. The result may be negative and must be reported honestly.",
            "1) Six single models.\n2) REWI.\n3) Ensemble exactly as C-13.\n4) Headline run.\n5) Ablations.\n6) Robustness.\n7) Results note.",
            "Inputs: dataset.parquet, folds.json, country labels, C-09/C-10/C-13, docs/PROPOSAL_ADDENDUM.md.\n\n"
            "Outputs: model code, scripts/07_run.py, outputs/runs/*, outputs/results/*, docs/EXPERIMENTS.md.\n\n"
            "Done when: make run reproduces the headline table from a clean clone; every result row has data version, features, folds, parameters, threshold and seed; ensemble rule applied once.",
            "Works with: can write code Week 1 against fake folds. Real runs after Part 2.\n\nMain risk: optional model packages not installed; different tuning budgets; temptation to change the ensemble after scores.",
        ),
        (
            "Part 4\nSuggested owner: Sathvik Boina",
            "Validation, integration and writing lead",
            "Job: Close the India question, keep the scope honest, and turn the four work packages into one coherent project.\n\n"
            "Why it matters: A good project is not just code. It needs a clear story, consistent documents, and proof that it reproduces.",
            "1) India downloads and count.\n2) Keep O-2 as Label-B-only.\n3) Scope decision O-4 after JPN/DEU.\n4) Keep docs in sync.\n5) Write the plain-English pitch.\n6) Clean-clone check.\n7) Final packaging after approval.",
            "Inputs: all outputs from Parts 1-3, docs/INDIA_COVERAGE_AUDIT.md, decisions log, test results.\n\n"
            "Outputs: data/india_core_coverage.csv, updated decisions and docs, final README/pitch, clean-clone evidence, final bundle after approval.\n\n"
            "Done when: India has a downloaded-data count; docs agree; clean clone passes; no unsupported forecast claim; final bundle approved.",
            "Works with: starts Week 1 with India; integration throughout; final assembly last.\n\nMain risk: waiting for other parts; document drift; scope creep.",
        ),
    ]
    row = table(
        ws,
        4,
        ["Package and owner", "Role", "Job and why it matters", "Main tasks", "Inputs, outputs and done test", "Parallel work and main risk"],
        rows,
        [26, 24, 58, 76, 66, 48],
        bold_first=True,
    )
    note(
        ws,
        row,
        "Rule: one package, one owner. If someone is away, the package pauses; do not merge two packages into one person without recording the change.",
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
        "Detailed task list",
        "Every task has one owner, one output and one simple 'done' test. Weeks are a guide, not a promise.",
        [7, 8, 20, 30, 62, 40, 40, 46, 10, 20],
    )
    rows = [
        ("1.1", "Part 1", "Data/label lead", "Map Japan sources",
         "List every core indicator, the exact BOJ, e-Stat, Cabinet Office or OECD series, frequency, seasonal adjustment and first/last date. Do not guess.",
         "data/scope.csv, country source rules", "data/series_resolution.csv rows", "21/21 rows have a source or a written reason for pending", "W1", "None"),
        ("1.2", "Part 1", "Data/label lead", "Map Germany sources",
         "Same for Germany using OECD QNA/STES, BIS and Destatis. Note the 1990-91 reunification break.",
         "data/scope.csv, source rules", "series_resolution rows", "21/21 rows resolved or pending with reason", "W1", "1.1"),
        ("1.3", "Part 1", "Data/label lead", "Write fetch scripts",
         "Add OECD and BOJ fetchers. Cache raw files under data/raw/<source>/<date>. Record SHA-256, units, frequency and coverage. Respect the OECD limit of 60 downloads per hour.",
         "Source map, API access", "scripts/fetch_oecd.py, scripts/fetch_boj.py, manifest rows", "Re-running does not overwrite raw files; manifest is complete", "W1-W2", "1.1, 1.2"),
        ("1.4", "Part 1", "Data/label lead", "Harmonise by country",
         "Add a --country option. Monthly to quarterly mean with complete quarters only. No interpolation. Sign-align growth. Keep the US output byte-identical.",
         "Raw downloads, harmoniser", "JPN/DEU clean levels and growth", "Coverage table produced; US hashes do not move", "W2", "1.3"),
        ("1.5", "Part 1", "Data/label lead", "Apply the 6-of-8 gate",
         "Compute coverage over 1990Q1-2025Q4. 70% means 101 quarters. Count how many of the eight core indicators pass. Write the missing list.",
         "Clean panels", "Coverage table, verification note", "Each country passes 6/8 or the failure is written down", "W2-W3", "1.4"),
        ("1.6", "Part 1", "Data/label lead", "Build country labels",
         "Add a --country option to the label script. Keep the estimator, BBQ settings and diffusion gate frozen. Freeze the first label per country with hashes.",
         "Clean growth panels, label code", "outputs/labels/JPN/*, DEU/*", "Label reproducible; metadata records inputs and outputs", "W2-W3", "1.5"),
        ("1.7", "Part 1", "Data/label lead", "Check the chronology",
         "Compare Japan with ESRI reference dates and Germany with the official chronology. Report matches, misses, false episodes and boundary shifts.",
         "Country labels, label_references.csv", "Two validation notes", "Comparison written; no tuning to the chronology", "W3-W4", "1.6"),
        ("1.8", "Part 1", "Data/label lead", "Finish provenance and tests",
         "Update verification, state and decision records. Add country tests. Confirm the US label hashes did not change.",
         "All Part 1 outputs", "Docs, tests, manifest", "make check test green; US hashes unchanged", "W4", "1.7"),
        ("2.1", "Part 2", "ML engineering lead", "Write the feature spec",
         "Write the exact list of predictor series, transforms, lags and missing-data rules. No BEAI factor, no NBER, no label output.",
         "Scope, C-01/C-05/C-06/C-07", "Feature spec and column list", "Every column has a source, transform and lag", "W1", "None"),
        ("2.2", "Part 2", "ML engineering lead", "Build the feature table",
         "Build one row per country-quarter. Store unscaled values only. Missing stays missing. Include the separate predictor copies of BEAI rows.",
         "Clean panels, feature spec", "src/ews/features.py, scripts/05_features.py, dataset.parquet", "make features runs; row count and keys check out", "W1-W2", "2.1"),
        ("2.3", "Part 2", "ML engineering lead", "Add feature tests",
         "Test that no BEAI factor, NBER column, future observation, country id or country-size level enters the table. Test that missing stays missing.",
         "Feature table", "tests/test_features.py", "All tests pass; a deliberately leaking table fails", "W2", "2.2"),
        ("2.4", "Part 2", "ML engineering lead", "Build the fold builder",
         "Expanding-window walk-forward. Inner folds are time-ordered. y(t,H)=1 if a recession starts in t+1 to t+H. Horizons 1, 2 and 4 quarters; 2 is primary.",
         "Labels, feature table, C-08", "src/ews/harness.py, scripts/06_folds.py, folds.json", "make folds runs; boundaries are written to JSON", "W2-W3", "2.2"),
        ("2.5", "Part 2", "ML engineering lead", "Add fold tests",
         "Test that boundaries move forward only, no test row appears in training, the threshold is locked before the test block, and a shuffled pipeline fails.",
         "Fold builder", "tests/test_harness.py", "All tests pass; leaky variant fails", "W3", "2.4"),
        ("2.6", "Part 2", "ML engineering lead", "Add baselines",
         "Majority class, term-spread probit/logit, and plain logistic. These are the floor, not the headline.",
         "Feature table, folds", "Baseline results", "Baselines run on the same folds as the main models", "W3", "2.4"),
        ("2.7", "Part 2", "ML engineering lead", "Document and hand off",
         "Write the feature dictionary. Freeze dataset.parquet and folds.json. Hand both to Part 3 with the exact build commands.",
         "All Part 2 outputs", "Feature dictionary, hand-off note", "Part 3 can run from the handed files and a seed", "W3-W4", "2.3, 2.5, 2.6"),
        ("3.1", "Part 3", "Modelling lead", "Implement six models",
         "Logistic, elastic net, random forest, XGBoost, SVM and MLP. Use the same tuning budget and class weights. MLP averages at least three seeds.",
         "Feature table, folds, C-09", "Model code, scripts/07_run.py", "Every model runs on the same folds", "W1-W3", "2.4"),
        ("3.2", "Part 3", "Modelling lead", "Implement REWI",
         "Build the weighted index from training-fold coefficients only. Exclude the intercept. Report which features are selected and how stable they are.",
         "Feature table, folds", "REWI results", "No full-sample weights; stability table produced", "W3", "3.1"),
        ("3.3", "Part 3", "Modelling lead", "Implement the ensemble",
         "Equal-weight probability average of the top-3 models by inner-fold pooled PR-AUC. Same folds, same features, threshold locked. Apply the C-13 test exactly.",
         "Single-model inner-fold scores", "Ensemble code and per-fold member list", "Rule matches docs/PROPOSAL_ADDENDUM.md exactly", "W3-W4", "3.1"),
        ("3.4", "Part 3", "Modelling lead", "Run the headline experiment",
         "For each country and horizon, run six singles, the ensemble and the baselines. Primary metric is pooled out-of-sample PR-AUC. Add episode metrics.",
         "Models, ensemble, folds, labels", "outputs/results/headline.md, episodes.md", "Table reproducible from a seed; every row has metadata", "W4", "3.1-3.3"),
        ("3.5", "Part 3", "Modelling lead", "Run ablations",
         "Track 1: activity, labour, income, credit, prices, external. Track 2: I = activity+labour+income, II = +credit, III = +prices+external.",
         "Headline pipeline", "outputs/results/ablations.md", "Every ablation uses the same folds and threshold rule", "W4", "3.4"),
        ("3.6", "Part 3", "Modelling lead", "Run robustness",
         "COVID with and without 2020. Diffusion and minimum-phase variants. LOCO only if there are at least 6 countries, 20 episodes and no country above 40%.",
         "Headline pipeline", "outputs/results/robustness.md", "Any conditional experiment is clearly labelled exploratory", "W5", "3.4"),
        ("3.7", "Part 3", "Modelling lead", "Write the results note",
         "Write the headline, episode, ablation and ensemble decision. If the ensemble fails, say so and keep the best single model as primary.",
         "All Part 3 outputs", "docs/EXPERIMENTS.md, outputs/results/*", "Claims match the out-of-sample numbers; caveats present", "W5", "3.4-3.6"),
        ("4.1", "Part 4", "Validation/integration lead", "Download India data",
         "Download the candidate MoSPI and RBI series. Fill actual first/last date, frequency, coverage and status in a coverage table.",
         "India source notes", "data/india_core_coverage.csv", "Every India core row has a downloaded-data status", "W1-W2", "None"),
        ("4.2", "Part 4", "Validation/integration lead", "Close the India verdict",
         "Confirm whether a quarterly business/non-residential GFCF split exists and whether an official monthly retail series covers the window. Recompute 6/8.",
         "India coverage table", "Final India count and note", "Final count recorded; no proxy substituted", "W2", "4.1"),
        ("4.3", "Part 4", "Validation/integration lead", "Record the decisions",
         "Keep O-2 as Label-B-only unless the evidence changes. Update decisions_log.csv, unresolved_questions.csv and verification.",
         "India verdict", "Updated decision files and verification", "Docs agree with the downloaded-data count", "W2-W3", "4.2"),
        ("4.4", "Part 4", "Validation/integration lead", "Handle the scope decision",
         "Do not widen to P0-P2 until Japan and Germany pass their own label checks. If they pass, update scope and record the change.",
         "JPN/DEU label status", "Scope update or a written decision to wait", "No silent widening", "W3-W4", "1.7, 4.3"),
        ("4.5", "Part 4", "Validation/integration lead", "Keep the documents honest",
         "Keep README, STATE, DECISIONS, VERIFICATION and the work log in sync. Write the plain-English project story and pitch.",
         "Outputs from Parts 1-3", "Updated docs and pitch", "No unsupported forecast claim; counts and hashes agree", "W2-W5", "All parts"),
        ("4.6", "Part 4", "Validation/integration lead", "Clean clone and package",
         "Run make check test in a fresh clone. Rebuild the bundle, mirror and zip and tag the release only after approval.",
         "All outputs", "Clean-clone evidence, final bundle after approval", "Clean clone passes; approval recorded", "W5", "All parts"),
    ]
    table(
        ws,
        4,
        ["ID", "Part", "Owner", "Task", "What to do in plain English", "Inputs", "Outputs", "Done when", "Week", "Depends on"],
        rows,
        [7, 8, 20, 30, 62, 40, 40, 46, 10, 20],
        bold_first=True,
    )


# ---------------------------------------------------------------------------
# Sheet 6 - Parallel Schedule
# ---------------------------------------------------------------------------
def sheet_schedule(wb: Workbook) -> None:
    ws = start_sheet(
        wb,
        "Parallel Schedule",
        "Five-week parallel schedule",
        "The four parts run at the same time. Milestones are review points, not hand-off delays.",
        [36, 12, 11, 11, 11, 11, 11, 16],
    )
    rows = [
        ("M0 - US label frozen", "Done", "", "", "", "", "", ""),
        ("Part 1 - Japan source map", "", "Work", "Work", "Review", "", "", ""),
        ("Part 1 - Japan label + chronology", "", "", "Work", "Work", "Review", "", ""),
        ("Part 1 - Germany source map", "", "Work", "Work", "Work", "", "", ""),
        ("Part 1 - Germany label + chronology", "", "", "Work", "Work", "Review", "", ""),
        ("Part 1 - Freeze JPN/DEU + notes", "", "", "", "", "Work", "Review", ""),
        ("M1 - Japan label frozen", "", "", "M1", "", "", "", ""),
        ("M2 - Germany label frozen", "", "", "", "M2", "", "", ""),
        ("Part 2 - Feature spec", "", "Work", "", "", "", "", ""),
        ("Part 2 - Feature table + tests", "", "Work", "Work", "Review", "", "", ""),
        ("Part 2 - Folds + tests", "", "", "Work", "Work", "Review", "", ""),
        ("Part 2 - Baselines + hand-off", "", "", "", "Work", "Review", "", ""),
        ("M3 - Features and folds accepted", "", "", "", "", "M3", "", ""),
        ("Part 3 - Model code on fake folds", "", "Work", "Work", "", "", "", ""),
        ("Part 3 - Singles + REWI", "", "", "", "Work", "Review", "", ""),
        ("Part 3 - Ensemble + headline run", "", "", "", "", "Work", "Work", ""),
        ("Part 3 - Ablations + robustness", "", "", "", "", "Work", "Work", ""),
        ("Part 3 - Results note", "", "", "", "", "", "Work", ""),
        ("M4 - Ensemble result reported", "", "", "", "", "", "M4", ""),
        ("Part 4 - India downloads and count", "", "Work", "Work", "Review", "", "", ""),
        ("Part 4 - Decisions and scope", "", "", "Work", "Work", "", "", ""),
        ("Part 4 - Docs sync", "", "", "Work", "Work", "Work", "Review", ""),
        ("Part 4 - Pitch + clean clone", "", "", "", "", "Work", "Work", ""),
        ("M5 - Final package ready", "", "", "", "", "", "M5", ""),
        ("Final bundle and tag", "", "", "", "", "", "", "Approval"),
    ]
    row_fills = {}
    for i, row in enumerate(rows):
        if any(str(x).startswith("M") for x in row[1:]):
            row_fills[i] = AMBER
        elif "Done" in row:
            row_fills[i] = GREEN
        elif "Approval" in row:
            row_fills[i] = RED
    row = table(
        ws,
        4,
        ["Work stream", "Before W1", "Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "After W5"],
        rows,
        [36, 12, 11, 11, 11, 11, 11, 16],
        row_fills=row_fills,
        bold_first=True,
        header_height=30,
    )
    for r in range(5, 5 + len(rows)):
        for c in range(2, 9):
            cell = ws.cell(row=r, column=c)
            cell.alignment = CENTER
            if cell.value == "Work":
                cell.fill = PatternFill("solid", fgColor=LIGHT)
            elif cell.value == "Review":
                cell.fill = PatternFill("solid", fgColor=GREEN)
            elif str(cell.value).startswith("M"):
                cell.fill = PatternFill("solid", fgColor=AMBER)
            elif cell.value == "Approval":
                cell.fill = PatternFill("solid", fgColor=RED)
            elif cell.value == "Done":
                cell.fill = PatternFill("solid", fgColor=GREEN)
    add_legend(ws, row, [("Work", LIGHT), ("Review", GREEN), ("Milestone", AMBER), ("Approval needed", RED)], 8)
    note(
        ws,
        row + 1,
        "Parallel rule: Parts 1 and 2 start in Week 1. Part 3 writes model code in Weeks 1-2 against fake folds, then runs on real folds in Weeks 3-5. "
        "Part 4 starts India in Week 1 and integrates throughout. The schedule assumes one full-time person per part.",
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
        [7, 18, 22, 22, 50, 48, 44, 16],
    )
    rows = [
        ("H1", "Part 4 -> all", "India early warning",
         "India best case is 4/8. Do not wait for India to start the country labels.",
         "docs/INDIA_COVERAGE_AUDIT.md", "Everyone reads it", "Week 1"),
        ("H2", "Part 1 -> Part 2", "Clean country panels",
         "Clean JPN/DEU levels and growth, coverage table and source resolution.",
         "data/clean/, data/series_resolution.csv", "6/8 passed or failure written; no imputation", "As each country finishes"),
        ("H3", "Part 1 -> Part 3", "Frozen country labels",
         "The target labels and the chronology note for each country.",
         "outputs/labels/JPN/*, outputs/labels/DEU/*", "Hash recorded; chronology compared", "Before model run"),
        ("H4", "Part 2 -> Part 3", "Feature table and folds",
         "One predictor table and one fold file used by every model.",
         "data/clean/dataset.parquet, outputs/folds/folds.json", "Leakage tests pass; no BEAI/NBER; boundaries frozen", "Week 4"),
        ("H5", "Part 3 -> Part 4", "Model results",
         "Headline, episode, ablation and ensemble tables.",
         "outputs/results/*", "Same folds and features; C-13 applied once", "Week 5"),
        ("H6", "Part 4 -> all", "Final package",
         "Final docs, clean-clone evidence and the approved bundle.",
         "Repository, final bundle", "All checks green; approval recorded", "After Week 5"),
    ]
    row = table(ws, 4, ["ID", "From -> to", "Hand-off", "What is passed", "Where it lives", "Check before passing", "When"], rows, [7, 18, 22, 22, 50, 48, 44, 16], bold_first=True)

    row = section(ws, row, "Merge order - do not change this order", 8)
    merge_rows = [
        ("1", "Merge the Part 1 label branches first.", "Labels are the foundation. No model result is meaningful before the answer key is frozen."),
        ("2", "Merge the Part 2 feature and fold branch.", "The feature table and folds must match the labels that are now on main."),
        ("3", "Merge the Part 3 model branch.", "Models run only after the folds and labels are on main."),
        ("4", "Merge the Part 4 docs and integration branch.", "The final story is written after the results are known."),
        ("5", "Run a full clean-clone check.", "Proves the combined project reproduces on a fresh machine."),
        ("6", "Build the final bundle and tag only after approval.", "Packaging is a release step, not a development step."),
    ]
    merged_table(ws, row, ["Order", "Merge step", "Why"], merge_rows, [(1, 1), (2, 4), (5, 8)], [7, 18, 22, 22, 50, 48, 44, 16], bold_first=True)


# ---------------------------------------------------------------------------
# Sheet 8 - How We Combine
# ---------------------------------------------------------------------------
def sheet_combine(wb: Workbook) -> None:
    ws = start_sheet(
        wb,
        "How We Combine",
        "How the four parts become one project",
        "Think of the project as a small factory with four stations. Each station has one output that the next station needs.",
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
        ("Three country labels", "The answer key for the US, Japan and Germany, each with a chronology check.", "outputs/labels/"),
        ("India case study", "A downloaded-data verdict showing why India does or does not pass the 6-of-8 rule.", "data/india_core_coverage.csv, docs/INDIA_COVERAGE_AUDIT.md"),
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
        ("One branch per part.", "Do not mix two parts in one branch. It makes review and rollback impossible."),
        ("Fixed output paths.", "Each part writes to the paths in the Handoffs sheet. Do not move another part's files."),
        ("No hand-editing another part's output.", "If a number is wrong, fix the generator and rerun it."),
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
        ("R2", "No label change without a new version.", "Archive the old files, record hashes, re-validate the chronology and write a decision.", "D-R26 to D-R28"),
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
        ("RK1", "OECD and BOJ series IDs are unresolved.",
         "Warning: Part 1 spends a week guessing keys.\nAction: resolve the dataflow and series keys first. Do not guess. Ask for help early.",
         "Part 1"),
        ("RK2", "Japan or Germany may fail 6/8.",
         "Warning: a country cannot produce a label.\nAction: write the missing indicators, report the finding and move on. Do not relax the rule.",
         "Part 1"),
        ("RK3", "Germany's 1990-91 reunification break.",
         "Warning: the long history has a structural break.\nAction: use the source as published, record the break and let the audit choose the usable start.",
         "Part 1"),
        ("RK4", "Only four US recessions.",
         "Warning: small sample; unstable scores.\nAction: state the caveat, do not overclaim, and treat country labels as the main fix.",
         "All"),
        ("RK5", "Revised historical data.",
         "Warning: results are not a real-time vintage test.\nAction: say so in every report. Do not call it a real-time forecast.",
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
         "Warning: Part 3 cannot run XGBoost or SHAP.\nAction: install the full development environment before Week 3.",
         "Part 3"),
        ("RK10", "Four people working in parallel.",
         "Warning: files collide and docs drift.\nAction: use one branch per part, fixed output paths and the hand-off checks.",
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
        ("US recession label", "Solid", "Built from the eight activity measures, matches 4/4 NBER recessions, frozen as labels-v2. The old labels-v1 is archived byte-identical."),
        ("Two data defects", "Solid", "GPDIC1 (housing and inventories) and PAYEMS (establishment survey) are replaced and explicitly signed off for the US. HOANBS coverage is documented."),
        ("Decision source", "Solid", "spec.py and decisions_log.csv now agree. A regression test fails if they drift, so a rebuild cannot silently revert the decisions."),
        ("India", "Watch", "Pre-audit best case is 4/8. India is Label-B-only under O-2. The final downloaded-data count is still owed by Part 4."),
        ("Ensemble rule", "Solid", "Pre-registered before any model result: equal-weight top-3, at least +0.01 pooled PR-AUC, bootstrap interval excluding zero, no episode-recall loss."),
        ("Wording", "Solid", "The README and validation note say the current deliverable is a validated label, not a forecasting system."),
        ("Software checks", "Solid", "32 tests pass. make check gives 26 ok, 3 warnings for optional model packages, 0 failures."),
        ("Frozen artefacts", "Solid", "The v1 and v2 label hashes match. The archive SHA256SUMS file verifies. A fresh clone reproduces the same hashes."),
        ("Japan and Germany labels", "Gap", "Not started. This is the largest project gap and Part 1 starts with source resolution."),
        ("Features, folds and models", "Gap", "Not started. Parts 2 and 3 build them. No out-of-sample score exists yet."),
        ("Final bundle and tag", "Waiting", "Deliberately not built. It waits for explicit approval after the combined project passes its checks."),
    ]
    fills = []
    for _, status, _ in rows:
        fills.append(GREEN if status == "Solid" else AMBER if status == "Watch" else RED if status == "Gap" else GREY)
    row = table(ws, row, ["Area", "Status", "What the review found"], rows, [34, 14, 90], row_fills={i: c for i, c in enumerate(fills)}, bold_first=True)

    row = section(ws, row, "Verification results", 3)
    verify = [
        ("Tests", "32 passed", "pytest, 2026-11-06"),
        ("Config check", "26 ok, 3 warnings, 0 failures", "make check"),
        ("labels-v2 label hash", "f5ed42a6...16dc8e", "SHA-256"),
        ("labels-v2 metadata hash", "1fb38a76...09e74", "SHA-256"),
        ("labels-v1 label hash", "1a1b1f6a...b749e29a", "SHA-256, archive"),
        ("labels-v1 metadata hash", "954565d2...991834", "SHA-256, archive"),
        ("Fresh clone", "32 tests pass; same hashes", "git clone + pytest"),
        ("Working tree", "Clean; no tags; not pushed", "git status, git tag"),
    ]
    row = table(ws, row, ["Check", "Result", "How / when"], verify, [34, 14, 90], bold_first=True)

    row = section(ws, row, "Open decisions", 3)
    decisions = [
        ("O-1", "Use pre-1990 history for long-series countries?", "No, 1990-2025 for now", "Before the next label report"),
        ("O-2", "India fallback if 6/8 fails?", "Label-B-only case study", "Already applied provisionally; final count pending"),
        ("O-3", "Threshold objective: max F1 or recall at a precision floor?", "Max F1", "Before the harness"),
        ("O-4", "Widen scope from P0-P1 to P0-P2?", "No, until JPN/DEU pass", "After the country labels"),
        ("O-5", "COVID treatment and with/without evaluation?", "Keep, document, evaluate", "Before experiments"),
        ("Release", "Build the final bundle and tag?", "Not yet", "After explicit approval"),
    ]
    row = table(ws, row, ["ID", "Question", "Current default", "Needed by"], decisions, [34, 14, 90, 30], bold_first=True)

    row = section(ws, row, "Review verdict", 3)
    note(
        ws,
        row,
        "The project is in a good, honest state for the next stage. The US label is solid and reproducible, the two data defects are closed, India has been checked before collection, and the ensemble rule is frozen before results. "
        "The main gap is country coverage, not model code. That is why the team plan starts with Japan and Germany. Nothing in this review changed the frozen label.",
        3,
        height=66,
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
        ("2026-11-06", "This workbook", "Built Team_Plan.xlsx with the simple plan and the review.", "One place for the team to see what happened, what is next and how the work combines."),
        ("2026-11-06", "This workbook", "Updated EWS_Work_Log.xlsx with the team plan and this session.", "The detailed work log stays current."),
    ]
    table(ws, 4, ["Date", "Part / person", "What was done", "Result in plain English"], rows, [13, 24, 76, 60], bold_first=True)
    note(
        ws,
        4 + len(rows) + 2,
        "Rule: add one row whenever a package reaches a milestone or a decision is made. Do not rewrite old rows. If a decision changes, add a new row with the new date.",
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
        ("Coverage gate", "A country needs at least 6 of the 8 core indicators, each covering at least 70% of the 144 quarters."),
        ("Label B", "A simpler fallback label for a country that cannot build the main BEAI label."),
        ("Seasonal adjustment (SA)", "Removing normal seasonal patterns so quarter-to-quarter changes are comparable."),
        ("Clean clone", "A fresh copy of the repository used to prove the project reproduces from scratch."),
        ("Out-of-sample", "A test on data the model did not see during training."),
    ]
    table(ws, 4, ["Word", "Plain meaning"], rows, [30, 100], bold_first=True)


def main() -> int:
    wb = Workbook()
    wb.remove(wb.active)
    wb.properties.title = "Recession Early-Warning - Team Plan"
    wb.properties.subject = "Plain-English plan for four parallel work packages"
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
