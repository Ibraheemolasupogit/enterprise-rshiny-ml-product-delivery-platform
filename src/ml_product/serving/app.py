"""FastAPI app factory for local model scoring."""

from __future__ import annotations

import time
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

from ml_product.registry.config import GovernanceConfig, RegistryConfig
from ml_product.serving.authentication import require_api_key
from ml_product.serving.config import ServingConfig
from ml_product.serving.health import readiness_payload
from ml_product.serving.loader import resolve_model
from ml_product.serving.logging import write_prediction_event
from ml_product.serving.metadata import model_metadata
from ml_product.serving.predictor import score_request
from ml_product.serving.schemas import BatchPredictionRequest, PredictionRequest, PredictionResponse


def create_app(
    serving_config: ServingConfig | None = None,
    registry_config: RegistryConfig | None = None,
    governance_config: GovernanceConfig | None = None,
    *,
    root: Path = Path("."),
) -> FastAPI:
    serving = serving_config or ServingConfig.from_file(root / "config/serving.yaml")
    registry = registry_config or RegistryConfig.from_file(root / "config/model_registry.yaml")
    governance = governance_config or GovernanceConfig.from_file(
        root / "config/model_governance.yaml"
    )
    loaded = resolve_model(
        registry_config=registry,
        governance_config=governance,
        serving_config=serving,
        root=root,
    )
    app = FastAPI(title=serving.service.title, version=serving.service.api_version)
    if serving.cors.enabled:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=serving.cors.allowed_origins,
            allow_credentials=serving.cors.allow_credentials,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["X-API-Key", "Content-Type", "Accept"],
        )
    app.state.serving_config = serving
    app.state.loaded_model = loaded

    def auth_dependency(request: Request) -> None:
        require_api_key(serving, request)

    @app.get("/health/live")
    def live() -> dict[str, object]:
        return {"live": True}

    @app.get("/health/ready")
    def ready() -> dict[str, object]:
        payload = readiness_payload(app.state.loaded_model)
        if not payload["ready"]:
            return payload
        return payload

    @app.get("/v1/model", dependencies=[Depends(auth_dependency)])
    def model() -> dict[str, object]:
        return model_metadata(app.state.loaded_model)

    @app.get("/v1/registry/status", dependencies=[Depends(auth_dependency)])
    def registry_status() -> dict[str, object]:
        payload = readiness_payload(app.state.loaded_model)
        return {
            "registry_health": "valid",
            "active_version": payload.get("registry_version"),
            "pending_versions": [] if app.state.loaded_model else ["registered_candidate"],
            "approval_state": (
                "review_mode"
                if app.state.loaded_model and app.state.loaded_model.review_mode
                else "not_active"
            ),
            "review_mode": bool(app.state.loaded_model and app.state.loaded_model.review_mode),
        }

    @app.post("/v1/predict", dependencies=[Depends(auth_dependency)])
    def predict(payload: PredictionRequest, request: Request) -> PredictionResponse:
        del request
        if app.state.loaded_model is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No approved active model is available.",
            )
        started = time.perf_counter()
        request_id = payload.request_id or f"REQ-{uuid.uuid4().hex[:16].upper()}"
        response = score_request(
            request=payload,
            loaded=app.state.loaded_model,
            config=serving,
            request_id=request_id,
        )
        if serving.logging.log_predictions:
            write_prediction_event(
                path=root / serving.logging.event_log_path,
                response=response,
                latency_ms=(time.perf_counter() - started) * 1000,
                success=True,
            )
        return response

    @app.post("/v1/predict/batch", dependencies=[Depends(auth_dependency)])
    def predict_batch(
        payload: BatchPredictionRequest, request: Request
    ) -> list[PredictionResponse]:
        del request
        if len(payload.records) > serving.limits.maximum_batch_size:
            raise HTTPException(status_code=413, detail="Batch size exceeds configured maximum.")
        responses = []
        for record in payload.records:
            if app.state.loaded_model is None:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="No approved active model is available.",
                )
            request_id = record.request_id or f"REQ-{uuid.uuid4().hex[:16].upper()}"
            responses.append(
                score_request(
                    request=record,
                    loaded=app.state.loaded_model,
                    config=serving,
                    request_id=request_id,
                )
            )
        return responses

    return app


def app_from_config() -> FastAPI:
    return create_app()
