from pathlib import Path

from ml_product.monitoring.config import DriftThresholdConfig, MonitoringConfig


def test_monitoring_config_disables_automatic_mutation() -> None:
    config = MonitoringConfig.from_file(Path("config/monitoring.yaml"))
    assert config.alerts.automatic_retraining is False
    assert config.alerts.automatic_model_replacement is False
    assert config.schema_checks.fail_on_missing_required_column is True
    assert config.schema_checks.fail_on_unexpected_column is True
    assert config.outputs.committed_evidence_directory == Path("reports/monitoring")


def test_drift_threshold_config_is_implemented() -> None:
    thresholds = DriftThresholdConfig.from_file(Path("config/drift_thresholds.yaml"))
    assert thresholds.implementation_status == "implemented"
    assert thresholds.numeric.psi.warning < thresholds.numeric.psi.critical
    assert thresholds.prediction.psi.warning < thresholds.prediction.psi.critical
