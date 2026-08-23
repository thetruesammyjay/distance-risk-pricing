from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from services.common.errors import DomainError


@dataclass(frozen=True)
class DemandEstimate:
    requests: int
    available_drivers: int
    multiplier: Decimal
    source_type: str


def demand_multiplier(
    requests: int,
    available_drivers: int,
    sensitivity: Decimal,
    cap: Decimal,
) -> Decimal:
    if requests < 0 or available_drivers < 0:
        raise DomainError("INVALID_DEMAND", "Demand counts cannot be negative.")
    if sensitivity < 0 or cap < 1:
        raise DomainError("INVALID_DEMAND_CONFIGURATION", "Demand sensitivity and cap are invalid.")
    if available_drivers == 0:
        return Decimal("1.0") if requests == 0 else cap
    ratio = Decimal(requests) / Decimal(available_drivers)
    if ratio <= 1:
        return Decimal("1.0")
    return min(Decimal("1") + sensitivity * (ratio - Decimal("1")), cap)


class DemandService:
    def __init__(self, mode: str, sensitivity: Decimal, cap: Decimal) -> None:
        self.mode = mode
        self.sensitivity = sensitivity
        self.cap = cap

    def estimate(self) -> DemandEstimate:
        if self.mode != "simulated":
            raise DomainError(
                "DEMAND_DATA_UNAVAILABLE", "No configured demand source is available."
            )
        requests, available = 42, 28
        return DemandEstimate(
            requests=requests,
            available_drivers=available,
            multiplier=demand_multiplier(requests, available, self.sensitivity, self.cap),
            source_type="simulated",
        )
