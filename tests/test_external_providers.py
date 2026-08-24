from datetime import UTC, datetime
from decimal import Decimal

import httpx
import pytest

from services.demand_service.service import ExternalDemandProvider
from services.risk_service.service import ExternalRiskProvider


@pytest.mark.asyncio
async def test_external_risk_provider_validates_and_maps_response():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer risk-key"
        return httpx.Response(
            200,
            json={
                "components": {"accident": 0.2, "road": 0.4, "security": None},
                "source_type": "external",
                "data_sources": ["validated-risk-feed"],
                "model_version": "risk-2026-01",
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = ExternalRiskProvider(
            "https://risk.example.test/score", client=client, api_key="risk-key"
        )
        observation = await provider.get_observation(
            (5.3, 7.0), (5.4, 7.1), datetime.now(UTC)
        )
    assert observation.components.accident == Decimal("0.2")
    assert observation.components.security is None
    assert observation.data_sources == ("validated-risk-feed",)


@pytest.mark.asyncio
async def test_external_demand_provider_maps_response():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"requests": 120, "available_drivers": 40, "source_type": "external"},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = ExternalDemandProvider("https://demand.example.test/snapshot", client=client)
        snapshot = await provider.get_snapshot()
    assert snapshot.requests == 120
    assert snapshot.available_drivers == 40
    assert snapshot.source_type == "external"
