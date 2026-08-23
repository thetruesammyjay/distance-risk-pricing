from __future__ import annotations

from database.repositories import InMemoryFareQuoteRepository, SqlAlchemyFareQuoteRepository
from database.session import create_session_factory
from services.api_gateway.app.application import FareEstimationService
from services.api_gateway.app.config import Settings
from services.demand_service.service import DemandService
from services.risk_service.service import RiskComponents, RiskService
from services.routing_service.osrm import OSRMAdapter
from services.routing_service.service import RoutingService


def build_fare_service(settings: Settings) -> FareEstimationService:
    routing = RoutingService(
        OSRMAdapter(settings.routing_base_url, settings.routing_timeout_seconds)
    )
    risk = RiskService(
        settings.risk_mode,
        RiskComponents(
            accident=settings.risk_accident_weight,
            road=settings.risk_road_weight,
            security=settings.risk_security_weight,
        ),
    )
    demand = DemandService(
        settings.demand_mode,
        settings.pricing_demand_sensitivity,
        settings.pricing_demand_cap,
    )
    if settings.database_url:
        repository = SqlAlchemyFareQuoteRepository(create_session_factory(settings.database_url))
    else:
        repository = InMemoryFareQuoteRepository()
    return FareEstimationService(settings, routing, risk, demand, repository)
