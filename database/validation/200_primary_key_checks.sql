select 'raw_patients_duplicate_keys' as check_name, count(*) as failing_groups
from (select patient_id from raw.patients group by patient_id having count(*) > 1);
