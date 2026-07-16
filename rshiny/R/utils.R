`%||%` <- function(left, right) {
  if (is.null(left) || length(left) == 0) right else left
}

digest_text <- function(value) {
  raw <- charToRaw(as.character(value))
  paste(sprintf("%02x", as.integer(raw)), collapse = "")
}

session_hash <- function(session_token = Sys.time()) {
  substr(digest_text(session_token), 1, 16)
}

write_jsonl <- function(path, record) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  line <- jsonlite::toJSON(record, auto_unbox = TRUE, null = "null")
  con <- file(path, open = "a", encoding = "UTF-8")
  on.exit(close(con), add = TRUE)
  writeLines(line, con = con)
  invisible(path)
}

write_feedback_record <- function(feedback, config, status) {
  validate_feedback(feedback)
  path <- config$feedback$output_path
  validate_relative_output_path(path)
  record <- list(
    feedback_id = paste0("FB-", toupper(substr(digest_text(Sys.time()), 1, 12))),
    timestamp = format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC"),
    session_hash = session_hash(),
    understandable_rating = feedback$understandable_rating,
    explanation_rating = feedback$explanation_rating,
    usability_rating = feedback$usability_rating,
    governance_clarity_rating = feedback$governance_clarity_rating,
    comment = feedback$comment %||% "",
    comment_length = nchar(feedback$comment %||% ""),
    review_mode = is_review_mode(status),
    model_registry_version = status$model$data$registry_version %||% NA
  )
  write_jsonl(path, record)
}
