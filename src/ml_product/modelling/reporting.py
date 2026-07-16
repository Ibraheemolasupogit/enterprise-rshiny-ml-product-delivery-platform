"""Markdown reports for Milestone 6 model development."""

from __future__ import annotations

from typing import Any


def evaluation_report(payload: dict[str, Any]) -> str:
    recommendation = payload["candidate_recommendation"]
    selected = recommendation["recommended_model"] or "none"
    return "\n".join(
        [
            "# Model Evaluation Report",
            "",
            "Milestone 6 trains deterministic candidate models on Milestone 5 feature outputs.",
            "The test set is evaluated only after validation-led model and threshold selection.",
            "",
            f"Recommended candidate: `{selected}`",
            f"Recommendation status: `{recommendation['recommendation_status']}`",
            f"Selected threshold: `{recommendation['selected_threshold']}`",
            "",
            "Accuracy is reported but is not used as the primary selection metric because the "
            "positive class is highly prevalent in the synthetic data.",
            "",
            "No model registration, serving, R-Shiny integration, production approval, or "
            "deployment is implemented in this milestone.",
            "",
        ]
    )


def model_card(payload: dict[str, Any]) -> str:
    recommendation = payload["candidate_recommendation"]
    return "\n".join(
        [
            "# Model Card",
            "",
            "## Model Purpose",
            "Synthetic admission-time long-stay risk decision-support candidate.",
            "",
            "## Intended Users",
            "Data scientists, analysts, governance reviewers, and future operational "
            "product teams.",
            "",
            "## Intended Use",
            "Portfolio evidence for model-development workflow on synthetic data.",
            "",
            "## Out-of-Scope Use",
            "Clinical diagnosis, automated care decisions, production scoring, or real "
            "patient use.",
            "",
            "## Synthetic-Data Statement",
            "All training and evaluation data are synthetic.",
            "",
            "## Prediction Point",
            "Shortly after admission.",
            "",
            "## Target Definition",
            "`long_stay_flag_governed`, length of stay greater than or equal to seven days.",
            "",
            "## Candidate Models",
            "Prevalence baseline, majority baseline, logistic regression, Random Forest, XGBoost.",
            "",
            "## Selection Rule",
            "Validation-only comparison using recall, probability quality, threshold cost, and "
            "simplicity. Test metrics do not influence selection.",
            "",
            f"Recommended model: `{recommendation['recommended_model']}`",
            f"Selected calibration: `{recommendation['recommended_calibration']}`",
            f"Selected threshold: `{recommendation['selected_threshold']}`",
            "",
            "## Limitations",
            "Small synthetic splits, high positive prevalence, unstable subgroup estimates, and "
            "non-causal explainability evidence.",
            "",
            "## Required Status",
            "Model registration: implemented locally; candidate registered for governance review",
            "Model serving: implemented locally; not ready without approved active model",
            "R-Shiny integration: implemented locally as a FastAPI review-mode client",
            "Production approval: not granted",
            "Deployment: not performed",
            "Denodo integration: externally blocked and not implemented",
            "SAS Viya integration: externally blocked and not implemented",
            "",
        ]
    )
