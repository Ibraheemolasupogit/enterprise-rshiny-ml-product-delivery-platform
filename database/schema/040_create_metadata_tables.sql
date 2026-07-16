create table if not exists metadata.datasets(dataset_name varchar, row_count integer, column_count integer);
create table if not exists metadata.columns(dataset_name varchar, column_name varchar);
create table if not exists metadata.relationships(child_object varchar, parent_object varchar, join_rule varchar);
create table if not exists metadata.generation_manifest(manifest_json varchar);
create table if not exists metadata.database_builds(
  build_id varchar,
  source_fingerprint varchar,
  dataset_version varchar,
  engine varchar,
  provider varchar
);
create table if not exists metadata.logical_views(view_name varchar, source_objects varchar);
