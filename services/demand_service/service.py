from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Protocol
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx

from services.common.errors import DomainError

DEMAND_SOURCE_TYPES = frozenset({"observed", "external", "simulated"})


@dataclass(frozen=True)
class DemandEstimate:
    requests: int
    available_drivers: int
    multiplier: Decimal
    source_type: str
    data_sources: tuple[str, ...] = ()


@dataclass(frozen=True)
class TimeOfDayDemandProfile:
    label: str
    pressure: Decimal


def time_of_day_demand_profile(local_timestamp: datetime) -> TimeOfDayDemandProfile:
    """Return a transparent academic demand-pressure profile for local time."""

    minute = local_timestamp.hour * 60 + local_timestamp.minute
    if 7 * 60 <= minute < 9 * 60:
        return TimeOfDayDemandProfile("morning peak", Decimal("1.50"))
    if 12 * 60 <= minute < 13 * 60:
        return TimeOfDayDemandProfile("midday activity", Decimal("1.20"))
    if 15 * 60 <= minute < 16 * 60:
        return TimeOfDayDemandProfile("afternoon slight peak", Decimal("1.10"))
    if 18 * 60 <= minute < 21 * 60:
        return TimeOfDayDemandProfile("evening medium peak", Decimal("1.30"))

    # Shoulders add small transitions around the main windows without making
    # the academic scenario look like a set of unrealistic step changes.
    if 6 * 60 <= minute < 7 * 60 or 9 * 60 <= minute < 10 * 60:
        return TimeOfDayDemandProfile("morning shoulder", Decimal("1.10"))
    if 11 * 60 <= minute < 12 * 60 or 13 * 60 <= minute < 14 * 60:
        return TimeOfDayDemandProfile("midday shoulder", Decimal("1.05"))
    if 16 * 60 <= minute < 18 * 60 or 21 * 60 <= minute < 22 * 60:
        return TimeOfDayDemandProfile("evening shoulder", Decimal("1.10"))

    return TimeOfDayDemandProfile("off-peak baseline", Decimal("0.85"))


class DemandProvider(Protocol):
    async def get_snapshot(
        self,
        origin: tuple[float, float] | None = None,
        destination: tuple[float, float] | None = None,
        requested_at: datetime | None = None,
    ) -> DemandEstimate: ...

    async def health_check(self) -> bool: ...


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

    async def get_snapshot(
        self, origin=None, destination=None, requested_at: datetime | None = None
    ) -> DemandEstimate:
        del origin, destination, requested_at
        return DemandEstimate(
            requests=self.requests,
            available_drivers=self.available_drivers,
            multiplier=Decimal("1"),
            source_type="simulated",
            data_sources=("simulated development scenario",),
        )

    async def health_check(self) -> bool:
        return True


class TimeOfDayDemandProvider:
    """Deterministic demand scenario based on local time, not live traffic."""

    def __init__(
        self,
        baseline_requests: int = 100,
        baseline_available_drivers: int = 100,
        timezone_name: str = "Africa/Lagos",
    ) -> None:
        if baseline_requests < 0 or baseline_available_drivers <= 0:
            raise ValueError("time-of-day demand baseline counts are invalid")
        try:
            timezone = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"unknown demand timezone: {timezone_name}") from exc
        self.baseline_requests = baseline_requests
        self.baseline_available_drivers = baseline_available_drivers
        self.timezone_name = timezone_name
        self.timezone = timezone

    async def get_snapshot(
        self,
        origin: tuple[float, float] | None = None,
        destination: tuple[float, float] | None = None,
        requested_at: datetime | None = None,
    ) -> DemandEstimate:
        del origin, destination
        timestamp = requested_at or datetime.now(UTC)
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise DomainError(
                "INVALID_REQUESTED_AT", "Time-of-day demand requires a timezone-aware timestamp."
            )
        local_timestamp = timestamp.astimezone(self.timezone)
        profile = time_of_day_demand_profile(local_timestamp)
        baseline_ratio = Decimal(self.baseline_requests) / Decimal(self.baseline_available_drivers)
        requests = int(
            (Decimal(self.baseline_available_drivers) * baseline_ratio * profile.pressure)
            .to_integral_value(rounding=ROUND_HALF_UP)
        )
        return DemandEstimate(
            requests=requests,
            available_drivers=self.baseline_available_drivers,
            multiplier=Decimal("1"),
            source_type="simulated",
            data_sources=(
                "time-of-day demand simulation",
                f"{profile.label} ({self.timezone_name})",
                f"academic scenario pressure factor={profile.pressure}",
            ),
        )

    async def health_check(self) -> bool:
        return True


class ExternalDemandProvider:
    """HTTP adapter for a validated demand snapshot service."""

    def __init__(
        self,
        endpoint: str,
        *,
        client: httpx.AsyncClient,
        api_key: str | None = None,
        timeout_seconds: float = 10.0,
        retries: int = 2,
    ) -> None:
        if not endpoint.startswith(("http://", "https://")):
            raise ValueError("demand provider URL must use HTTP or HTTPS")
        self.endpoint = endpoint
        self.client = client
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.retries = retries

    async def get_snapshot(
        self, origin=None, destination=None, requested_at: datetime | None = None
    ) -> DemandEstimate:
        del origin, destination, requested_at
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        for attempt in range(self.retries + 1):
            try:
                response = await self.client.get(
                    self.endpoint, headers=headers, timeout=self.timeout_seconds
                )
                if response.status_code >= 500 and attempt < self.retries:
                    await response.aclose()
                    await asyncio.sleep(0.1 * (2**attempt))
                    continue
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise ValueError("demand response must be an object")
                return _parse_demand_response(payload)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code < 500:
                    raise DomainError(
                        "DEMAND_DATA_UNAVAILABLE", "The demand provider rejected the request."
                    ) from exc
                if attempt < self.retries:
                    await asyncio.sleep(0.1 * (2**attempt))
                    continue
                raise DomainError(
                    "DEMAND_DATA_UNAVAILABLE", "The demand provider returned a server error."
                ) from exc
            except (httpx.RequestError, ValueError, TypeError) as exc:
                if attempt < self.retries:
                    await asyncio.sleep(0.1 * (2**attempt))
                    continue
                raise DomainError(
                    "DEMAND_DATA_UNAVAILABLE", "The demand provider could not be reached."
                ) from exc
        raise DomainError("DEMAND_DATA_UNAVAILABLE", "The demand provider could not be reached.")

    async def health_check(self) -> bool:
        return bool(self.endpoint and self.client)


class UnavailableDemandProvider:
    """Explicit failure mode used until a real demand feed is configured."""

    async def get_snapshot(
        self, origin=None, destination=None, requested_at: datetime | None = None
    ) -> DemandEstimate:
        del origin, destination, requested_at
        raise DomainError(
            "DEMAND_DATA_UNAVAILABLE",
            "No observed or externally sourced demand provider is configured.",
        )

    async def health_check(self) -> bool:
        return False


class DemandService:
    def __init__(self, provider: DemandProvider, sensitivity: Decimal, cap: Decimal) -> None:
        self.provider = provider
        self.sensitivity = sensitivity
        self.cap = cap
        if not sensitivity.is_finite() or not cap.is_finite() or sensitivity < 0 or cap < 1:
            raise ValueError("demand sensitivity must be non-negative and cap must be >= 1")

    async def estimate(
        self,
        origin: tuple[float, float] | None = None,
        destination: tuple[float, float] | None = None,
        requested_at: datetime | None = None,
    ) -> DemandEstimate:
        snapshot = await self.provider.get_snapshot(origin, destination, requested_at)
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
            data_sources=snapshot.data_sources,
        )

    async def ready(self) -> bool:
        return await self.provider.health_check()


def _parse_demand_response(payload: dict[str, Any]) -> DemandEstimate:
    try:
        requests = payload["requests"]
        available_drivers = payload["available_drivers"]
        if not isinstance(requests, int) or not isinstance(available_drivers, int):
            raise TypeError("demand counts must be integers")
        sources = payload.get("data_sources", ["external demand provider"])
        if (
            not isinstance(sources, list)
            or not sources
            or not all(isinstance(item, str) and item.strip() for item in sources)
        ):
            raise ValueError("data_sources must be a non-empty array")
        return DemandEstimate(
            requests=int(requests),
            available_drivers=int(available_drivers),
            multiplier=Decimal("1"),
            source_type=str(payload.get("source_type", "external")),
            data_sources=tuple(sources),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("demand response is invalid") from exc
