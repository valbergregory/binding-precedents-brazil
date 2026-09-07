# Deliverables 4 and 5 — Empirical design and identification risks

## 1. Units, universe and time

- **Precedent** *p*: an STJ repetitive theme with a fixation date *T_p* (judgment date of the
  paradigm; publication date used in robustness). STF themes enter as cited precedents once
  their registry is loaded with provenance.
- **Document** *d*: one STJ terminative decision or judgment published in the DJe
  (`documents`), with text, publication date, document type (monocratic or collegiate),
  organ, internal appeal, outcome label (`teor`), CNJ subject codes.
- **Case** *c*: the STJ case the document belongs to, with court of origin *j(c)*, branch,
  UF, class, filing dates; from atas, acervo snapshot, text and DataJud.
- **Court of origin** *j*: 27 state courts and 6 federal regional courts (33 units); panels
  (câmaras/turmas of the origin) only where the quoted ementa identifies them.
- **Calendar**: monthly event time *k = month(d) − month(T_p)*, from −24 to +24.

Everything is measured in the STJ flow. Formally, the outcome for court *j* is
*Y_{jpk}* = a property of the STJ documents from origin *j* that engage precedent *p* in
month *k*. The article states this in its first data paragraph.

## 2. Six measurement categories and how each is operationalised

| Category (brief) | Level | Operational definition | Instrument |
|---|---|---|---|
| 1. Formal citation | document × precedent | Text contains a reference to *p* (theme number with STJ context, paradigm appeal number, thesis quotation) | `bpb.citations` regex + dictionary of variants; validated against espelhos `tema` |
| 2. Material application | document × precedent | The reasoning relies on the thesis of *p* to decide the point, with or without citation | Supervised classifier; embeddings for related-without-citation candidates; gold standard |
| 3. Outcome conformity | document × precedent | The disposition is consistent with the thesis (e.g. appeal decided the way the thesis prescribes) | Classifier + `teor` field + manual audit |
| 4. Reasoned distinction | document × precedent | The document explicitly distinguishes the case from *p* (distinguishing) | Classifier; regex `distinção` as feature; manual audit of all positives |
| 5. Departure / possible non-compliance | document × precedent | The document decides contrary to *p* without distinction, or the **quoted lower-court reasoning** contradicts *p* after *T_p* | Classifier; **100 % manual audit**; reported as rates with intervals, never per judge |
| 6. Diffusion time | court × precedent | Months from *T_p* to the first document from origin *j* with category 2 or 3; also to the first citation (category 1) | Survival analysis |

The **quoted lower-court reasoning** (the appealed ementa transcribed in the STJ text) gets its
own label (`lower_court_conformity`: conform / nonconform / unclear / not quoted), which is the
closest observable to lower-court behaviour available under the reformulated universe.

## 3. Annotation and models

- Annotation manual (Phase 4) with decision rules, examples and edge cases; stratified sample
  by theme, period (before/after), branch, document type; double annotation of at least 200
  pairs; Krippendorff's α (ordinal-agnostic, handles missing) as the primary reliability
  statistic, Cohen's κ reported for the two-annotator subsample.
- Model comparison on the same folds: TF-IDF + logistic regression / linear SVM; gradient
  boosting (LightGBM or scikit-learn HistGradientBoosting) on TF-IDF SVD + metadata;
  fine-tuned Portuguese BERT (BERTimbau-base or a legal-domain variant); sentence-embedding
  nearest-neighbour retrieval to surface related documents without explicit citation.
  Metrics: macro-F1, per-class F1, calibration (ECE), and precision/recall of the departure
  class. Any local LLM used as a labeller is a measurement instrument with versioned prompts,
  temperature 0, fixed seed and the same validation (see `docs/AI_POLICY_AND_REPRODUCIBILITY.md`,
  section 5.3).
- The econometric stage uses (a) the manually labelled set, (b) model labels with
  label-error correction (misclassification-adjusted estimators or bounds), and reports both.

## 4. Models by research question

| RQ | Quantity | Model | Notes |
|---|---|---|---|
| RQ1 diffusion time | Time to first citation and to first material application, by court × precedent | Kaplan–Meier curves; Cox proportional hazards with precedent strata and court covariates; discrete-time hazard (monthly logit) as a check | Right-censoring at 2026-08; left-truncation is not an issue because *T_p* is inside the corpus |
| RQ2 heterogeneity | Citation and application rates by court, region, STJ organ, subject | Multilevel logistic model: document-level outcome ~ event-time spline + document type + random intercepts for origin court, STJ organ and subject family; random slopes on event time by court | Variance components quantify heterogeneity; posterior/shrunken court effects are what gets mapped |
| RQ2 spatial | Court-level adoption speed on the map | Moran's I on court-level adoption lags with contiguity weights; spatial lag or error model only if the test rejects and N (27 TJs) is judged sufficient; otherwise descriptive maps | Small N is the binding constraint, stated as such |
| RQ3 citation vs conformity | P(conformity ∣ citation) vs P(conformity ∣ no citation) | Cross-tabulation with intervals; multilevel logit of conformity on citation with court and precedent effects | **Association**, not causation: citation is not randomised |
| RQ4 institutional determinants | Adoption lag and application rate on JN covariates (congestion, workload per judge, size) | Court-level regressions and the multilevel model with court-year covariates; year fixed effects | Association; 33 units, few degrees of freedom; report with caution |
| RQ5 effects of fixation | Dispersion of outcomes in the subject (share of STJ reversals of the lower court on the point; entropy of `teor`), duration (filing → STJ decision, DataJud), appeal volume on the subject | Event study around *T_p* with precedent × month effects; **DiD only if** a comparison subject family without fixation in the window is documented and pre-trends hold (Gate 5); otherwise interrupted time series with placebo dates and explicit non-causal language | See section 6 |

Terminology discipline in the article: *association* (RQ2-RQ4), *prediction* (NLP models,
out-of-sample themes fixed after 2024-08), *causal effect* only for RQ5 and only if Gate 5 passes.

## 5. Hypotheses mapped to tests

| H | Test |
|---|---|
| H1 material adoption slower than formal citation | Survival curves for category 1 vs category 2 within the same court × precedent; paired comparison of medians |
| H2 congestion slows incorporation | Cox/multilevel coefficient on JN congestion rate (`tc`, `tc2`) and workload (`k`) |
| H3 spatial heterogeneity | Variance component of court random effects; Moran's I; map |
| H4 clearer, less complex theses diffuse faster | Precedent-level covariates: thesis length, number of conditional clauses, number of legal references, presence of open-textured terms (coded by the author); Cox with precedent covariates; needs ≥ 5 themes to say anything, so mostly descriptive |
| H5 fixation reduces heterogeneity of outcomes but not short-run appeal volume | Event study on dispersion and on appeal volume, separately |

## 6. Identification risks (deliverable 5)

| # | Risk | Why it matters here | Mitigation built into the design |
|---|---|---|---|
| R1 | **Selection into appeal.** Only contested cases reach the STJ; compliant lower courts generate fewer appeals | The measured "non-conformity" is conditional on appeal; rates are not population rates | State the conditional nature; use within-court changes over event time (each court is its own control); complement with DataJud counts of new cases on the subject at origin to model the appeal-generating process |
| R2 | **Composition shift after fixation.** Under CPC arts. 1,030 and 1,040 the origin court must apply the thesis and deny admission of contrary appeals; what reaches the STJ after *T_p* is a different mix (more AREsp against inadmissibility) | A drop in "departure" after *T_p* may reflect filtering, not compliance | Model by class and internal appeal (`recurso`), stratify by AREsp vs REsp; report results separately for documents that quote the lower-court ementa |
| R3 | **Backlog release.** Cases stayed at origin and at the STJ during the affetação are decided in a burst after *T_p* | Mechanical spike in "applications" right after fixation inflates early diffusion | Use `dataRecebimento`/`dataDistribuicao` and DataJud filing dates to separate cases filed before affetação (backlog) from cases filed after; diffusion curves reported for both |
| R4 | **Anticipation.** The affetação date precedes *T_p* by months to years; courts may align with the expected thesis | Pre-period contaminated; pre-trends bend upward | Use `dataPrimeiraAfetacao` as a second event; exclude the affetação–fixation interval in a robustness run |
| R5 | **Origin recovery differs by period** (deterministic from mid-2023, regex before) | Court-level analysis before 2023-07 is noisier and possibly selected on text form | Report coverage by month; run court-level models on post-2023-07 documents only as a check; treat "unknown origin" as a stratum |
| R6 | **Theme-number ambiguity** (STJ vs STF share numbers; súmula vs theme) | False citations | Court-attributed hits only in the main analysis; ambiguous hits excluded and counted |
| R7 | **Label noise** from automatic classification | Attenuation and bias in rates | Gold standard, calibration, misclassification-corrected estimates, 100 % audit of departures |
| R8 | **Monocratic vs collegiate** documents differ in length and structure; monocratic decisions dominate (56 %) | Application may be terse in monocratic decisions | Document type as covariate and stratum; separate reliability statistics by type |
| R9 | **Duplicate engagements** (embargos, agravos internos on the same case) | Over-counting | Cluster at case level; primary analysis at first engagement per case × precedent |
| R10 | **Censoring for late themes** (2024 fixations) | Shorter follow-up | Survival methods handle it; event-study windows truncated and shown |
| R11 | **Small court N** for spatial and institutional models (33 units) | Low power, fragile inference | Report as descriptive/association; use shrinkage estimates; no strong causal wording |
| R12 | **No lower-court text** | Cannot observe compliance in cases never appealed | Stated scope limitation in the title's framing and in the first paragraph of Data; the quoted-ementa label is the partial substitute |
| R13 | **Comparison group for DiD** may not exist (every subject family eventually gets a theme) | Parallel trends unverifiable | Gate 5; fallback to ITS with placebo dates and explicit non-causal language |

## 7. Robustness plan

Placebo fixation dates (±12 months); alternative citation definitions (number only vs number +
paradigm vs thesis quotation); exclusion of ambiguous theme numbers; models on manual labels
only; origin from atas only; publication vs judgment date as *T_p*; exclusion of the
affetação interval; descriptive replication on the classic themes (905, 692, 1076) without
pre-period; out-of-sample diffusion prediction on themes fixed after 2024-08.
