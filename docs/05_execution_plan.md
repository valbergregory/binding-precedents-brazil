# Deliverable 7 — Execution plan by phase

Single researcher, part-time. Durations are working-time estimates, not calendar promises.
Each phase ends with the gate named in `docs/07_go_no_go_criteria.md`. Nothing in a later
phase starts before the gate of the previous phase is recorded in `CLAUDE.md`.

| Phase | Goal | Main tasks | Outputs | Gate | Effort |
|-------|------|-----------|---------|------|--------|
| 0 | Feasibility (done 2026-09-05) | Source probes, samples, design, repository skeleton | `docs/00`-`07`, `config/sources.yml`, schema, tests | — | done |
| 1 | Proof of concept | One STJ theme from the strict window; download 20 publication days before and 20 after fixation; run regex + origin recovery; hand-check 200 hits; measure volumes; test STF registry channel | `scripts/04_download_integras.py` (windowed, resumable), `scripts/05_load_integras.py`, PoC notebook-free report `docs/08_poc_report.md` with measured numbers | Gate 1 | 2-3 weeks |
| 2 | Full ingestion | Download all íntegras metadata and ZIPs (2021-2026), all espelhos, atas (2023-06 onwards, party fields dropped), acervo snapshot, JN base, STF registry; load to DuckDB | Populated `documents`, `documents_raw_text`, `cases`, `precedents`, `court_year_stats` | — | 1-2 weeks (mostly background) |
| 3 | Corpus and citations | Text normalisation; regex extraction over the whole corpus; validation against espelhos `tema`; theme disambiguation (STJ vs STF); subject-based relevance screening for pre-periods; final theme selection (3-5) | `citations` table, `docs/09_precedent_selection_protocol.md`, corpus statistics | Gate 2 | 3-4 weeks |
| 4 | Annotation | Annotation manual (6 application classes + quoted lower-court conformity); stratified sample; double annotation of a subsample; Krippendorff's α; adjudication | `docs/annotation_manual.md`, `annotations` table, reliability report | Gate 3 | 4-6 weeks (annotation-heavy) |
| 5 | NLP models | TF-IDF + logistic/linear SVM; gradient boosting on TF-IDF and metadata; fine-tuned Portuguese BERT; sentence-embedding retrieval for related-without-citation documents; calibration; audit of all "departure" predictions | `classifications`, `model_runs`, model card | Gate 4 | 3-4 weeks |
| 6 | Econometrics | Diffusion curves and survival (time to first adoption by court and panel); event study around fixation; multilevel models (court, panel, subject); DiD only if a comparison group is defensible; spatial models at court level | R targets, `outputs/tables`, `outputs/figures` | Gate 5 | 3-4 weeks |
| 7 | Robustness | Placebo dates; pre-trends; alternative citation definitions; label-error corrections; exclusion of ambiguous theme numbers; sensitivity to origin-recovery channel | Robustness appendix | — | 2 weeks |
| 8 | Writing | Article in Quarto (English), methodological appendix, data availability statement, model card, data card, limitations report; CNJ notification for DataJud-derived results | `article/`, `docs/` | — | 3-4 weeks |

## Phase 1 in detail (the next step, not yet started)

1. Choose the PoC theme from `docs/02_candidate_precedents.md` (author decision).
2. Implement `scripts/04_download_integras.py --from YYYY-MM-DD --to YYYY-MM-DD --resume`
   using `bpb.manifest.download`; it lists CKAN resources once, filters by date, and skips
   files already hashed.
3. Implement `scripts/05_load_integras.py` (metadata → `documents`; ZIP members →
   `documents_raw_text`; no text modification).
4. Run `bpb.citations` and `bpb.origin` on the loaded texts; write `citations` and `cases`.
5. Download the atas for the same window; join on `numeroRegistro`; compute origin coverage.
6. Manually check 200 regex hits (precision) and 100 random documents mentioning the theme's
   subject without a regex hit (recall proxy).
7. Write `docs/08_poc_report.md` with the measured numbers and the Gate 1 verdict.

## Risks to the schedule

- Annotation is the bottleneck for a single researcher; the plan assumes about 1,500 pairs
  at 3-5 minutes each. A second annotator is needed for the reliability subsample (at least
  200 pairs); this must be arranged before Phase 4.
- Full download depends on the CKAN server's throughput; the manifest makes it resumable.
