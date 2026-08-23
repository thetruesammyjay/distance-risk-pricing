from decimal import Decimal

import pytest

from services.common.errors import DomainError
from services.demand_service.service import demand_multiplier


def test_zero_demand_and_supply_is_neutral() -> None:
    assert demand_multiplier(0, 0, Decimal("1"), Decimal("2.5")) == Decimal("1.0")


def test_demand_without_supply_hits_cap() -> None:
    assert demand_multiplier(3, 0, Decimal("1"), Decimal("2.5")) == Decimal("2.5")


def test_lower_demand_is_neutral() -> None:
    assert demand_multiplier(5, 10, Decimal("1"), Decimal("2.5")) == Decimal("1.0")


def test_multiplier_is_capped() -> None:
    assert demand_multiplier(100, 1, Decimal("1"), Decimal("2.5")) == Decimal("2.5")


def test_negative_counts_are_rejected() -> None:
    with pytest.raises(DomainError, match="negative"):
        demand_multiplier(-1, 2, Decimal("1"), Decimal("2.5"))
