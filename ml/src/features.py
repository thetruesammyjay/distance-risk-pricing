from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from ml.src.contracts import RiskRecord
from ml.src.futo_survey import FutoSurveyObservation
from ml.src.route_catalog import FutoRouteMetadata, validate_catalog_covers_observations

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
FutoFeatureSet = Literal["route", "time", "route_time", "physical", "route_time_physical"]
PHYSICAL_FEATURE_NAMES = (
    "origin_latitude",
    "origin_longitude",
    "destination_latitude",
    "destination_longitude",
    "distance_km",
    "duration_minutes",
    "route_speed_kmh",
)


@dataclass(frozen=True, slots=True)
class FeatureRow:
    values: tuple[float, ...]
    target_label: str | None
    observation_id: str
    respondent_id: str


@dataclass(frozen=True, slots=True)
class FutoFeatureMatrix:
    feature_set: FutoFeatureSet
    feature_names: tuple[str, ...]
    values: tuple[tuple[float, ...], ...]
    target_labels: tuple[str, ...]
    target_ordinals: tuple[int, ...]
    respondent_ids: tuple[str, ...]


def build_feature_row(record: RiskRecord) -> FeatureRow:
    """Build leakage-safe route/time features for a risk experiment."""

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
    *,
    feature_set: FutoFeatureSet = "route_time",
    route_catalog: Mapping[str, FutoRouteMetadata] | None = None,
) -> FutoFeatureMatrix:
    """Build route/time ablations and optional documented physical features.

    The questionnaire labels are targets and are never included in predictors.
    Physical features require a complete route catalog; no distance or duration
    is inferred from the route name.
    """

    if not observations:
        raise ValueError("at least one FUTO observation is required")
    if feature_set not in {"route", "time", "route_time", "physical", "route_time_physical"}:
        raise ValueError(f"unsupported FUTO feature set: {feature_set}")
    needs_physical = feature_set in {"physical", "route_time_physical"}
    if needs_physical:
        if route_catalog is None:
            raise ValueError("physical FUTO features require a route catalog")
        validate_catalog_covers_observations(observations, dict(route_catalog))
    routes = tuple(sorted({observation.route_id for observation in observations}))
    time_bands = tuple(sorted({observation.time_band for observation in observations}))
    names: list[str] = []
    if feature_set in {"route", "route_time", "route_time_physical"}:
        names.extend(f"route_id={route}" for route in routes)
    if feature_set in {"time", "route_time", "route_time_physical"}:
        names.extend(f"time_band={time_band}" for time_band in time_bands)
    if needs_physical:
        names.extend(PHYSICAL_FEATURE_NAMES)
    values: list[tuple[float, ...]] = []
    for observation in observations:
        row: list[float] = []
        if feature_set in {"route", "route_time", "route_time_physical"}:
            row.extend(float(observation.route_id == route) for route in routes)
        if feature_set in {"time", "route_time", "route_time_physical"}:
            row.extend(float(observation.time_band == time_band) for time_band in time_bands)
        if needs_physical:
            metadata = route_catalog[observation.route_id]
            row.extend(
                (
                    metadata.origin_latitude,
                    metadata.origin_longitude,
                    metadata.destination_latitude,
                    metadata.destination_longitude,
                    metadata.distance_km,
                    metadata.duration_minutes,
                    metadata.distance_km / (metadata.duration_minutes / 60),
                )
            )
        values.append(tuple(row))
    return FutoFeatureMatrix(
        feature_set=feature_set,
        feature_names=tuple(names),
        values=tuple(values),
        target_labels=tuple(observation.risk_label for observation in observations),
        target_ordinals=tuple(observation.risk_ordinal for observation in observations),
        respondent_ids=tuple(observation.respondent_id for observation in observations),
    )
