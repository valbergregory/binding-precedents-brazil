-- DuckDB schema, version 001 (Phase 0 design). Raw text and processed text live in
-- separate tables; nothing here is ever derived by hand. All statements are idempotent.
-- Migration to PostgreSQL is planned only if the corpus exceeds what a single DuckDB file
-- handles comfortably (see docs/06_storage_compute_estimate.md).

CREATE TABLE IF NOT EXISTS courts (
    court_id        VARCHAR PRIMARY KEY,   -- e.g. TJSP, TRF4, STJ
    name            VARCHAR,
    branch          VARCHAR,               -- estadual | federal | superior | ...
    uf              VARCHAR,               -- state code when applicable
    region          VARCHAR,               -- macro-region or TRF region
    cnj_j           VARCHAR,               -- J segment of the CNJ number
    cnj_tr          VARCHAR                -- TR segment of the CNJ number
);

-- Registry of qualified precedents (STJ temas/controvérsias/IAC/PUIL/SIRDR; STF RG themes).
CREATE TABLE IF NOT EXISTS precedents (
    precedent_id            VARCHAR PRIMARY KEY,   -- e.g. STJ-TEMA-1218, STF-RG-1234
    court_id                VARCHAR REFERENCES courts(court_id),
    precedent_type          VARCHAR,               -- Tema | Controvérsia | IAC | PUIL | SIRDR | RG
    number                  INTEGER,
    stj_sequencial          INTEGER,               -- sequencialPrecedente in STJ registry
    date_affetacao          DATE,
    date_judgment           DATE,
    date_publication        DATE,
    status                  VARCHAR,
    question                TEXT,
    thesis                  TEXT,
    legal_references        TEXT,
    subjects                TEXT,
    organ                   VARCHAR,               -- S1, S2, S3, CE, Plenário
    linked_stf_rg_number    INTEGER,
    source_file             VARCHAR,
    source_sha256           VARCHAR
);

-- Paradigm cases attached to each precedent (processos.csv).
CREATE TABLE IF NOT EXISTS precedent_cases (
    precedent_id        VARCHAR REFERENCES precedents(precedent_id),
    case_label          VARCHAR,           -- e.g. REsp 1633613
    numero_registro     VARCHAR,
    leading_case        BOOLEAN,
    origin_court_id     VARCHAR,
    origin_uf           VARCHAR,
    origin_branch       VARCHAR,
    date_judgment       DATE,
    PRIMARY KEY (precedent_id, case_label)
);

-- One row per STJ decision/judgment published in the DJe (íntegras metadata).
CREATE TABLE IF NOT EXISTS documents (
    seq_documento       BIGINT PRIMARY KEY,
    publication_date    DATE,
    document_type       VARCHAR,           -- DECISÃO | ACÓRDÃO
    numero_registro     VARCHAR,
    case_label          VARCHAR,           -- e.g. "AREsp 2046805"
    class_sigla         VARCHAR,
    class_number        BIGINT,
    date_received       DATE,
    date_distributed    DATE,
    reporter_hash       VARCHAR,           -- salted hash of ministro name (never the name)
    internal_appeal     VARCHAR,           -- recurso field
    outcome_label       VARCHAR,           -- teor field
    monocratic_summary  VARCHAR,
    subject_codes       VARCHAR,           -- ';'-separated CNJ codes
    source_file         VARCHAR,
    source_sha256       VARCHAR
);

-- Raw text, exactly as extracted from the ZIP (never modified).
CREATE TABLE IF NOT EXISTS documents_raw_text (
    seq_documento   BIGINT PRIMARY KEY REFERENCES documents(seq_documento),
    raw_text        TEXT,
    raw_sha256      VARCHAR
);

-- Processed text (line breaks normalised, boilerplate removed), versioned by pipeline.
CREATE TABLE IF NOT EXISTS documents_text (
    seq_documento   BIGINT REFERENCES documents(seq_documento),
    pipeline_version VARCHAR,
    text            TEXT,
    n_chars         INTEGER,
    PRIMARY KEY (seq_documento, pipeline_version)
);

-- Case-level attributes (from atas de distribuição, acervo snapshot, DataJud). No party data.
CREATE TABLE IF NOT EXISTS cases (
    numero_registro     VARCHAR PRIMARY KEY,
    numero_unico_cnj    VARCHAR,
    origin_court_id     VARCHAR REFERENCES courts(court_id),
    origin_uf           VARCHAR,
    origin_branch       VARCHAR,
    origin_channel      VARCHAR,           -- atas | acervo | cnj_number_in_text | regex_tj | regex_trf | datajud
    class_sigla         VARCHAR,
    class_cnj_code      INTEGER,
    main_subject_code   INTEGER,
    date_distributed    TIMESTAMP,
    organ               VARCHAR,
    datajud_id          VARCHAR,
    date_filed_origin   DATE               -- dataAjuizamento from DataJud when available
);

-- Every candidate citation found by regex in a document.
CREATE TABLE IF NOT EXISTS citations (
    citation_id     BIGINT PRIMARY KEY,
    seq_documento   BIGINT REFERENCES documents(seq_documento),
    ref_type        VARCHAR,               -- tema | sumula | paradigma | cpc_regime
    ref_court       VARCHAR,               -- STJ | STF | NULL (ambiguous)
    ref_number      INTEGER,
    ref_label       VARCHAR,               -- matched string
    char_start      INTEGER,
    char_end        INTEGER,
    extractor_version VARCHAR
);

-- Manual annotations (gold standard). One row per (document, precedent, annotator, round).
CREATE TABLE IF NOT EXISTS annotations (
    annotation_id   BIGINT PRIMARY KEY,
    seq_documento   BIGINT REFERENCES documents(seq_documento),
    precedent_id    VARCHAR REFERENCES precedents(precedent_id),
    annotator_id    VARCHAR,
    round           INTEGER,
    label           VARCHAR,   -- no_relation | formal_citation_only | material_application | outcome_conform | reasoned_distinction | departure
    lower_court_conformity VARCHAR, -- as observable from the quoted lower-court reasoning: conform | nonconform | unclear | not_quoted
    confidence      INTEGER,
    notes           TEXT,
    annotated_at    TIMESTAMP
);

-- Model outputs (probabilistic evidence, never a verdict).
CREATE TABLE IF NOT EXISTS classifications (
    seq_documento   BIGINT REFERENCES documents(seq_documento),
    precedent_id    VARCHAR REFERENCES precedents(precedent_id),
    model_id        VARCHAR,
    label           VARCHAR,
    probabilities   JSON,
    embedding_similarity DOUBLE,
    scored_at       TIMESTAMP,
    PRIMARY KEY (seq_documento, precedent_id, model_id)
);

-- Court-year institutional covariates (CNJ Justiça em Números).
CREATE TABLE IF NOT EXISTS court_year_stats (
    court_id            VARCHAR REFERENCES courts(court_id),
    year                INTEGER,
    congestion_rate     DOUBLE,   -- tc
    congestion_rate_2g  DOUBLE,   -- tc2
    workload_per_judge  DOUBLE,   -- k
    magistrates         DOUBLE,   -- mag
    pending_cases       DOUBLE,   -- cp
    new_cases           DOUBLE,
    decisions           DOUBLE,   -- sent
    source_file         VARCHAR,
    PRIMARY KEY (court_id, year)
);

-- Model registry and metrics (model cards are generated from here).
CREATE TABLE IF NOT EXISTS model_runs (
    model_id        VARCHAR PRIMARY KEY,
    family          VARCHAR,   -- tfidf_linear | gradient_boosting | transformer | embedding_knn
    trained_at      TIMESTAMP,
    train_rows      INTEGER,
    metrics         JSON,
    config          JSON,
    artifact_path   VARCHAR
);
