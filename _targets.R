# targets pipeline (R side). Phase 0: skeleton with the planned DAG. Only `manifest` and
# `precedents_registry` are runnable now; every other target stops with an explicit message
# so that nothing can silently look "done". Extend in Phase 1 after the go/no-go review.
#
# Quick test in the RStudio console:  targets::tar_make(names = "precedents_registry")
# Full run as a Background Job:        source("scripts/run_targets.R")

library(targets)
tar_option_set(packages = c("data.table", "DBI", "duckdb", "yaml", "here"), format = "qs")
tar_source("R")

not_ready <- function(name) stop(sprintf("target '%s' is not implemented yet (Phase %s)", name[1], name[2]), call. = FALSE)

list(
  tar_target(manifest_file, here::here("data", "raw", "MANIFEST.csv"), format = "file"),
  tar_target(manifest, data.table::fread(manifest_file)),
  tar_target(precedents_registry, {
    f <- manifest[resource_key == "temas_csv"][.N, local_path]
    data.table::fread(here::here(f), encoding = "UTF-8")
  }),
  # Phase 3: corpus and citations (loaded into DuckDB by Python; read here)
  tar_target(citations_panel, not_ready(c("citations_panel", 3))),
  # Phase 5: descriptive statistics and diffusion curves
  tar_target(diffusion_curves, not_ready(c("diffusion_curves", 5))),
  # Phase 6: event study (fixest), survival (survival), multilevel (lme4/brms), spatial (sf/spatialreg)
  tar_target(event_study, not_ready(c("event_study", 6))),
  tar_target(survival_first_adoption, not_ready(c("survival_first_adoption", 6))),
  tar_target(multilevel_models, not_ready(c("multilevel_models", 6))),
  tar_target(spatial_models, not_ready(c("spatial_models", 6))),
  # Phase 7: robustness (placebo dates, pre-trends, alternative specifications)
  tar_target(robustness, not_ready(c("robustness", 7)))
)
