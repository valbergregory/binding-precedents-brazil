# Do Binding Precedents Actually Bind?
### Measuring Judicial Compliance and Diffusion Across Brazilian Courts

**Status: Phase 0 (feasibility) complete, 2026-09-08. No empirical results exist yet.**
Nothing in this repository is a finding. The proof of concept (Phase 1) has not been executed.

## What this project is

A reproducible jurimetrics study of whether, when and how *qualified precedents* of the
Superior Tribunal de Justiça (STJ, repetitive-appeal themes) and the Supremo Tribunal
Federal (STF, general-repercussion themes) are incorporated by later judicial decisions,
distinguishing formal citation, material application, outcome conformity, reasoned
distinction, departure, and diffusion time.

## Observable universe (decided in Phase 0)

Official bulk full text of **lower-court** decisions is **not** available at scale in Brazil
(`docs/00_feasibility_report.md`). The study therefore measures the **observable
manifestation of precedent adoption in the appellate flow that reached the STJ**: the full
text of STJ terminative decisions and judgments (2021 onwards, about 650 thousand documents
per year, CC-BY), grouped by **court of origin**. Lower-court reasoning is observed only as
quoted inside STJ decisions. The article states this scope explicitly and does not claim to
measure total lower-court compliance.

## Phase 0 deliverables (`docs/`)

| # | Deliverable | File |
|---|-------------|------|
| 1 | Feasibility diagnosis | `docs/00_feasibility_report.md` |
| 2 | Matrix of real data sources (verified 2026-09-04/05) | `docs/01_source_matrix.md`, `config/sources.yml` |
| 3 | Candidate precedents (77 themes screened, shortlist proposed) | `docs/02_candidate_precedents.md`, `docs/candidates_stj_temas.csv` |
| 4 | Empirical design | `docs/03_empirical_design.md` |
| 5 | Identification risks | `docs/03_empirical_design.md`, section 6 |
| 6 | Repository architecture | `docs/04_repository_architecture.md` |
| 7 | Phased execution plan | `docs/05_execution_plan.md` |
| 8 | Storage and compute estimate | `docs/06_storage_compute_estimate.md` |
| 9 | Go / no-go criteria | `docs/07_go_no_go_criteria.md` |

Also: `docs/RUNBOOK.md` (execution order, what each step reads and writes), `docs/ETHICS.md`,
`docs/AI_POLICY_AND_REPRODUCIBILITY.md` (portfolio policy on AI use and disclosure),
`docs/data_dictionary/` (official dictionaries copied verbatim).

## Reproduce (what can run today)

Interpreter versions: Python 3.13.2 (`requirements.lock`), R 4.4.3 (`renv.lock`, auxiliary).

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.lock
pip install -e .
Copy-Item .env.example .env     # paste the public DataJud key from the wiki
python scripts/01_verify_sources.py             # probes every source, logs to logs/source_checks/
python scripts/02_download_precedent_registry.py # STJ precedent registry -> data/raw + MANIFEST.csv
python scripts/03_init_duckdb.py                # schema -> data/processed/bpb.duckdb
pytest -q                                       # 11 tests: extractors, origin, manifest, export
```

Later steps are listed in `docs/RUNBOOK.md` and are added only when they exist.

## Languages

**Python is the pipeline**: ingestion, parsing, DuckDB store, NLP, econometrics. The R layer
(`_targets.R`, `R/`, `renv.lock`) is **auxiliary**, kept for optional robustness checks
(`fixest`, `did`, `survival`); it only reads DuckDB and can be removed without affecting the
pipeline. Article: LaTeX skeleton in `article/` (prose written by the author on Overleaf;
tables, figures and numbers exported by `scripts/90_export_overleaf.py`).

## Layout

```
config/      sources.yml (verified URLs), config.yml
data/        raw (immutable + MANIFEST.csv), interim, processed (DuckDB)   [git-ignored]
docs/        Phase 0 deliverables, RUNBOOK, ETHICS, AI policy, data dictionaries
src/python/  package `bpb`: manifest, sources_check, citations, origin, export_overleaf
sql/         001_schema.sql (courts, precedents, documents, cases, citations, annotations, ...)
scripts/     numbered entry points
tests/       pytest
prompts/     versioned LLM prompts (none yet)
article/     main.tex skeleton, disclosure snippets, references.bib
outputs/     tables, figures, overleaf (generated)                          [git-ignored]
```

## Data licences and ethics

Code: MIT ([LICENSE](LICENSE)). Text, documentation and data: see [LICENSING.md](LICENSING.md).

STJ open data: CC-BY (attribution in the article). CNJ DataJud: terms of use (non-commercial;
no redistribution; CNJ notified of publications). STF and CNJ portals: their own terms.
Raw data are never committed; the manifest lets anyone re-download them. No personal data
of parties, lawyers or individual judges appear in outputs (`docs/ETHICS.md`).

## Citation and licence

Code: MIT (`LICENSE`). Cite via `CITATION.cff`. A tagged release will be archived on Zenodo
before submission.
