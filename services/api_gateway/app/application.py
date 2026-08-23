from __future__ import annotations

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

    async def estimate(self, request: FareEstimateRequest) -> FareEstimateResponse:
        origin = Coordinates(request.origin.latitude, request.origin.longitude)
        destination = Coordinates(request.destination.latitude, request.destination.longitude)
        route = await self.routing.estimate(origin, destination)
        risk = self.risk.assess(
            (origin.latitude, origin.longitude),
            (destination.latitude, destination.longitude),
            request.requested_at,
        )
        demand = self.demand.estimate()
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
                data_sources=list(risk.data_sources),
                model_version=risk.model_version,
            ),
            demand=DemandResponse(
                requests=demand.requests,
                available_drivers=demand.available_drivers,
                multiplier=float(demand.multiplier),
                source_type=demand.source_type,
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
        )
        await self.repository.save(response.model_dump(mode="json"))
        return response


def route_response(route: RouteResult) -> RouteResponse:
    return RouteResponse(
        distance_km=route.distance_km,
        estimated_duration_minutes=route.estimated_duration_minutes,
        geometry=route.geometry,
        provider=route.provider,
    )
