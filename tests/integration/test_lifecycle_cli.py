import subprocess
import sys
from pathlib import Path


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "ml_product.cli", *args],
        check=False,
        text=True,
        capture_output=True,
    )


def test_lifecycle_describe_provider_cli() -> None:
    result = run_cli("lifecycle-describe-provider")

    assert result.returncode == 0
    assert "Selected provider: local" in result.stdout


def test_lifecycle_check_readiness_cli() -> None:
    result = run_cli("lifecycle-check-readiness")

    assert result.returncode == 0
    assert "healthy=True" in result.stdout


def test_lifecycle_build_model_package_cli_does_not_mutate_registry(tmp_path: Path) -> None:
    registry_path = Path("models/registry.json")
    before = registry_path.read_text(encoding="utf-8")
    output_path = tmp_path / "lifecycle-package.json"

    result = run_cli("lifecycle-build-model-package", "--output-path", str(output_path))

    assert result.returncode == 0, result.stderr
    assert output_path.is_file()
    assert "Built lifecycle package for long_stay_admission_risk:1" in result.stdout
    assert registry_path.read_text(encoding="utf-8") == before
