from ml.src.futo_survey import FutoSurveyDataset, FutoSurveyObservation
from ml.src.training import run_futo_experiment


def make_dataset() -> FutoSurveyDataset:
    observations = []
    labels = ("Low Risk", "Moderate Risk", "High Risk", "Very High Risk")
    for respondent_number in range(8):
        respondent_id = f"respondent-{respondent_number}"
        for index, label in enumerate(labels):
            observations.append(
                FutoSurveyObservation(
                    observation_id=f"{respondent_id}-{index}",
                    respondent_id=respondent_id,
                    route_id=f"route-{index % 2}",
                    route_name=f"Route {index % 2}",
                    time_band=f"band-{index}",
                    risk_label=label,
                    risk_ordinal=index + 1,
                )
            )
    return FutoSurveyDataset(tuple(observations), 8, ())


def test_futo_experiment_reports_grouped_metrics_for_each_baseline():
    report = run_futo_experiment(make_dataset(), n_splits=4, random_state=42)

    assert report.observation_count == 32
    assert report.respondent_count == 8
    assert [experiment.feature_set for experiment in report.experiments] == [
        "route",
        "time",
        "route_time",
    ]
    expected_models = {
        "majority_baseline",
        "logistic_regression",
        "decision_tree",
        "random_forest",
        "logistic_regression_balanced",
        "decision_tree_balanced",
        "random_forest_balanced",
    }
    for experiment in report.experiments:
        assert set(model.name for model in experiment.models) == expected_models
        for model in experiment.models:
            assert len(model.folds) == 4
            assert all(fold.train_group_count == 6 for fold in model.folds)
            assert all(fold.test_group_count == 2 for fold in model.folds)
            assert all(
                set(fold.per_class_recall) == {
                    "Low Risk",
                    "Moderate Risk",
                    "High Risk",
                    "Very High Risk",
                }
                for fold in model.folds
            )
            assert all(
                set(row) == {
                    "Low Risk",
                    "Moderate Risk",
                    "High Risk",
                    "Very High Risk",
                }
                for fold in model.folds
                for row in fold.confusion_matrix.values()
            )
            assert 0 <= model.mean_macro_f1 <= 1
            assert 0 <= model.mean_accuracy <= 1