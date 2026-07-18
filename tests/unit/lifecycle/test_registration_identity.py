from pathlib import Path

from ml_product.lifecycle.config import LifecycleConfig
from ml_product.lifecycle.identity import registration_fingerprint
from ml_product.lifecycle.package import build_model_package


def test_registration_fingerprint_is_deterministic_and_stable() -> None:
    config = LifecycleConfig.from_file(Path("config/model_lifecycle.yaml"))
    package = build_model_package(config)

    first = registration_fingerprint(package)
    second = registration_fingerprint(package)

    assert first == second
    assert len(first) == 64
