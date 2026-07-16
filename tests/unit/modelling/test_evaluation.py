import numpy as np

from ml_product.modelling.evaluation import evaluate_predictions


def test_evaluation_metrics_and_confusion_matrix() -> None:
    metrics = evaluate_predictions(
        np.asarray([True, False, True, False]),
        np.asarray([0.9, 0.7, 0.8, 0.1]),
        threshold=0.5,
        prevalence=0.5,
    )
    assert metrics["confusion_matrix"]["true_positives"] == 2
    assert metrics["confusion_matrix"]["false_positives"] == 1
    assert metrics["recall"] == 1.0
    assert metrics["specificity"] == 0.5
