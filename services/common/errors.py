from __future__ import annotations

from typing import Any


class DomainError(Exception):
    """An expected application failure that can be safely returned to clients."""

    _STATUS_BY_CODE = {
        "INVALID_COORDINATES": 422,
        "INVALID_DEMAND": 422,
        "INVALID_DEMAND_CONFIGURATION": 500,
        "INVALID_PRICING_CONFIGURATION": 500,
        "INVALID_RISK_CONFIGURATION": 500,
        "QUOTE_NOT_FOUND": 404,
        "ROUTE_NOT_FOUND": 404,
        "DATABASE_ERROR": 503,
        "DEMAND_DATA_UNAVAILABLE": 503,
        "RISK_DATA_UNAVAILABLE": 503,
        "ROUTING_UNAVAILABLE": 503,
        "INTERNAL_ERROR": 500,
    }

    def __init__(
        self,
        code: str,
        message: str,
        details: Any = None,
        *,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details
        self.status_code = status_code or self._STATUS_BY_CODE.get(code, 400)
