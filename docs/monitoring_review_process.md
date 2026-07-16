# Monitoring Review Process

The Milestone 11 review process begins when monitoring evidence is generated or refreshed. Reviewers inspect the summary, section reports and alerts, then decide whether data quality, distribution movement, labelled performance, calibration or service health needs follow-up.

The review outcome can be `no_action_required`, `review_required` or a similarly bounded advisory disposition. It cannot approve, activate, retire, roll back or replace a model. It cannot change the registry, serving threshold, calibration method or deployment state.

Recommended next steps are written as human-readable guidance in `monitoring_review.json`. The guidance is intentionally conservative: investigate evidence, compare labelled outcomes when available, document findings, and raise a separate governance or retraining proposal only when a future controlled workflow exists.
