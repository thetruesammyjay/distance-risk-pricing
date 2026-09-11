from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from database.repositories import FareQuoteRepository
from services.api_gateway.app.config import Settings
from services.api_gateway.app.schemas import (
    DemandResponse,
    FareEstimateRequest,
    FareEstimateResponse,
    FareResponse,
    RiskComponentsResponse,
    RiskResponse,
    RouteResponse,
)
from services.demand_service.service import DemandService
from services.pricing_engine.calculator import calculate_fare
from services.pricing_engine.models import PricingConfig, PricingContext
from services.risk_service.service import RiskService
from services.routing_service.models import Coordinates, RouteResult
from services.routing_service.service import RoutingService

logger = logging.getLogger(__name__)


class FareEstimationService:
    def __init__(
        self,
        settings: Settings,
        routing: RoutingService,
        risk: RiskService,
        demand: DemandService,
        repository: FareQuoteRepository,
    ) -> None:
        self.settings = settings
        self.routing = routing
        self.risk = risk
        self.demand = demand
        self.repository = repository

    async def close(self) -> None:
        close = getattr(self.routing, "close", None)
        if close is not None:
            await close()

    async def estimate(self, request: FareEstimateRequest) -> FareEstimateResponse:
        origin = Coordinates(request.origin.latitude, request.origin.longitude)
        destination = Coordinates(request.destination.latitude, request.destination.longitude)
        timings_ms: dict[str, float] = {}

        started = time.perf_counter()
        route = await self.routing.estimate(origin, destination)
        timings_ms["routing"] = _elapsed_ms(started)

        started = time.perf_counter()
        risk = await self.risk.assess(
            (origin.latitude, origin.longitude),
            (destination.latitude, destination.longitude),
            request.requested_at,
        )
        timings_ms["risk"] = _elapsed_ms(started)

        started = time.perf_counter()
        demand = await self.demand.estimate(
            (origin.latitude, origin.longitude),
            (destination.latitude, destination.longitude),
            request.requested_at,
        )
        timings_ms["demand"] = _elapsed_ms(started)

        started = time.perf_counter()
        pricing_config = PricingConfig(
            base_fare=self.settings.pricing_base_fare,
            distance_rate=self.settings.pricing_distance_rate,
            risk_rate=self.settings.pricing_risk_rate,
            demand_sensitivity=self.settings.pricing_demand_sensitivity,
            demand_cap=self.settings.pricing_demand_cap,
            formula_mode=self.settings.pricing_formula_mode,  # type: ignore[arg-type]
            formula_version=self.settings.pricing_formula_version,
            coefficient_version=self.settings.pricing_coefficient_version,
        )
        fare = calculate_fare(
            PricingContext(
                distance_km=Decimal(str(route.distance_km)),
                risk_score=risk.score,
                demand_multiplier=demand.multiplier,
            ),
            pricing_config,
        )
        timings_ms["pricing"] = _elapsed_ms(started)

        created_at = datetime.now(UTC)
        response = FareEstimateResponse(
            quote_id=str(uuid4()),
            created_at=created_at,
            requested_at=request.requested_at,
            origin=request.origin,
            destination=request.destination,
            route=RouteResponse(
                distance_km=route.distance_km,
                estimated_duration_minutes=route.estimated_duration_minutes,
                geometry=route.geometry,
                provider=route.provider,
            ),
            risk=RiskResponse(
                score=float(risk.score),
                classification=risk.classification,
                components=RiskComponentsResponse(
                    accident=float(risk.components.accident)
                    if risk.components.accident is not None
                    else None,
                    road=float(risk.components.road) if risk.components.road is not None else None,
                    security=float(risk.components.security)
                    if risk.components.security is not None
                    else None,
                ),
                components_available=list(risk.components_available),
                components_missing=list(risk.components_missing),
                weight_strategy=risk.weight_strategy,
                source_type=risk.source_type,
                data_sources=list(risk.data_sources),
                model_version=risk.model_version,
            ),
            demand=DemandResponse(
                requests=demand.requests,
                available_drivers=demand.available_drivers,
                multiplier=float(demand.multiplier),
                source_type=demand.source_type,
                data_sources=list(demand.data_sources),
            ),
            fare=FareResponse(
                currency=fare.currency,
                base_fare=float(fare.base_fare),
                distance_component=float(fare.distance_component),
                risk_adjustment=float(fare.risk_adjustment),
                demand_adjustment=float(fare.demand_adjustment),
                total=float(fare.total),
                formula_mode=fare.formula_mode,
                formula_version=fare.formula_version,
                coefficient_version=fare.coefficient_version,
            ),
            timings_ms={**timings_ms, "database_persistence": 0.0},
        )

        started = time.perf_counter()
        await self.repository.save(response.model_dump(mode="json"))
        timings_ms["database_persistence"] = _elapsed_ms(started)
        response.timings_ms = timings_ms
        logger.info("quote_id=%s stage_timings_ms=%s", response.quote_id, timings_ms)
        return response

    async def readiness(self) -> dict[str, bool]:
        checks = {
            "repository": await _check_async(self.repository, "health_check"),
            "risk_provider": await self.risk.ready(),
            "demand_provider": await self.demand.ready(),
            "routing_provider": await _check_async(self.routing, "ready"),
        }
        return checks


def route_response(route: RouteResult) -> RouteResponse:
    return RouteResponse(
        distance_km=route.distance_km,
        estimated_duration_minutes=route.estimated_duration_minutes,
        geometry=route.geometry,
        provider=route.provider,
    )


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 2)


async def _check_async(target: object, method_name: str) -> bool:
    method = getattr(target, method_name, None)
    if method is None:
        return True
    result = method()
    if hasattr(result, "__await__"):
        result = await result
    return bool(result)
