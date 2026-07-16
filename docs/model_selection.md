# Model Selection

Candidate recommendation is validation-led. A candidate must meet minimum recall, have probability quality no worse than the prevalence baseline, and produce valid deterministic outputs. When performance differences are small, the simpler model is preferred.

The current Milestone 6 evidence recommends XGBoost for registration review after the OpenMP remediation allowed the official XGBoost candidate to train successfully. This changed the recommendation from the earlier logistic-regression fallback evidence while preserving the same validation-only selection rule.

The recommendation status is `recommended_for_registration_review` only. It is not approval, registration, serving, deployment, or production readiness. Milestone 7 may use the evidence for registry and serving work, but that work is not implemented here.
