from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Protocol

from sqlalchemy.orm import Session, sessionmaker

from database.models import FareQuoteModel


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


class SqlAlchemyFareQuoteRepository:
    def __init__(self, factory: sessionmaker[Session]) -> None:
        self.factory = factory

    async def save(self, quote: Mapping[str, object]) -> None:
        route = quote["route"]
        risk = quote["risk"]
        demand = quote["demand"]
        fare = quote["fare"]
        origin = quote["origin"]
        destination = quote["destination"]
        assert isinstance(route, Mapping)
        assert isinstance(risk, Mapping)
        assert isinstance(demand, Mapping)
        assert isinstance(fare, Mapping)
        assert isinstance(origin, Mapping)
        assert isinstance(destination, Mapping)
        created_at = quote["created_at"]
        requested_at = quote["requested_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        if isinstance(requested_at, str):
            requested_at = datetime.fromisoformat(requested_at.replace("Z", "+00:00"))
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

    async def get(self, quote_id: str) -> dict[str, object] | None:
        with self.factory() as session:
            record = session.get(FareQuoteModel, quote_id)
            return record.payload if record else None
