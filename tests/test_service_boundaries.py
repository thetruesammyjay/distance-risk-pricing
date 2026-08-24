from datetime import UTC, datetime
from decimal import Decimal

import pytest

from services.common.errors import DomainError
from services.demand_service.service import DemandService, UnavailableDemandProvider
from services.risk_service.service import (
    RiskComponents,
    RiskService,
    SimulatedRiskProvider,
    UnavailableRiskProvider,
)


async def test_simulated_risk_is_explicitly_labelled_and_timezone_aware():
    service = RiskService(
        SimulatedRiskProvider(seed=7), RiskComponents(Decimal(".4"), Decimal(".3"), Decimal(".3"))
    )
    estimate = await service.assess((5.3, 7.0), (5.4, 7.1), datetime.now(UTC))
    assert estimate.source_type == "simulated"
    assert estimate.data_sources == ("simulated development scenario",)


async def test_unavailable_risk_provider_fails_explicitly():
    service = RiskService(
        UnavailableRiskProvider(), RiskComponents(Decimal(".4"), Decimal(".3"), Decimal(".3"))
    )
    with pytest.raises(DomainError, match="No observed"):
        await service.assess((5.3, 7.0), (5.4, 7.1), datetime.now(UTC))


async def test_unavailable_demand_provider_fails_explicitly():
    service = DemandService(UnavailableDemandProvider(), Decimal("1"), Decimal("2.5"))
    with pytest.raises(DomainError, match="No observed"):
        await service.estimate()
