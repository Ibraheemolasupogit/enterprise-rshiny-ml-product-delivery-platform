# User Journeys

## Single-Patient Risk Review

Future milestone. A discharge-planning user opens the R-Shiny product, selects a synthetic admission, reviews risk context, checks explanatory information, and records whether the signal was useful. Milestone 1 only documents this journey.

## Cohort-Scoring Journey

Future milestone. An operational flow manager reviews a cohort of synthetic admissions, filters by ward or pathway, and uses decision-support signals to prioritise follow-up. The system must present risk as support for human judgement, not an instruction.

## User-Feedback Journey

Future milestone. Users record feedback about usefulness, false positives, missing context, and operational outcome. Feedback will later be stored in a controlled local feedback database and used in monitoring review.

## Monitoring-Review Journey

Future milestone. Data scientists, QA, and service support review data quality, drift, model-performance indicators, and user feedback. Any alert must be traceable to synthetic data and documented thresholds.

## Controlled Model-Retraining Journey

Future milestone. A data scientist proposes retraining, validates evidence, documents expected impact, seeks human approval, and promotes only after governance review. Automated promotion is out of scope.

## Incident and Rollback Journey

Future milestone. Service support identifies an issue, records impact, escalates to product and platform owners, rolls back to the last approved model or service version, and captures evidence for handover.
