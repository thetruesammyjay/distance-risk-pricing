from __future__ import annotations

from typing import Protocol

from services.routing_service.models import Coordinates, RouteResult


class RoutingProvider(Protocol):
    async def get_route(self, origin: Coordinates, destination: Coordinates) -> RouteResult: ...


class RoutingService:
    def __init__(self, provider: RoutingProvider) -> None:
        self.provider = provider

    async def estimate(self, origin: Coordinates, destination: Coordinates) -> RouteResult:
        return await self.provider.get_route(origin, destination)

    async def close(self) -> None:
        close = getattr(self.provider, "close", None)
        if close is not None:
            await close()
