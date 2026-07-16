import subprocess
import sys


def test_model_cli_report_commands() -> None:
    commands = [
        "validate-models",
        "compare-models",
        "describe-model-results",
        "show-threshold-analysis",
        "show-calibration-report",
        "show-fairness-report",
        "show-candidate-recommendation",
    ]
    for command in commands:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ml_product.cli",
                command,
                "--config",
                "config/model_training.yaml",
            ],
            check=False,
            text=True,
            capture_output=True,
        )
        assert result.returncode == 0, result.stderr
