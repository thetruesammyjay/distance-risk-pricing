from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Coordinates:
    latitude: float
    longitude: float


@dataclass(frozen=True)
class RouteResult:
    distance_km: float
    estimated_duration_minutes: int
    geometry: Any
    origin: Coordinates
    destination: Coordinates
    provider: str
