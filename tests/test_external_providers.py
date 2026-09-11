from datetime import UTC, datetime
from decimal import Decimal

import httpx
import pytest

from services.demand_service.service import ExternalDemandProvider, TomTomTrafficDemandProvider
from services.risk_service.service import ExternalRiskProvider, OpenMeteoRiskProvider


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
        observation = await provider.get_observation((5.3, 7.0), (5.4, 7.1), datetime.now(UTC))
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


@pytest.mark.asyncio
async def test_open_meteo_provider_derives_external_road_signal():
    def handler(request: httpx.Request) -> httpx.Response:
        assert (
            request.url.params["hourly"] == "precipitation,wind_gusts_10m,visibility,weather_code"
        )
        return httpx.Response(
            200,
            json={
                "hourly": {
                    "time": ["2026-01-01T00:00", "2026-01-01T01:00"],
                    "precipitation": [2.0, 2.0],
                    "wind_gusts_10m": [20.0, 20.0],
                    "visibility": [8000.0, 8000.0],
                    "weather_code": [61, 61],
                }
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = OpenMeteoRiskProvider("https://api.open-meteo.test/v1/forecast", client=client)
        observation = await provider.get_observation(
            (5.3, 7.0), (5.4, 7.1), datetime(2026, 1, 1, tzinfo=UTC)
        )
    assert observation.source_type == "external"
    assert observation.components.accident is None
    assert observation.components.road is not None
    assert observation.data_sources == ("Open-Meteo forecast API weather signal",)


@pytest.mark.asyncio
async def test_tomtom_provider_maps_traffic_pressure_proxy():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["key"] == "traffic-key"
        assert request.url.params["point"] == "5.35,7.05"
        return httpx.Response(
            200,
            json={"flowSegmentData": {"currentSpeed": 40, "freeFlowSpeed": 80}},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = TomTomTrafficDemandProvider(
            "https://api.tomtom.test/traffic/services/4/flowSegmentData/absolute/10/json",
            client=client,
            api_key="traffic-key",
        )
        snapshot = await provider.get_snapshot((5.3, 7.0), (5.4, 7.1))
    assert snapshot.source_type == "external"
    assert snapshot.requests == 200
    assert snapshot.available_drivers == 100
    assert "demand-pressure proxy" in snapshot.data_sources[1]
