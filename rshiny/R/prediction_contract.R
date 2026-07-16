prediction_fields <- c(
  "age", "sex", "postcode_region", "deprivation_decile", "comorbidity_count",
  "previous_admissions_12m", "admission_type", "source_of_admission",
  "initial_news2_score", "mobility_status", "primary_diagnosis_group",
  "primary_diagnosis_complexity", "diagnosis_count", "secondary_diagnosis_count",
  "staffed_beds", "occupied_beds", "closed_beds", "isolation_capacity",
  "registered_nurses", "support_workers", "medical_staff", "agency_hours",
  "vacancy_rate", "occupancy_rate", "staff_to_bed_ratio", "admission_datetime",
  "request_id"
)

synthetic_example_record <- function() {
  list(
    age = 78, sex = "female", postcode_region = "SR-CENTRAL",
    deprivation_decile = 4L, comorbidity_count = 3, previous_admissions_12m = 2,
    admission_type = "emergency", source_of_admission = "home",
    initial_news2_score = 7, mobility_status = "limited",
    primary_diagnosis_group = "respiratory_synthetic",
    primary_diagnosis_complexity = "moderate", diagnosis_count = 4,
    secondary_diagnosis_count = 2, staffed_beds = 36, occupied_beds = 32,
    closed_beds = 2, isolation_capacity = 4, registered_nurses = 9,
    support_workers = 11, medical_staff = 5, agency_hours = 12,
    vacancy_rate = 0.08, occupancy_rate = 0.89, staff_to_bed_ratio = 0.69,
    admission_datetime = "2026-07-15T09:30:00Z",
    request_id = paste0("SHINY-", toupper(substr(digest_text(Sys.time()), 1, 12)))
  )
}

build_prediction_payload <- function(record) {
  validate_prediction_record(record)
  record[prediction_fields]
}
