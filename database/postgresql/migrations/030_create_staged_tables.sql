create table if not exists staged.patients (
  patient_id text,
  age integer,
  sex text,
  postcode_region text,
  deprivation_decile integer,
  comorbidity_count integer,
  previous_admissions_12m integer,
  patient_quality_status text,
  _source_file text,
  _source_row_number integer,
  _ingestion_run_id text,
  _dataset_version text,
  _configuration_fingerprint text,
  _source_checksum text
);

create table if not exists staged.admissions (
  admission_id text,
  patient_id text,
  admission_datetime timestamp,
  admission_date date,
  admission_type text,
  source_of_admission text,
  ward_id text,
  initial_news2_score integer,
  mobility_status text,
  admission_quality_status text,
  _source_file text,
  _source_row_number integer,
  _ingestion_run_id text,
  _dataset_version text,
  _configuration_fingerprint text,
  _source_checksum text
);

create table if not exists staged.diagnoses (
  diagnosis_id text,
  admission_id text,
  diagnosis_group text,
  diagnosis_complexity text,
  primary_diagnosis_flag boolean,
  diagnosis_quality_status text,
  _source_file text,
  _source_row_number integer,
  _ingestion_run_id text,
  _dataset_version text,
  _configuration_fingerprint text,
  _source_checksum text
);

create table if not exists staged.ward_capacity (
  ward_id text,
  record_date date,
  staffed_beds integer,
  occupied_beds integer,
  closed_beds integer,
  isolation_capacity integer,
  capacity_quality_status text,
  _source_file text,
  _source_row_number integer,
  _ingestion_run_id text,
  _dataset_version text,
  _configuration_fingerprint text,
  _source_checksum text
);

create table if not exists staged.workforce (
  workforce_record_id text,
  ward_id text,
  record_date date,
  registered_nurses integer,
  support_workers integer,
  medical_staff integer,
  agency_hours double precision,
  vacancy_rate double precision,
  workforce_quality_status text,
  _source_file text,
  _source_row_number integer,
  _ingestion_run_id text,
  _dataset_version text,
  _configuration_fingerprint text,
  _source_checksum text
);

create table if not exists staged.outcomes (
  admission_id text,
  discharge_datetime timestamp,
  length_of_stay_days_source integer,
  long_stay_flag_source boolean,
  length_of_stay_days_governed integer,
  long_stay_flag_governed boolean,
  readmission_30d boolean,
  discharge_destination text,
  outcome_quality_status text,
  _source_file text,
  _source_row_number integer,
  _ingestion_run_id text,
  _dataset_version text,
  _configuration_fingerprint text,
  _source_checksum text
);

