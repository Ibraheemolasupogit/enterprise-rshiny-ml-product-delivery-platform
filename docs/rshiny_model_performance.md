# R-Shiny Model Performance

The Model Performance page reads committed Milestone 6 evidence from `reports/model_evaluation`. It does not recalculate metrics from Shiny usage, feedback, uploads, or live service traffic.

The page compares prevalence baseline, majority baseline, logistic regression, Random Forest, and XGBoost validation evidence. It displays locked test results for the recommended registered candidate, including PR-AUC, ROC-AUC, Brier score, log loss, precision, recall, specificity, F1, balanced accuracy, and the confusion matrix.

Validation and test evidence remain separate. The weak locked test specificity of 0.4 and balanced accuracy near 0.561 are shown as limitations, not hidden.

No monitoring, drift detection, retraining, or live metric recalculation is implemented.
