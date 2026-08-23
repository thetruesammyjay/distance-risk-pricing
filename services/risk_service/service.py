from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from services.common.errors import DomainError

RISK_CLASSES = ("Low", "Moderate", "High", "Very High")


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
    data_sources: tuple[str, ...]
    model_version: str


def classify_risk(score: Decimal) -> str:
    if not Decimal("0") <= score <= Decimal("1"):
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
    available = tuple(name for name, value in values.items() if value is not None)
    missing = tuple(name for name, value in values.items() if value is None)
    if not available:
        raise DomainError("RISK_DATA_UNAVAILABLE", "No route-risk components are available.")
    for name, value in values.items():
        if value is not None and not Decimal("0") <= value <= Decimal("1"):
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


class RiskService:
    def __init__(
        self, mode: str, weights: RiskComponents, model_version: str = "simulated-v1"
    ) -> None:
        configured_weights = (weights.accident, weights.road, weights.security)
        if any(weight is None or weight < 0 for weight in configured_weights):
            raise ValueError("risk weights must be non-negative and configured")
        if sum(configured_weights, Decimal("0")) != Decimal("1"):
            raise ValueError("risk weights must sum to 1")
        self.mode = mode
        self.weights = weights
        self.model_version = model_version

    def assess(
        self, origin: tuple[float, float], destination: tuple[float, float], requested_at: datetime
    ) -> RiskEstimate:
        if self.mode != "simulated":
            raise DomainError(
                "RISK_DATA_UNAVAILABLE", "No configured route-risk source is available."
            )
        # Stable synthetic fixture for development only; it is always labelled simulated.
        key = (
            f"{origin[0]:.5f}:{origin[1]:.5f}:"
            f"{destination[0]:.5f}:{destination[1]:.5f}:{requested_at.hour}"
        )
        digest = hashlib.sha256(key.encode("utf-8")).digest()
        values = [Decimal("0.25") + Decimal(byte) / Decimal("510") for byte in digest[:3]]
        components = RiskComponents(*values)
        score, available, missing, strategy = aggregate_risk(components, self.weights)
        return RiskEstimate(
            score=score.quantize(Decimal("0.0001")),
            classification=classify_risk(score),
            components=components,
            components_available=available,
            components_missing=missing,
            weight_strategy=strategy,
            data_sources=("simulated development scenario",),
            model_version=self.model_version,
        )
