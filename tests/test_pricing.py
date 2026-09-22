from decimal import Decimal

import pytest

from services.pricing_engine.calculator import calculate_fare
from services.pricing_engine.models import PricingConfig, PricingContext


def config(mode: str = "additive") -> PricingConfig:
    return PricingConfig(
        base_fare=Decimal("500"),
        distance_rate=Decimal("150"),
        risk_rate=Decimal("10"),
        demand_sensitivity=Decimal("100"),
        demand_cap=Decimal("2.5"),
        formula_mode=mode,  # type: ignore[arg-type]
    )


def context() -> PricingContext:
    return PricingContext(Decimal("10"), Decimal("0.5"), Decimal("1.5"))


def test_additive_formula_is_deterministic_and_rounded() -> None:
    result = calculate_fare(context(), config())
    assert result.base_fare == Decimal("1500.00")
    assert result.distance_component == Decimal("0.00")
    assert result.risk_adjustment == Decimal("50.00")
    assert result.demand_adjustment == Decimal("150.00")
    assert result.total == Decimal("1700.00")


def test_multiplicative_formula_is_supported() -> None:
    result = calculate_fare(context(), config("multiplicative"))
    assert result.total == Decimal("2325.00")
    assert result.demand_adjustment == Decimal("775.00")


def test_distance_adjusted_base_fare_respects_minimum() -> None:
    short_trip = calculate_fare(
        PricingContext(Decimal("2"), Decimal("0"), Decimal("1")),
        config(),
    )
    assert short_trip.base_fare == Decimal("500.00")
    assert short_trip.distance_component == Decimal("0.00")


def test_invalid_distance_is_rejected() -> None:
    with pytest.raises(ValueError, match="distance"):
        PricingContext(Decimal("0"), Decimal("0"), Decimal("1"))


def test_negative_coefficient_is_rejected() -> None:
    with pytest.raises(ValueError, match="negative"):
        PricingConfig(Decimal("-1"), Decimal("1"), Decimal("1"), Decimal("1"), Decimal("2"))
