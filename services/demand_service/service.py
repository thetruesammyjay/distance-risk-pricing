from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from services.common.errors import DomainError

DEMAND_SOURCE_TYPES = frozenset({"observed", "external", "simulated"})


@dataclass(frozen=True)
class DemandEstimate:
    requests: int
    available_drivers: int
    multiplier: Decimal
    source_type: str


class DemandProvider(Protocol):
    def get_snapshot(self) -> DemandEstimate: ...


def demand_multiplier(
    requests: int,
    available_drivers: int,
    sensitivity: Decimal,
    cap: Decimal,
) -> Decimal:
    if requests < 0 or available_drivers < 0:
        raise DomainError("INVALID_DEMAND", "Demand counts cannot be negative.")
    if not sensitivity.is_finite() or not cap.is_finite() or sensitivity < 0 or cap < 1:
        raise DomainError("INVALID_DEMAND_CONFIGURATION", "Demand sensitivity and cap are invalid.")
    if available_drivers == 0:
        return Decimal("1.0") if requests == 0 else cap
    ratio = Decimal(requests) / Decimal(available_drivers)
    if ratio <= 1:
        return Decimal("1.0")
    return min(Decimal("1") + sensitivity * (ratio - Decimal("1")), cap)


class SimulatedDemandProvider:
    """Deterministic development provider; values are not live market activity."""

    def __init__(self, requests: int = 42, available_drivers: int = 28) -> None:
        if requests < 0 or available_drivers < 0:
            raise ValueError("simulated demand counts cannot be negative")
        self.requests = requests
        self.available_drivers = available_drivers

    def get_snapshot(self) -> DemandEstimate:
        return DemandEstimate(
            requests=self.requests,
            available_drivers=self.available_drivers,
            multiplier=Decimal("1"),
            source_type="simulated",
        )


class UnavailableDemandProvider:
    """Explicit failure mode used until a real demand feed is configured."""

    def get_snapshot(self) -> DemandEstimate:
        raise DomainError(
            "DEMAND_DATA_UNAVAILABLE",
            "No observed or externally sourced demand provider is configured.",
        )


class DemandService:
    def __init__(self, provider: DemandProvider, sensitivity: Decimal, cap: Decimal) -> None:
        self.provider = provider
        self.sensitivity = sensitivity
        self.cap = cap
        if not sensitivity.is_finite() or not cap.is_finite() or sensitivity < 0 or cap < 1:
            raise ValueError("demand sensitivity must be non-negative and cap must be >= 1")

    def estimate(self) -> DemandEstimate:
        snapshot = self.provider.get_snapshot()
        if snapshot.source_type not in DEMAND_SOURCE_TYPES:
            raise DomainError(
                "DEMAND_DATA_UNAVAILABLE", "The demand provider returned an unknown source type."
            )
        return DemandEstimate(
            requests=snapshot.requests,
            available_drivers=snapshot.available_drivers,
            multiplier=demand_multiplier(
                snapshot.requests,
                snapshot.available_drivers,
                self.sensitivity,
                self.cap,
            ),
            source_type=snapshot.source_type,
        )
