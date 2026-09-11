from __future__ import annotations

from dataclasses import dataclass

from ml.src.contracts import RiskRecord
from ml.src.futo_survey import FutoSurveyObservation

FEATURE_NAMES = (
    "origin_latitude",
    "origin_longitude",
    "destination_latitude",
    "destination_longitude",
    "distance_km",
    "duration_minutes",
    "route_speed_kmh",
    "observed_hour_utc",
    "observed_weekday_utc",
)


@dataclass(frozen=True, slots=True)
class FeatureRow:
    values: tuple[float, ...]
    target_label: str | None
    observation_id: str
    respondent_id: str


@dataclass(frozen=True, slots=True)
class FutoFeatureMatrix:
    """One-hot route/time features and untouched questionnaire targets."""

    feature_names: tuple[str, ...]
    values: tuple[tuple[float, ...], ...]
    target_labels: tuple[str, ...]
    target_ordinals: tuple[int, ...]
    respondent_ids: tuple[str, ...]


def build_feature_row(record: RiskRecord) -> FeatureRow:
    """Build leakage-safe route/time features for a risk experiment.

    Risk component columns are intentionally not included as predictors. If a
    component is the target, feeding that same component into the model would
    produce target leakage.
    """

    speed = record.distance_km / (record.duration_minutes / 60)
    values = (
        record.origin_latitude,
        record.origin_longitude,
        record.destination_latitude,
        record.destination_longitude,
        record.distance_km,
        record.duration_minutes,
        speed,
        float(record.observed_at.hour),
        float(record.observed_at.weekday()),
    )
    return FeatureRow(values, record.risk_label, record.observation_id, record.respondent_id)


def build_feature_rows(
    records: tuple[RiskRecord, ...] | list[RiskRecord],
) -> tuple[FeatureRow, ...]:
    return tuple(build_feature_row(record) for record in records)


def build_futo_feature_matrix(
    observations: tuple[FutoSurveyObservation, ...] | list[FutoSurveyObservation],
) -> FutoFeatureMatrix:
    """Create categorical route/time features without target leakage.

    The current Google Forms export contains route names and time bands but no
    route coordinates, distances, or durations. Those physical route features
    must be joined from a documented FUTO route catalog in a later step.
    """

    if not observations:
        raise ValueError("at least one FUTO observation is required")
    routes = tuple(sorted({observation.route_id for observation in observations}))
    time_bands = tuple(sorted({observation.time_band for observation in observations}))
    feature_names = tuple(
        [f"route_id={route}" for route in routes]
        + [f"time_band={time_band}" for time_band in time_bands]
    )
    values = []
    for observation in observations:
        values.append(
            tuple(float(observation.route_id == route) for route in routes)
            + tuple(float(observation.time_band == time_band) for time_band in time_bands)
        )
    return FutoFeatureMatrix(
        feature_names=feature_names,
        values=tuple(values),
        target_labels=tuple(observation.risk_label for observation in observations),
        target_ordinals=tuple(observation.risk_ordinal for observation in observations),
        respondent_ids=tuple(observation.respondent_id for observation in observations),
    )