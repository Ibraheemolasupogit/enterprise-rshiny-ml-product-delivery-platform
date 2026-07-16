-- Raw tables are created by the deterministic Python loader from Milestone 2 files.
-- They preserve source values and append separated ingestion metadata columns.
create table if not exists raw.patients(patient_id varchar);
create table if not exists raw.admissions(admission_id varchar);
create table if not exists raw.diagnoses(diagnosis_id varchar);
create table if not exists raw.ward_capacity(ward_id varchar, record_date varchar);
create table if not exists raw.workforce(workforce_record_id varchar);
create table if not exists raw.outcomes(admission_id varchar);
