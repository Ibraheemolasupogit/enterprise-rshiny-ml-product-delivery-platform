"""Local FastAPI serving package for Milestone 7."""

from ml_product.serving.app import create_app
from ml_product.serving.config import ServingConfig

__all__ = ["ServingConfig", "create_app"]
