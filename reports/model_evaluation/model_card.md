# Model Card

## Model Purpose
Synthetic admission-time long-stay risk decision-support candidate.

## Intended Users
Data scientists, analysts, governance reviewers, and future operational product teams.

## Intended Use
Portfolio evidence for model-development workflow on synthetic data.

## Out-of-Scope Use
Clinical diagnosis, automated care decisions, production scoring, or real patient use.

## Synthetic-Data Statement
All training and evaluation data are synthetic.

## Prediction Point
Shortly after admission.

## Target Definition
`long_stay_flag_governed`, length of stay greater than or equal to seven days.

## Candidate Models
Prevalence baseline, majority baseline, logistic regression, Random Forest, XGBoost.

## Selection Rule
Validation-only comparison using recall, probability quality, threshold cost, and simplicity. Test metrics do not influence selection.

Recommended model: `xgboost`
Selected calibration: `sigmoid`
Selected threshold: `0.75`

## Limitations
Small synthetic splits, high positive prevalence, unstable subgroup estimates, and non-causal explainability evidence.

## Required Status
Model registration: implemented locally; candidate registered for governance review
Model serving: implemented locally; not ready without approved active model
R-Shiny integration: implemented locally as a FastAPI review-mode client
Production approval: not granted
Deployment: not performed
Denodo integration: externally blocked and not implemented
SAS Viya integration: externally blocked and not implemented
