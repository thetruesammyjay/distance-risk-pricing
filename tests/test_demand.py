from datetime import UTC, datetime
from decimal import Decimal

import pytest

from services.common.errors import DomainError
from services.demand_service.service import (
    DemandService,
    TimeOfDayDemandProvider,
    demand_multiplier,
)


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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("utc_hour", "expected_multiplier", "profile"),
    [
        (6, Decimal("1.5"), "morning peak"),
        (11, Decimal("1.2"), "midday activity"),
        (14, Decimal("1.1"), "afternoon slight peak"),
        (17, Decimal("1.3"), "evening medium peak"),
        (22, Decimal("1.0"), "off-peak baseline"),
    ],
)
async def test_time_of_day_demand_uses_lagos_schedule(
    utc_hour: int, expected_multiplier: Decimal, profile: str
) -> None:
    provider = TimeOfDayDemandProvider()
    service = DemandService(provider, Decimal("1"), Decimal("2.5"))

    estimate = await service.estimate(
        requested_at=datetime(2026, 1, 5, utc_hour, 30, tzinfo=UTC)
    )

    assert estimate.multiplier == expected_multiplier
    assert estimate.source_type == "simulated"
    assert profile in estimate.data_sources[1]
