"""Small HTTP load smoke test; run with `uv run python scripts/load_test.py`."""

from __future__ import annotations

import asyncio
import os
import statistics
import time

import httpx


async def main() -> None:
    base_url = os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    requests = int(os.getenv("REQUESTS", "100"))
    concurrency = max(1, int(os.getenv("CONCURRENCY", "10")))
    api_key = os.getenv("API_KEY")
    headers = {"X-API-Key": api_key} if api_key else {}
    semaphore = asyncio.Semaphore(concurrency)
    durations: list[float] = []
    statuses: dict[int, int] = {}

    async with httpx.AsyncClient(timeout=15) as client:
        async def request_once() -> None:
            async with semaphore:
                started = time.perf_counter()
                response = await client.get(f"{base_url}/ready", headers=headers)
                durations.append(time.perf_counter() - started)
                statuses[response.status_code] = statuses.get(response.status_code, 0) + 1

        await asyncio.gather(*(request_once() for _ in range(requests)))

    print(f"requests={requests} concurrency={concurrency} statuses={statuses}")
    print(
        "latency_ms="
        f"p50={statistics.median(durations) * 1000:.2f} "
        f"max={max(durations) * 1000:.2f}"
    )
    if statuses.get(200, 0) != requests:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
