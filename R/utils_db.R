# R helpers shared by _targets.R. Phase 0: connection and config only.

bpb_config <- function(root = here::here()) {
  yaml::read_yaml(file.path(root, "config", "config.yml"))
}

bpb_connect <- function(root = here::here(), read_only = TRUE) {
  cfg <- bpb_config(root)
  DBI::dbConnect(duckdb::duckdb(), dbdir = file.path(root, cfg$paths$duckdb), read_only = read_only)
}

# Read a table or query into a data.table; the DuckDB file is written only by Python loaders.
bpb_query <- function(sql, root = here::here()) {
  con <- bpb_connect(root)
  on.exit(DBI::dbDisconnect(con, shutdown = TRUE))
  data.table::as.data.table(DBI::dbGetQuery(con, sql))
}
