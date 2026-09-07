"""bpb: Binding Precedents Brazil.

Ingestion, parsing and NLP utilities for the study
"Do Binding Precedents Actually Bind? Measuring Judicial Compliance and Diffusion Across Brazilian Courts".

Phase 0 modules:
- manifest: hashed, logged downloads into data/raw (raw data are never modified).
- sources_check: reachability checks for config/sources.yml.
- citations: regex extraction of precedent references (theme numbers, súmulas, paradigm appeals).
"""

__version__ = "0.0.1"
