create or replace view curated.daily_ward_operational_context as
select
  c.ward_id,
  c.record_date,
  c.staffed_beds,
  c.occupied_beds,
  c.closed_beds,
  c.isolation_capacity,
  w.registered_nurses,
  w.support_workers,
  w.medical_staff,
  w.agency_hours,
  w.vacancy_rate,
  case when c.staffed_beds = 0 then null else c.occupied_beds::double / c.staffed_beds end as occupancy_rate,
  case when c.staffed_beds = 0 then null else (w.registered_nurses + w.support_workers + w.medical_staff)::double / c.staffed_beds end as staff_to_bed_ratio,
  c.capacity_quality_status,
  w.workforce_quality_status
from staged.ward_capacity c
join staged.workforce w on w.ward_id = c.ward_id and w.record_date = c.record_date;
