# RUNBOOK — execution order

Every step says what it reads, what it writes and how long it takes on the reference machine
(Windows 11, Python 3.13, R 4.4.3, RTX 4060 8 GB). Steps marked **[Phase 1+]** do not exist
yet; the runbook lists them so the order is fixed before they are written. Run from the
repository root. PowerShell is assumed; Git Bash works with `make`.

## 0. Environment (once)

| Step | Command | Reads | Writes | Time |
|---|---|---|---|---|
| 0.1 | `python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -e ".[dev]"` | `pyproject.toml` | `.venv/` | 2 min |
| 0.2 (NLP, Phase 5) | `pip install -e ".[nlp]"` | | torch + transformers | 10 min |
| 0.3 (auxiliary R layer) | `Rscript -e "renv::restore()"` | `renv.lock` | `renv/library` | 5-15 min |
| 0.4 | copy `.env.example` to `.env`, paste the public DataJud key from the wiki | | `.env` (git-ignored) | 1 min |
| 0.5 | `pip freeze > requirements.lock` after any dependency change | | `requirements.lock`, `logs/pip_freeze_<date>.txt` | seconds |

## 1. Verification and registry (Phase 0, runnable now)

| Step | Command | Reads | Writes | Time |
|---|---|---|---|---|
| 1.1 | `python scripts/01_verify_sources.py` | `config/sources.yml`, `DATAJUD_API_KEY` | `logs/source_checks/<stamp>.csv` | 1-2 min |
| 1.2 | `python scripts/02_download_precedent_registry.py` | `config/sources.yml` | `data/raw/stj_precedentes/*.csv`, rows in `data/raw/MANIFEST.csv` | 10 s |
| 1.3 | `python scripts/03_init_duckdb.py` | `sql/*.sql` | `data/processed/bpb.duckdb` (empty tables) | 1 s |
| 1.4 | `pytest -q` | `tests/` | console | 1 s |

## 2. Proof of concept **[Phase 1+]**

| Step | Command | Reads | Writes | Time |
|---|---|---|---|---|
| 2.1 | `python scripts/04_download_integras.py --from 2022-08-01 --to 2024-08-31 --resume` (window set by the PoC theme) | CKAN listing | `data/raw/stj_integras/{metadados,textos}*`, manifest rows | minutes per month of data |
| 2.2 | `python scripts/05_load_integras.py --resume` | 2.1 | `documents`, `documents_raw_text` | ~1 min per month |
| 2.3 | `python scripts/06_download_atas.py --from ... --resume` (drops `partes`/`advogados` before writing) | CKAN | `data/interim/atas/*.parquet`, `cases` | minutes |
| 2.4 | `python scripts/07_extract_citations.py --extractor-version v1` | `documents_raw_text` | `citations` | seconds per 10k docs |
| 2.5 | `python scripts/08_recover_origin.py` | `documents_raw_text`, `cases` | `cases.origin_*` | seconds |
| 2.6 | `python scripts/09_poc_report.py --tema <N>` | DuckDB | `docs/08_poc_report.md`, `outputs/tables/poc_*.csv` | seconds |

## 3. Full ingestion, corpus, annotation, models, econometrics **[Phase 2-7]**

Numbered scripts 10-49 (Python) and `targets` (auxiliary R) will be added phase by phase; each
one gets a row here when it exists, never before.

## 9. Export to Overleaf (any phase)

| Step | Command | Reads | Writes | Time |
|---|---|---|---|---|
| 9.1 | `python scripts/90_export_overleaf.py` | `outputs/tables/*.csv`, `outputs/figures/*.{pdf,png}`, `outputs/numbers.json` | `outputs/overleaf/tables/*.tex` (booktabs), `outputs/overleaf/figures/`, `outputs/overleaf/numbers.tex` | seconds |
| 9.2 | `make article` (or `latexmk -pdf -cd article/main.tex`) | `article/`, `outputs/overleaf/` | `article/main.pdf` | seconds |

Upload to Overleaf: the `article/` folder plus `outputs/overleaf/`. The author writes the prose
on Overleaf and syncs `article/` back to the repository.

## Resume rules

- Downloads: re-run the same command; the manifest skips files already hashed.
- Loads: re-run; `ON CONFLICT DO NOTHING` on the source identifier.
- Long jobs: RStudio Background Jobs or a second PowerShell window; logs in `logs/`.
