from datetime import UTC, datetime

import pytest

from ml.src.contracts import RiskRecord
from ml.src.evaluation import evaluate_classification
from ml.src.features import FEATURE_NAMES, build_feature_row
from ml.src.preprocessing import preprocess_csv
from ml.src.splitting import assert_no_group_overlap, grouped_train_test_split


def make_record(index: int, respondent_id: str = "respondent-1") -> RiskRecord:
    return RiskRecord(
        observation_id=f"observation-{index}",
        respondent_id=respondent_id,
        route_id="route-1",
        observed_at=datetime(2026, 1, 1, 8, tzinfo=UTC),
        origin_latitude=5.39,
        origin_longitude=7.03,
        destination_latitude=5.48,
        destination_longitude=7.02,
        distance_km=12.8,
        duration_minutes=32,
        source_type="questionnaire",
        road_risk=0.4,
        risk_label="Moderate",
    )


def test_preprocessing_reports_bad_rows_without_mutating_csv(tmp_path):
    path = tmp_path / "observations.csv"
    path.write_text(
        "observation_id,respondent_id,route_id,observed_at,origin_latitude,origin_longitude,"
        "destination_latitude,destination_longitude,distance_km,duration_minutes,source_type,"
        "road_risk,risk_label\n"
        "obs-1,r-1,route-1,2026-01-01T08:00:00Z,5.39,7.03,5.48,7.02,12.8,32,questionnaire,0.4,Moderate\n"
        "obs-2,r-2,route-1,not-a-date,5.39,7.03,5.48,7.02,12.8,32,questionnaire,0.4,Moderate\n",
        encoding="utf-8",
    )
    original = path.read_bytes()

    result = preprocess_csv(path)

    assert result.accepted_count == 1
    assert result.rejected_count == 1
    assert result.issues[0].row_number == 3
    assert path.read_bytes() == original


def test_feature_engineering_derives_route_speed_and_preserves_target():
    row = build_feature_row(make_record(1))

    assert len(row.values) == len(FEATURE_NAMES)
    assert row.values[6] == pytest.approx(24.0)
    assert row.target_label == "Moderate"


def test_grouped_split_has_no_respondent_leakage():
    records = tuple(
        [make_record(1, "respondent-1"), make_record(2, "respondent-1")]
        + [make_record(3, "respondent-2"), make_record(4, "respondent-2")]
        + [make_record(5, "respondent-3"), make_record(6, "respondent-3")]
    )

    split = grouped_train_test_split(records, test_size=0.34, seed=7)
    assert_no_group_overlap(split)
    assert split.train and split.test


def test_classification_metrics_are_computed_from_predictions():
    metrics = evaluate_classification(
        ["Low", "Moderate", "High", "High"],
        ["Low", "Moderate", "Moderate", "High"],
        labels=["Low", "Moderate", "High"],
    )

    assert metrics.support == 4
    assert metrics.accuracy == pytest.approx(0.75)
    assert 0 <= metrics.macro_f1 <= 1