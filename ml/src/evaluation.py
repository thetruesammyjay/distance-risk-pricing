from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ClassificationMetrics:
    accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    support: int


def evaluate_classification(
    actual: Sequence[str], predicted: Sequence[str], *, labels: Sequence[str] | None = None
) -> ClassificationMetrics:
    """Calculate metrics from real predictions without depending on a library."""

    if not actual or len(actual) != len(predicted):
        raise ValueError("actual and predicted must have the same non-empty length")
    classes = tuple(labels or sorted(set(actual) | set(predicted)))
    if not classes:
        raise ValueError("at least one class is required")
    pairs = tuple(zip(actual, predicted, strict=True))
    accuracy = sum(left == right for left, right in pairs) / len(actual)
    precisions: list[float] = []
    recalls: list[float] = []
    f1_scores: list[float] = []
    for label in classes:
        true_positive = sum(left == label and right == label for left, right in pairs)
        false_positive = sum(left != label and right == label for left, right in pairs)
        false_negative = sum(left == label and right != label for left, right in pairs)
        precision = _ratio(true_positive, true_positive + false_positive)
        recall = _ratio(true_positive, true_positive + false_negative)
        precisions.append(precision)
        recalls.append(recall)
        f1_scores.append(_ratio(2 * precision * recall, precision + recall))
    return ClassificationMetrics(
        accuracy=accuracy,
        macro_precision=sum(precisions) / len(classes),
        macro_recall=sum(recalls) / len(classes),
        macro_f1=sum(f1_scores) / len(classes),
        support=len(actual),
    )


def _ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0