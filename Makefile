PY ?= python3
VENV ?= .venv
BIN := $(VENV)/bin

.PHONY: help env check config scope bootstrap test clean

help:
	@echo "make env        create .venv and install the package (editable)"
	@echo "make config     regenerate config/*.yaml from spec.py"
	@echo "make scope      rebuild data/scope.csv from the catalogue + scope.yaml"
	@echo "make check      environment and configuration gate"
	@echo "make test       run the test suite"
	@echo "make bootstrap  config + scope + check + test"

env:
	$(PY) -m venv $(VENV)
	$(BIN)/python -m pip install --upgrade pip
	$(BIN)/pip install -e ".[dev]"

config:
	$(PY) scripts/export_spec.py

scope:
	$(PY) scripts/scope_catalog.py

check:
	$(PY) scripts/00_env.py

test:
	$(PY) -m pytest

bootstrap: config scope check test

clean:
	rm -rf build dist *.egg-info .pytest_cache
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
