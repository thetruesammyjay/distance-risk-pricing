from __future__ import annotations

import asyncio
from dataclasses import dataclass
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


class DemandProvider(Protocol):
    async def get_snapshot(self) -> DemandEstimate: ...

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

    async def get_snapshot(self) -> DemandEstimate:
        return DemandEstimate(
            requests=self.requests,
            available_drivers=self.available_drivers,
            multiplier=Decimal("1"),
            source_type="simulated",
        )

    async def health_check(self) -> bool:
        return True


class ExternalDemandProvider:
    """HTTP adapter for a live demand snapshot service."""

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

    async def get_snapshot(self) -> DemandEstimate:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        for attempt in range(self.retries + 1):
            try:
                response = await self.client.get(
                    self.endpoint, headers=headers, timeout=self.timeout_seconds
                )
                if response.status_code >= 500 and attempt < self.retries:
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

    async def get_snapshot(self) -> DemandEstimate:
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

    async def estimate(self) -> DemandEstimate:
        snapshot = await self.provider.get_snapshot()
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

    async def ready(self) -> bool:
        return await self.provider.health_check()


def _parse_demand_response(payload: dict[str, Any]) -> DemandEstimate:
    try:
        requests = payload["requests"]
        available_drivers = payload["available_drivers"]
        if not isinstance(requests, int) or not isinstance(available_drivers, int):
            raise TypeError("demand counts must be integers")
        return DemandEstimate(
            requests=int(requests),
            available_drivers=int(available_drivers),
            multiplier=Decimal("1"),
            source_type=str(payload.get("source_type", "external")),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("demand response is invalid") from exc
