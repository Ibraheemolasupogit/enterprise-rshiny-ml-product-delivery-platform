-- Staged tables are typed by the build pipeline. This file documents their stable names.
create table if not exists staged.patients(patient_id varchar, patient_quality_status varchar);
create table if not exists staged.admissions(admission_id varchar, admission_quality_status varchar);
create table if not exists staged.diagnoses(diagnosis_id varchar, diagnosis_quality_status varchar);
create table if not exists staged.ward_capacity(ward_id varchar, capacity_quality_status varchar);
create table if not exists staged.workforce(workforce_record_id varchar, workforce_quality_status varchar);
create table if not exists staged.outcomes(admission_id varchar, outcome_quality_status varchar);
