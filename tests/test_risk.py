from decimal import Decimal

import pytest

from services.common.errors import DomainError
from services.risk_service.service import RiskComponents, aggregate_risk, classify_risk


@pytest.mark.parametrize(
    ("score", "classification"),
    [
        ("0", "Low"),
        ("0.25", "Low"),
        ("0.250001", "Moderate"),
        ("0.5", "Moderate"),
        ("0.500001", "High"),
        ("0.75", "High"),
        ("0.750001", "Very High"),
        ("1", "Very High"),
    ],
)
def test_risk_classification_boundaries(score: str, classification: str) -> None:
    assert classify_risk(Decimal(score)) == classification


def test_missing_component_is_explicitly_renormalized() -> None:
    score, available, missing, strategy = aggregate_risk(
        RiskComponents(Decimal("0.4"), Decimal("0.8"), None),
        RiskComponents(Decimal("0.4"), Decimal("0.3"), Decimal("0.3")),
    )
    assert score == Decimal("0.5714285714285714285714285715")
    assert available == ("accident", "road")
    assert missing == ("security",)
    assert strategy == "renormalized_available_components"


def test_no_components_is_an_error() -> None:
    with pytest.raises(DomainError, match="No route-risk"):
        aggregate_risk(
            RiskComponents(None, None, None),
            RiskComponents(Decimal(".4"), Decimal(".3"), Decimal(".3")),
        )
