from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_env: Literal["development", "staging", "production"] = "development"
    app_name: str = "distance-risk-pricing"
    debug: bool = False
    database_url: str | None = None
    database_pool_size: int = Field(default=5, ge=1, le=50)
    database_max_overflow: int = Field(default=10, ge=0, le=100)
    database_pool_timeout_seconds: int = Field(default=30, ge=1, le=120)
    frontend_url: str = "http://localhost:3000"
    location_catalog_path: str = (
        "data/FUTO Route Endpoint Coordinate Collection.csv"
    )
    routing_base_url: str = "https://router.project-osrm.org"
    routing_timeout_seconds: float = Field(default=10.0, gt=0)
    routing_retries: int = Field(default=2, ge=0, le=5)
    routing_profile: str = "driving"
    routing_cache_ttl_seconds: float = Field(default=300.0, ge=0, le=86400)
    routing_cache_max_entries: int = Field(default=512, ge=1, le=10000)
    provider_timeout_seconds: float = Field(default=10.0, gt=0, le=60)
    provider_retries: int = Field(default=2, ge=0, le=5)
    pricing_base_fare: Decimal = Field(default=Decimal("500"), ge=0)
    pricing_distance_rate: Decimal = Field(default=Decimal("150"), ge=0)
    pricing_risk_rate: Decimal = Field(default=Decimal("1"), ge=0)
    pricing_demand_sensitivity: Decimal = Field(default=Decimal("1"), ge=0)
    pricing_demand_cap: Decimal = Field(default=Decimal("2.5"), ge=1)
    pricing_formula_mode: Literal["additive", "multiplicative"] = "additive"
    pricing_formula_version: str = "v1"
    pricing_coefficient_version: str = "prototype-v1"
    risk_mode: Literal["simulated", "open_meteo", "external"] = "simulated"
    risk_provider_url: str | None = None
    risk_provider_api_key: SecretStr | None = None
    risk_accident_weight: Decimal = Field(default=Decimal("0.4"), ge=0)
    risk_road_weight: Decimal = Field(default=Decimal("0.3"), ge=0)
    risk_security_weight: Decimal = Field(default=Decimal("0.3"), ge=0)
    demand_mode: Literal["simulated", "time_of_day", "external"] = "time_of_day"
    demand_provider_url: str | None = None
    demand_provider_api_key: SecretStr | None = None
    demand_simulated_requests: int = Field(default=100, ge=0)
    demand_simulated_drivers: int = Field(default=100, ge=1)
    demand_timezone: str = "Africa/Lagos"
    allow_simulated_data: bool = False
    simulation_seed: int = 42
    log_level: str = "INFO"
    api_auth_enabled: bool = False
    api_key: SecretStr | None = None
    rate_limit_requests: int = Field(default=120, ge=1, le=10000)
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug_flag(cls, value: object) -> object:
        """Accept deployment-style DEBUG=release as the disabled state."""
        if isinstance(value, str) and value.lower() in {"release", "production", "prod"}:
            return False
        return value

    @model_validator(mode="after")
    def validate_runtime_safety(self) -> Settings:
        weights = (
            self.risk_accident_weight,
            self.risk_road_weight,
            self.risk_security_weight,
        )
        if sum(weights, Decimal("0")) != Decimal("1"):
            raise ValueError("risk weights must sum to 1")
        if self.app_env == "production":
            if not self.database_url:
                raise ValueError("DATABASE_URL is required in production")
            if not self.allow_simulated_data and (
                self.risk_mode == "simulated"
                or self.demand_mode in {"simulated", "time_of_day"}
            ):
                raise ValueError("simulated risk or demand is disabled in production")
            if not self.api_auth_enabled:
                raise ValueError("API authentication must be enabled in production")
        if self.risk_mode in {"open_meteo", "external"} and not self.risk_provider_url:
            raise ValueError("RISK_PROVIDER_URL is required for external risk modes")
        if self.demand_mode == "external" and not self.demand_provider_url:
            raise ValueError("DEMAND_PROVIDER_URL is required for external demand modes")
        if self.api_auth_enabled and (
            self.api_key is None or len(self.api_key.get_secret_value()) < 32
        ):
            raise ValueError(
                "API_KEY must contain at least 32 characters when authentication is enabled"
            )
        if self.frontend_url.strip() == "*":
            raise ValueError("wildcard CORS is not permitted")
        return self


def get_settings() -> Settings:
    return Settings()
