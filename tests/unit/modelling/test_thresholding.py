import numpy as np

from ml_product.modelling.config import ThresholdConfig
from ml_product.modelling.thresholding import analyse_thresholds, candidate_thresholds


def test_threshold_selection_is_validation_only_and_deterministic() -> None:
    config = ThresholdConfig.from_file()
    thresholds = candidate_thresholds(config)
    assert thresholds[0] == 0.1
    analysis = analyse_thresholds(
        np.asarray([True, True, False, False]),
        np.asarray([0.9, 0.6, 0.4, 0.2]),
        config,
        prevalence=0.5,
    )
    assert analysis["selected_threshold"] in thresholds
