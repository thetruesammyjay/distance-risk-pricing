from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import ROUND_HALF_UP, Decimal

from services.pricing_engine.models import FareBreakdown, PricingConfig, PricingContext

CENT = Decimal("0.01")
LOW_RISK_CUTOFF = Decimal("0.25")
# Upper bounds of the classification bands in Table 4.3 of the report.
MODERATE_RISK_CUTOFF = Decimal("0.50")
HIGH_RISK_CUTOFF = Decimal("0.75")


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


def risk_premium_score(risk_score: Decimal) -> Decimal:
    """Apply the classification rule that Low risk has no risk premium."""

    if not risk_score.is_finite() or not Decimal("0") <= risk_score <= Decimal("1"):
        raise ValueError("risk score must be between 0 and 1")
    return Decimal("0") if risk_score <= LOW_RISK_CUTOFF else risk_score


def classify_risk(risk_score: Decimal) -> str:
    """Return the Table 4.3 classification for a risk score."""

    if not risk_score.is_finite() or not Decimal("0") <= risk_score <= Decimal("1"):
        raise ValueError("risk score must be between 0 and 1")
    if risk_score <= LOW_RISK_CUTOFF:
        return "Low"
    if risk_score <= MODERATE_RISK_CUTOFF:
        return "Moderate"
    if risk_score <= HIGH_RISK_CUTOFF:
        return "High"
    return "Very High"


def risk_uplift_pct(classification: str, config: PricingConfig) -> Decimal:
    """Percentage of the distance-adjusted base fare added for this risk class."""

    return {
        "Low": Decimal("0"),
        "Moderate": config.risk_uplift_moderate,
        "High": config.risk_uplift_high,
        "Very High": config.risk_uplift_very_high,
    }[classification]


def round_to_increment(value: Decimal, increment: Decimal) -> Decimal:
    """Round half-up to the nearest multiple of ``increment`` (e.g. NGN 50)."""

    steps = (value / increment).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return money(steps * increment)


class PricingStrategy(ABC):
    @abstractmethod
    def calculate(self, context: PricingContext, config: PricingConfig) -> FareBreakdown:
        raise NotImplementedError


class AdditivePricingStrategy(PricingStrategy):
    """Implements B_D + bDR_p + gM, where B_D = max(B_min, aD)."""

    def calculate(self, context: PricingContext, config: PricingConfig) -> FareBreakdown:
        base = distance_adjusted_base_fare(
            context.distance_km,
            config.base_fare,
            config.distance_rate,
        )
        distance = Decimal("0")
        risk = (
            config.risk_rate
            * context.distance_km
            * risk_premium_score(context.risk_score)
        )
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
    """Experimental alternative: (B_D + bDR_p) * M."""

    def calculate(self, context: PricingContext, config: PricingConfig) -> FareBreakdown:
        base = distance_adjusted_base_fare(
            context.distance_km,
            config.base_fare,
            config.distance_rate,
        )
        distance = Decimal("0")
        risk = (
            config.risk_rate
            * context.distance_km
            * risk_premium_score(context.risk_score)
        )
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


class TieredRiskPricingStrategy(PricingStrategy):
    """v3 rule: risk is a percentage uplift of the distance-adjusted base fare.

    risk_adjustment = B_D * u(class)
    additive:        demand_adjustment = gamma * B_D * (M - 1)           (uplifts sum)
    multiplicative:  demand_adjustment = gamma * (B_D + risk) * (M - 1)  (uplifts compound)

    The extra charge (risk + demand) is capped at B_D * (max_total_multiplier - 1)
    and the final total is rounded to ``rounding_increment``. Any rounding is
    reported separately in ``rounding_adjustment`` so components always sum to
    the total.
    """

    def calculate(self, context: PricingContext, config: PricingConfig) -> FareBreakdown:
        base = distance_adjusted_base_fare(
            context.distance_km,
            config.base_fare,
            config.distance_rate,
        )
        classification = classify_risk(context.risk_score)
        uplift = risk_uplift_pct(classification, config)

        raw_risk = base * uplift
        demand_excess = context.demand_multiplier - Decimal("1")
        if config.formula_mode == "multiplicative":
            raw_demand = (base + raw_risk) * config.demand_sensitivity * demand_excess
        else:
            raw_demand = base * config.demand_sensitivity * demand_excess

        # Equity cap: total extra charge may not exceed (cap - 1) * base fare.
        max_extra = base * (config.max_total_multiplier - Decimal("1"))
        cap_applied = raw_risk + raw_demand > max_extra
        risk = min(raw_risk, max_extra)
        demand = min(raw_demand, max_extra - risk)

        base_m, risk_m, demand_m = money(base), money(risk), money(demand)
        subtotal = base_m + risk_m + demand_m
        total = round_to_increment(subtotal, config.rounding_increment)

        return FareBreakdown(
            currency=config.currency,
            base_fare=base_m,
            distance_component=money(Decimal("0")),
            risk_adjustment=risk_m,
            demand_adjustment=demand_m,
            total=total,
            formula_mode=config.formula_mode,
            formula_version=config.formula_version,
            coefficient_version=config.coefficient_version,
            risk_classification=classification,
            risk_uplift_pct=uplift,
            cap_applied=cap_applied,
            rounding_adjustment=money(total - subtotal),
        )


def calculate_fare(context: PricingContext, config: PricingConfig) -> FareBreakdown:
    strategy: PricingStrategy
    if config.risk_mode == "tiered":
        strategy = TieredRiskPricingStrategy()
    elif config.formula_mode == "multiplicative":
        strategy = MultiplicativePricingStrategy()
    else:
        strategy = AdditivePricingStrategy()
    return strategy.calculate(context, config)
