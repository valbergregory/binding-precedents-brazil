# Orchestrates Python (pipeline), SQL (DuckDB), the auxiliary R layer and the LaTeX article.
# Run from Git Bash (`make <target>`); PowerShell users can call the scripts directly
# (see docs/RUNBOOK.md).
PY ?= .venv/Scripts/python.exe
RSCRIPT ?= "C:/Program Files/R/R-4.4.3/bin/Rscript.exe"

.PHONY: help env check-sources registry db-init test overleaf article targets clean-logs

help:
	@echo "env            create .venv and install the package (dev extras)"
	@echo "check-sources  verify every URL in config/sources.yml (logs/source_checks/)"
	@echo "registry       download STJ precedent registry CSVs into data/raw with manifest rows"
	@echo "db-init        create data/processed/bpb.duckdb from sql/*.sql"
	@echo "test           run pytest"
	@echo "overleaf       export outputs/ to outputs/overleaf/ (tables, figures, numbers.tex)"
	@echo "article        compile article/main.tex with latexmk (skeleton; prose by the author)"
	@echo "targets        run the auxiliary R targets pipeline (skeleton)"

env:
	python -m venv .venv && $(PY) -m pip install -q --upgrade pip && $(PY) -m pip install -e ".[dev]"

check-sources:
	$(PY) scripts/01_verify_sources.py

registry:
	$(PY) scripts/02_download_precedent_registry.py

db-init:
	$(PY) scripts/03_init_duckdb.py

test:
	$(PY) -m pytest -q

overleaf:
	$(PY) scripts/90_export_overleaf.py

article: overleaf
	latexmk -pdf -interaction=nonstopmode -cd article/main.tex

targets:
	$(RSCRIPT) scripts/run_targets.R

clean-logs:
	find logs -type f ! -name .gitkeep -delete
