import pytest

from ml.src.features import build_futo_feature_matrix
from ml.src.futo_survey import FutoSurveyObservation
from ml.src.route_catalog import FutoRouteMetadata


def test_physical_futo_features_require_and_use_route_metadata():
    observation = FutoSurveyObservation(
        observation_id="observation-1",
        respondent_id="respondent-1",
        route_id="route-1",
        route_name="FUTO Main Gate to School Roundabout",
        time_band="7:00 AM - 10:00 AM",
        risk_label="Moderate Risk",
        risk_ordinal=2,
    )
    catalog = {
        "route-1": FutoRouteMetadata(
            route_id="route-1",
            route_name="FUTO Main Gate to School Roundabout",
            origin_latitude=5.39,
            origin_longitude=7.03,
            destination_latitude=5.40,
            destination_longitude=7.02,
            distance_km=2.5,
            duration_minutes=8,
            source="OSRM route lookup",
            source_url="https://router.project-osrm.org/",
        )
    }

    matrix = build_futo_feature_matrix(
        (observation,), feature_set="route_time_physical", route_catalog=catalog
    )

    assert matrix.feature_names[-7:] == (
        "origin_latitude",
        "origin_longitude",
        "destination_latitude",
        "destination_longitude",
        "distance_km",
        "duration_minutes",
        "route_speed_kmh",
    )
    assert matrix.values[0][-3:] == pytest.approx((2.5, 8.0, 18.75))


def test_physical_futo_features_reject_missing_catalog():
    observation = FutoSurveyObservation(
        observation_id="observation-1",
        respondent_id="respondent-1",
        route_id="route-1",
        route_name="Route 1",
        time_band="Morning",
        risk_label="Low Risk",
        risk_ordinal=1,
    )

    with pytest.raises(ValueError, match="require a route catalog"):
        build_futo_feature_matrix((observation,), feature_set="physical")