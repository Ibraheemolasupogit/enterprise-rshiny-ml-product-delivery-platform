from pathlib import Path

import pytest

from ml_product.registry.config import GovernanceConfig, RegistryConfig
from ml_product.registry.metadata import sha256_file
from ml_product.registry.models import (
    ArtefactReference,
    EvaluationSummary,
    FeatureContract,
    GovernanceAssessment,
    ModelVersion,
    PreprocessorContract,
    RegistryEntry,
    RegistryRecord,
)
from ml_product.registry.registry import LocalModelRegistry
from ml_product.registry.storage import save_registry


def test_registered_candidate_rematerialises_existing_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    registry = _registry(tmp_path)
    version = _version(model_sha256="stale-model", calibrator_sha256="stale-calibrator")
    save_registry(
        tmp_path / "models/registry.json",
        RegistryRecord(
            version=1,
            registry_type="local_filesystem",
            models=[RegistryEntry(model_name=version.model_name, versions=[version])],
        ),
    )
    candidate_dir = tmp_path / "models/candidate"
    candidate_dir.mkdir(parents=True)
    (candidate_dir / "xgboost.json").write_text('{"model":"canonical"}\n', encoding="utf-8")
    (candidate_dir / "calibrator.joblib").write_bytes(b"canonical-calibrator")
    model_checksum = sha256_file(candidate_dir / "xgboost.json")
    calibrator_checksum = sha256_file(candidate_dir / "calibrator.joblib")

    def rebuild(**kwargs: object) -> ModelVersion:
        return _version(model_sha256=model_checksum, calibrator_sha256=calibrator_checksum)

    monkeypatch.setattr("ml_product.registry.registry.build_model_version", rebuild)

    rematerialised = registry.rematerialise_registered_candidate(
        candidate_identifier="CAND-85EA9202CAD6FE7F",
        model_config_path=Path("config/model_training.yaml"),
        candidate_dir=candidate_dir,
    )

    record = registry.load()
    assert len(record.models[0].versions) == 1
    assert rematerialised.registry_version == 1
    assert rematerialised.artefacts.model_sha256 == model_checksum
    assert rematerialised.artefacts.calibrator_sha256 == calibrator_checksum
    assert (tmp_path / "models/registered/v000001/xgboost.json").is_file()
    assert (tmp_path / "models/registered/v000001/calibrator.joblib").is_file()
    assert record.active_model is None
    assert record.active_version is None
    assert record.models[0].versions[0].approval_decision is None
    assert record.audit_events[-1].event_type == "registered_artefacts_rematerialized"


def test_registered_candidate_rematerialisation_rejects_semantic_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    registry = _registry(tmp_path)
    version = _version(model_sha256="stale-model", calibrator_sha256="stale-calibrator")
    save_registry(
        tmp_path / "models/registry.json",
        RegistryRecord(
            version=1,
            registry_type="local_filesystem",
            models=[RegistryEntry(model_name=version.model_name, versions=[version])],
        ),
    )
    candidate_dir = tmp_path / "models/candidate"
    candidate_dir.mkdir(parents=True)
    (candidate_dir / "xgboost.json").write_text('{"model":"different"}\n', encoding="utf-8")
    (candidate_dir / "calibrator.joblib").write_bytes(b"different-calibrator")

    def rebuild(**kwargs: object) -> ModelVersion:
        rebuilt = _version(
            model_sha256=sha256_file(candidate_dir / "xgboost.json"),
            calibrator_sha256=sha256_file(candidate_dir / "calibrator.joblib"),
        )
        rebuilt.feature_contract.feature_build_identifier = "FBUILD-DIFFERENT"
        return rebuilt

    monkeypatch.setattr("ml_product.registry.registry.build_model_version", rebuild)

    with pytest.raises(ValueError, match="semantic contract mismatch"):
        registry.rematerialise_registered_candidate(
            candidate_identifier="CAND-85EA9202CAD6FE7F",
            model_config_path=Path("config/model_training.yaml"),
            candidate_dir=candidate_dir,
        )


def _registry(root: Path) -> LocalModelRegistry:
    return LocalModelRegistry(
        RegistryConfig.from_file(Path("config/model_registry.yaml")),
        GovernanceConfig.from_file(Path("config/model_governance.yaml")),
        root=root,
    )


def _version(*, model_sha256: str, calibrator_sha256: str) -> ModelVersion:
    return ModelVersion(
        model_name="long_stay_admission_risk",
        registry_id="MODEL-REG-000001",
        registry_version=1,
        status="registered",
        model_family="xgboost",
        candidate_identifier="CAND-85EA9202CAD6FE7F",
        calibration="sigmoid",
        threshold=0.75,
        artefacts=ArtefactReference(
            model_path="models/registered/v000001/xgboost.json",
            calibrator_path="models/registered/v000001/calibrator.joblib",
            model_sha256=model_sha256,
            calibrator_sha256=calibrator_sha256,
        ),
        feature_contract=FeatureContract(
            feature_count=2,
            feature_names=["age", "news2"],
            feature_schema_fingerprint="feature-fingerprint",
            feature_build_identifier="FBUILD-ADB1D374A8E41F8E",
        ),
        preprocessor_contract=PreprocessorContract(
            preprocessor_fingerprint="preprocessor-fingerprint",
            preprocessor_checksum="preprocessor-checksum",
            source_path="reports/model_evaluation/preprocessor_metadata.json",
        ),
        evaluation_summary=EvaluationSummary(
            validation_pr_auc=0.9,
            validation_brier_score=0.1,
            validation_recall=0.8,
            validation_precision=0.7,
            test_pr_auc=0.85,
            test_roc_auc=0.8,
            test_brier_score=0.12,
            test_recall=0.75,
            test_specificity=0.65,
            test_balanced_accuracy=0.7,
            test_set_used_for_selection=False,
        ),
        governance=GovernanceAssessment(
            recommended_decision="defer",
            hard_requirements={"feature_schema_match": True},
            review_flags=[],
            conditions=[],
            informational_limitations=[],
        ),
        created_at_utc="2026-07-15T00:41:38+00:00",
        training_configuration_fingerprint="training-fingerprint",
        evidence_fingerprint="evidence-fingerprint",
        synthetic_data_declaration="Synthetic data only.",
    )
