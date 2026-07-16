# Data Dictionary

Milestone 2 implements deterministic synthetic source systems only. The data is generated, not extracted from real systems, and is unsuitable for clinical or operational use.

Identifier formats are deterministic and synthetic: `PAT-000001`, `ADM-000001`, `DIA-000001`, `WARD-01`, and `WRK-000001`. Dates use ISO 8601 strings. Booleans are represented as `true` or `false` in metadata and as standard CSV/Parquet boolean values where supported. `long_stay_flag` is defined as `length_of_stay_days >= 7`.

Controlled quality fixtures are documented in `data/sample/data_quality_issues.json`. Clean generation mode disables intentional defects.

## patients

| Field | Type | Nullable | Description | Example | Allowed values or range | Primary key | Foreign key | Synthetic note | Quality rule |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| patient_id | string | No | Synthetic patient source identifier. | PAT-000001 | `PAT-` plus six digits | Yes | None | Not NHS-number-like. | Unique in clean data. |
| age | integer | No | Synthetic age in years. | 72 | 18 to 98 | No | None | Bounded synthetic range. | Must remain in range. |
| sex | string | No | Small demographic category. | female | female, male, not_specified | No | None | No names or identity fields. | Controlled vocabulary. |
| postcode_region | string | No | Fictional broad region code. | SR-NORTH | SR-NORTH, SR-SOUTH, SR-EAST, SR-WEST, SR-CENTRAL | No | None | Not a full real postcode. | Controlled vocabulary. |
| deprivation_decile | integer | Yes | Synthetic relative deprivation decile. | 4 | 1 to 10 | No | None | Broad synthetic socioeconomic indicator. | May be missing only as documented fixture. |
| comorbidity_count | integer | No | Synthetic count-like acuity context. | 2 | 0 to 8 | No | None | Not a clinical coding field. | Non-negative. |
| previous_admissions_12m | integer | No | Synthetic prior-admission count. | 1 | 0 to 6 | No | None | Generated relationship to comorbidity. | Non-negative. |

## admissions

| Field | Type | Nullable | Description | Example | Allowed values or range | Primary key | Foreign key | Synthetic note | Quality rule |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| admission_id | string | No | Synthetic admission identifier. | ADM-000001 | `ADM-` plus six digits | Yes | None | Not a real encounter identifier. | Unique in clean data. |
| patient_id | string | No | Patient source identifier. | PAT-000001 | Existing patient_id | No | patients.patient_id | Preserves source relationship only. | Must resolve unless documented fixture. |
| admission_datetime | datetime | No | Synthetic admission timestamp. | 2025-01-07T14:30 | Configured date range | No | None | Not extracted from a real hospital. | Within source range. |
| admission_type | string | No | Admission route category. | emergency | emergency, urgent, planned | No | None | Broad operational category. | Controlled vocabulary. |
| source_of_admission | string | No | Synthetic admission source. | home | home, clinic, transfer, care_facility | No | None | Broad source only. | Controlled vocabulary. |
| ward_id | string | No | Initial ward allocation. | WARD-01 | Configured ward IDs | No | ward_capacity.ward_id and workforce.ward_id | Synthetic ward only. | Must resolve. |
| initial_news2_score | integer | No | Synthetic initial acuity score. | 5 | 0 to 20 | No | None | Non-clinical simulation value. | Must remain in range. |
| mobility_status | string | Yes | Synthetic mobility category. | assisted | independent, assisted, limited, bedbound | No | None | Broad generated category. | May be missing only as documented fixture. |

## diagnoses

| Field | Type | Nullable | Description | Example | Allowed values or range | Primary key | Foreign key | Synthetic note | Quality rule |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| diagnosis_id | string | No | Synthetic diagnosis row identifier. | DIA-000001 | `DIA-` plus six digits | Yes | None | Not a clinical code. | Unique. |
| admission_id | string | No | Admission identifier. | ADM-000001 | Existing admission_id | No | admissions.admission_id | Maintains source relationship. | Must resolve unless documented orphan fixture. |
| diagnosis_group | string | No | Broad synthetic diagnosis group. | respiratory_synthetic | respiratory_synthetic, cardiovascular_synthetic, frailty_synthetic, infection_synthetic, surgical_synthetic, other_synthetic | No | None | No detailed clinical coding. | Controlled vocabulary. |
| diagnosis_complexity | string | No | Broad complexity category. | moderate | low, moderate, high | No | None | Generated context only. | Controlled vocabulary. |
| primary_diagnosis_flag | boolean | No | Marks primary broad diagnosis per admission. | true | true, false | No | None | No clinical coding inference. | Exactly one primary diagnosis per clean admission. |

## ward_capacity

| Field | Type | Nullable | Description | Example | Allowed values or range | Primary key | Foreign key | Synthetic note | Quality rule |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ward_id | string | No | Synthetic ward identifier. | WARD-01 | `WARD-` plus two digits | Yes with record_date | None | Not a real ward. | Must match admissions and workforce. |
| record_date | date | No | Daily capacity date. | 2025-01-01 | Configured date range | Yes with ward_id | None | Daily generated record. | Required for each ward/date. |
| staffed_beds | integer | No | Synthetic staffed bed count. | 28 | Positive integer | No | None | Operational simulation only. | Must be positive. |
| occupied_beds | integer | No | Synthetic occupied bed count. | 24 | Normally 0 to staffed_beds | No | None | Capacity pressure signal. | May exceed staffed beds only as documented fixture. |
| closed_beds | integer | No | Synthetic closed bed count. | 1 | 0 or greater | No | None | Generated operational context. | Non-negative. |
| isolation_capacity | integer | No | Synthetic isolation capacity. | 3 | 0 or greater | No | None | Generated operational context. | Non-negative. |

## workforce

| Field | Type | Nullable | Description | Example | Allowed values or range | Primary key | Foreign key | Synthetic note | Quality rule |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| workforce_record_id | string | No | Synthetic workforce record identifier. | WRK-000001 | `WRK-` plus six digits | Yes | None | Ward-level only; no personnel records. | Unique. |
| ward_id | string | No | Synthetic ward identifier. | WARD-01 | Configured ward IDs | No | ward_capacity.ward_id | No real staffing unit. | Must resolve. |
| record_date | date | No | Workforce record date. | 2025-01-01 | Configured date range | No | None | Daily generated record. | Required. |
| registered_nurses | integer | No | Ward-level registered nurse count. | 8 | 0 or greater | No | None | No staff identities. | Non-negative. |
| support_workers | integer | No | Ward-level support worker count. | 6 | 0 or greater | No | None | No staff identities. | Non-negative. |
| medical_staff | integer | No | Ward-level medical staff count. | 3 | 0 or greater | No | None | No staff identities. | Non-negative. |
| agency_hours | number | No | Synthetic agency hours. | 7.25 | 0 or greater | No | None | Generated staffing pressure. | Non-negative. |
| vacancy_rate | number | No | Synthetic vacancy-rate estimate. | 0.08 | Normally 0.0 to 1.0 | No | None | Generated staffing pressure. | May exceed range only as documented fixture. |

## outcomes

| Field | Type | Nullable | Description | Example | Allowed values or range | Primary key | Foreign key | Synthetic note | Quality rule |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| admission_id | string | No | Admission identifier. | ADM-000001 | Existing admission_id | Yes | admissions.admission_id | One outcome per clean admission. | Must resolve unless documented fixture. |
| discharge_datetime | datetime | No | Synthetic discharge timestamp. | 2025-01-09T10:30 | Later than admission_datetime | No | None | Generated outcome only. | Must follow admission unless documented fixture. |
| length_of_stay_days | integer | No | Derived synthetic stay length. | 8 | 1 to 28 | No | None | Derived from generation logic. | Must be positive and consistent. |
| long_stay_flag | boolean | No | Target-style outcome flag. | true | `length_of_stay_days >= 7` | No | None | Future modelling target, not a feature. | May be inconsistent only as documented fixture. |
| readmission_30d | boolean | No | Synthetic 30-day readmission flag. | false | true, false | No | None | Generated outcome only. | Boolean. |
| discharge_destination | string | No | Synthetic broad destination. | home_with_support | home, home_with_support, community_rehab, care_facility, transfer | No | None | Broad operational category. | Controlled vocabulary. |

## Known Intentional Quality Issues

The committed sample includes missing deprivation decile, missing mobility status, duplicate patient row, duplicate admission row, orphan diagnosis, inconsistent long-stay flag, occupied beds over capacity, and vacancy rate outside range. Each is listed in `data/sample/data_quality_issues.json` with an issue identifier, dataset, issue type, affected identifier, expected rule, injected value summary, seed, and intentional flag.
