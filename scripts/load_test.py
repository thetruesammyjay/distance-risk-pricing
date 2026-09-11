"""Small fare endpoint load smoke test; run with `uv run python scripts/load_test.py`."""

from __future__ import annotations

import asyncio
import os
import statistics
import time
from datetime import UTC, datetime

import httpx
from dotenv import load_dotenv


async def main() -> None:
    load_dotenv()
    base_url = os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    requests = int(os.getenv("REQUESTS", "20"))
    concurrency = max(1, int(os.getenv("CONCURRENCY", "5")))
    api_key = os.getenv("API_KEY")
    headers = {"X-API-Key": api_key} if api_key else {}
    payload = {
        "origin": {"latitude": 5.3921, "longitude": 7.0337},
        "destination": {"latitude": 5.4865, "longitude": 7.0259},
        "requested_at": datetime.now(UTC).isoformat(),
    }
    semaphore = asyncio.Semaphore(concurrency)
    durations: list[float] = []
    statuses: dict[int, int] = {}

    async with httpx.AsyncClient(timeout=30) as client:

        async def request_once() -> None:
            async with semaphore:
                started = time.perf_counter()
                response = await client.post(
                    f"{base_url}/api/v1/fares/estimate", json=payload, headers=headers
                )
                durations.append(time.perf_counter() - started)
                statuses[response.status_code] = statuses.get(response.status_code, 0) + 1

        await asyncio.gather(*(request_once() for _ in range(requests)))

    durations.sort()
    p95_index = min(len(durations) - 1, max(0, int(len(durations) * 0.95) - 1))
    print(f"requests={requests} concurrency={concurrency} statuses={statuses}")
    print(
        "latency_ms="
        f"p50={statistics.median(durations) * 1000:.2f} "
        f"p95={durations[p95_index] * 1000:.2f} "
        f"max={max(durations) * 1000:.2f}"
    )
    if statuses.get(200, 0) != requests:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
