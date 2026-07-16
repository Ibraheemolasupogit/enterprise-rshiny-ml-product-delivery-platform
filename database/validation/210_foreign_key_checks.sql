select 'diagnosis_orphan_keys' as check_name, count(*) as failing_rows
from staged.diagnoses d
left join staged.admissions a on a.admission_id = d.admission_id
where a.admission_id is null;
