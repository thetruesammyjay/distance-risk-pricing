from __future__ import annotations

from services.routing_service.models import Coordinates, RouteResult
from services.routing_service.osrm import OSRMAdapter


class RoutingService:
    def __init__(self, provider: OSRMAdapter) -> None:
        self.provider = provider

    async def estimate(self, origin: Coordinates, destination: Coordinates) -> RouteResult:
        return await self.provider.get_route(origin, destination)
