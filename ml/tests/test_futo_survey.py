from ml.src.features import build_futo_feature_matrix
from ml.src.futo_survey import load_futo_survey
from ml.src.splitting import grouped_train_test_indices


def test_google_forms_export_is_normalized_to_long_format(tmp_path):
    path = tmp_path / "futo.csv"
    path.write_text(
        "Timestamp,Route: FUTO Main Gate to School Roundabout [7:00 AM - 10:00 AM],"
        "Route: FUTO Main Gate to School Roundabout [7:00 PM - 10:00 PM]\n"
        "01/01/2026 08:00:00 AM MDT,Low Risk,Very High Risk\n",
        encoding="utf-8",
    )

    dataset = load_futo_survey(path)

    assert dataset.response_count == 1
    assert len(dataset.observations) == 2
    assert dataset.observations[0].respondent_id == "futo-respondent-0001"
    assert dataset.observations[0].risk_ordinal == 1
    assert dataset.observations[1].risk_ordinal == 4
    assert dataset.observations[0].source_type == "questionnaire"


def test_futo_features_are_route_time_only_and_groupable():
    observations = load_futo_survey_from_rows("Low Risk", "Moderate Risk")
    matrix = build_futo_feature_matrix(observations)

    assert matrix.feature_names == (
        "route_id=futo-main-gate-to-school-roundabout",
        "time_band=7:00 AM - 10:00 AM",
        "time_band=7:00 PM - 10:00 PM",
    )
    assert all(len(row) == len(matrix.feature_names) for row in matrix.values)
    assert matrix.target_ordinals == (1, 2)
    split = grouped_train_test_indices(
        ("respondent-1", "respondent-1", "respondent-2", "respondent-2"),
        test_size=0.5,
        seed=42,
    )
    assert split.train_groups.isdisjoint(split.test_groups)


def load_futo_survey_from_rows(morning: str, evening: str):
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "futo.csv"
        path.write_text(
            "Timestamp,Route: FUTO Main Gate to School Roundabout [7:00 AM - 10:00 AM],"
            "Route: FUTO Main Gate to School Roundabout [7:00 PM - 10:00 PM]\n"
            f"01/01/2026 08:00:00 AM MDT,{morning},{evening}\n",
            encoding="utf-8",
        )
        return load_futo_survey(path).observations