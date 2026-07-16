create table if not exists metadata.controlled_vocabularies(
  vocabulary_name varchar,
  allowed_value varchar
);
insert into metadata.controlled_vocabularies values
  ('admission_type', 'emergency'),
  ('admission_type', 'urgent'),
  ('admission_type', 'planned'),
  ('mobility_status', 'independent'),
  ('mobility_status', 'assisted'),
  ('mobility_status', 'limited'),
  ('mobility_status', 'bedbound');
