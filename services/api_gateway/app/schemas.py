from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    FiniteFloat,
    field_validator,
    model_validator,
)


class CoordinateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latitude: FiniteFloat = Field(ge=-90, le=90)
    longitude: FiniteFloat = Field(ge=-180, le=180)


class FareEstimateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    origin: CoordinateInput
    destination: CoordinateInput
    requested_at: datetime

    @field_validator("requested_at")
    @classmethod
    def requested_at_must_include_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("requested_at must include a timezone offset")
        return value

    @model_validator(mode="after")
    def points_must_differ(self) -> FareEstimateRequest:
        if self.origin == self.destination:
            raise ValueError("origin and destination must be different")
        return self


class RouteResponse(BaseModel):
    distance_km: float
    estimated_duration_minutes: int
    geometry: Any = None
    provider: str


class LocationResponse(BaseModel):
    location_id: str
    endpoint_name: str
    latitude: float
    longitude: float
    collected_at: str
    source: str
    source_url: str
    notes: str


class RiskComponentsResponse(BaseModel):
    accident: float | None
    road: float | None
    security: float | None
    questionnaire: float | None = None


class RiskResponse(BaseModel):
    score: float
    classification: Literal["Low", "Moderate", "High", "Very High"]
    components: RiskComponentsResponse
    components_available: list[str]
    components_missing: list[str]
    weight_strategy: str
    source_type: str
    data_sources: list[str]
    model_version: str


class DemandResponse(BaseModel):
    requests: int
    available_drivers: int
    multiplier: float
    source_type: str
    data_sources: list[str] = Field(default_factory=list)


class FareResponse(BaseModel):
    currency: str
    base_fare: float
    distance_component: float
    risk_adjustment: float
    demand_adjustment: float
    total: float
    formula_mode: Literal["additive", "multiplicative"]
    formula_version: str
    coefficient_version: str


class FareEstimateResponse(BaseModel):
    quote_id: str
    created_at: datetime
    requested_at: datetime
    origin: CoordinateInput
    destination: CoordinateInput
    route: RouteResponse
    risk: RiskResponse
    demand: DemandResponse
    fare: FareResponse
    timings_ms: dict[str, float] = Field(default_factory=dict)


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Any = None


class ErrorResponse(BaseModel):
    error: ErrorBody
