from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import ROUND_HALF_UP, Decimal

from services.pricing_engine.models import FareBreakdown, PricingConfig, PricingContext

CENT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    if not value.is_finite():
        raise ValueError("monetary values must be finite")
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def distance_adjusted_base_fare(
    distance_km: Decimal,
    minimum_base_fare: Decimal,
    distance_rate: Decimal,
) -> Decimal:
    """Calculate the distance-aware base fare without a second distance charge."""

    return max(minimum_base_fare, distance_rate * distance_km)


class PricingStrategy(ABC):
    @abstractmethod
    def calculate(self, context: PricingContext, config: PricingConfig) -> FareBreakdown:
        raise NotImplementedError


class AdditivePricingStrategy(PricingStrategy):
    """Implements B_D + bDR + gM, where B_D = max(B_min, aD)."""

    def calculate(self, context: PricingContext, config: PricingConfig) -> FareBreakdown:
        base = distance_adjusted_base_fare(
            context.distance_km,
            config.base_fare,
            config.distance_rate,
        )
        distance = Decimal("0")
        risk = config.risk_rate * context.distance_km * context.risk_score
        demand = config.demand_sensitivity * context.demand_multiplier
        return FareBreakdown(
            currency=config.currency,
            base_fare=money(base),
            distance_component=money(distance),
            risk_adjustment=money(risk),
            demand_adjustment=money(demand),
            total=money(base + distance + risk + demand),
            formula_mode="additive",
            formula_version=config.formula_version,
            coefficient_version=config.coefficient_version,
        )


class MultiplicativePricingStrategy(PricingStrategy):
    """Experimental alternative: (B_D + bDR) * M."""

    def calculate(self, context: PricingContext, config: PricingConfig) -> FareBreakdown:
        base = distance_adjusted_base_fare(
            context.distance_km,
            config.base_fare,
            config.distance_rate,
        )
        distance = Decimal("0")
        risk = config.risk_rate * context.distance_km * context.risk_score
        subtotal = base + distance + risk
        demand = subtotal * (context.demand_multiplier - Decimal("1"))
        return FareBreakdown(
            currency=config.currency,
            base_fare=money(base),
            distance_component=money(distance),
            risk_adjustment=money(risk),
            demand_adjustment=money(demand),
            total=money(subtotal * context.demand_multiplier),
            formula_mode="multiplicative",
            formula_version=config.formula_version,
            coefficient_version=config.coefficient_version,
        )


def calculate_fare(context: PricingContext, config: PricingConfig) -> FareBreakdown:
    strategy: PricingStrategy
    if config.formula_mode == "multiplicative":
        strategy = MultiplicativePricingStrategy()
    else:
        strategy = AdditivePricingStrategy()
    return strategy.calculate(context, config)
