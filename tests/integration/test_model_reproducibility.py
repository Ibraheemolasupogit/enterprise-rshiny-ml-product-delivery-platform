import subprocess
import sys


def test_model_reproducibility_script() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/verify_model_build.py"],
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert "verified" in result.stdout
