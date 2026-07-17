create or replace view curated.patient_admission_view as
with trusted_patients as (
  select distinct on (patient_id) *
  from staged.patients
  where patient_id not in (
    select record_identifier from quality.rejected_records where issue_type = 'duplicate_patient'
  )
  order by patient_id, _source_row_number
),
trusted_admissions as (
  select distinct on (admission_id) *
  from staged.admissions
  where admission_id not in (
    select record_identifier from quality.rejected_records where issue_type = 'duplicate_admission'
  )
  order by admission_id, _source_row_number
)
select a.admission_id, a.patient_id, a.admission_datetime, a.admission_date,
       a.admission_type, a.source_of_admission, a.ward_id, a.initial_news2_score,
       a.mobility_status, p.age, p.sex, p.postcode_region, p.deprivation_decile,
       p.comorbidity_count, p.previous_admissions_12m,
       p.patient_quality_status, a.admission_quality_status
from trusted_admissions a
join trusted_patients p on p.patient_id = a.patient_id;

create or replace view curated.admission_diagnosis_summary as
with trusted_diagnoses as (
  select d.*
  from staged.diagnoses d
  where d.diagnosis_id not in (
    select record_identifier from quality.rejected_records where issue_type = 'orphan_diagnosis'
  )
)
select admission_id,
       max(case when primary_diagnosis_flag then diagnosis_group end) as primary_diagnosis_group,
       max(case when primary_diagnosis_flag then diagnosis_complexity end) as primary_diagnosis_complexity,
       count(*)::integer as diagnosis_count,
       sum(case when primary_diagnosis_flag then 0 else 1 end)::integer as secondary_diagnosis_count,
       case when sum(case when diagnosis_quality_status != 'trusted' then 1 else 0 end) > 0
            then 'intentional_quality_fixture' else 'trusted' end as diagnosis_quality_status
from trusted_diagnoses
group by admission_id;

create or replace view curated.daily_ward_operational_context as
select c.ward_id, c.record_date, c.staffed_beds, c.occupied_beds, c.closed_beds,
       c.isolation_capacity, w.registered_nurses, w.support_workers, w.medical_staff,
       w.agency_hours,
       case when w.workforce_quality_status = 'intentional_quality_fixture'
            then null else w.vacancy_rate end as vacancy_rate,
       case when c.staffed_beds = 0 then null
            else c.occupied_beds::double precision / c.staffed_beds end as occupancy_rate,
       case when c.staffed_beds = 0 then null
            else (w.registered_nurses + w.support_workers + w.medical_staff)::double precision
                 / c.staffed_beds end as staff_to_bed_ratio,
       c.capacity_quality_status, w.workforce_quality_status
from staged.ward_capacity c
join staged.workforce w on w.ward_id = c.ward_id and w.record_date = c.record_date;

create or replace view curated.admission_operational_context as
select p.admission_id, p.ward_id, p.admission_date,
       o.record_date as context_record_date,
       case when o.record_date is null then 'unmatched' else 'exact_date' end as context_match_type,
       o.record_date is not null as operational_context_available,
       o.staffed_beds, o.occupied_beds, o.closed_beds, o.isolation_capacity,
       o.registered_nurses, o.support_workers, o.medical_staff, o.agency_hours,
       o.vacancy_rate, o.occupancy_rate, o.staff_to_bed_ratio,
       o.capacity_quality_status, o.workforce_quality_status
from curated.patient_admission_view p
left join curated.daily_ward_operational_context o
  on o.ward_id = p.ward_id and o.record_date = p.admission_date;

create or replace view curated.outcome_context_view as
select admission_id, discharge_datetime, length_of_stay_days_source,
       long_stay_flag_source, length_of_stay_days_governed, long_stay_flag_governed,
       readmission_30d, discharge_destination, outcome_quality_status
from staged.outcomes;

create or replace view curated.model_source_view as
select p.admission_id, p.patient_id, p.admission_datetime, p.admission_date,
       p.admission_type, p.source_of_admission, p.ward_id, p.initial_news2_score,
       p.mobility_status, p.age, p.sex, p.postcode_region, p.deprivation_decile,
       p.comorbidity_count, p.previous_admissions_12m,
       d.primary_diagnosis_group, d.primary_diagnosis_complexity,
       d.diagnosis_count, d.secondary_diagnosis_count,
       o.operational_context_available, o.context_match_type,
       o.occupancy_rate, o.staff_to_bed_ratio, o.capacity_quality_status,
       o.workforce_quality_status,
       oc.discharge_datetime, oc.length_of_stay_days_source,
       oc.long_stay_flag_source, oc.length_of_stay_days_governed,
       oc.long_stay_flag_governed, oc.readmission_30d, oc.discharge_destination,
       p.patient_quality_status, p.admission_quality_status, d.diagnosis_quality_status,
       oc.outcome_quality_status,
       case when d.admission_id is null then false
            when oc.admission_id is null then false
            when o.operational_context_available is false then false
            else true end as eligibility_flag,
       case when d.admission_id is null then 'missing_diagnosis_summary'
            when oc.admission_id is null then 'missing_outcome'
            when o.operational_context_available is false then 'missing_operational_context'
            else 'eligible' end as exclusion_reason,
       coalesce((select dataset_version from quality.ingestion_runs limit 1), '') as dataset_version,
       coalesce((select build_id from quality.ingestion_runs limit 1), '') as build_identifier
from curated.patient_admission_view p
left join curated.admission_diagnosis_summary d on d.admission_id = p.admission_id
left join curated.admission_operational_context o on o.admission_id = p.admission_id
left join curated.outcome_context_view oc on oc.admission_id = p.admission_id;
