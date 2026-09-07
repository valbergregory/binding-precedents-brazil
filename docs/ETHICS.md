# Ethics and data-handling rules

These rules bind every script and every output of this repository.

1. **Public records only.** All sources are official open-data portals or public APIs. The STJ
   provider already excludes secret-of-justice cases from the íntegras dataset; DataJud
   exposes a `nivelSigilo` field and only level 0 records are used. No attempt is made to access
   sealed cases.
2. **No circumvention.** No CAPTCHA solving, no session spoofing, no authentication bypass.
   Endpoints that answer challenge pages to non-browser clients (STF jurisprudence search,
   STF Corte Aberta) are treated as manual sources. The DataJud public key is used as published.
3. **Personal data (LGPD).** Party and lawyer names appear in the STJ atas de distribuição
   (`partes`, `advogados`) and inside decision texts. The loader drops the structured fields
   at ingestion. Names inside texts are never extracted, indexed or printed; outputs are
   aggregated at court, panel and subject level. Reporter (minister) names are stored as
   salted hashes; no analysis is run at the individual-judge level.
4. **No individual blame.** The study never labels a judge or reporter as non-compliant. All
   compliance measures are court-level or panel-level rates with uncertainty.
5. **Probabilistic evidence.** Automatic labels carry probabilities and a model id. Every
   document classified as departure/non-conformity in the final sample is manually audited
   before being counted, and the audit outcome is recorded in `annotations`.
6. **Terms of use.** STJ open data: CC-BY (attribution in the article and data card). DataJud:
   non-commercial use, no redistribution of the raw payload, CNJ is to be notified of
   publications derived from it. STF and CNJ portals: their own terms; no bulk redistribution.
7. **AI governance benchmark.** CNJ Resolution 615/2025 (AI in the Judiciary) does not
   regulate external research directly, but its transparency, human-oversight and
   risk-classification requirements are adopted as the standard for the model card.
8. **Reproducibility without re-identification.** Released derived datasets contain document
   identifiers (`seqDocumento`), labels and features, never full texts of the atas records.
