create table if not exists quality.data_quality_issues (
  issue_id text,
  dataset text,
  issue_type text,
  record_identifier text,
  column_name text,
  expected_rule text,
  injected_value_summary text,
  seed integer,
  intentional boolean,
  treatment text
);

create table if not exists quality.rejected_records (
  issue_id text,
  dataset text,
  issue_type text,
  record_identifier text,
  column_name text,
  treatment text,
  rejection_category text
);

create table if not exists quality.ingestion_runs (
  build_id text,
  dataset_version text,
  configuration_fingerprint text,
  engine text,
  provider text,
  evidence_label text
);

create table if not exists quality.validation_results (
  validation_name text,
  validation_status text,
  observed_count integer,
  expected_count integer,
  details text
);

create table if not exists metadata.generation_manifest (
  manifest_json text
);

create table if not exists metadata.database_builds (
  build_id text,
  source_fingerprint text,
  dataset_version text,
  engine text,
  provider text
);

create table if not exists metadata.logical_views (
  view_name text,
  source_objects text
);

create table if not exists metadata.datasets (
  dataset_name text,
  row_count integer,
  column_count integer
);

create table if not exists metadata.columns (
  dataset_name text,
  column_name text
);

create table if not exists metadata.relationships (
  child_object text,
  parent_object text,
  join_rule text
);

