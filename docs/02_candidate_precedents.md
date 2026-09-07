# Deliverable 3 — Candidate precedents

Status: **candidates only**. No theme has been selected. Selection happens after the
proof of concept (Phase 1) measures real volumes; see Gate 1 in `docs/07_go_no_go_criteria.md`.

## 1. How the list was built

1. Source: STJ registry `temas.csv` (2026-09-03 version, `data/raw/stj_precedentes/`),
   type `Tema` (repetitive themes), status "Trânsito em Julgado" or "Acórdão Publicado",
   thesis text of at least 80 characters, judgment date between **2022-07-01 and 2024-08-31**
   (relaxed window: at least 18 months of pre-period inside the íntegras coverage that starts
   in January 2021, and 24 months of post-period before August 2026). The strict window
   (2023-01-01 to 2024-08-31) gives two full years on both sides.
   Result: **77 themes** (65 in the strict window). Full list with theses:
   `docs/candidates_stj_temas.csv`.
2. Origin of the paradigm cases and branch (state or federal) from `processos.csv`.
3. A **rough citation proxy**: regex counts of "Tema N" in 24,056 STJ decisions from nine
   publication days (2023-05-10; 2024-02-06, 05-14, 08-13, 11-05; 2025-02-11, 05-13, 08-12,
   11-04). "STJ ctx" counts only hits whose context names the STJ or the repetitive regime;
   "any ctx" counts every "Tema N" string, which for numbers that also exist as STF themes
   (1199, 1170 and others) includes STF citations. **Nine days are a screening device, not a
   sample size estimate.** A theme cited once in nine days may still yield a few hundred
   documents over two years; the PoC measures this properly.

## 2. Screening table (top 20 of 77 by the citation proxy)

| Tema | Organ | Subject (registry) | Judgment | Origin of paradigms | Thesis chars | STF RG link | Cites, STJ ctx (9 days) | Cites, any ctx (9 days) | Strict window |
|---|---|---|---|---|---|---|---|---|---|
| 1218 | S3 | Contrabando ou descaminho | 2024-02-28 | TRF3 | 575 |  | 9 | 9 | True |
| 1139 | S3 | Direito Penal | 2022-08-10 | TJPR | 127 |  | 3 | 16 | False |
| 1105 | S1 | Auxílio-Acidente (Art. 86) | 2023-03-07 | TJSP | 178 |  | 3 | 7 | True |
| 1182 | S1 | IRPJ/Imposto de Renda de Pessoa Jurídica | 2023-04-26 | TRF4 | 1374 | 843 | 3 | 4 | True |
| 769 | S1 | Dívida Ativa (Execução Fiscal) | 2024-04-18 | TJSP,TRF3 | 1360 |  | 3 | 3 | True |
| 1150 | S1 | Atualização de Conta | 2023-09-13 | TJDFT,TJTO | 706 |  | 2 | 7 | True |
| 1059 | CE | Aposentadoria Especial (Art. 57/8) | 2023-11-09 | TRF4 | 407 |  | 2 | 4 | True |
| 1079 | S1 | Contribuições para o SEBRAE | 2024-03-13 | TRF4,TRF5 | 1004 |  | 2 | 4 | True |
| 1115 | S1 | Aposentadoria Rural (Art. 48/51) | 2022-11-23 | TRF4 | 193 | 1362 | 2 | 2 | False |
| 1190 | S1 | Adicional por Tempo de Serviço | 2024-06-20 | TJSP | 252 |  | 2 | 2 | True |
| 1199 | S1 | Taxa de Ocupação / Laudêmio / Foro | 2023-09-13 | TRF1 | 437 | 1201 | 1 | 43 | True |
| 1132 | S2 | Direito Civil | 2023-08-09 | TJRS | 363 |  | 1 | 4 | True |
| 1143 | S3 | Direito Penal | 2023-09-13 | TRF3 | 403 |  | 1 | 3 | True |
| 1069 | S2 | Planos de saúde | 2023-09-13 | TJSPCF | 766 |  | 1 | 2 | True |
| 1095 | S2 | Promessa de Compra e Venda | 2022-10-25 | TJSPCF | 380 |  | 1 | 2 | False |
| 1125 | S1 | Cofins | 2023-12-13 | TRF3,TRF4 | 161 | 1365 | 1 | 2 | True |
| 1237 | S1 | IRPJ/Imposto de Renda de Pessoa Jurídica | 2024-06-20 | TRF2,TRF4 | 494 | 1314 | 1 | 2 | True |
| 986 | S1 | ICMS/ Imposto sobre Circulação de Mercad | 2024-03-13 | TJMT,TJRS,TJSP,TJTO | 321 | 956 | 1 | 1 | True |
| 1155 | S3 | Direito Penal | 2022-11-23 | TJSC | 818 |  | 1 | 1 | False |
| 1176 | S1 | Certificado de Regularidade - FGTS | 2024-05-22 | TRF3,TRF5 | 577 |  | 1 | 1 | True |

"Subject (registry)" is the first CNJ subject label in the registry and is sometimes narrower
than the theme (Tema 1059, for instance, is about attorney fees on appeal, filed under a
social-security subject because of its paradigm case).

## 3. Assessment of the strongest candidates against the selection criteria

Criteria from the brief: identifiable fixation date; enough later decisions; text-searchable;
reasonably objective legal delimitation; decisions from several courts; two years before and
after. The thesis summaries below are paraphrases of the registry text for orientation only;
the literal theses are in the CSV.

| Tema | What it decides (paraphrase) | Courts of origin expected in the STJ flow | Objectivity of the rule | Fit |
|---|---|---|---|---|
| **1132** (S2, 2023-08-09) | In fiduciary-alienation repossession suits, proof of default requires only sending the extrajudicial notice to the contractual address; proof of receipt is not needed | All 27 state courts (bank/consumer litigation) | High: a binary procedural requirement | **Strong PoC candidate**: broad spatial coverage, simple rule, clear pre/post |
| **1059** (CE, 2023-11-09) | Fee increase on appeal (CPC art. 85 §11) applies only when the appeal is wholly denied or not admitted | Every court and every subject (transversal) | High: mechanical | Strong contrast case for H4 (clarity); very high expected volume; risk of trivial "application" |
| **1105** (S1, 2023-03-07) | Súmula 111/STJ on attorney fees in social-security suits remains applicable under CPC/2015 | TRFs and state courts under delegated federal jurisdiction | High | Strong: mixed federal/state origins allow branch comparison |
| **1218** (S3, 2024-02-28) | Repeat offending bars the insignificance principle in *descaminho*, with a case-by-case safety valve | Federal courts only (TRF1-TRF6) | Medium: contains a discretionary clause ("socially recommendable") | Good for the "distinção" category; limited spatial variation (6 units); the highest proxy count |
| **1182** (S1, 2023-04-26) | ICMS tax benefits cannot be excluded from the IRPJ/CSLL base unless statutory requirements are met | Federal courts only | Medium-low: long thesis, conditional rules, linked to STF RG 843 | Good for H4 as a "complex thesis" case; federal only |
| **769** (S1, 2024-04-18) | Rules for garnishment of business revenue in tax executions (no exhaustion requirement; order of preference; percentage) | State and federal courts | Medium: three-part thesis | Reasonable; short post-period (fixation April 2024) |
| **1150** (S1, 2023-09-13) | Banco do Brasil is a proper defendant in PASEP-account suits; ten-year limitation | State courts (many) | High | Reasonable; volume unknown |
| 1199 (S1, 2023-09-13) | Validity of edict-only notification in marine-land demarcation for a 2007-2011 window | Federal courts | High but narrow | **Ambiguous number**: 43 "any ctx" hits are mostly STF Tema 1199; exclude unless disambiguation is verified |

## 4. What is deliberately excluded from the strict design

- Classic high-volume themes fixed before 2021 (905, 692, 1076, 877): no pre-period in the
  íntegras. They will be used for **descriptive diffusion curves** and as a robustness set
  (`docs/03_empirical_design.md`, section 7), never for the event study.
- Themes fixed after 2024-08 (61 in 2025 alone): post-period too short. They form a natural
  **out-of-sample set** for the diffusion model at the end of the project.
- STF general-repercussion themes: the registry channel is not settled (`docs/00`, section 6).
  STF themes appear as **cited inside STJ decisions** (181, 339, 1234, 280, 810 dominate the
  sample) and will be treated as a secondary population once the registry is loaded with
  provenance. No STF candidate is listed here because no verified fixation dates are loaded.

## 5. Proposed shortlist for the proof of concept (author's decision pending)

Primary PoC theme: **1132**. Secondary, to be added if the PoC passes Gate 1: **1059**, **1105**,
**1218**, **1182**, giving two state-court-wide rules (one simple, one transversal), one mixed
branch rule and two federal-only rules of contrasting complexity. Final selection of the
3-5 themes follows the protocol in `docs/09_precedent_selection_protocol.md` (Phase 3).
