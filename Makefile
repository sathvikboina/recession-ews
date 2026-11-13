PY ?= .venv/bin/python
VENV ?= .venv
BIN := $(VENV)/bin

.PHONY: help env config scope fetch harmonize labels validate pipeline check test team-plan worklog reports dashboard bootstrap clean

help:
	@echo "make env        create .venv and install the package (editable)"
	@echo "make config     regenerate config/*.yaml from spec.py"
	@echo "make scope      rebuild data/scope.csv from the catalogue + scope.yaml"
	@echo "make fetch      verify + download the FRED series (data/raw, manifest)"
	@echo "make harmonize  quarterly panel + label growth matrix (data/clean)"
	@echo "make labels     DFM -> BBQ -> diffusion label (outputs/labels)"
	@echo "make validate   NBER agreement report (outputs/results)"
	@echo "make pipeline   fetch + harmonize + labels + validate"
	@echo "make check      environment and configuration gate"
	@echo "make test       run the test suite"
	@echo "make team-plan  rebuild Team_Plan.xlsx (plain-English team plan)"
	@echo "make worklog    rebuild EWS_Work_Log.xlsx (detailed work log)"
	@echo "make reports    rebuild both generated workbooks"
	@echo "make dashboard  build the static USA dashboard (dashboard/index.html)"

env:
	python3 -m venv $(VENV)
	$(BIN)/python -m pip install --upgrade pip
	$(BIN)/pip install -e ".[dev]"

config:
	"$(PY)" scripts/export_spec.py

scope:
	"$(PY)" scripts/scope_catalog.py

fetch:
	"$(PY)" scripts/fetch_fred.py

harmonize:
	"$(PY)" scripts/harmonize.py

labels:
	"$(PY)" scripts/03_labels.py

validate:
	"$(PY)" scripts/04_compare_nber.py

pipeline: fetch harmonize labels validate

check:
	"$(PY)" scripts/00_env.py

test:
	"$(PY)" -m pytest

team-plan:
	"$(PY)" scripts/make_team_plan.py

worklog:
	"$(PY)" scripts/make_worklog.py

reports: team-plan worklog

dashboard:
	"$(PY)" scripts/05_dashboard.py

bootstrap: config scope check test

clean:
	rm -rf build dist *.egg-info .pytest_cache
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
