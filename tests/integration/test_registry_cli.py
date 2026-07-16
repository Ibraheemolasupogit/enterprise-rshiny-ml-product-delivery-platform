from typer.testing import CliRunner

from ml_product.cli import app


def test_registry_cli_lists_registered_model() -> None:
    result = CliRunner().invoke(app, ["list-models", "--config", "config/model_registry.yaml"])
    assert result.exit_code == 0
    assert "long_stay_admission_risk:1" in result.stdout
    assert "registered" in result.stdout
