# Model Evaluation Report

Milestone 6 trains deterministic candidate models on Milestone 5 feature outputs.
The test set is evaluated only after validation-led model and threshold selection.

Recommended candidate: `xgboost`
Recommendation status: `recommended_for_registration_review`
Selected threshold: `0.75`

Accuracy is reported but is not used as the primary selection metric because the positive class is highly prevalent in the synthetic data.

No model registration, serving, R-Shiny integration, production approval, or deployment is implemented in this milestone.
