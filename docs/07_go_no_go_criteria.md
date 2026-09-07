# Deliverable 9 — Objective continuation and abandonment criteria

Each gate is evaluated at the end of the phase named in `docs/05_execution_plan.md`. A gate
either passes, triggers the listed **reformulation**, or aborts. Thresholds were fixed in
Phase 0, before any data beyond samples were seen, and must not be revised after the fact
without recording the change and the reason in this file.

## Gate 1 — after the proof of concept (Phase 1)

| Criterion | Pass | Reformulate | Abort |
|-----------|------|-------------|-------|
| G1.1 Origin recovery rate on documents from 2023-07 onwards (atas crosswalk + text) | ≥ 85 % of citing documents assigned to a court | 70-85 %: restrict the court-level analysis to the post-2023-07 window and treat earlier documents as "origin unknown" stratum | < 70 % |
| G1.2 Origin recovery rate on documents from 2021-01 to 2023-06 (text channels only) | ≥ 60 % | 40-60 %: use origin only for descriptive RQ2 and drop court fixed effects for the early period | < 40 % and no alternative channel |
| G1.3 Regex citation precision on a 200-document manual check | ≥ 0.90 for court-attributed hits | 0.80-0.90: add dictionary rules and re-check | < 0.80 after one revision |
| G1.4 Volume for the PoC theme in the 24 months after fixation | ≥ 300 citing STJ documents | 100-300: keep the theme only as a secondary case | < 100 |
| G1.5 Pre-period relevance: documents on the same subject in the 24 months before fixation, identified by subject codes and thesis-keyword screening | ≥ 100 | 30-100: pre-period used only for survival and descriptive baselines, no event study for this theme | < 30 for every candidate |

## Gate 2 — after corpus and citation extraction (Phase 3)

| Criterion | Pass | Reformulate | Abort |
|-----------|------|-------------|-------|
| G2.1 Number of themes satisfying G1.4 and G1.5 simultaneously | ≥ 3 | 2: single-theme-pair design with heavier descriptive weight | ≤ 1 |
| G2.2 Agreement between regex `tema` hits and the structured `tema` field of the espelhos (recall on espelho records with a non-empty `tema`) | ≥ 0.90 | 0.75-0.90: revise patterns | < 0.75 |
| G2.3 Courts of origin with ≥ 30 citing documents per theme | ≥ 10 courts | 5-10: pool by region or by branch (state vs federal) | < 5 |

## Gate 3 — after annotation (Phase 4)

| Criterion | Pass | Reformulate | Abort |
|-----------|------|-------------|-------|
| G3.1 Inter-annotator reliability on the double-annotated subsample (Krippendorff's α, 6-class application scheme) | α ≥ 0.67 | 0.50-0.67: collapse to 3 classes (no relation / citation only / application with outcome) and re-measure, requiring α ≥ 0.75 | < 0.50 after collapsing |
| G3.2 Reliability of the lower-court conformity label (as quoted) | α ≥ 0.67 | below: report this label only for the manually audited subset | — |
| G3.3 Gold-standard size | ≥ 1,500 labelled (document, theme) pairs, stratified by theme, period, court branch and document type | 800-1,500: use cross-validation only, no separate test set claims | < 800 |

## Gate 4 — after NLP models (Phase 5)

| Criterion | Pass | Reformulate | Abort |
|-----------|------|-------------|-------|
| G4.1 Macro-F1 of the best model on held-out folds (6-class) | ≥ 0.75 | 0.60-0.75: use model labels only for screening; econometrics on the manually labelled and audited set | < 0.60 |
| G4.2 Calibration (expected calibration error) | ≤ 0.10 | above: report label-error-corrected estimates and widen intervals | — |
| G4.3 Every document predicted as *departure* is manually audited | 100 % | — | — |

## Gate 5 — before any causal claim (Phase 6-7)

| Criterion | Pass | Reformulate | Abort |
|-----------|------|-------------|-------|
| G5.1 Pre-trend test on the event-study coefficients for the main outcome (joint Wald test on leads, 5 % level), for each theme | not rejected | rejected for some themes: exclude them from the pooled estimate and report separately | rejected for all: report associations only, no DiD |
| G5.2 A defensible comparison group exists (same subject family, no fixation in the window) | documented and approved in `docs/03_empirical_design.md` | otherwise: interrupted time series with placebo dates, explicitly labelled as non-causal | — |
| G5.3 Placebo fixation dates (±12 months) produce no effect of comparable size | passes for the pooled estimate | fails: drop the causal language from the article |

## Global stop rules

- **Time.** If Gate 2 has not been reached within 4 calendar months of starting Phase 1,
  reduce the design to the descriptive and survival components (RQ1-RQ3) and publish that.
- **Access.** If the STJ open-data portal changes its licence away from CC-BY or removes the
  íntegras dataset, stop and re-evaluate; do not substitute scraped sources.
- **Ethics.** Any finding that the corpus contains sealed cases or that outputs could identify
  an individual judge's behaviour halts publication until the pipeline is corrected.
