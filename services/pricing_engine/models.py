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

    def __post_init__(self) -> None:
        if self.base_fare < 0 or self.distance_rate < 0 or self.risk_rate < 0:
            raise ValueError("pricing coefficients cannot be negative")
        if self.demand_sensitivity < 0 or self.demand_cap < 1:
            raise ValueError("demand sensitivity must be non-negative and cap must be >= 1")
        if self.formula_mode not in ("additive", "multiplicative"):
            raise ValueError("formula_mode must be additive or multiplicative")


@dataclass(frozen=True)
class PricingContext:
    distance_km: Decimal
    risk_score: Decimal
    demand_multiplier: Decimal

    def __post_init__(self) -> None:
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
