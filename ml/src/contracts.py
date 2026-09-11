from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

RiskSourceType = Literal["observed", "questionnaire", "derived", "external", "simulated"]
RISK_SOURCE_TYPES = frozenset({"observed", "questionnaire", "derived", "external", "simulated"})
RISK_LABELS = frozenset({"Low", "Moderate", "High", "Very High"})


@dataclass(frozen=True, slots=True)
class RiskRecord:
    """One route/time observation used by the research pipeline.

    Risk components are optional because the pipeline must preserve missingness
    instead of fabricating an unavailable signal. ``risk_label`` is a supplied
    target label, not a label inferred by this module.
    """

    observation_id: str
    respondent_id: str
    route_id: str
    observed_at: datetime
    origin_latitude: float
    origin_longitude: float
    destination_latitude: float
    destination_longitude: float
    distance_km: float
    duration_minutes: float
    source_type: RiskSourceType
    accident_risk: float | None = None
    road_risk: float | None = None
    security_risk: float | None = None
    risk_label: str | None = None

    def __post_init__(self) -> None:
        for name in ("observation_id", "respondent_id", "route_id"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} cannot be empty")
        if self.observed_at.tzinfo is None:
            raise ValueError("observed_at must include timezone information")
        _validate_coordinate(self.origin_latitude, "origin_latitude", -90, 90)
        _validate_coordinate(self.destination_latitude, "destination_latitude", -90, 90)
        _validate_coordinate(self.origin_longitude, "origin_longitude", -180, 180)
        _validate_coordinate(self.destination_longitude, "destination_longitude", -180, 180)
        if self.distance_km < 0 or self.duration_minutes <= 0:
            raise ValueError(
                "distance_km must be non-negative and duration_minutes must be positive"
            )
        if self.source_type not in RISK_SOURCE_TYPES:
            raise ValueError(f"unsupported source_type: {self.source_type}")
        if self.risk_label is not None and self.risk_label not in RISK_LABELS:
            raise ValueError(f"unsupported risk_label: {self.risk_label}")
        for name in ("accident_risk", "road_risk", "security_risk"):
            value = getattr(self, name)
            if value is not None and not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1")


def _validate_coordinate(value: float, name: str, minimum: float, maximum: float) -> None:
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")