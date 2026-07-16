# Model Explainability

Milestone 6 produces global and local explanation evidence. Logistic regression evidence includes coefficients, odds ratios, direction of association, and absolute coefficient ranking. Tree evidence includes native feature importance where available and permutation importance on validation data. XGBoost evidence includes both validation-set permutation importance and native gain importance with stable transformed feature names.

Local explanations are deterministic synthetic examples: highest predicted risk, lowest predicted risk, near-threshold case, and available false-positive or false-negative examples. Explanations use synthetic admission and patient identifiers only.

All explainability evidence is non-causal. One-hot encoded and correlated features can split importance across related columns, and small validation/test sets make stability limited.
