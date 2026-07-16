from pathlib import Path

from ml_product.release.containers import validate_container_files


def test_container_files_follow_milestone_13_boundaries() -> None:
    result = validate_container_files(Path("."))
    assert result["status"] == "passed"
    checks = result["checks"]
    assert checks["api_non_root_user"] is True
    assert checks["rshiny_non_root_user"] is True
    assert checks["review_mode_disabled_by_default"] is True
    assert checks["no_docker_socket"] is True
