import subprocess
import sys


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "ml_product.cli", *args],
        check=False,
        text=True,
        capture_output=True,
    )


def test_cli_version() -> None:
    result = run_cli("version")

    assert result.returncode == 0
    assert result.stdout.strip() == "0.1.0"


def test_cli_validate_structure() -> None:
    result = run_cli("validate-structure")

    assert result.returncode == 0
    assert "[structure] ok" in result.stdout


def test_cli_validate_config() -> None:
    result = run_cli("validate-config")

    assert result.returncode == 0
    assert "[config] ok" in result.stdout
