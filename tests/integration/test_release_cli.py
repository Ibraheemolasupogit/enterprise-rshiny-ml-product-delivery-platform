from typer.testing import CliRunner

from ml_product.cli import app


def test_release_cli_commands_do_not_deploy() -> None:
    runner = CliRunner()
    for command in [
        ["validate-release-config"],
        ["build-release-manifest"],
        ["assess-release-readiness"],
        ["validate-containers"],
        ["describe-release"],
        ["show-release-gates"],
    ]:
        result = runner.invoke(app, command)
        assert result.exit_code == 0, result.output
    assert (
        "Operational release readiness: blocked_for_operational_release"
        in runner.invoke(app, ["assess-release-readiness"]).output
    )
