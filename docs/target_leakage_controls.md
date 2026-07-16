# Target Leakage Controls

Milestone 5 implements explicit leakage controls before feature outputs are written. The checks combine configuration validation, a prohibited predictor registry, admission-time derivation boundaries, and output validation.

Direct leakage is controlled by rejecting `long_stay_flag_governed`, `long_stay_flag_source`, `length_of_stay_days_governed`, and `length_of_stay_days_source` as predictors. Temporal leakage is controlled by rejecting `discharge_datetime`, discharge destination, readmission status, and outcome quality fields. Identifier leakage is controlled by excluding `admission_id` and `patient_id` from the transformed feature matrix.

Group leakage is addressed by patient-group splitting. A patient can appear in only one of train, validation, or test, and the split summary records patient and admission overlap counts. Training/validation/test contamination is further reduced by fitting preprocessing state only on training rows.

The committed leakage report is `reports/model_evaluation/leakage_report.json`. For the Milestone 5 build it records zero direct, temporal, identifier, and group leakage violations. Known limitations remain: the local data is synthetic, small, and generated for product demonstration, so leakage controls prove implementation behaviour rather than real-world clinical validity.
