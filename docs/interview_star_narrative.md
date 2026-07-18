# STAR Project Narrative

## Situation

I needed to demonstrate end-to-end ML product delivery for a healthcare operations use case without using real patient data or overstating operational readiness. The challenge was to show enterprise delivery discipline while keeping the repository runnable locally.

## Task

The task was to build a portfolio-ready platform that covers synthetic data generation, governed data access, leakage-safe feature engineering, model evidence, registry governance, serving, R Shiny review workflows, monitoring, retraining, release assurance and optional enterprise lifecycle integrations.

## Actions

I built deterministic synthetic healthcare source systems with data contracts and quality controls. I added DuckDB for the fast local analytical path, then added PostgreSQL and Denodo-compatible governed views to demonstrate an enterprise data foundation without breaking local workflows.

I implemented a provider-neutral logical-view client so the feature pipeline can read the same governed contract through DuckDB, PostgreSQL or Denodo. Feature engineering excludes identifiers, outcomes, discharge fields and post-prediction signals, and it writes reproducible feature metadata and leakage evidence.

I trained baseline and candidate models in Python, selected the candidate using validation evidence only, then locked calibration, threshold and fairness summaries into committed review evidence. I registered the selected XGBoost candidate into a local filesystem registry while preserving approval-pending and inactive state.

I added FastAPI serving with fail-closed operational defaults and labelled local review mode. I built R Shiny review pages for overview, prediction, cohort scoring, model performance, governance, monitoring and retraining evidence without adding governance mutation controls.

I implemented monitoring and retraining as review workflows. They write evidence and recommendations but do not retrain, approve, activate, promote or deploy automatically.

I added a provider-neutral lifecycle boundary for SAS Viya-compatible package, registration, metadata reconciliation, champion-challenger comparison and promotion assessment. I kept SAS Viya optional and mock-tested so CI remains offline-safe. I then added a canonical resumable lifecycle orchestration runner that sequences data, model, lifecycle, serving, monitoring and release gates without bypassing governance.

Finally, I added release assurance, security summaries, SBOM evidence, container contracts and interview documentation so a reviewer can inspect the product coherently in 10-15 minutes.

## Results

The repository now demonstrates a complete synthetic ML product delivery lifecycle. Local validation covers data, features, models, governance, serving, R Shiny, monitoring, retraining, release assurance and lifecycle orchestration. The candidate remains pending and inactive, and operational release remains blocked, which is the intended governance outcome.

## Technical Challenges

The hardest trade-off was balancing enterprise realism with honest local reproducibility. I avoided fabricating Denodo or SAS Viya evidence and used explicit capability statuses. Another challenge was keeping external promotion separate from local activation so lifecycle integration could not accidentally weaken serving governance.

## Trade-Offs

DuckDB remains the default for speed and checkout safety, while PostgreSQL and Denodo provide enterprise integration paths. SAS Viya is a lifecycle provider rather than the modelling engine because model development and evaluation are already reproducible in Python. Monitoring and retraining stay review-only to avoid unsafe automation.

## Lessons Learned

A credible ML product is mostly boundaries and evidence: when data is governed, features are reproducible, model selection is auditable, lifecycle mutations are explicit and release claims are honest, the project is easier to trust and easier to explain.
