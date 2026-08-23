from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol
from zoneinfo import ZoneInfo

from services.common.errors import DomainError

RISK_CLASSES = ("Low", "Moderate", "High", "Very High")
RISK_SOURCE_TYPES = frozenset({"observed", "questionnaire", "derived", "external", "simulated"})


@dataclass(frozen=True)
class RiskComponents:
    accident: Decimal | None
    road: Decimal | None
    security: Decimal | None


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


class RiskProvider(Protocol):
    def get_observation(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
        requested_at: datetime,
    ) -> RiskObservation: ...


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

    def get_observation(
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


class UnavailableRiskProvider:
    """Explicit failure mode used until a real risk data adapter is configured."""

    def get_observation(
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

    def assess(
        self, origin: tuple[float, float], destination: tuple[float, float], requested_at: datetime
    ) -> RiskEstimate:
        if requested_at.tzinfo is None:
            requested_at = requested_at.replace(tzinfo=UTC)
        observation = self.provider.get_observation(origin, destination, requested_at)
        if observation.source_type not in RISK_SOURCE_TYPES:
            raise DomainError(
                "RISK_DATA_UNAVAILABLE", "The risk provider returned an unknown source type."
            )
        score, available, missing, strategy = aggregate_risk(observation.components, self.weights)
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
