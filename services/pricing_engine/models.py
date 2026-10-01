from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

FormulaMode = Literal["additive", "multiplicative"]
RiskMode = Literal["tiered", "legacy"]


@dataclass(frozen=True)
class PricingConfig:
    base_fare: Decimal
    distance_rate: Decimal
    risk_rate: Decimal
    demand_sensitivity: Decimal
    demand_cap: Decimal
    formula_mode: FormulaMode = "additive"
    formula_version: str = "v3-risk-uplift"
    coefficient_version: str = "prototype-v2"
    currency: str = "NGN"
    # --- v3 risk-uplift settings -------------------------------------------
    # "tiered": risk is a percentage uplift of the distance-adjusted base fare.
    # "legacy": the original v2 rule (beta * D * R_p), kept for reproducing
    #           old quotes. In legacy mode the settings below are ignored.
    risk_mode: RiskMode = "tiered"
    risk_uplift_moderate: Decimal = Decimal("0.10")
    risk_uplift_high: Decimal = Decimal("0.25")
    risk_uplift_very_high: Decimal = Decimal("0.40")
    # Fare can never exceed base_fare_distance_adjusted * this value.
    max_total_multiplier: Decimal = Decimal("2.0")
    # Final fare is rounded to the nearest multiple of this amount (NGN).
    # NGN 5 keeps the 10/25/40% tier values exact. Larger steps (e.g. 50)
    # can hide small day/night differences: 525 would round up to 550.
    # Use Decimal("0.01") to disable rounding.
    rounding_increment: Decimal = Decimal("5")

    def __post_init__(self) -> None:
        coefficients = (
            self.base_fare,
            self.distance_rate,
            self.risk_rate,
            self.demand_sensitivity,
            self.demand_cap,
            self.risk_uplift_moderate,
            self.risk_uplift_high,
            self.risk_uplift_very_high,
            self.max_total_multiplier,
            self.rounding_increment,
        )
        if any(not coefficient.is_finite() for coefficient in coefficients):
            raise ValueError("pricing coefficients must be finite")
        if self.base_fare < 0 or self.distance_rate < 0 or self.risk_rate < 0:
            raise ValueError("pricing coefficients cannot be negative")
        if self.demand_sensitivity < 0 or self.demand_cap < 1:
            raise ValueError("demand sensitivity must be non-negative and cap must be >= 1")
        if self.formula_mode not in ("additive", "multiplicative"):
            raise ValueError("formula_mode must be additive or multiplicative")
        if self.risk_mode not in ("tiered", "legacy"):
            raise ValueError("risk_mode must be tiered or legacy")
        if not (
            Decimal("0")
            <= self.risk_uplift_moderate
            <= self.risk_uplift_high
            <= self.risk_uplift_very_high
        ):
            raise ValueError(
                "risk uplifts must be non-negative and non-decreasing "
                "(moderate <= high <= very_high)"
            )
        if self.max_total_multiplier < 1:
            raise ValueError("max_total_multiplier must be >= 1")
        if self.rounding_increment <= 0:
            raise ValueError("rounding_increment must be greater than zero")
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
    # --- v3 additions (all defaulted so existing constructors keep working) --
    risk_classification: str | None = None
    risk_uplift_pct: Decimal = Decimal("0")
    cap_applied: bool = False
    rounding_adjustment: Decimal = Decimal("0")