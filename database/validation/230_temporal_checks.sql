select 'discharge_before_admission' as check_name, count(*) as failing_rows
from staged.outcomes o
join staged.admissions a on a.admission_id = o.admission_id
where o.discharge_datetime <= a.admission_datetime;
