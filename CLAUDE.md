# CLAUDE.md — working rules for this repository

Project: "Do Binding Precedents Actually Bind? Measuring Judicial Compliance and Diffusion
Across Brazilian Courts". Single researcher (PhD Economics, law degree, IS professor).
Conversation language: Portuguese (pt-BR). Repository, code comments and article: English.
Portfolio-wide policy: `docs/AI_POLICY_AND_REPRODUCIBILITY.md` (binding for this repository).

## Non-negotiable rules
1. Never fabricate data, APIs, results, references or access possibilities. If a source was
   not verified in this repository (`logs/source_checks/`), say so.
2. Never report a step as done unless it actually ran and its output exists on disk.
3. Never modify anything under `data/raw/`. Every download is recorded in
   `data/raw/MANIFEST.csv` (url, date, sha256, size, license, filters, version) by
   `src/python/bpb/manifest.py`. Re-downloads append manifest rows, never overwrite.
4. Personal data: drop `partes` and `advogados` at ingestion (STJ atas de distribuição).
   Never print party or lawyer names in outputs, logs or commits. Hash identifiers when needed.
5. Never classify individual judges as non-compliant. Court level and panel level only.
6. Automatic classifications are probabilistic evidence; divergent cases get manual audit.
7. No CAPTCHA or authentication circumvention. Public endpoints only, polite rate limits
   (DataJud: at most 1 request per second, user agent identifies the project).
8. Git: commit and push only when the user asks. Never skip hooks. Secrets are never committed
   (`.env` is git-ignored); the DataJud public key is read from `DATAJUD_API_KEY`.

## AI use and article prose
- Claude Code writes code, tests, SQL, configuration, runbooks and repository documentation
  (`docs/`). It **never writes the article's prose**: `article/` holds only the LaTeX skeleton
  (`main.tex` with `\input` lines, headings, `% AUTHOR WRITES` markers, the two disclosure
  snippets, `references.bib`). The author writes on Overleaf and syncs `article/` back.
- Every number, table and figure that reaches the article is produced by a script and exported
  by `scripts/90_export_overleaf.py` to `outputs/overleaf/` (`tables/*.tex` booktabs,
  `figures/*.pdf|png`, `numbers.tex` with one `\newcommand` per quoted number). Nothing is typed by hand.
- Any classifier or LLM that labels "application / distinction / departure" is a **measurement
  instrument**: model name and version or hash, prompt file under `prompts/vNN/`, temperature 0,
  seed, date, and validation metrics against the author-annotated gold set (precision, recall,
  F1; α/κ with a second annotator) are stored in `model_runs` and reported in Methods
  (template: policy section 5.3). Only local models (Ollama `llama3.1:8b`, `qwen2.5:7b`) unless
  the author authorises a paid API in writing.
- `references.bib` receives only entries the author has read and verified.

## Languages
- **Python is the pipeline** (ingestion, parsing, DuckDB, NLP, econometrics via statsmodels /
  lifelines / bambi-PyMC when reached), per the author's decision of 2026-09-04 for this article.
- The R layer (`_targets.R`, `R/`, `renv.lock`) is **auxiliary**: kept because the original brief
  requested it, usable for robustness checks with `fixest`/`did`/`survival`; it reads DuckDB only
  and can be removed without touching the pipeline. Final confirmation still pending from the author.

## Where things live
- `config/sources.yml` is the only list of sources; every URL there carries its verification date.
- `docs/` holds the Phase 0 deliverables, `docs/RUNBOOK.md` (execution order), `docs/ETHICS.md`,
  `docs/data_dictionary/` (official dictionaries copied verbatim).
- `src/python/bpb/` is the Python package. `sql/` holds the DuckDB schema as numbered migrations.
- `scripts/` holds numbered entry points (01-09 Phase 0/1; 10-49 later phases; 90 export).
- `logs/` holds run logs, source checks and `pip_freeze_<date>.txt` (git-ignored except `.gitkeep`).

## Command conventions
- Quick tests: `pytest -q tests/test_<x>.py`; R console: `targets::tar_make(names = <one target>)`.
- Long jobs: `python scripts/<nn>_<name>.py --resume` in a second PowerShell window or an RStudio
  Background Job; idempotent, skips files already in the manifest.
- Terminal only: `pip install -e .[dev]`, `Rscript -e "renv::restore()"`, `git`, `python scripts/03_init_duckdb.py`.
- Safe resume: every downloader is idempotent by (url, sha256); every DuckDB load uses
  `INSERT ... ON CONFLICT DO NOTHING` keyed on the source identifier.
- Incremental update: downloaders only fetch CKAN resources whose `last_modified` is newer than
  the newest manifest row for that resource.

## Current state (keep updated)
- 2026-09-08: Phase 0 complete (docs/00-07, ETHICS, RUNBOOK, sources.yml probed, schema applied,
  extractors with tests, manifest with the STJ registry, requirements.lock, renv.lock, LaTeX
  skeleton, Overleaf exporter). Repository public on GitHub.
- Pending author decisions: (1) confirm Python-only (R layer removal); (2) PoC theme
  (proposal: Tema 1132, see docs/02). Phase 1 (proof of concept) NOT started.
