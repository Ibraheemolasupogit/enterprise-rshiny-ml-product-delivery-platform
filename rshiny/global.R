shiny_app_root <- normalizePath(
  if (dir.exists(file.path("rshiny", "R"))) "rshiny" else ".",
  mustWork = FALSE
)

source_dir <- function(path) {
  files <- list.files(path, pattern = "[.]R$", full.names = TRUE)
  if (basename(path) == "R") {
    priority <- c(
      "utils.R", "validation.R", "prediction_contract.R", "error_handling.R",
      "app_config.R", "api_client.R", "prediction_presenter.R", "batch_contract.R",
      "batch_validation.R", "batch_presenter.R", "export_utils.R", "evidence_client.R",
      "performance_presenter.R", "governance_presenter.R", "review_mode.R",
      "monitoring_validation.R", "monitoring_client.R", "monitoring_presenter.R",
      "retraining_validation.R", "retraining_client.R", "retraining_presenter.R",
      "accessibility.R"
    )
    ranked <- match(basename(files), priority)
    files <- files[order(is.na(ranked), ranked, basename(files))]
  }
  for (file in files) {
    source(file, local = FALSE)
  }
}

source_dir(file.path(shiny_app_root, "R"))
source_dir(file.path(shiny_app_root, "modules"))
