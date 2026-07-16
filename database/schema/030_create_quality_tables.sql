create table if not exists quality.data_quality_issues(
  issue_id varchar,
  dataset varchar,
  issue_type varchar,
  record_identifier varchar,
  column varchar,
  treatment varchar
);
create table if not exists quality.rejected_records(
  issue_id varchar,
  dataset varchar,
  issue_type varchar,
  record_identifier varchar,
  column varchar,
  treatment varchar,
  rejection_category varchar
);
create table if not exists quality.validation_results(
  validation_name varchar,
  validation_status varchar,
  observed_count integer,
  expected_count integer,
  details varchar
);
create table if not exists quality.ingestion_runs(
  build_id varchar,
  dataset_version varchar,
  configuration_fingerprint varchar,
  engine varchar,
  provider varchar,
  evidence_label varchar
);
