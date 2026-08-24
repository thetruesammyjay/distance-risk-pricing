"""Validate liveness, readiness, and metrics on a deployed API."""

from __future__ import annotations

import os
import sys

import httpx


def main() -> None:
    base_url = os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    api_key = os.getenv("API_KEY")
    headers = {"X-API-Key": api_key} if api_key else {}
    with httpx.Client(timeout=15) as client:
        for path, expected in (("/health", 200), ("/ready", 200), ("/metrics", 200)):
            response = client.get(f"{base_url}{path}", headers=headers)
            print(f"{path}: {response.status_code}")
            if response.status_code != expected:
                sys.exit(1)


if __name__ == "__main__":
    main()
