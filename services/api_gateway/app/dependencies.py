from __future__ import annotations

import httpx

from database.repositories import InMemoryFareQuoteRepository, SqlAlchemyFareQuoteRepository
from database.session import create_session_factory
from services.api_gateway.app.application import FareEstimationService
from services.api_gateway.app.config import Settings
from services.demand_service.service import (
    DemandService,
    SimulatedDemandProvider,
    UnavailableDemandProvider,
)
from services.risk_service.service import (
    RiskComponents,
    RiskService,
    SimulatedRiskProvider,
    UnavailableRiskProvider,
)
from services.routing_service.osrm import OSRMAdapter
from services.routing_service.service import RoutingService


def build_fare_service(settings: Settings) -> FareEstimationService:
    client = httpx.AsyncClient(
        timeout=httpx.Timeout(
            settings.routing_timeout_seconds, connect=settings.routing_timeout_seconds
        )
    )
    routing = RoutingService(
        OSRMAdapter(
            settings.routing_base_url,
            settings.routing_timeout_seconds,
            retries=settings.routing_retries,
            profile=settings.routing_profile,
            client=client,
        )
    )
    risk_provider = (
        SimulatedRiskProvider(settings.simulation_seed)
        if settings.risk_mode == "simulated"
        else UnavailableRiskProvider()
    )
    risk = RiskService(
        risk_provider,
        RiskComponents(
            accident=settings.risk_accident_weight,
            road=settings.risk_road_weight,
            security=settings.risk_security_weight,
        ),
    )
    demand_provider = (
        SimulatedDemandProvider(
            settings.demand_simulated_requests, settings.demand_simulated_drivers
        )
        if settings.demand_mode == "simulated"
        else UnavailableDemandProvider()
    )
    demand = DemandService(
        demand_provider,
        settings.pricing_demand_sensitivity,
        settings.pricing_demand_cap,
    )
    if settings.database_url:
        repository = SqlAlchemyFareQuoteRepository(
            create_session_factory(
                settings.database_url,
                pool_size=settings.database_pool_size,
                max_overflow=settings.database_max_overflow,
                pool_timeout=settings.database_pool_timeout_seconds,
            )
        )
    else:
        repository = InMemoryFareQuoteRepository()
    return FareEstimationService(settings, routing, risk, demand, repository)
