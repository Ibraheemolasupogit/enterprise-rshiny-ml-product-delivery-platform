"""Risk-band helpers."""

from __future__ import annotations

from typing import Literal

from ml_product.serving.config import ServingConfig


def risk_band(probability: float, config: ServingConfig) -> Literal["low", "medium", "high"]:
    bands = config.risk_bands
    if bands["low"].minimum <= probability < bands["low"].maximum:
        return "low"
    if bands["medium"].minimum <= probability < bands["medium"].maximum:
        return "medium"
    if bands["high"].minimum <= probability <= bands["high"].maximum:
        return "high"
    raise ValueError(f"Probability outside risk-band range: {probability}")
