# Prediction Contract

The Milestone 5 prediction contract is admission-time decision support for inpatient operational flow. The intended decision is early prioritisation of discharge planning, capacity review, or operational coordination for admissions that may become long stays. It is not a clinical diagnosis, treatment recommendation, eligibility decision, or automated action.

The unit of analysis is an admission. The prediction point is shortly after admission, using information that is available at admission or initial assessment. The target is `long_stay_flag_governed`, with positive class `true`, defined as governed length of stay greater than or equal to seven days.

The eligible population is the governed model-source view after Milestone 3 quality reconciliation and eligibility controls. Each eligible row must have a unique `admission_id`, a `patient_id`, a non-missing target, and a valid admission timestamp. Ineligible or target-missing records are retained in exclusion evidence.

Permitted predictors include age, sex, postcode region, deprivation decile, comorbidity count, previous admissions, admission type, source of admission, initial NEWS2 score, mobility status, diagnosis summary fields, occupancy rate, staff-to-bed ratio, and admission-time date derivations.

Excluded outcome fields include discharge timestamp, source and governed length of stay, source and governed long-stay flags, readmission status, discharge destination, outcome quality status, direct identifiers, lineage fields, and future outcome derivatives. The contract is non-causal and should not be used to infer that changing a predictor will change length of stay.
