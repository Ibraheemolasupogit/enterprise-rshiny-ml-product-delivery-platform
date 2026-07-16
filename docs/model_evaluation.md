# Model Evaluation

The synthetic target has high positive-class prevalence, so accuracy is not sufficient and can be misleading. A majority-positive classifier can look accurate while providing limited operational discrimination. Milestone 6 therefore reports ROC-AUC, PR-AUC, PR-AUC lift over prevalence, precision, recall, specificity, F1, balanced accuracy, Brier score, log loss, calibration error, and weighted operational cost.

PR-AUC is interpreted relative to split prevalence. Probability metrics are included because operational users may rely on calibrated risk bands and thresholds rather than only rank ordering. False negatives and false positives are both shown because they represent different operational costs.

Bootstrap intervals are deterministic and bounded, but the test set is small and synthetic. Performance differences should not be treated as statistically definitive or clinically meaningful.

After resolving the local macOS OpenMP dependency, XGBoost trained through the standard pipeline and was included in validation comparison. The validation-only rule selected XGBoost with sigmoid calibration and threshold `0.75`; the locked test set remained excluded from selection.
