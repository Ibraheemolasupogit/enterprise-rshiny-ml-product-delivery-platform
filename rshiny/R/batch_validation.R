read_batch_csv <- function(path, config = load_app_config()) {
  validate_safe_upload_path(path)
  info <- file.info(path)
  if (is.na(info$size) || info$size == 0) {
    stop("Uploaded CSV is empty.", call. = FALSE)
  }
  max_bytes <- config$cohort_scoring$maximum_file_size_mb * 1024 * 1024
  if (info$size > max_bytes) {
    stop("Uploaded CSV exceeds the configured file-size limit.", call. = FALSE)
  }
  data <- tryCatch(
    utils::read.csv(path, stringsAsFactors = FALSE, check.names = FALSE),
    error = function(err) stop("Uploaded CSV could not be parsed.", call. = FALSE)
  )
  validate_batch_dataframe(data, config)
  data
}

validate_safe_upload_path <- function(path) {
  if (!is.character(path) || length(path) != 1 || path == "") {
    stop("Upload path is invalid.", call. = FALSE)
  }
  normal <- normalizePath(path, mustWork = FALSE)
  if (grepl("(^|/)\\.\\.(/|$)", path) || grepl("models/|data/processed|[.]duckdb", normal)) {
    stop("Upload path is not permitted.", call. = FALSE)
  }
  invisible(TRUE)
}

validate_batch_dataframe <- function(data, config = load_app_config()) {
  if (!is.data.frame(data) || nrow(data) == 0) {
    stop("Uploaded CSV must contain at least one synthetic row.", call. = FALSE)
  }
  if (nrow(data) > config$cohort_scoring$maximum_rows) {
    stop("Uploaded CSV exceeds the configured batch row limit.", call. = FALSE)
  }
  duplicate_columns <- names(data)[duplicated(names(data))]
  if (length(duplicate_columns) > 0) {
    stop("Uploaded CSV contains duplicate column names.", call. = FALSE)
  }
  present_prohibited <- intersect(names(data), batch_prohibited_fields)
  if (length(present_prohibited) > 0) {
    stop("Uploaded CSV contains prohibited identifier or outcome columns.", call. = FALSE)
  }
  missing <- setdiff(batch_input_fields, names(data))
  extra <- setdiff(names(data), batch_input_fields)
  if (length(missing) > 0) {
    stop(sprintf("Uploaded CSV is missing required column(s): %s", paste(missing, collapse = ", ")),
         call. = FALSE)
  }
  if (length(extra) > 0) {
    stop(sprintf("Uploaded CSV contains unsupported column(s): %s", paste(extra, collapse = ", ")),
         call. = FALSE)
  }
  invisible(TRUE)
}

batch_validation_table <- function(data) {
  rows <- lapply(seq_len(nrow(data)), function(i) {
    record <- batch_row_to_record(data[i, , drop = FALSE])
    err <- tryCatch({
      validate_prediction_record(record)
      NULL
    }, error = function(e) e$message)
    data.frame(
      row_number = i,
      validation_status = if (is.null(err)) "valid" else "invalid",
      error_count = if (is.null(err)) 0L else 1L,
      error_fields = if (is.null(err)) "" else infer_error_field(err),
      error_summary = err %||% "",
      stringsAsFactors = FALSE
    )
  })
  do.call(rbind, rows)
}

batch_row_to_record <- function(row) {
  record <- as.list(row[1, batch_input_fields, drop = TRUE])
  for (field in names(numeric_ranges)) {
    record[[field]] <- suppressWarnings(as.numeric(record[[field]]))
  }
  record$deprivation_decile <- as.integer(record$deprivation_decile)
  record
}

batch_records_from_dataframe <- function(data) {
  validate_batch_dataframe(data)
  validation <- batch_validation_table(data)
  if (any(validation$validation_status != "valid")) {
    stop("Uploaded CSV must pass validation before scoring.", call. = FALSE)
  }
  lapply(seq_len(nrow(data)), function(i) batch_row_to_record(data[i, , drop = FALSE]))
}

infer_error_field <- function(message) {
  fields <- c(batch_input_fields, batch_prohibited_fields)
  hit <- fields[vapply(fields, function(field) grepl(field, message, fixed = TRUE), logical(1))]
  if (length(hit) == 0) "" else paste(hit, collapse = ", ")
}
