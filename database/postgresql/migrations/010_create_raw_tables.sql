create table if not exists raw.patients (
  patient_id text,
  age integer,
  sex text,
  postcode_region text,
  deprivation_decile integer,
  comorbidity_count integer,
  previous_admissions_12m integer,
  _source_file text not null,
  _source_row_number integer not null,
  _ingestion_run_id text not null,
  _dataset_version text not null,
  _configuration_fingerprint text not null,
  _source_checksum text not null
);

create table if not exists raw.admissions (
  admission_id text,
  patient_id text,
  admission_datetime timestamp,
  admission_type text,
  source_of_admission text,
  ward_id text,
  initial_news2_score integer,
  mobility_status text,
  _source_file text not null,
  _source_row_number integer not null,
  _ingestion_run_id text not null,
  _dataset_version text not null,
  _configuration_fingerprint text not null,
  _source_checksum text not null
);

create table if not exists raw.diagnoses (
  diagnosis_id text,
  admission_id text,
  diagnosis_group text,
  diagnosis_complexity text,
  primary_diagnosis_flag boolean,
  _source_file text not null,
  _source_row_number integer not null,
  _ingestion_run_id text not null,
  _dataset_version text not null,
  _configuration_fingerprint text not null,
  _source_checksum text not null
);

create table if not exists raw.ward_capacity (
  ward_id text,
  record_date date,
  staffed_beds integer,
  occupied_beds integer,
  closed_beds integer,
  isolation_capacity integer,
  _source_file text not null,
  _source_row_number integer not null,
  _ingestion_run_id text not null,
  _dataset_version text not null,
  _configuration_fingerprint text not null,
  _source_checksum text not null
);

create table if not exists raw.workforce (
  workforce_record_id text,
  ward_id text,
  record_date date,
  registered_nurses integer,
  support_workers integer,
  medical_staff integer,
  agency_hours double precision,
  vacancy_rate double precision,
  _source_file text not null,
  _source_row_number integer not null,
  _ingestion_run_id text not null,
  _dataset_version text not null,
  _configuration_fingerprint text not null,
  _source_checksum text not null
);

create table if not exists raw.outcomes (
  admission_id text,
  discharge_datetime timestamp,
  length_of_stay_days integer,
  long_stay_flag boolean,
  readmission_30d boolean,
  discharge_destination text,
  _source_file text not null,
  _source_row_number integer not null,
  _ingestion_run_id text not null,
  _dataset_version text not null,
  _configuration_fingerprint text not null,
  _source_checksum text not null
);

