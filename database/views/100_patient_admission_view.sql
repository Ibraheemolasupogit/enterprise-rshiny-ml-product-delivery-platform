create or replace view curated.patient_admission_view as
select
  a.admission_id,
  a.patient_id,
  a.admission_datetime,
  a.admission_date,
  a.admission_type,
  a.source_of_admission,
  a.ward_id,
  a.initial_news2_score,
  a.mobility_status,
  p.age,
  p.sex,
  p.postcode_region,
  p.deprivation_decile,
  p.comorbidity_count,
  p.previous_admissions_12m,
  p.patient_quality_status,
  a.admission_quality_status
from staged.admissions a
join staged.patients p on p.patient_id = a.patient_id;
