# Feature Engineering

Milestone 5 builds deterministic admission-time feature datasets from `curated.model_source_view` through the governed logical-view client. The source provider remains `denodo_compatible_local`, backed by DuckDB, and no raw source tables are queried by the feature package.

The prediction point is shortly after admission. The unit of analysis is one inpatient admission. The target is `long_stay_flag_governed`, defined from the governed reference outcome `length_of_stay_days >= 7`. The length-of-stay fields, discharge fields, readmission fields, and governed target fields are evaluation or lineage fields only and are excluded from predictors.

Eligibility uses the governed `eligibility_flag`, target completeness, and unique admission grain. Excluded rows are counted and reported in `reports/model_evaluation/exclusion_summary.json`; no row is silently dropped. The current governed source contains only eligible model-source rows, so the exclusion evidence records zero excluded rows for the committed sample build.

Configured predictors include demographic, admission, diagnosis, and operational context columns available at or shortly after admission. Admission-time derivations are `admission_hour`, `admission_day_of_week`, `weekend_admission`, `admission_month`, and `admission_season`. These are derived from `admission_datetime`; `discharge_datetime` is never used.

Preprocessing is fitted only on the training split. Numeric predictors use median imputation and standard scaling. Categorical predictors use an explicit `__missing__` category and one-hot encoding with unknown categories ignored in validation and test. Boolean predictors use training-split mode imputation and integer encoding. Missingness indicators are emitted where configured.

Outputs are written under the ignored directory `data/processed/features` in Parquet and CSV form. Committed evidence is limited to small JSON and Markdown files in `reports/model_evaluation`. The feature build records source, configuration, split, output, and preprocessing fingerprints to support reproducibility without committing generated datasets.
