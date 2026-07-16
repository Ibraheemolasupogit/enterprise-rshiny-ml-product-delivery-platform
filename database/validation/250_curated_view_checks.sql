select 'model_source_duplicate_admissions' as check_name, count(*) as failing_groups
from (
  select admission_id
  from curated.model_source_view
  group by admission_id
  having count(*) > 1
);
