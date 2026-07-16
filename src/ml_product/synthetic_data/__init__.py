"""Deterministic synthetic source-system generation."""

from ml_product.synthetic_data.config import SyntheticDataConfig
from ml_product.synthetic_data.generator import GenerationResult, generate_synthetic_data

__all__ = ["GenerationResult", "SyntheticDataConfig", "generate_synthetic_data"]
