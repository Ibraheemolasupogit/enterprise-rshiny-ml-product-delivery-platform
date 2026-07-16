import subprocess
import sys
from pathlib import Path


def test_feature_cli_commands_succeed() -> None:
    commands = [
        [
            sys.executable,
            "-m",
            "ml_product.cli",
            "check-feature-leakage",
            "--config",
            "config/features.yaml",
        ],
        [
            sys.executable,
            "-m",
            "ml_product.cli",
            "describe-features",
            "--config",
            "config/features.yaml",
        ],
        [
            sys.executable,
            "-m",
            "ml_product.cli",
            "list-features",
            "--config",
            "config/features.yaml",
        ],
        [
            sys.executable,
            "-m",
            "ml_product.cli",
            "show-split-summary",
            "--config",
            "config/features.yaml",
        ],
        [
            sys.executable,
            "-m",
            "ml_product.cli",
            "validate-features",
            "--config",
            "config/features.yaml",
        ],
    ]
    for command in commands:
        result = subprocess.run(command, check=False, text=True, capture_output=True)
        assert result.returncode == 0, result.stderr


def test_feature_cli_replace_protection(tmp_path: Path) -> None:
    output_dir = tmp_path / "features"
    output_dir.mkdir()
    (output_dir / "marker.txt").write_text("existing", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ml_product.cli",
            "build-features",
            "--config",
            "config/features.yaml",
            "--output-dir",
            str(output_dir),
        ],
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
    assert "not empty" in result.stderr
