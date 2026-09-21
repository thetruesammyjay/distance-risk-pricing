from __future__ import annotations

import httpx

from database.repositories import InMemoryFareQuoteRepository, SqlAlchemyFareQuoteRepository
from database.session import create_session_factory
from services.api_gateway.app.application import FareEstimationService
from services.api_gateway.app.config import Settings
from services.demand_service.service import (
    DemandService,
    ExternalDemandProvider,
    SimulatedDemandProvider,
    TimeOfDayDemandProvider,
    UnavailableDemandProvider,
)
from services.risk_service.service import (
    ExternalRiskProvider,
    OpenMeteoRiskProvider,
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
            cache_ttl_seconds=settings.routing_cache_ttl_seconds,
            cache_max_entries=settings.routing_cache_max_entries,
        )
    )
    if settings.risk_mode == "simulated":
        risk_provider = SimulatedRiskProvider(settings.simulation_seed)
    elif settings.risk_mode == "open_meteo" and settings.risk_provider_url:
        risk_provider = OpenMeteoRiskProvider(
            settings.risk_provider_url,
            client=client,
            timeout_seconds=settings.provider_timeout_seconds,
            retries=settings.provider_retries,
        )
    elif settings.risk_provider_url:
        risk_provider = ExternalRiskProvider(
            settings.risk_provider_url,
            client=client,
            api_key=(
                settings.risk_provider_api_key.get_secret_value()
                if settings.risk_provider_api_key
                else None
            ),
            timeout_seconds=settings.provider_timeout_seconds,
            retries=settings.provider_retries,
        )
    else:
        risk_provider = UnavailableRiskProvider()
    risk = RiskService(
        risk_provider,
        RiskComponents(
            accident=settings.risk_accident_weight,
            road=settings.risk_road_weight,
            security=settings.risk_security_weight,
        ),
    )
    if settings.demand_mode == "simulated":
        demand_provider = SimulatedDemandProvider(
            settings.demand_simulated_requests, settings.demand_simulated_drivers
        )
    elif settings.demand_mode == "time_of_day":
        demand_provider = TimeOfDayDemandProvider(
            baseline_requests=settings.demand_simulated_requests,
            baseline_available_drivers=settings.demand_simulated_drivers,
            timezone_name=settings.demand_timezone,
        )
    elif settings.demand_provider_url:
        demand_provider = ExternalDemandProvider(
            settings.demand_provider_url,
            client=client,
            api_key=(
                settings.demand_provider_api_key.get_secret_value()
                if settings.demand_provider_api_key
                else None
            ),
            timeout_seconds=settings.provider_timeout_seconds,
            retries=settings.provider_retries,
        )
    else:
        demand_provider = UnavailableDemandProvider()
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
