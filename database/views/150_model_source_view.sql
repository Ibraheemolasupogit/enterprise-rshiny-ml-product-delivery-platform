create or replace view curated.model_source_view as
select
  p.admission_id,
  p.patient_id,
  p.admission_datetime,
  p.admission_date,
  p.admission_type,
  p.source_of_admission,
  p.ward_id,
  p.initial_news2_score,
  p.mobility_status,
  p.age,
  p.sex,
  p.postcode_region,
  p.deprivation_decile,
  p.comorbidity_count,
  p.previous_admissions_12m,
  d.primary_diagnosis_group,
  d.primary_diagnosis_complexity,
  d.diagnosis_count,
  o.operational_context_available,
  oc.length_of_stay_days_governed,
  oc.long_stay_flag_governed,
  true as eligibility_flag,
  'eligible' as exclusion_reason
from curated.patient_admission_view p
left join curated.admission_diagnosis_summary d on d.admission_id = p.admission_id
left join curated.admission_operational_context o on o.admission_id = p.admission_id
left join curated.outcome_context_view oc on oc.admission_id = p.admission_id;
