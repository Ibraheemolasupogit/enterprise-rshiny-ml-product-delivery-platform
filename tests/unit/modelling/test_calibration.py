import numpy as np

from ml_product.modelling.calibration import select_calibration
from ml_product.modelling.config import ModelTrainingConfig


def test_isotonic_blocked_for_small_validation_set() -> None:
    config = ModelTrainingConfig.from_file()
    _, report = select_calibration(
        np.asarray([True, False, True, True]),
        np.asarray([0.8, 0.7, 0.9, 0.6]),
        threshold=0.5,
        prevalence=0.75,
        config=config,
    )
    assert report["method_eligibility"]["isotonic"]["eligible"] is False
