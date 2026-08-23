from __future__ import annotations

from typing import Any

import httpx

from services.common.errors import DomainError
from services.routing_service.models import Coordinates, RouteResult


class OSRMAdapter:
    def __init__(self, base_url: str, timeout_seconds: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def get_route(self, origin: Coordinates, destination: Coordinates) -> RouteResult:
        url = (
            f"{self.base_url}/route/v1/driving/"
            f"{origin.longitude},{origin.latitude};{destination.longitude},{destination.latitude}"
        )
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(
                    url, params={"overview": "full", "geometries": "geojson"}
                )
                response.raise_for_status()
                payload: dict[str, Any] = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise DomainError("ROUTING_UNAVAILABLE", "The route could not be calculated.") from exc
        routes = payload.get("routes")
        if payload.get("code") != "Ok" or not isinstance(routes, list) or not routes:
            raise DomainError(
                "ROUTE_NOT_FOUND", "No drivable route was found for the selected points."
            )
        route = routes[0]
        try:
            distance_km = float(route["distance"]) / 1000
            duration_minutes = round(float(route["duration"]) / 60)
            geometry = route.get("geometry")
        except (KeyError, TypeError, ValueError) as exc:
            raise DomainError(
                "ROUTING_UNAVAILABLE", "The routing provider returned an invalid response."
            ) from exc
        return RouteResult(
            distance_km=distance_km,
            estimated_duration_minutes=duration_minutes,
            geometry=geometry,
            origin=origin,
            destination=destination,
            provider="osrm",
        )
