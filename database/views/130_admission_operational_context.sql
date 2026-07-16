create or replace view curated.admission_operational_context as
select
  p.admission_id,
  p.ward_id,
  p.admission_date,
  o.record_date as context_record_date,
  case when o.record_date is null then 'unmatched' else 'exact_date' end as context_match_type,
  o.record_date is not null as operational_context_available,
  o.occupancy_rate,
  o.staff_to_bed_ratio,
  o.capacity_quality_status,
  o.workforce_quality_status
from curated.patient_admission_view p
left join curated.daily_ward_operational_context o
  on o.ward_id = p.ward_id and o.record_date = p.admission_date;
