from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import datetime
from typing import Protocol

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from database.models import FareQuoteModel
from services.common.errors import DomainError


class FareQuoteRepository(Protocol):
    async def save(self, quote: Mapping[str, object]) -> None: ...

    async def get(self, quote_id: str) -> dict[str, object] | None: ...


class InMemoryFareQuoteRepository:
    def __init__(self) -> None:
        self._quotes: dict[str, dict[str, object]] = {}

    async def save(self, quote: Mapping[str, object]) -> None:
        quote_id = str(quote["quote_id"])
        self._quotes[quote_id] = dict(quote)

    async def get(self, quote_id: str) -> dict[str, object] | None:
        return self._quotes.get(quote_id)

    async def health_check(self) -> bool:
        return True


class SqlAlchemyFareQuoteRepository:
    def __init__(self, factory: sessionmaker[Session]) -> None:
        self.factory = factory

    async def save(self, quote: Mapping[str, object]) -> None:
        await asyncio.to_thread(self._save_sync, dict(quote))

    def _save_sync(self, quote: Mapping[str, object]) -> None:
        route = quote["route"]
        risk = quote["risk"]
        demand = quote["demand"]
        fare = quote["fare"]
        origin = quote["origin"]
        destination = quote["destination"]
        mappings = {
            "route": route,
            "risk": risk,
            "demand": demand,
            "fare": fare,
            "origin": origin,
            "destination": destination,
        }
        if any(not isinstance(value, Mapping) for value in mappings.values()):
            raise DomainError("DATABASE_ERROR", "The fare quote payload is invalid.")
        created_at = quote["created_at"]
        requested_at = quote["requested_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        if isinstance(requested_at, str):
            requested_at = datetime.fromisoformat(requested_at.replace("Z", "+00:00"))
        try:
            with self.factory() as session:
                session.add(
                    FareQuoteModel(
                        id=str(quote["quote_id"]),
                        created_at=created_at,
                        requested_at=requested_at,
                        origin_latitude=origin["latitude"],
                        origin_longitude=origin["longitude"],
                        destination_latitude=destination["latitude"],
                        destination_longitude=destination["longitude"],
                        distance_km=route["distance_km"],
                        estimated_duration_minutes=route["estimated_duration_minutes"],
                        risk_score=risk["score"],
                        risk_classification=risk["classification"],
                        demand_multiplier=demand["multiplier"],
                        currency=fare["currency"],
                        base_fare=fare["base_fare"],
                        distance_component=fare["distance_component"],
                        risk_adjustment=fare["risk_adjustment"],
                        demand_adjustment=fare["demand_adjustment"],
                        total_fare=fare["total"],
                        formula_mode=fare["formula_mode"],
                        formula_version=fare["formula_version"],
                        pricing_coefficient_version=fare["coefficient_version"],
                        risk_source_summary=", ".join(risk["data_sources"]),
                        demand_source_type=demand["source_type"],
                        payload=dict(quote),
                    )
                )
                session.commit()
        except SQLAlchemyError as exc:
            raise DomainError("DATABASE_ERROR", "The fare quote could not be saved.") from exc

    async def get(self, quote_id: str) -> dict[str, object] | None:
        return await asyncio.to_thread(self._get_sync, quote_id)

    async def health_check(self) -> bool:
        return await asyncio.to_thread(self._health_check_sync)

    def _health_check_sync(self) -> bool:
        try:
            with self.factory() as session:
                session.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError:
            return False

    def _get_sync(self, quote_id: str) -> dict[str, object] | None:
        try:
            with self.factory() as session:
                record = session.get(FareQuoteModel, quote_id)
                return record.payload if record else None
        except SQLAlchemyError as exc:
            raise DomainError("DATABASE_ERROR", "The fare quote could not be retrieved.") from exc
