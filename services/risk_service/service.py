from __future__ import annotations

import asyncio
import hashlib
import math
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Protocol
from zoneinfo import ZoneInfo

import httpx

from services.common.errors import DomainError

RISK_CLASSES = ("Low", "Moderate", "High", "Very High")
RISK_SOURCE_TYPES = frozenset({"observed", "questionnaire", "derived", "external", "simulated"})


@dataclass(frozen=True)
class RiskComponents:
    accident: Decimal | None
    road: Decimal | None
    security: Decimal | None
    questionnaire: Decimal | None = None


@dataclass(frozen=True)
class RiskEstimate:
    score: Decimal
    classification: str
    components: RiskComponents
    components_available: tuple[str, ...]
    components_missing: tuple[str, ...]
    weight_strategy: str
    source_type: str
    data_sources: tuple[str, ...]
    model_version: str


@dataclass(frozen=True)
class RiskObservation:
    components: RiskComponents
    source_type: str
    data_sources: tuple[str, ...]
    model_version: str
    composite_score: Decimal | None = None


class RiskProvider(Protocol):
    async def get_observation(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
        requested_at: datetime,
    ) -> RiskObservation: ...

    async def health_check(self) -> bool: ...


def classify_risk(score: Decimal) -> str:
    if not score.is_finite() or not Decimal("0") <= score <= Decimal("1"):
        raise ValueError("risk score must be between 0 and 1")
    if score <= Decimal("0.25"):
        return RISK_CLASSES[0]
    if score <= Decimal("0.50"):
        return RISK_CLASSES[1]
    if score <= Decimal("0.75"):
        return RISK_CLASSES[2]
    return RISK_CLASSES[3]


def aggregate_risk(
    components: RiskComponents,
    weights: RiskComponents,
    *,
    renormalize_available: bool = True,
) -> tuple[Decimal, tuple[str, ...], tuple[str, ...], str]:
    values = {
        "accident": components.accident,
        "road": components.road,
        "security": components.security,
    }
    configured = {"accident": weights.accident, "road": weights.road, "security": weights.security}
    if any(
        weight is None or not weight.is_finite() or weight < 0 for weight in configured.values()
    ):
        raise DomainError(
            "INVALID_RISK_CONFIGURATION", "Risk weights must be non-negative and configured."
        )
    if sum(configured.values(), Decimal("0")) != Decimal("1"):
        raise DomainError("INVALID_RISK_CONFIGURATION", "Risk weights must sum to 1.")
    available = tuple(name for name, value in values.items() if value is not None)
    missing = tuple(name for name, value in values.items() if value is None)
    if not available:
        raise DomainError("RISK_DATA_UNAVAILABLE", "No route-risk components are available.")
    for name, value in values.items():
        if value is not None and (
            not value.is_finite() or not Decimal("0") <= value <= Decimal("1")
        ):
            raise DomainError("INVALID_RISK_CONFIGURATION", f"{name} risk must be between 0 and 1.")
    available_weight = sum((configured[name] or Decimal("0") for name in available), Decimal("0"))
    if available_weight <= 0:
        raise DomainError(
            "INVALID_RISK_CONFIGURATION", "Available risk weights must sum to a positive value."
        )
    strategy = (
        "renormalized_available_components"
        if missing and renormalize_available
        else "configured_components"
    )
    score = sum(
        (values[name] or Decimal("0")) * (configured[name] or Decimal("0")) / available_weight
        for name in available
    )
    return score, available, missing, strategy


class SimulatedRiskProvider:
    """Deterministic development provider; never represents observed risk."""

    def __init__(self, seed: int = 42, model_version: str = "simulated-v1") -> None:
        self.seed = seed
        self.model_version = model_version

    async def get_observation(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
        requested_at: datetime,
    ) -> RiskObservation:
        if requested_at.tzinfo is None:
            requested_at = requested_at.replace(tzinfo=UTC)
        local_time = requested_at.astimezone(ZoneInfo("Africa/Lagos"))
        key = (
            f"{self.seed}:{origin[0]:.5f}:{origin[1]:.5f}:"
            f"{destination[0]:.5f}:{destination[1]:.5f}:{local_time.hour}"
        )
        digest = hashlib.sha256(key.encode("utf-8")).digest()
        values = [Decimal("0.25") + Decimal(byte) / Decimal("510") for byte in digest[:3]]
        return RiskObservation(
            components=RiskComponents(*values),
            source_type="simulated",
            data_sources=("simulated development scenario",),
            model_version=self.model_version,
        )

    async def health_check(self) -> bool:
        return True


class OpenMeteoRiskProvider:
    """Derive a clearly labelled road-condition signal from Open-Meteo weather data.

    Open-Meteo provides weather observations/forecasts, not accident or security
    records. Those components therefore remain missing and are renormalized by
    RiskService until a validated route-risk dataset is selected.
    """

    def __init__(
        self,
        endpoint: str,
        *,
        client: httpx.AsyncClient,
        timeout_seconds: float = 10.0,
        retries: int = 2,
    ) -> None:
        if not endpoint.startswith(("http://", "https://")):
            raise ValueError("Open-Meteo URL must use HTTP or HTTPS")
        if timeout_seconds <= 0 or retries < 0:
            raise ValueError("provider timeout must be positive and retries cannot be negative")
        self.endpoint = endpoint
        self.client = client
        self.timeout_seconds = timeout_seconds
        self.retries = retries

    async def get_observation(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
        requested_at: datetime,
    ) -> RiskObservation:
        latitude = (origin[0] + destination[0]) / 2
        longitude = (origin[1] + destination[1]) / 2
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "precipitation,wind_gusts_10m,visibility,weather_code",
            "forecast_days": 2,
            "timezone": "UTC",
        }
        payload = await self._request(params)
        try:
            hourly = payload["hourly"]
            times = hourly["time"]
            if not isinstance(hourly, dict) or not isinstance(times, list) or not times:
                raise TypeError("hourly weather data is invalid")
            target = requested_at.astimezone(UTC).replace(minute=0, second=0, microsecond=0)
            candidates = [datetime.fromisoformat(str(value)).replace(tzinfo=UTC) for value in times]
            index = min(range(len(candidates)), key=lambda item: abs(candidates[item] - target))
            precipitation = _weather_value(hourly, "precipitation", index)
            wind_gusts = _weather_value(hourly, "wind_gusts_10m", index)
            visibility = _weather_value(hourly, "visibility", index)
            weather_code = _weather_value(hourly, "weather_code", index)
        except (KeyError, TypeError, ValueError, IndexError, OverflowError) as exc:
            raise DomainError(
                "RISK_DATA_UNAVAILABLE", "Open-Meteo returned an invalid weather response."
            ) from exc
        road_score = _weather_risk_score(precipitation, wind_gusts, visibility, weather_code)
        return RiskObservation(
            components=RiskComponents(None, road_score, None),
            source_type="external",
            data_sources=("Open-Meteo forecast API weather signal",),
            model_version="open-meteo-best-match",
        )

    async def health_check(self) -> bool:
        return bool(self.endpoint and self.client)

    async def _request(self, params: dict[str, object]) -> dict[str, Any]:
        for attempt in range(self.retries + 1):
            try:
                response = await self.client.get(
                    self.endpoint, params=params, timeout=self.timeout_seconds
                )
                if response.status_code >= 500 and attempt < self.retries:
                    await response.aclose()
                    await asyncio.sleep(0.1 * (2**attempt))
                    continue
                response.raise_for_status()
                result = response.json()
                if not isinstance(result, dict):
                    raise ValueError("weather response must be an object")
                return result
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code < 500:
                    raise DomainError(
                        "RISK_DATA_UNAVAILABLE", "Open-Meteo rejected the request."
                    ) from exc
                if attempt < self.retries:
                    await asyncio.sleep(0.1 * (2**attempt))
                    continue
                raise DomainError(
                    "RISK_DATA_UNAVAILABLE", "Open-Meteo returned a server error."
                ) from exc
            except (httpx.RequestError, ValueError) as exc:
                if attempt < self.retries:
                    await asyncio.sleep(0.1 * (2**attempt))
                    continue
                raise DomainError(
                    "RISK_DATA_UNAVAILABLE", "Open-Meteo could not be reached."
                ) from exc
        raise DomainError("RISK_DATA_UNAVAILABLE", "Open-Meteo could not be reached.")


class ExternalRiskProvider:
    """HTTP adapter for an externally hosted route-risk scoring service.

    The provider contract is intentionally small: POST a route observation
    request and return ``components``, ``source_type``, ``data_sources``, and
    ``model_version``. The response is validated again by ``RiskService``.
    """

    def __init__(
        self,
        endpoint: str,
        *,
        client: httpx.AsyncClient,
        api_key: str | None = None,
        timeout_seconds: float = 10.0,
        retries: int = 2,
    ) -> None:
        if not endpoint.startswith(("http://", "https://")):
            raise ValueError("risk provider URL must use HTTP or HTTPS")
        self.endpoint = endpoint
        self.client = client
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.retries = retries

    async def get_observation(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
        requested_at: datetime,
    ) -> RiskObservation:
        payload = {
            "origin": {"latitude": origin[0], "longitude": origin[1]},
            "destination": {"latitude": destination[0], "longitude": destination[1]},
            "requested_at": requested_at.isoformat(),
        }
        response = await self._request(payload)
        try:
            components = response["components"]
            if not isinstance(components, dict):
                raise TypeError("components must be an object")
            observation = RiskObservation(
                components=RiskComponents(
                    _decimal_or_none(components.get("accident")),
                    _decimal_or_none(components.get("road")),
                    _decimal_or_none(components.get("security")),
                    _decimal_or_none(components.get("questionnaire")),
                ),
                source_type=str(response.get("source_type", "external")),
                data_sources=tuple(str(item) for item in response.get("data_sources", ())),
                model_version=str(response.get("model_version", "external-v1")),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise DomainError(
                "RISK_DATA_UNAVAILABLE", "The risk provider returned an invalid response."
            ) from exc
        if not observation.data_sources:
            raise DomainError(
                "RISK_DATA_UNAVAILABLE", "The risk provider did not identify its data source."
            )
        return observation

    async def health_check(self) -> bool:
        return bool(self.endpoint and self.client)

    async def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        for attempt in range(self.retries + 1):
            try:
                response = await self.client.post(
                    self.endpoint,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout_seconds,
                )
                if response.status_code >= 500 and attempt < self.retries:
                    await asyncio.sleep(0.1 * (2**attempt))
                    continue
                response.raise_for_status()
                result = response.json()
                if not isinstance(result, dict):
                    raise ValueError("risk response must be an object")
                return result
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code < 500:
                    raise DomainError(
                        "RISK_DATA_UNAVAILABLE", "The risk provider rejected the request."
                    ) from exc
                if attempt < self.retries:
                    await asyncio.sleep(0.1 * (2**attempt))
                    continue
                raise DomainError(
                    "RISK_DATA_UNAVAILABLE", "The risk provider returned a server error."
                ) from exc
            except (httpx.RequestError, ValueError) as exc:
                if attempt < self.retries:
                    await asyncio.sleep(0.1 * (2**attempt))
                    continue
                raise DomainError(
                    "RISK_DATA_UNAVAILABLE", "The risk provider could not be reached."
                ) from exc
        raise DomainError("RISK_DATA_UNAVAILABLE", "The risk provider could not be reached.")


class UnavailableRiskProvider:
    """Explicit failure mode used until a real risk data adapter is configured."""

    async def get_observation(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
        requested_at: datetime,
    ) -> RiskObservation:
        del origin, destination, requested_at
        raise DomainError(
            "RISK_DATA_UNAVAILABLE",
            "No observed or externally sourced route-risk provider is configured.",
        )

    async def health_check(self) -> bool:
        return False


class RiskService:
    def __init__(self, provider: RiskProvider, weights: RiskComponents) -> None:
        self.provider = provider
        self.weights = weights
        if any(
            weight is None or not weight.is_finite() or weight < 0
            for weight in (weights.accident, weights.road, weights.security)
        ):
            raise ValueError("risk weights must be non-negative and configured")
        if sum((weights.accident, weights.road, weights.security), Decimal("0")) != Decimal("1"):
            raise ValueError("risk weights must sum to 1")

    async def assess(
        self, origin: tuple[float, float], destination: tuple[float, float], requested_at: datetime
    ) -> RiskEstimate:
        if requested_at.tzinfo is None:
            requested_at = requested_at.replace(tzinfo=UTC)
        observation = await self.provider.get_observation(origin, destination, requested_at)
        if observation.source_type not in RISK_SOURCE_TYPES:
            raise DomainError(
                "RISK_DATA_UNAVAILABLE", "The risk provider returned an unknown source type."
            )
        if observation.composite_score is not None:
            score = _validate_risk_score(observation.composite_score)
            available = ("questionnaire",)
            missing = ("accident", "road", "security")
            strategy = "questionnaire_composite_score"
        else:
            score, available, missing, strategy = aggregate_risk(
                observation.components, self.weights
            )
        return RiskEstimate(
            score=score.quantize(Decimal("0.0001")),
            classification=classify_risk(score),
            components=observation.components,
            components_available=available,
            components_missing=missing,
            weight_strategy=strategy,
            source_type=observation.source_type,
            data_sources=observation.data_sources,
            model_version=observation.model_version,
        )

    async def ready(self) -> bool:
        return await self.provider.health_check()


def _weather_value(hourly: dict[str, Any], name: str, index: int) -> float:
    values = hourly[name]
    if not isinstance(values, list):
        raise TypeError(f"{name} must be an array")
    value = float(values[index])
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def _weather_risk_score(
    precipitation: float, wind_gusts: float, visibility: float, weather_code: float
) -> Decimal:
    precipitation_risk = min(max(precipitation / 10.0, 0.0), 1.0)
    wind_risk = min(max(wind_gusts / 80.0, 0.0), 1.0)
    visibility_risk = 1.0 - min(max(visibility / 10000.0, 0.0), 1.0)
    severe_weather_risk = 0.0
    if weather_code in {45, 48}:
        severe_weather_risk = 0.35
    elif weather_code in {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82}:
        severe_weather_risk = 0.55
    elif weather_code in {71, 73, 75, 77, 85, 86}:
        severe_weather_risk = 0.7
    elif weather_code in {95, 96, 99}:
        severe_weather_risk = 0.9
    score = min(
        1.0,
        0.30 * precipitation_risk
        + 0.25 * wind_risk
        + 0.20 * visibility_risk
        + 0.25 * severe_weather_risk,
    )
    return Decimal(str(score)).quantize(Decimal("0.0001"))


def _decimal_or_none(value: object) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (ArithmeticError, ValueError) as exc:
        raise ValueError("risk component must be numeric") from exc


def _validate_risk_score(score: Decimal) -> Decimal:
    if not score.is_finite() or not Decimal("0") <= score <= Decimal("1"):
        raise DomainError(
            "INVALID_RISK_CONFIGURATION", "Composite risk score must be between 0 and 1."
        )
    return score
