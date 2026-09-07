# Run the targets pipeline. Intended for RStudio Background Jobs (Jobs > Start Local Job)
# or from the Terminal:  Rscript scripts/run_targets.R
# Resumes safely: targets skips anything already up to date.
setwd(here::here())
targets::tar_make()
