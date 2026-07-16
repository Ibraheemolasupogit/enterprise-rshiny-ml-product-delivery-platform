create or replace view curated.admission_diagnosis_summary as
select
  admission_id,
  max(case when primary_diagnosis_flag then diagnosis_group end) as primary_diagnosis_group,
  max(case when primary_diagnosis_flag then diagnosis_complexity end) as primary_diagnosis_complexity,
  count(*) as diagnosis_count,
  sum(case when primary_diagnosis_flag then 0 else 1 end) as secondary_diagnosis_count,
  max(diagnosis_quality_status) as diagnosis_quality_status
from staged.diagnoses
group by admission_id;
