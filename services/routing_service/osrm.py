from __future__ import annotations

import asyncio
import time
from collections import OrderedDict
from typing import Any

import httpx

from services.common.errors import DomainError
from services.routing_service.models import Coordinates, RouteResult


class OSRMAdapter:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float = 10.0,
        *,
        retries: int = 2,
        profile: str = "driving",
        client: httpx.AsyncClient | None = None,
        cache_ttl_seconds: float = 300.0,
        cache_max_entries: int = 512,
    ) -> None:
        if not base_url.startswith(("http://", "https://")):
            raise ValueError("routing base URL must use HTTP or HTTPS")
        if timeout_seconds <= 0 or retries < 0:
            raise ValueError("routing timeout must be positive and retries cannot be negative")
        if cache_ttl_seconds < 0 or cache_max_entries < 1:
            raise ValueError("routing cache TTL cannot be negative and size must be positive")
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.profile = profile
        self.client = client
        self.cache_ttl_seconds = cache_ttl_seconds
        self.cache_max_entries = cache_max_entries
        self._cache: OrderedDict[tuple[str, str, str, str, str], tuple[float, RouteResult]] = (
            OrderedDict()
        )
        self._inflight: dict[tuple[str, str, str, str, str], asyncio.Task[RouteResult]] = {}
        self._cache_lock = asyncio.Lock()

    async def close(self) -> None:
        if self.client is not None:
            await self.client.aclose()

    async def health_check(self) -> bool:
        return bool(self.base_url and self.profile)

    async def get_route(self, origin: Coordinates, destination: Coordinates) -> RouteResult:
        key = self._cache_key(origin, destination)
        cached = await self._get_cached(key)
        if cached is not None:
            return cached

        async with self._cache_lock:
            task = self._inflight.get(key)
            if task is None:
                task = asyncio.create_task(self._fetch_route(origin, destination))
                self._inflight[key] = task
        try:
            route = await task
        finally:
            if task.done():
                async with self._cache_lock:
                    if self._inflight.get(key) is task:
                        self._inflight.pop(key, None)
        await self._store_cached(key, route)
        return route

    async def _fetch_route(self, origin: Coordinates, destination: Coordinates) -> RouteResult:
        url = (
            f"{self.base_url}/route/v1/{self.profile}/"
            f"{origin.longitude},{origin.latitude};{destination.longitude},{destination.latitude}"
        )
        owns_client = self.client is None
        client = self.client or httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout_seconds, connect=self.timeout_seconds)
        )
        try:
            payload = await self._request_with_retries(client, url)
        finally:
            if owns_client:
                await client.aclose()
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
            if not isinstance(geometry, dict):
                raise ValueError("route geometry must be a JSON object")
        except (KeyError, TypeError, ValueError) as exc:
            raise DomainError(
                "ROUTING_UNAVAILABLE", "The routing provider returned an invalid response."
            ) from exc
        try:
            return RouteResult(
                distance_km=distance_km,
                estimated_duration_minutes=duration_minutes,
                geometry=geometry,
                origin=origin,
                destination=destination,
                provider="osrm",
            )
        except ValueError as exc:
            raise DomainError(
                "ROUTING_UNAVAILABLE", "The routing provider returned an invalid route."
            ) from exc

    async def _request_with_retries(self, client: httpx.AsyncClient, url: str) -> dict[str, Any]:
        for attempt in range(self.retries + 1):
            try:
                response = await client.get(
                    url, params={"overview": "full", "geometries": "geojson"}
                )
                if response.status_code >= 500 and attempt < self.retries:
                    await response.aclose()
                    await asyncio.sleep(0.1 * (2**attempt))
                    continue
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise ValueError("routing response must be a JSON object")
                return payload
            except httpx.HTTPStatusError as exc:
                raise DomainError(
                    "ROUTING_UNAVAILABLE", "The routing provider returned an error."
                ) from exc
            except (httpx.RequestError, ValueError) as exc:
                if attempt < self.retries:
                    await asyncio.sleep(0.1 * (2**attempt))
                    continue
                raise DomainError(
                    "ROUTING_UNAVAILABLE", "The route could not be calculated."
                ) from exc
        raise DomainError("ROUTING_UNAVAILABLE", "The route could not be calculated.")

    async def _get_cached(self, key: tuple[str, str, str, str, str]) -> RouteResult | None:
        if self.cache_ttl_seconds == 0:
            return None
        now = time.monotonic()
        async with self._cache_lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            expires_at, route = entry
            if expires_at <= now:
                self._cache.pop(key, None)
                return None
            self._cache.move_to_end(key)
            return route

    async def _store_cached(self, key: tuple[str, str, str, str, str], route: RouteResult) -> None:
        if self.cache_ttl_seconds == 0:
            return
        async with self._cache_lock:
            self._cache[key] = (time.monotonic() + self.cache_ttl_seconds, route)
            self._cache.move_to_end(key)
            while len(self._cache) > self.cache_max_entries:
                self._cache.popitem(last=False)

    def _cache_key(
        self, origin: Coordinates, destination: Coordinates
    ) -> tuple[str, str, str, str, str]:
        return (
            self.profile,
            f"{origin.latitude:.5f}",
            f"{origin.longitude:.5f}",
            f"{destination.latitude:.5f}",
            f"{destination.longitude:.5f}",
        )
