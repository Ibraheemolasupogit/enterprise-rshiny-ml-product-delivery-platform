app_root <- normalizePath(file.path("..", ".."), mustWork = TRUE)
library(shiny)
r_files <- list.files(file.path(app_root, "R"), pattern = "[.]R$", full.names = TRUE)
priority <- c(
  "utils.R", "validation.R", "prediction_contract.R", "error_handling.R",
  "app_config.R", "api_client.R", "prediction_presenter.R", "batch_contract.R",
  "batch_validation.R", "batch_presenter.R", "export_utils.R", "evidence_client.R",
  "performance_presenter.R", "governance_presenter.R", "review_mode.R",
  "monitoring_validation.R", "monitoring_client.R", "monitoring_presenter.R",
  "retraining_validation.R", "retraining_client.R", "retraining_presenter.R",
  "accessibility.R"
)
ranked <- match(basename(r_files), priority)
r_files <- r_files[order(is.na(ranked), ranked, basename(r_files))]
for (file in r_files) {
  sys.source(file, envir = environment())
}
for (file in sort(list.files(file.path(app_root, "modules"), pattern = "[.]R$", full.names = TRUE))) {
  sys.source(file, envir = environment())
}
