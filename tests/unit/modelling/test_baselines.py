import numpy as np

from ml_product.modelling.baselines import fit_majority_baseline, fit_prevalence_baseline


def test_prevalence_and_majority_use_training_only() -> None:
    y_train = np.asarray([True, True, False, True])
    prevalence = fit_prevalence_baseline(y_train)
    majority = fit_majority_baseline(y_train)
    assert prevalence.probability == 0.75
    assert majority.probability == 1.0
    assert majority.majority_class is True
