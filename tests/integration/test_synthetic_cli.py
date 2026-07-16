import subprocess
import sys
from pathlib import Path


def test_synthetic_cli_generate_validate_describe(tmp_path: Path) -> None:
    generate = subprocess.run(
        [
            sys.executable,
            "-m",
            "ml_product.cli",
            "generate-synthetic-data",
            "--config",
            "config/synthetic_data.yaml",
            "--output-dir",
            str(tmp_path),
            "--overwrite",
        ],
        check=False,
        text=True,
        capture_output=True,
    )
    assert generate.returncode == 0, generate.stderr

    validate = subprocess.run(
        [
            sys.executable,
            "-m",
            "ml_product.cli",
            "validate-synthetic-data",
            "--config",
            "config/synthetic_data.yaml",
            "--output-dir",
            str(tmp_path),
        ],
        check=False,
        text=True,
        capture_output=True,
    )
    assert validate.returncode == 0, validate.stderr

    describe = subprocess.run(
        [
            sys.executable,
            "-m",
            "ml_product.cli",
            "describe-synthetic-data",
            "--config",
            "config/synthetic_data.yaml",
            "--output-dir",
            str(tmp_path),
        ],
        check=False,
        text=True,
        capture_output=True,
    )
    assert describe.returncode == 0, describe.stderr
    assert "Configuration fingerprint" in describe.stdout
