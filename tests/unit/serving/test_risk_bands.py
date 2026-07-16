from pathlib import Path

from ml_product.serving.config import ServingConfig
from ml_product.serving.risk_bands import risk_band


def test_risk_band_boundaries_are_deterministic() -> None:
    config = ServingConfig.from_file(Path("config/serving.yaml"))
    assert risk_band(0.39, config) == "low"
    assert risk_band(0.4, config) == "medium"
    assert risk_band(0.75, config) == "high"
