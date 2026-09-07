# Deliverable 6 — Repository architecture

```
binding-precedents-brazil/
├── README.md, CLAUDE.md, LICENSE, CITATION.cff, .gitignore
├── pyproject.toml            Python package `bpb` (src layout) + optional [nlp] extras
├── renv.lock, renv/          R lockfile (implicit snapshot of packages used by R code)
├── _targets.R                R pipeline DAG (skeleton; unimplemented targets fail loudly)
├── Makefile                  Orchestrates Python, SQL, R and Quarto entry points
├── config/
│   ├── sources.yml           The only list of data sources, each with verification date
│   └── config.yml            Paths, windows, rate limits (no secrets)
├── data/
│   ├── raw/                  Immutable downloads + MANIFEST.csv (url, date, sha256, size, licence, filters, version)
│   ├── interim/              Parsed/normalised Parquet, versioned by pipeline step
│   └── processed/            bpb.duckdb and analysis-ready Parquet
├── src/python/bpb/
│   ├── manifest.py           Hashed, logged, idempotent downloads
│   ├── sources_check.py      Reachability probes → logs/source_checks/
│   ├── citations.py          Regex extractors (theme, súmula, paradigm, CPC regime, distinção)
│   └── origin.py             Court-of-origin recovery (CNJ number, text regex)
├── R/
│   └── utils_db.R            DuckDB read helpers for targets
├── sql/
│   └── 001_schema.sql        Normalised schema (courts, precedents, precedent_cases, documents,
│                             documents_raw_text, documents_text, cases, citations, annotations,
│                             classifications, court_year_stats, model_runs)
├── scripts/                  Numbered entry points
│   ├── 01_verify_sources.py
│   ├── 02_download_precedent_registry.py
│   ├── 03_init_duckdb.py
│   └── run_targets.R         For RStudio Background Jobs
├── tests/                    pytest (regex, origin, manifest); R tests added with targets
├── logs/                     Run logs and source-check CSVs (git-ignored)
├── models/                   Model artefacts (git-ignored)
├── outputs/tables, outputs/figures
├── article/                  Quarto article skeleton, _quarto.yml, references.bib
└── docs/                     Phase 0 deliverables, ETHICS.md, data_dictionary/ (official dictionaries)
```

## Data flow

```
CKAN / DataJud / CNJ / STF  ──(manifest.download)──▶  data/raw  (never modified)
        │
        ▼  Python parsers (JSON, CSV, ZIP, XLSX) → Parquet in data/interim
        ▼  Python loaders → DuckDB tables (raw text and processed text kept apart)
        ▼  Python NLP: citations → `citations`; embeddings/classifiers → `classifications`
        ▼  Manual annotation (CSV exported from DuckDB, imported back) → `annotations`
        ▼  R targets: read DuckDB → panels → fixest/did/survival/lme4/brms/sf → outputs/
        ▼  Quarto article reads outputs/tables and outputs/figures only
```

Contract between languages: **only DuckDB tables and Parquet files**. R never parses raw
files; Python never produces article tables.

## Conventions

- Raw immutability: `data/raw` is write-once; a changed upstream file gets a versioned name.
- Every DuckDB table that comes from a file carries `source_file` and `source_sha256`.
- Every model output carries `model_id`, and `model_runs` stores metrics and config (the
  model card is generated from it).
- Pipeline versions are strings (`extractor_version`, `pipeline_version`) stored with the rows
  they produced, so that re-running a step never silently overwrites older evidence.
- Personal data never enter DuckDB (see `docs/ETHICS.md`).

## Where each command runs

| Purpose | Where | Command |
|---------|-------|---------|
| Quick R test | RStudio Console | `targets::tar_make(names = "precedents_registry")` |
| Quick Python test | RStudio Terminal or PowerShell | `pytest -q tests/test_citations.py` |
| Long download or NLP job | RStudio Background Jobs (Python via `system2`) or a PowerShell window | `python scripts/NN_name.py --resume` |
| Long R pipeline | RStudio Background Jobs | `scripts/run_targets.R` |
| Install, git, DB admin | Terminal | `pip install -e .[dev]`, `Rscript -e "renv::restore()"`, `python scripts/03_init_duckdb.py`, `git ...` |
| Resume after failure | any | re-run the same command; manifest and `ON CONFLICT DO NOTHING` make it idempotent |
| Incremental update | Terminal | re-run `02_...` and the future íntegras downloader; only newer CKAN resources are fetched |
