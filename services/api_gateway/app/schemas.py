from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CoordinateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class FareEstimateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    origin: CoordinateInput
    destination: CoordinateInput
    requested_at: datetime

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


class RiskComponentsResponse(BaseModel):
    accident: float | None
    road: float | None
    security: float | None


class RiskResponse(BaseModel):
    score: float
    classification: Literal["Low", "Moderate", "High", "Very High"]
    components: RiskComponentsResponse
    components_available: list[str]
    components_missing: list[str]
    weight_strategy: str
    data_sources: list[str]
    model_version: str


class DemandResponse(BaseModel):
    requests: int
    available_drivers: int
    multiplier: float
    source_type: str


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


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Any = None


class ErrorResponse(BaseModel):
    error: ErrorBody
