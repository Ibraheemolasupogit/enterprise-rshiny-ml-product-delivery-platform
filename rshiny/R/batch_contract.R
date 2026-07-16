batch_input_fields <- c(
  "age", "sex", "postcode_region", "deprivation_decile", "comorbidity_count",
  "previous_admissions_12m", "admission_type", "source_of_admission",
  "initial_news2_score", "mobility_status", "primary_diagnosis_group",
  "primary_diagnosis_complexity", "diagnosis_count", "secondary_diagnosis_count",
  "staffed_beds", "occupied_beds", "closed_beds", "isolation_capacity",
  "registered_nurses", "support_workers", "medical_staff", "agency_hours",
  "vacancy_rate", "occupancy_rate", "staff_to_bed_ratio", "admission_datetime",
  "request_id"
)

batch_result_fields <- c(
  "row_number", "long_stay_probability", "predicted_long_stay", "risk_band",
  "model_registry_version", "model_family", "threshold", "review_mode"
)

batch_export_fields <- c(
  batch_result_fields, "candidate_identifier", "synthetic_data_statement",
  "export_timestamp_utc"
)

batch_prohibited_fields <- c(
  "patient_id", "admission_id", "name", "nhs_number", "address",
  "discharge_datetime", "length_of_stay", "length_of_stay_days",
  "long_stay_flag", "readmission", "readmission_30d", "discharge_destination"
)

batch_contract <- function(config = load_app_config()) {
  list(
    required_columns = batch_input_fields,
    prohibited_columns = batch_prohibited_fields,
    maximum_rows = config$cohort_scoring$maximum_rows,
    accepted_formats = config$cohort_scoring$accepted_formats,
    response_fields = batch_result_fields,
    export_fields = batch_export_fields,
    ordering_rule = "Responses must preserve input row order and request_id order."
  )
}

synthetic_template_records <- function() {
  base <- synthetic_example_record()
  second <- base
  second$age <- 64
  second$sex <- "male"
  second$postcode_region <- "SR-WEST"
  second$admission_type <- "planned"
  second$source_of_admission <- "clinic"
  second$initial_news2_score <- 3
  second$mobility_status <- "independent"
  second$primary_diagnosis_group <- "surgical_synthetic"
  second$primary_diagnosis_complexity <- "low"
  second$admission_datetime <- "2026-07-15T11:15:00Z"
  second$request_id <- "SHINY-SYNTHETIC-0002"
  base$request_id <- "SHINY-SYNTHETIC-0001"
  data.frame(
    lapply(batch_input_fields, function(field) c(base[[field]], second[[field]])),
    check.names = FALSE
  ) |>
    stats::setNames(batch_input_fields)
}
