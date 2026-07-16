create or replace view curated.outcome_context_view as
select
  admission_id,
  discharge_datetime,
  length_of_stay_days_source,
  long_stay_flag_source,
  length_of_stay_days_governed,
  long_stay_flag_governed,
  readmission_30d,
  discharge_destination,
  outcome_quality_status
from staged.outcomes;
