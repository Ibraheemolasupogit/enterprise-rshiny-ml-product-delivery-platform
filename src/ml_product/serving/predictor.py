"""Prediction orchestration."""

from __future__ import annotations

from ml_product.modelling.prediction import predict_probability
from ml_product.serving.config import ServingConfig
from ml_product.serving.explanations import explanation_summary
from ml_product.serving.loader import LoadedModel
from ml_product.serving.preprocessing import transform_request
from ml_product.serving.risk_bands import risk_band
from ml_product.serving.schemas import (
    ExplanationPayload,
    ModelPayload,
    PredictionPayload,
    PredictionRequest,
    PredictionResponse,
    RequestPayload,
)


def score_request(
    *,
    request: PredictionRequest,
    loaded: LoadedModel,
    config: ServingConfig,
    request_id: str,
) -> PredictionResponse:
    features = transform_request(request, loaded.preprocessor_metadata)
    probability = float(predict_probability(loaded.model, features)[0])
    calibrated = float(loaded.calibrator.transform([probability])[0])
    threshold = loaded.version.threshold
    predicted = calibrated >= threshold
    approval_status = (
        "pending"
        if loaded.version.approval_decision is None
        else loaded.version.approval_decision.decision
    )
    activation_status = "active" if loaded.version.status == "active" else "inactive"
    statuses = []
    if loaded.review_mode:
        statuses = ["review_mode", "unapproved_model", "not_for_operational_use"]
    return PredictionResponse(
        prediction=PredictionPayload(
            long_stay_probability=calibrated,
            predicted_long_stay=bool(predicted),
            risk_band=risk_band(calibrated, config),
        ),
        model=ModelPayload(
            model_name=loaded.version.model_name,
            registry_version=loaded.version.registry_version,
            candidate_identifier=loaded.version.candidate_identifier,
            model_family=loaded.version.model_family,
            calibration=loaded.version.calibration,
            threshold=threshold,
            approval_status=approval_status,
            activation_status=activation_status,
        ),
        explanation=ExplanationPayload(
            method="registered_global_and_local_summary",
            important_factors=explanation_summary(loaded.feature_importance),
            warning="Associations only; this is not causal or clinical advice.",
        ),
        limitations=[
            "Synthetic-data decision-support prototype",
            "Not clinical advice",
            "Not for operational use" if loaded.review_mode else "Requires approved active model",
        ],
        request=RequestPayload(
            request_id=request_id,
            review_mode=loaded.review_mode,
            status=statuses,
        ),
    )
