from __future__ import annotations

import asyncio
import time
from collections import defaultdict


class MetricsRegistry:
    """Small dependency-free request metrics registry.

    The endpoint is intentionally Prometheus-compatible while keeping the
    application free of a mandatory metrics vendor dependency. For multiple
    replicas, replace this registry with a shared metrics backend.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._requests: dict[tuple[str, str, str], int] = defaultdict(int)
        self._durations: dict[tuple[str, str], float] = defaultdict(float)

    async def observe(
        self, method: str, path: str, status: int, duration_seconds: float
    ) -> None:
        async with self._lock:
            self._requests[(method, path, str(status))] += 1
            self._durations[(method, path)] += duration_seconds

    async def render(self) -> str:
        async with self._lock:
            requests = dict(self._requests)
            durations = dict(self._durations)
        lines = [
            "# HELP http_requests_total Total HTTP requests.",
            "# TYPE http_requests_total counter",
        ]
        for (method, path, status), count in sorted(requests.items()):
            lines.append(
                f'http_requests_total{{method="{_label(method)}",path="{_label(path)}",'
                f'status="{status}"}} {count}'
            )
        lines.extend(
            [
                "# HELP http_request_duration_seconds_total Total request duration in seconds.",
                "# TYPE http_request_duration_seconds_total counter",
            ]
        )
        for (method, path), duration in sorted(durations.items()):
            lines.append(
                f'http_request_duration_seconds_total{{method="{_label(method)}",'
                f'path="{_label(path)}"}} {duration:.6f}'
            )
        return "\n".join(lines) + "\n"


class SlidingWindowRateLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._events: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def allow(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        async with self._lock:
            events = [timestamp for timestamp in self._events[key] if timestamp > cutoff]
            if len(events) >= self.limit:
                self._events[key] = events
                return False
            events.append(now)
            self._events[key] = events
            if len(self._events) > 10000:
                self._events = defaultdict(
                    list,
                    {
                        item_key: item_events
                        for item_key, item_events in self._events.items()
                        if item_events and item_events[-1] > cutoff
                    },
                )
            return True


def _label(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
