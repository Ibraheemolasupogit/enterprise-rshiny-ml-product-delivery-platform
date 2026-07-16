import hashlib
from pathlib import Path

from ml_product.retraining import ComparisonConfig, RetrainingConfig, run_retraining


def test_retraining_does_not_mutate_real_registry() -> None:
    registry = Path("models/registry.json")
    before = hashlib.sha256(registry.read_bytes()).hexdigest()
    run_retraining(
        RetrainingConfig.from_file(Path("config/retraining.yaml")),
        ComparisonConfig.from_file(Path("config/champion_challenger.yaml")),
        replace=True,
    )
    after = hashlib.sha256(registry.read_bytes()).hexdigest()
    assert after == before
