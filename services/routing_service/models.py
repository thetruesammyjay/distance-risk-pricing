from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Coordinates:
    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.latitude) or not -90 <= self.latitude <= 90:
            raise ValueError("latitude must be finite and between -90 and 90")
        if not math.isfinite(self.longitude) or not -180 <= self.longitude <= 180:
            raise ValueError("longitude must be finite and between -180 and 180")


@dataclass(frozen=True)
class RouteResult:
    distance_km: float
    estimated_duration_minutes: int
    geometry: Any
    origin: Coordinates
    destination: Coordinates
    provider: str

    def __post_init__(self) -> None:
        if not math.isfinite(self.distance_km) or self.distance_km <= 0:
            raise ValueError("route distance must be finite and greater than zero")
        if self.estimated_duration_minutes < 0:
            raise ValueError("route duration cannot be negative")
        if not self.provider.strip():
            raise ValueError("route provider is required")
