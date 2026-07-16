# Entity Linking

Milestone 3 uses deterministic source identifiers only. It does not implement probabilistic person matching, fuzzy matching, or identity resolution.

## Rules

Patients link to admissions through `patient_id`. Admissions link to diagnoses and outcomes through `admission_id`. Admissions link to operational context through `ward_id + DATE(admission_datetime)`.

The default operational-context rule uses exact same-day matching. It does not silently use future observations. If a future fallback is added, it must be explicitly configured and reported.

## Duplicate and Unmatched Records

Duplicate patient and admission identifiers are detected and recorded. Orphan diagnoses are quarantined. Linkage quality evidence is written under `reports/data_quality/linkage_quality.json`.
