# Retraining Governance

Milestone 12 implements controlled retraining review only. The workflow starts from monitoring review evidence, checks eligibility, prepares a governed labelled synthetic dataset, trains challenger candidates, compares them with the registered champion, evaluates gates, and writes a human-review recommendation.

The champion is the current registered comparison model: registry version 1, candidate `CAND-85EA9202CAD6FE7F`, XGBoost, sigmoid calibration and threshold 0.75. Champion does not mean approved, active, deployed or production.

The workflow never automatically approves, activates, deploys, retires, replaces or rolls back a model. Registration for review is a separate explicit command and is blocked unless the recommendation is `recommend_challenger_for_registration_review`.
