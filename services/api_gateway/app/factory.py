from __future__ import annotations

from fastapi import FastAPI

from services.api_gateway.app.main import app


def create_app() -> FastAPI:
    """Return the configured application; kept as a seam for integration tests."""
    return app
