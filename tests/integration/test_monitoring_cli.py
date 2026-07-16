from typer.testing import CliRunner

from ml_product.cli import app


def test_monitoring_cli_describes_committed_run() -> None:
    result = CliRunner().invoke(app, ["describe-monitoring", "--config", "config/monitoring.yaml"])
    assert result.exit_code == 0
    assert "Monitoring run:" in result.stdout
    assert "Disposition:" in result.stdout


def test_monitoring_cli_lists_review_alerts() -> None:
    result = CliRunner().invoke(
        app, ["list-monitoring-alerts", "--config", "config/monitoring.yaml"]
    )
    assert result.exit_code == 0
    assert "critical" in result.stdout
    assert "numeric_drift" in result.stdout
