# Denodo Developer Tier Artefacts

These artefacts define the Milestone 14.2 governed virtual-view layer over the local PostgreSQL datastore. They are source-controlled setup guidance, not proof that a live Denodo environment was executed.

## Naming Convention

PostgreSQL base views use `bv_pg_<schema>_<object>`. Governed derived views use the contract names under the logical `curated` namespace:

- `curated.patient_admission_view`
- `curated.admission_diagnosis_summary`
- `curated.daily_ward_operational_context`
- `curated.admission_operational_context`
- `curated.outcome_context_view`
- `curated.model_source_view`

## Files

- `vql/010_postgresql_datasource.vql`: PostgreSQL source connection template.
- `vql/020_base_views.vql`: base-view mapping over PostgreSQL tables/views.
- `vql/030_governed_virtual_views.vql`: derived/joined governed view definitions.

## Provenance And Access Control

The source system is the local PostgreSQL Milestone 14.1 datastore. Denodo should expose read-only governed virtual views to feature-pipeline users. Write privileges remain outside Denodo for this milestone. No SAS Viya, cloud deployment, model approval, feedback workflow, staging, or production release is introduced here.

