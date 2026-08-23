from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

FormulaMode = Literal["additive", "multiplicative"]


@dataclass(frozen=True)
class PricingConfig:
    base_fare: Decimal
    distance_rate: Decimal
    risk_rate: Decimal
    demand_sensitivity: Decimal
    demand_cap: Decimal
    formula_mode: FormulaMode = "additive"
    formula_version: str = "v1"
    coefficient_version: str = "prototype-v1"
    currency: str = "NGN"

    def __post_init__(self) -> None:
        coefficients = (
            self.base_fare,
            self.distance_rate,
            self.risk_rate,
            self.demand_sensitivity,
            self.demand_cap,
        )
        if any(not coefficient.is_finite() for coefficient in coefficients):
            raise ValueError("pricing coefficients must be finite")
        if self.base_fare < 0 or self.distance_rate < 0 or self.risk_rate < 0:
            raise ValueError("pricing coefficients cannot be negative")
        if self.demand_sensitivity < 0 or self.demand_cap < 1:
            raise ValueError("demand sensitivity must be non-negative and cap must be >= 1")
        if self.formula_mode not in ("additive", "multiplicative"):
            raise ValueError("formula_mode must be additive or multiplicative")
        if len(self.currency) != 3 or not self.currency.isalpha() or not self.currency.isupper():
            raise ValueError("currency must be a three-letter uppercase code")
        if not self.formula_version.strip() or not self.coefficient_version.strip():
            raise ValueError("formula and coefficient versions are required")


@dataclass(frozen=True)
class PricingContext:
    distance_km: Decimal
    risk_score: Decimal
    demand_multiplier: Decimal

    def __post_init__(self) -> None:
        values = (self.distance_km, self.risk_score, self.demand_multiplier)
        if any(not value.is_finite() for value in values):
            raise ValueError("pricing inputs must be finite")
        if self.distance_km <= 0:
            raise ValueError("distance must be greater than zero")
        if not Decimal("0") <= self.risk_score <= Decimal("1"):
            raise ValueError("risk score must be between 0 and 1")
        if self.demand_multiplier < Decimal("1"):
            raise ValueError("demand multiplier must be at least 1")


@dataclass(frozen=True)
class FareBreakdown:
    currency: str
    base_fare: Decimal
    distance_component: Decimal
    risk_adjustment: Decimal
    demand_adjustment: Decimal
    total: Decimal
    formula_mode: FormulaMode
    formula_version: str
    coefficient_version: str
