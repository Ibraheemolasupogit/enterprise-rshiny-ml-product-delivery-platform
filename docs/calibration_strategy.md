# Calibration Strategy

Milestone 6 compares uncalibrated probabilities, sigmoid calibration, and isotonic calibration eligibility. Calibration is fitted using validation data only after the base model is fitted on training data. Test data is never used to fit calibration.

Isotonic calibration is blocked when the validation set has fewer rows than the configured minimum. The current validation split has 23 rows and the configured minimum is 100, so isotonic is recorded as ineligible. Sigmoid calibration is eligible and is selected only when validation Brier score does not materially worsen relative to the uncalibrated model.

Calibration evidence is written to `reports/model_evaluation/calibration_report.json`.
