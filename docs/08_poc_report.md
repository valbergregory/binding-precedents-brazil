# 08 — Proof-of-concept report: STJ Tema 1132

Generated 2026-09-12 16:23 by `scripts/09_poc_report.py --tema 1132` (extractor `v1`). **Theme choice is provisional**: Tema 1132 is the primary candidate proposed in docs/02_candidate_precedents.md; the author has not yet confirmed it. Re-run with another `--tema` after the choice.

Registry (data/raw/stj_precedentes/temas.csv): first affetação 2022-03-31, judgment **2023-08-09**, acórdão published 2023-10-20, status Trânsito em Julgado, organ S2.
Pre/post split at the judgment date (2023-08-09). Subject codes (registry): 9582- Alienação Fiduciária, 899- DIREITO CIVIL, 7681- Obrigações, 9580- Espécies de Contratos

## 1. Corpus loaded (steps 2.1–2.2)

- Documents: **1,221,887** (1,139,818 with text; 893,433 distinct cases) published 2022-08-01 → 2024-08-30.
| document_type | documents |
|---|---|
| DECISAO | 952847 |
| ACORDAO | 269040 |

## 2. Documents citing Tema 1132 (step 2.4, regex `bpb.citations`)

- Documents with ≥1 mention: **790** (291 with explicit STJ attribution; 1873 mentions in total). Bare mentions (“Tema 1132” without court) can refer to the STF theme of the same number — treat as ambiguous until annotated.

### Pre/post the judgment date

| period | documents | citing_stj | citing_any |
|---|---|---|---|
| pre | 577123 | 52 | 153 |
| post | 644764 | 239 | 637 |

### Monthly series

| month | documents_total | citing_stj_attributed | citing_bare | citing_stf_attributed |
|---|---|---|---|---|
| 2022-08 | 76395 | 5 | 15 | 0 |
| 2022-09 | 53011 | 5 | 7 | 1 |
| 2022-10 | 47852 | 3 | 7 | 1 |
| 2022-11 | 50579 | 14 | 7 | 0 |
| 2022-12 | 36854 | 0 | 3 | 0 |
| 2023-01 | 5985 | 0 | 4 | 0 |
| 2023-02 | 47987 | 5 | 5 | 0 |
| 2023-03 | 61500 | 15 | 10 | 1 |
| 2023-04 | 44158 | 0 | 9 | 0 |
| 2023-05 | 60953 | 3 | 10 | 0 |
| 2023-06 | 60442 | 1 | 25 | 0 |
| 2023-07 | 16769 | 0 | 4 | 0 |
| 2023-08 | 62683 | 14 | 38 | 0 |
| 2023-09 | 50525 | 12 | 24 | 0 |
| 2023-10 | 49993 | 20 | 93 | 0 |
| 2023-11 | 47999 | 36 | 83 | 0 |
| 2023-12 | 40484 | 20 | 60 | 0 |
| 2024-01 | 4769 | 0 | 2 | 0 |
| 2024-02 | 57781 | 24 | 65 | 0 |
| 2024-03 | 52986 | 21 | 54 | 0 |
| 2024-04 | 62013 | 24 | 58 | 0 |
| 2024-05 | 63379 | 29 | 56 | 0 |
| 2024-06 | 62317 | 19 | 35 | 0 |
| 2024-07 | 29981 | 1 | 7 | 0 |
| 2024-08 | 74492 | 20 | 35 | 0 |

## 3. Recall proxy: documents whose CNJ subject codes include 9582

Share of subject-matched documents that cite the theme (a low share after fixation is either non-citation or regex miss — the manual check of step 6 in docs/05 decides).

| period | subject_documents | citing_theme | pct |
|---|---|---|---|
| pre | 4717 | 142 | 3.0 |
| post | 5395 | 537 | 10.0 |

## 4. Court of origin (step 2.5, text-only channels; atas not loaded yet)

All cases in the corpus:

| channel | cases | pct |
|---|---|---|
| none | 436490 | 51.8 |
| regex_tj | 187439 | 22.2 |
| cnj_number_in_text | 175479 | 20.8 |
| regex_trf | 43926 | 5.2 |

Cases citing Tema 1132:

| channel | citing_cases |
|---|---|
| regex_tj | 364 |
| none | 276 |
| cnj_number_in_text | 97 |

By origin court and period (cells with k ≥ 5 only):

| court | period | citing_cases |
|---|---|---|
| TJRS | post | 135 |
| TJRS | pre | 57 |
| TJSP | post | 45 |
| TJRJ | post | 39 |
| TJGO | post | 35 |
| TJBA | post | 22 |
| TJSC | post | 19 |
| TJMG | post | 17 |
| TJDF | post | 17 |
| TJMT | post | 13 |
| TJPR | post | 12 |
| TJCE | post | 10 |
| TJSP | pre | 5 |
| TJMA | post | 5 |

## 5. Other regex signals in the corpus

| ref_type | mentions | documents |
|---|---|---|
| sumula | 4579327 | 818058 |
| paradigma | 4239625 | 687309 |
| cpc_regime | 948936 | 361143 |
| tema | 565578 | 158829 |

## 6. Gate 1

Criteria in docs/07_go_no_go_criteria.md. Numbers above are measured; the verdict and the manual checks (200 regex hits for precision, 100 subject-matched non-hits for recall) are the author's — `% AUTHOR DECIDES`.

Reproduce: `python scripts/04_download_integras.py --from 2022-08-01 --to 2024-08-31` → `05_load_integras.py` → `07_extract_citations.py` → `08_recover_origin.py` → `09_poc_report.py --tema 1132 --subject 9582`.