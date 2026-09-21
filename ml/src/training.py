from __future__ import annotations

import json
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import fmean, pstdev
from typing import Any

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from ml.src.evaluation import ClassificationMetrics, evaluate_classification
from ml.src.features import FutoFeatureSet, build_futo_feature_matrix
from ml.src.futo_survey import FUTO_RISK_ORDINALS, FutoSurveyDataset
from ml.src.route_catalog import FutoRouteMetadata

ModelFactory = Callable[[], Any]


@dataclass(frozen=True, slots=True)
class FoldMetrics:
    fold: int
    accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    support: int
    train_group_count: int
    test_group_count: int
    per_class_recall: dict[str, float]
    confusion_matrix: dict[str, dict[str, int]]


@dataclass(frozen=True, slots=True)
class ModelSummary:
    name: str
    balanced: bool
    folds: tuple[FoldMetrics, ...]
    mean_accuracy: float
    std_accuracy: float
    mean_macro_f1: float
    std_macro_f1: float
    mean_per_class_recall: dict[str, float]


@dataclass(frozen=True, slots=True)
class FeatureExperiment:
    feature_set: str
    feature_names: tuple[str, ...]
    models: tuple[ModelSummary, ...]


@dataclass(frozen=True, slots=True)
class ExperimentReport:
    dataset_name: str
    observation_count: int
    respondent_count: int
    route_count: int
    time_band_count: int
    class_counts: dict[str, int]
    n_splits: int
    random_state: int
    sklearn_version: str
    experiments: tuple[FeatureExperiment, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def models(self) -> tuple[ModelSummary, ...]:
        return tuple(model for experiment in self.experiments for model in experiment.models)


def baseline_model_factories(
    random_state: int = 42, *, balanced: bool = False
) -> dict[str, ModelFactory]:
    """Return comparable candidate models, optionally using balanced classes."""

    suffix = "_balanced" if balanced else ""
    factories: dict[str, ModelFactory] = {
        "majority_baseline": lambda: DummyClassifier(strategy="most_frequent"),
        f"logistic_regression{suffix}": lambda: make_pipeline(
            StandardScaler(),
            LogisticRegression(
                max_iter=1000,
                random_state=random_state,
                class_weight="balanced" if balanced else None,
            ),
        ),
        f"decision_tree{suffix}": lambda: DecisionTreeClassifier(
            max_depth=6,
            random_state=random_state,
            class_weight="balanced" if balanced else None,
        ),
        f"random_forest{suffix}": lambda: RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            random_state=random_state,
            class_weight="balanced" if balanced else None,
            n_jobs=1,
        ),
    }
    return factories


def run_futo_experiment(
    dataset: FutoSurveyDataset,
    *,
    n_splits: int = 5,
    random_state: int = 42,
    feature_sets: Sequence[FutoFeatureSet] = ("route", "time", "route_time"),
    route_catalog: dict[str, FutoRouteMetadata] | None = None,
) -> ExperimentReport:
    """Compare feature ablations and balanced/unbalanced classifiers."""

    if dataset.issues:
        raise ValueError("cannot train with invalid FUTO observations")
    if not feature_sets:
        raise ValueError("at least one feature set is required")
    if "physical" in feature_sets or "route_time_physical" in feature_sets:
        if route_catalog is None:
            raise ValueError("physical feature sets require a route catalog")
    groups = {observation.respondent_id for observation in dataset.observations}
    if len(groups) < n_splits:
        raise ValueError("n_splits cannot exceed the number of respondent groups")

    labels = tuple(FUTO_RISK_ORDINALS)
    experiments: list[FeatureExperiment] = []
    for feature_set in feature_sets:
        matrix = build_futo_feature_matrix(
            dataset.observations,
            feature_set=feature_set,
            route_catalog=route_catalog,
        )
        X = np.asarray(matrix.values, dtype=float)
        y = np.asarray(matrix.target_labels, dtype=str)
        grouped = np.asarray(matrix.respondent_ids, dtype=str)
        model_summaries: list[ModelSummary] = []
        model_factories = {
            **baseline_model_factories(random_state),
            **baseline_model_factories(random_state, balanced=True),
        }
        for name, factory in model_factories.items():
            folds: list[FoldMetrics] = []
            splitter = StratifiedGroupKFold(
                n_splits=n_splits,
                shuffle=True,
                random_state=random_state,
            )
            for fold, (train_index, test_index) in enumerate(
                splitter.split(X, y, grouped), start=1
            ):
                train_groups = set(grouped[train_index])
                test_groups = set(grouped[test_index])
                if train_groups & test_groups:
                    raise RuntimeError("respondent leakage detected between train and test folds")
                model = factory()
                model.fit(X[train_index], y[train_index])
                predicted = model.predict(X[test_index])
                metrics = evaluate_classification(
                    y[test_index].tolist(), predicted.tolist(), labels=labels
                )
                folds.append(_fold_metrics(fold, metrics, len(train_groups), len(test_groups)))
            model_summaries.append(_summary(name, name.endswith("_balanced"), tuple(folds), labels))
        experiments.append(
            FeatureExperiment(feature_set, matrix.feature_names, tuple(model_summaries))
        )

    import sklearn

    return ExperimentReport(
        dataset_name="FUTO Road Risk Assessment Survey for Dynamic Transportation Pricing",
        observation_count=len(dataset.observations),
        respondent_count=dataset.response_count,
        route_count=len(dataset.route_ids),
        time_band_count=len(dataset.time_bands),
        class_counts=dict(Counter(observation.risk_label for observation in dataset.observations)),
        n_splits=n_splits,
        random_state=random_state,
        sklearn_version=sklearn.__version__,
        experiments=tuple(experiments),
    )


def save_report(report: ExperimentReport, path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")


def _fold_metrics(
    fold: int, metrics: ClassificationMetrics, train_group_count: int, test_group_count: int
) -> FoldMetrics:
    return FoldMetrics(
        fold=fold,
        accuracy=metrics.accuracy,
        macro_precision=metrics.macro_precision,
        macro_recall=metrics.macro_recall,
        macro_f1=metrics.macro_f1,
        support=metrics.support,
        train_group_count=train_group_count,
        test_group_count=test_group_count,
        per_class_recall=metrics.per_class_recall,
        confusion_matrix=metrics.confusion_matrix,
    )


def _summary(
    name: str,
    balanced: bool,
    folds: tuple[FoldMetrics, ...],
    labels: Sequence[str],
) -> ModelSummary:
    accuracy = tuple(fold.accuracy for fold in folds)
    macro_f1 = tuple(fold.macro_f1 for fold in folds)
    mean_recall = {label: fmean(fold.per_class_recall[label] for fold in folds) for label in labels}
    return ModelSummary(
        name=name,
        balanced=balanced,
        folds=folds,
        mean_accuracy=fmean(accuracy),
        std_accuracy=pstdev(accuracy),
        mean_macro_f1=fmean(macro_f1),
        std_macro_f1=pstdev(macro_f1),
        mean_per_class_recall=mean_recall,
    )
