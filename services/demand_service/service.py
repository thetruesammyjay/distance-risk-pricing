from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Protocol

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


class TomTomTrafficDemandProvider:
    """Use TomTom observed/free-flow speeds as a demand-pressure proxy.

    TomTom does not provide ride-request or available-driver counts here. We
    normalize the speed ratio to a fixed index so the pricing engine can consume
    it, and expose the transformation in data_sources.
    """

    def __init__(
        self,
        endpoint: str,
        *,
        client: httpx.AsyncClient,
        api_key: str | None,
        timeout_seconds: float = 10.0,
        retries: int = 2,
    ) -> None:
        if not endpoint.startswith(("http://", "https://")):
            raise ValueError("TomTom traffic URL must use HTTP or HTTPS")
        if not api_key:
            raise ValueError("TomTom traffic API key is required")
        self.endpoint = endpoint
        self.client = client
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.retries = retries

    async def get_snapshot(
        self,
        origin: tuple[float, float] | None = None,
        destination: tuple[float, float] | None = None,
        requested_at: datetime | None = None,
    ) -> DemandEstimate:
        del requested_at
        if origin is None or destination is None:
            raise DomainError(
                "DEMAND_DATA_UNAVAILABLE", "Traffic demand requires a route location."
            )
        latitude = (origin[0] + destination[0]) / 2
        longitude = (origin[1] + destination[1]) / 2
        params = {
            "key": self.api_key,
            "point": f"{latitude},{longitude}",
            "unit": "KMPH",
        }
        for attempt in range(self.retries + 1):
            try:
                response = await self.client.get(
                    self.endpoint, params=params, timeout=self.timeout_seconds
                )
                if response.status_code >= 500 and attempt < self.retries:
                    await response.aclose()
                    await asyncio.sleep(0.1 * (2**attempt))
                    continue
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise ValueError("TomTom traffic response must be an object")
                return _parse_tomtom_response(payload)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code < 500:
                    raise DomainError(
                        "DEMAND_DATA_UNAVAILABLE", "TomTom rejected the traffic request."
                    ) from exc
                if attempt < self.retries:
                    await asyncio.sleep(0.1 * (2**attempt))
                    continue
                raise DomainError(
                    "DEMAND_DATA_UNAVAILABLE", "TomTom returned a traffic server error."
                ) from exc
            except (httpx.RequestError, ValueError, TypeError, KeyError) as exc:
                if attempt < self.retries:
                    await asyncio.sleep(0.1 * (2**attempt))
                    continue
                raise DomainError(
                    "DEMAND_DATA_UNAVAILABLE", "TomTom traffic data could not be reached."
                ) from exc
        raise DomainError("DEMAND_DATA_UNAVAILABLE", "TomTom traffic data could not be reached.")

    async def health_check(self) -> bool:
        return bool(self.endpoint and self.api_key and self.client)


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


def _parse_tomtom_response(payload: dict[str, Any]) -> DemandEstimate:
    flow = payload.get("flowSegmentData")
    if not isinstance(flow, dict):
        raise ValueError("TomTom response is missing flowSegmentData")
    current_speed = float(flow["currentSpeed"])
    free_flow_speed = float(flow["freeFlowSpeed"])
    if current_speed <= 0 or free_flow_speed <= 0:
        raise ValueError("TomTom speeds must be positive")
    pressure = max(1.0, min(free_flow_speed / current_speed, 2.5))
    return DemandEstimate(
        requests=round(pressure * 100),
        available_drivers=100,
        multiplier=Decimal("1"),
        source_type="external",
        data_sources=(
            "TomTom Traffic Flow API observed speed",
            "demand-pressure proxy = free-flow speed / current speed",
        ),
    )
