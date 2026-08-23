from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_env: str = "development"
    app_name: str = "distance-risk-pricing"
    debug: bool = False
    database_url: str | None = None
    frontend_url: str = "http://localhost:3000"
    routing_base_url: str = "https://router.project-osrm.org"
    routing_timeout_seconds: float = Field(default=10.0, gt=0)
    pricing_base_fare: Decimal = Field(default=Decimal("500"), ge=0)
    pricing_distance_rate: Decimal = Field(default=Decimal("150"), ge=0)
    pricing_risk_rate: Decimal = Field(default=Decimal("1"), ge=0)
    pricing_demand_sensitivity: Decimal = Field(default=Decimal("1"), ge=0)
    pricing_demand_cap: Decimal = Field(default=Decimal("2.5"), ge=1)
    pricing_formula_mode: Literal["additive", "multiplicative"] = "additive"
    pricing_formula_version: str = "v1"
    pricing_coefficient_version: str = "prototype-v1"
    risk_mode: str = "simulated"
    risk_accident_weight: Decimal = Field(default=Decimal("0.4"), ge=0)
    risk_road_weight: Decimal = Field(default=Decimal("0.3"), ge=0)
    risk_security_weight: Decimal = Field(default=Decimal("0.3"), ge=0)
    demand_mode: str = "simulated"
    simulation_seed: int = 42
    log_level: str = "INFO"

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug_flag(cls, value: object) -> object:
        """Accept deployment-style DEBUG=release as the disabled state."""
        if isinstance(value, str) and value.lower() in {"release", "production", "prod"}:
            return False
        return value


def get_settings() -> Settings:
    return Settings()
