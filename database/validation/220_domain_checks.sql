select 'invalid_vacancy_rate' as check_name, count(*) as failing_rows
from staged.workforce
where vacancy_rate < 0 or vacancy_rate > 1;
