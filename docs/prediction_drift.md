# Prediction Drift

Prediction drift monitoring compares the distribution of model probabilities, positive prediction rates and risk-band proportions between the baseline and current synthetic window. This is useful for identifying operational movement in score outputs even when current labels are not yet available.

Prediction drift is not model performance drift. Without outcome labels it cannot say whether precision, recall, calibration or discrimination have degraded. The Milestone 11 evidence therefore records `performance_claim` as `not_performance_without_labels` and directs users toward labelled performance monitoring before any model-change proposal.

Prediction drift can raise warning or critical alerts. Those alerts request review only. They never alter the model threshold, never recalibrate probabilities, never retrain, and never replace the registered candidate.
