allowed_values <- list(
  sex = c("female", "male", "not_specified"),
  postcode_region = c("SR-CENTRAL", "SR-EAST", "SR-NORTH", "SR-SOUTH", "SR-WEST"),
  admission_type = c("emergency", "planned", "urgent"),
  source_of_admission = c("care_facility", "clinic", "home", "transfer"),
  mobility_status = c("assisted", "bedbound", "independent", "limited"),
  primary_diagnosis_group = c(
    "cardiovascular_synthetic", "frailty_synthetic", "infection_synthetic",
    "other_synthetic", "respiratory_synthetic", "surgical_synthetic"
  ),
  primary_diagnosis_complexity = c("high", "low", "moderate")
)

numeric_ranges <- list(
  age = c(18, 110), deprivation_decile = c(1, 10), comorbidity_count = c(0, Inf),
  previous_admissions_12m = c(0, Inf), initial_news2_score = c(0, 20),
  diagnosis_count = c(1, Inf), secondary_diagnosis_count = c(0, Inf),
  staffed_beds = c(.Machine$double.eps, Inf), occupied_beds = c(0, Inf),
  closed_beds = c(0, Inf), isolation_capacity = c(0, Inf),
  registered_nurses = c(0, Inf), support_workers = c(0, Inf),
  medical_staff = c(0, Inf), agency_hours = c(0, Inf),
  vacancy_rate = c(0, 1), occupancy_rate = c(0, 1.5),
  staff_to_bed_ratio = c(0, Inf)
)

prohibited_prediction_fields <- c(
  "patient_id", "admission_id", "name", "nhs_number", "address",
  "discharge_datetime", "length_of_stay", "length_of_stay_days",
  "long_stay_flag", "readmission", "readmission_30d", "discharge_destination"
)

validate_api_base_url <- function(base_url) {
  if (!grepl("^https?://", base_url)) {
    stop("MODEL_API_BASE_URL must be an HTTP(S) URL", call. = FALSE)
  }
  invisible(TRUE)
}

validate_prediction_record <- function(record) {
  present_prohibited <- intersect(names(record), prohibited_prediction_fields)
  if (length(present_prohibited) > 0) {
    stop(sprintf("Prohibited field(s): %s", paste(present_prohibited, collapse = ", ")),
         call. = FALSE)
  }
  for (field in names(allowed_values)) {
    if (!record[[field]] %in% allowed_values[[field]]) {
      stop(sprintf("%s has an unsupported value", field), call. = FALSE)
    }
  }
  for (field in names(numeric_ranges)) {
    value <- record[[field]]
    if (!is.null(value) && !is.na(value)) {
      bounds <- numeric_ranges[[field]]
      if (!is.numeric(value) || value < bounds[1] || value > bounds[2]) {
        stop(sprintf("%s is outside the permitted range", field), call. = FALSE)
      }
    }
  }
  if (!grepl("^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}", record$admission_datetime)) {
    stop("admission_datetime must be ISO-8601-like", call. = FALSE)
  }
  invisible(TRUE)
}

validate_feedback <- function(feedback) {
  ratings <- c("understandable_rating", "explanation_rating", "usability_rating",
               "governance_clarity_rating")
  for (field in ratings) {
    if (!is.numeric(feedback[[field]]) || feedback[[field]] < 1 || feedback[[field]] > 5) {
      stop(sprintf("%s must be between 1 and 5", field), call. = FALSE)
    }
  }
  if (nchar(feedback$comment %||% "") > 1000) {
    stop("Feedback comment must be 1000 characters or fewer", call. = FALSE)
  }
  invisible(TRUE)
}
