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

## 2. Proof of concept (Phase 1 — scripts written and run on 2026-09-12 for the provisional theme 1132)

| Step | Command | Reads | Writes | Time |
|---|---|---|---|---|
| 2.1 | `python scripts/04_download_integras.py --from 2022-08-01 --to 2024-08-31 --resume [--mirror DIR] [--no-mirror]` | CKAN listing (cached in `data/raw/stj_integras/package_show.json`); local mirror `../STJ-Moral-Damages-Jurimetrics/data/raw/stj_integras` (CKAN download of 2026-09-07/08, sha256 checked against its CHECKSUMS) or the network | `data/raw/stj_integras/{metadata,texts}/`, manifest rows (url = CKAN, notes = mirror or download) | ~3 min for 24 months from the mirror |
| 2.2 | `python scripts/05_load_integras.py --resume [--from --to]` | 2.1 | `documents`, `documents_raw_text`, `load_log` (reporter salted-hashed with `.secrets/salt`) | ~0.2 min per 10k docs |
| 2.3 | `python scripts/06_download_atas.py --from ... --resume` (**not written yet**: ~2.3 GB of atas for the window; needs the author's go-ahead; drops `partes`/`advogados` before writing) | CKAN | `data/interim/atas/*.parquet`, `cases` | minutes |
| 2.4 | `python scripts/07_extract_citations.py --extractor-version v1 --resume` | `documents_raw_text` | `citations`, `citations_done` | ~1 s per 2k docs |
| 2.5 | `python scripts/08_recover_origin.py --resume` | `documents_raw_text`, `cases` | `cases` (text-only channels: cnj_number_in_text, regex_trf, regex_tj; ≈60 % coverage on the 2023-08 sample), `courts` reference rows | minutes |
| 2.6 | `python scripts/09_poc_report.py --tema 1132 --subject 9582` | DuckDB, `data/raw/stj_precedentes/temas.csv` | `docs/08_poc_report.md` (counts only), `outputs/tables/poc_*.csv`, `outputs/numbers.json` | seconds |
| 2.x | `.\scriptsun_poc_chain.ps1 -Tema 1132 -Subject 9582 -From 2022-08-01 -To 2024-08-31` | runs 2.1 → 2.2 → 2.4 → 2.5 → 2.6 → 9.1 in sequence; log `logs/poc_chain.out` | | ~1 h |

Source finding (2026-09-12): text coverage of the íntegras varies by day — some days ship far fewer TXT than metadata rows
(e.g. 2023-08-02: 4,284 metadata rows, 71 texts) and the mirror matches the CKAN byte sizes, so it is a property of the
source. `documents` keeps every metadata row; analyses must condition on `documents_raw_text`.

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
