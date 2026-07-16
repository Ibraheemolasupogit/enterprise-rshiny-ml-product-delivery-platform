import subprocess
import sys
from pathlib import Path


def test_database_cli_build_validate_describe(tmp_path: Path) -> None:
    database_path = tmp_path / "cli.duckdb"
    build = subprocess.run(
        [
            sys.executable,
            "-m",
            "ml_product.cli",
            "build-database",
            "--config",
            "config/database.yaml",
            "--database-path",
            str(database_path),
            "--replace",
        ],
        check=False,
        text=True,
        capture_output=True,
    )
    assert build.returncode == 0, build.stderr

    validate = subprocess.run(
        [
            sys.executable,
            "-m",
            "ml_product.cli",
            "validate-database",
            "--config",
            "config/database.yaml",
            "--database-path",
            str(database_path),
        ],
        check=False,
        text=True,
        capture_output=True,
    )
    assert validate.returncode == 0, validate.stderr
