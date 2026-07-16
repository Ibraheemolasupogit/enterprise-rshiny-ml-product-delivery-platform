synthetic_results_statement <- paste(
  "These results were generated from synthetic inputs using an unapproved model",
  "in local review mode."
)

safe_export_filename <- function(timestamp = Sys.time()) {
  stamp <- format(as.POSIXct(timestamp, tz = "UTC"), "%Y%m%dT%H%M%SZ")
  paste0("synthetic_cohort_predictions_", stamp, ".csv")
}

build_export_dataframe <- function(results, timestamp = Sys.time()) {
  export <- results[batch_result_fields]
  export$candidate_identifier <- results$candidate_identifier
  export$synthetic_data_statement <- synthetic_results_statement
  export$export_timestamp_utc <- format(as.POSIXct(timestamp, tz = "UTC"), "%Y-%m-%dT%H:%M:%SZ")
  export[batch_export_fields]
}

write_export_csv <- function(results, file, timestamp = Sys.time()) {
  utils::write.csv(build_export_dataframe(results, timestamp), file, row.names = FALSE)
}
