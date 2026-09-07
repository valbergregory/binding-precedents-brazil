# Deliverable 8 — Storage and compute estimate

Machine inventory (verified 2026-09-04): Windows 11, Python 3.13.2, R 4.4.3, Quarto 1.9.38,
NVIDIA RTX 4060 Laptop (8 GB VRAM), 1.3 TB free on drive D. Missing and to be installed in
Phase 1: Python `torch`, `sentence-transformers`, `transformers`; R `arrow`, `brms`, `sf`,
`spatialreg` (`targets`, `here`, `qs` were installed during Phase 0 for the skeleton).

## Storage

Figures marked *observed* come from the CKAN API or from downloaded samples; the rest are
extrapolations and are labelled as such.

| Item | Basis | Estimate |
|------|-------|----------|
| STJ íntegras, compressed ZIPs 2021-01 to 2026-08 | observed (CKAN `size`) | 10.8 GB (2021: 2.0 GB, 2022: 1.4, 2023: 2.0, 2024: 2.3, 2025: 2.6, 2026 to Aug: 0.5) |
| STJ íntegras, daily metadata JSON | observed 0.8-1.9 MB/day × ~1,300 publication days | ~1.8 GB |
| Uncompressed text | observed 10.5 kB/doc × ~2,700 docs/day × ~1,300 days | ~3.5 million docs, ~37 GB |
| DuckDB with raw + processed text | DuckDB dictionary/zstd compression, typically 3-4× on Portuguese legal text | 10-15 GB |
| STJ espelhos, all organs | observed (two organs: 34 MB and 156 MB) | < 1 GB |
| STJ atas de distribuição | observed | 4.2 GB raw; ~300 MB after dropping party fields |
| STJ precedent registry, JN base, STF XLSX | observed | < 20 MB |
| DataJud responses (cases in the citing corpus) | assumption: ~150 k cases × ~15 kB JSON | ~2-3 GB |
| Embeddings, candidate-theme subset only | assumption: 150 k docs × 768 floats × 4 B | ~0.5 GB (float32), 0.25 GB (float16) |
| Embeddings, whole corpus (only if needed) | 3.5 M × 768 × 2 B | ~5.4 GB |
| Models (TF-IDF, boosting, one fine-tuned BERT-base checkpoint) | typical sizes | < 2 GB |
| **Total working set** | | **~40-60 GB**, comfortably within the 1.3 TB available |

Design implication: keep DuckDB as the store for the whole project. PostgreSQL migration is
justified only if concurrent writers or a multi-user server appear; neither is planned.

## Network

Full download of the íntegras (10.8 GB + 1.8 GB) at a residential 100 Mbit/s link:
about 20-30 minutes of transfer time, but the CKAN server throughput observed during Phase 0
(11 MB ZIP in a few seconds) suggests a few hours with polite pacing (one file at a time,
retries with backoff). Plan a Background Job of 3-6 hours, resumable by manifest.

## Compute

| Task | Method | Estimate (this machine) |
|------|--------|-------------------------|
| Regex screening of all 3.5 M texts (theme, súmula, paradigm patterns) | Python, multiprocessing over ZIP members, no decompression to disk | 1-3 hours |
| Origin recovery (atas crosswalk + text regex) | pandas/DuckDB joins | minutes |
| Embeddings of the candidate-theme subset (~150 k docs, 512 tokens) with a BERT-base Portuguese encoder | GPU, fp16, batch 64 | 1-2 hours |
| Fine-tuning a BERT-base classifier on 2-3 k labelled documents, 5 folds | GPU 8 GB, max length 512 | 30-90 minutes per fold set |
| TF-IDF + linear / gradient boosting baselines | CPU | minutes |
| Event study, survival and multilevel models (fixest, survival, lme4) | CPU | minutes |
| Bayesian multilevel model (brms) if used | CPU, 4 chains | 1-4 hours per specification |
| Spatial models (sf/spatialreg) at court level (27 TJs + 6 TRFs = 33 units) | CPU | seconds; the small N is the constraint, not compute |

## What is deliberately not planned

- Embedding or fine-tuning on the whole 3.5 M-document corpus. The subset defined by
  subject codes and regex pre-screening is sufficient for the research questions.
- Any cloud compute. The whole pipeline is sized for the local machine.
