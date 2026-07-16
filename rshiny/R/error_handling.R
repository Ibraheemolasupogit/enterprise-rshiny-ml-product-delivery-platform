error_categories <- c(
  "configuration_error", "api_unavailable", "api_not_ready", "authentication_error",
  "authorisation_error", "validation_error", "batch_limit_error", "malformed_response",
  "evidence_unavailable", "evidence_mismatch", "feedback_write_error",
  "unexpected_error"
)

safe_error_message <- function(error) {
  if (is.null(error$message)) {
    return("The scoring service returned an error. No prediction was generated.")
  }
  sanitize_error_text(error$message)
}

sanitize_error_text <- function(message) {
  message <- gsub("X-API-Key|MODEL_API_KEY|api[_-]?key", "[redacted]", message, ignore.case = TRUE)
  message <- gsub("/Users/[^ ,;\n]+", "[path redacted]", message)
  gsub("models/[^ ,;\n]+|data/processed/[^ ,;\n]+|reports/[^ ,;\n]+", "[path redacted]", message)
}

user_error <- function(category, message, request_id = NULL) {
  if (!category %in% error_categories) {
    category <- "unexpected_error"
  }
  clean <- sanitize_error_text(message)
  if (!is.null(request_id) && nzchar(request_id)) {
    clean <- paste(clean, sprintf("Request ID: %s", request_id))
  }
  list(category = category, message = clean, request_id = request_id)
}

error_panel <- function(error) {
  shiny::tags$section(
    class = "result-error",
    role = "alert",
    tabindex = "-1",
    shiny::tags$strong(gsub("_", " ", error$category %||% "unexpected_error")),
    shiny::tags$p(error$message %||% "The request could not be completed.")
  )
}

aria_status <- function(message) {
  shiny::tags$div(class = "sr-status", `aria-live` = "polite", message)
}
