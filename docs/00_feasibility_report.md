# Deliverable 1 — Feasibility diagnosis

Prepared 2026-09-05, before any large download. Everything stated here was either observed
directly (HTTP probes, downloaded samples, parsed files; logs in `logs/source_checks/`,
scratch analyses reproduced in `scripts/` as they are promoted) or is explicitly labelled as an
assumption. No result about precedent compliance exists yet.

## 1. Verdict

The study is **feasible with a reformulated universe**. The original ambition, measuring how
lower courts across Brazil incorporate STJ and STF qualified precedents from the lower courts'
own decisions, is **not** feasible with official sources: no official channel delivers bulk full
text of state or federal appellate decisions, and the CNJ DataJud API deliberately excludes
decision text. What is feasible, at scale and under an open licence, is the following:

> **Observable universe.** The full text of every terminative decision and judgment
> published by the STJ in the DJe from 2021-01-04 onwards (about 2,700 documents per
> publication day, 13.2 GB compressed, CC-BY), each attributed to a court of origin, together
> with the STJ registry of qualified precedents, the curated STJ "espelhos" with structured
> theme fields, DataJud case metadata, and CNJ court-year institutional indicators.

The article must therefore say that it measures **the observable manifestation of precedent
adoption in the appellate flow that reached the STJ**, grouped by court of origin, and not
total lower-court compliance. Three consequences follow and are built into the design:

1. Selection into appeal is the first-order identification threat (section 6 of
   `docs/03_empirical_design.md`). It is addressed by design choices, not assumed away.
2. Lower-court reasoning is observed only as **quoted** inside STJ decisions (the sampled
   texts routinely transcribe the appealed ementa: "acórdão assim ementado"). That quotation
   is a legitimate, if partial, window on lower-court conformity and will be labelled
   separately from the STJ's own application.
3. STF general-repercussion themes enter only as **cited inside STJ decisions**, because no
   bulk STF decision text is available. Interestingly, STF themes are cited more often than
   STJ themes in the sampled STJ texts (see section 4), so this is a real sub-population.

## 2. What was verified and how

| Check | Method | Result |
|-------|--------|--------|
| STJ Open Data portal, 21 datasets | CKAN `package_show` API; downloads of registry CSVs, 9 daily ZIPs of íntegras (about 24 thousand texts), one espelho month, one ata day, all dictionaries | Everything works; licence CC-BY; dictionaries copied to `docs/data_dictionary/` |
| DataJud public API | Public key read from the wiki; POST queries to the STJ and TJSP indices | HTTP 200; both indices report ≥ 10,000 hits; fields confirmed; no text fields |
| BNP/Pangea | Portal, SPA config (`env.js`), official PDPJ docs and manual, blind POST to backend | Public UI; backend exists but undocumented for external use (500 on blind POST); official API is OAuth2 for courts; no export documented |
| STF | Corte Aberta, Qlik panel, theses page and its POST feed, listas RG page, `temasrg.xlsx` | Reachable only with a browser user agent (403 otherwise) and incomplete TLS chain; XLSX obtained but stale (2020); feed parameters undiscovered; no bulk decision text |
| CNJ Justiça em Números | Downloaded `23-jun-2026.zip` | 1,595 court-years × 1,314 variables, 2009-2025, with congestion, workload and staffing indicators |
| CNJ Resolution 615/2025 | Portal page | Exists (11 March 2025, in force 14 July 2025) |
| Local toolchain | Version checks | Python 3.13.2, R 4.4.3, Quarto 1.9.38, RTX 4060 8 GB, 1.3 TB free; missing packages listed in `docs/06_storage_compute_estimate.md` |

## 3. The corpus: STJ íntegras

Facts observed on the dataset (`config/sources.yml` has the exact numbers):

- Daily pairs `metadados{date}.json` + `textos{date}.zip`, 2021-01-04 to 2026-08-26.
- Metadata fields: `seqDocumento`, `dataPublicacao` (epoch ms), `tipoDocumento`
  (DECISÃO 56 %, ACÓRDÃO 44 % on the sample day), `numeroRegistro`, `processo`
  (class + number, e.g. "AREsp 2046805"), `dataRecebimento`, `dataDistribuicao`, `ministro`,
  `recurso` (internal appeal), `teor` (outcome label such as "Concedendo"), `descricaoMonocratica`,
  `assuntos` (CNJ subject codes).
- Texts: one UTF-8 file per document with `<br>` line breaks, 10.5 kB on average, up to 1.2 MB.
- **Absent**: any court-of-origin field, any CNJ unified number, any theme linkage.

Citation density (9 publication days, 24,056 documents; regex, first version):
15.4 % of documents mention a "Tema N". In documents where the context names the court,
STF themes dominate (Tema 181 cited in 508 documents, Tema 339 in 251, Tema 1234 in 94),
while the most cited STJ themes are 905 (101), 692 (64), 1076 (36) and 877 (33). Themes
fixed in 2023-2024 are cited at a much lower daily rate (single digits over nine days), which
matters for sample size (section 5 and `docs/02_candidate_precedents.md`).

## 4. Recovering the court of origin

Because the íntegras carry no origin, three channels were tested:

| Channel | Coverage observed | Reliability |
|---------|-------------------|-------------|
| Atas de distribuição (`numeroRegistro` → `numeroUnico`; the CNJ number's J.TR segment identifies the court) | All cases distributed from 2023-06-30 (1,005 daily files) | Deterministic |
| CNJ number inside the decision text | 20 % of documents on the sample day | Deterministic when present |
| Regex on the opening of the text ("Tribunal de Justiça do Estado de …", "Tribunal Regional Federal da Nª Região") | 36 % of documents within the first 4,000 characters; expected to rise on full text | Good precision expected, to be measured |
| Acervo em tramitação snapshot (`origem`, `UF`) | Pending cases on 2026-09-02 only | Deterministic |
| DataJud STJ index (`numeroProcesso` is the CNJ number) | Only reachable once the CNJ number is known | Enrichment, not recovery |

Implication: origin attribution will be near-complete for documents whose case was
distributed after mid-2023 and partial before. Gate G1.1/G1.2 in
`docs/07_go_no_go_criteria.md` sets the thresholds.

## 5. Time window constraint

The íntegras start in January 2021. A design with two years before and two years after
fixation therefore admits themes fixed between **2023-01 and 2024-08** (strict) or, accepting
18 months of pre-period, from **2022-07** (relaxed). The STJ registry has 65 repetitive themes
with a published thesis in the strict window and 77 in the relaxed one. High-volume classic
themes (905, 692, 1076) predate the corpus and can only support descriptive diffusion curves
without a pre-period. The espelhos (history back to the 2000s, but curated) offer a partial
pre-period for those.

## 6. Precedent registries

- **STJ**: complete and current (`temas.csv`, `processos.csv`, updated 2026-09-03). Note the
  data-quality facts recorded in `config/sources.yml` (empty judgment dates for cancelled
  themes; a stay-count column that is always zero).
- **STF**: registry obtainable but not through a clean channel yet. Options, in order of
  preference: (a) Qlik "Corte Aberta" export through the browser, recorded with date and
  hash; (b) Base dos Dados mirror on BigQuery (Google account); (c) the 2020 XLSX as a stale
  fallback. Decision deferred to Phase 1.

## 7. Institutional covariates

CNJ Justiça em Números gives court-year indicators for every state and federal court
(congestion rates, workload per magistrate, magistrates, pending cases, decisions) for
2009-2025. This is sufficient for RQ4/H2 at the court level. Panel-level (câmara/turma)
covariates do not exist in any official source found; panel effects will be estimated as
random effects, not explained by covariates.

## 8. One language or two?

The brief asks for R, Python and SQL and also asks whether a single language would do.
Assessment:

| Option | What it costs | What it gains |
|--------|---------------|---------------|
| **Python only** | Staggered DiD estimators (Callaway–Sant'Anna, Sun–Abraham) exist but are less mature than R's `did`/`fixest`; Bayesian multilevel via `bambi`/PyMC is fine; survival via `lifelines`; spatial via `pysal/spreg`. `targets`-style caching would be replaced by a Makefile plus explicit checkpoints | One environment, one test suite, native transformers, no cross-language contract |
| **R only** | Transformers and sentence embeddings go through `reticulate`, which is Python anyway; large-corpus parsing of 3.5 M texts is slower and more memory-hungry in R | `targets`, `fixest`, `did`, `survival`, `brms`, `modelsummary` are best in class for the econometric half |
| **Hybrid (Python for ingestion/NLP, DuckDB as the contract, R for econometrics and figures)** | Two environments to lock (`pyproject.toml`, `renv.lock`), one more thing to document | Each half uses the strongest tools; DuckDB and Parquet make the boundary explicit |

Recommendation: **hybrid, with DuckDB/Parquet as the only interface**. If the author prefers
a single language for maintainability as a solo researcher, Python-only is the viable choice
(R-only is not, because of the NLP layer). The repository is laid out so that the R layer can
be dropped without touching ingestion: everything R reads comes from DuckDB tables written
by Python. This decision should be closed at the go/no-go review after Phase 1.

## 9. Environment inventory

Verified 2026-09-04: Python 3.13.2 (pandas, scikit-learn present; `duckdb`, `pyyaml`,
`pytest` installed in Phase 0; `torch`, `transformers`, `sentence-transformers` absent);
R 4.4.3 (`renv`, `duckdb`, `fixest`, `did`, `survival`, `modelsummary`, `ggplot2`, `lme4`,
`data.table`, `quarto` present; `targets`, `here`, `qs` installed in Phase 0; `arrow`, `brms`,
`sf`, `spatialreg` absent); Quarto 1.9.38; git; no `uv`; RTX 4060 8 GB; 1.3 TB free.

## 10. Open issues carried into Phase 1

1. Measure origin recovery on full texts (not the first 4,000 characters) for one month of 2022.
2. Discover the parameters of the STF theses feed or settle on the Qlik export; record provenance.
3. Confirm that the espelhos' `tema` field is populated for non-repetitive judgments (the
   sampled month for the First Section had the key present in all 44 records; population rate
   unknown for other organs).
4. Decide the PoC theme (candidates in `docs/02_candidate_precedents.md`).
5. Decide hybrid vs Python-only (section 8).
