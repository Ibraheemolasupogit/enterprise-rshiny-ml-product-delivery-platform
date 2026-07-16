from typer.testing import CliRunner

from ml_product.cli import app


def test_retraining_cli_shows_recommendation() -> None:
    result = CliRunner().invoke(app, ["show-retraining-recommendation"])
    assert result.exit_code == 0
    assert "Recommendation:" in result.stdout
    assert "Approval status: not_granted" in result.stdout


def test_registration_command_blocks_retain_champion_recommendation() -> None:
    result = CliRunner().invoke(
        app,
        [
            "register-retraining-candidate",
            "--recommendation",
            "reports/retraining/retraining_recommendation.json",
            "--actor",
            "TEST",
            "--reason",
            "test",
        ],
    )
    assert result.exit_code == 1
    assert "Registration requires" in result.stderr
