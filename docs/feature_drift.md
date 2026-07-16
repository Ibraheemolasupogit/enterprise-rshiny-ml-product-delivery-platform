# Feature Drift

Feature drift monitoring compares current synthetic feature distributions with the training baseline. Numeric features use population stability index, Kolmogorov-Smirnov style statistics and a normalised Wasserstein distance. Categorical features use Jensen-Shannon divergence and category coverage checks. Missingness is tracked separately because missing values can drift even when observed distributions look stable.

Drift means the input distribution has moved. It does not prove that the model is performing worse, and it does not authorize retraining. In Milestone 11 drift creates alerts that require human review of data generation, upstream contracts and labelled outcome evidence when available.

Feature drift outputs are stored in `numeric_drift.json`, `categorical_drift.json` and `missingness_drift.json`. The reports contain aggregate metrics, affected feature names and statuses only.
