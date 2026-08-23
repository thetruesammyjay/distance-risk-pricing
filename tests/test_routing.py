import pytest

from services.common.errors import DomainError
from services.routing_service.models import Coordinates
from services.routing_service.osrm import OSRMAdapter


class FakeResponse:
    status_code = 200

    async def aclose(self):
        return None

    def raise_for_status(self) -> None:
        pass

    def json(self):
        return {
            "code": "Ok",
            "routes": [
                {
                    "distance": 12800,
                    "duration": 1860,
                    "geometry": {"type": "LineString", "coordinates": []},
                }
            ],
        }


class FakeClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return None

    async def get(self, *_args, **_kwargs):
        return FakeResponse()

    async def aclose(self):
        return None


@pytest.mark.asyncio
async def test_osrm_response_is_mapped(monkeypatch):
    monkeypatch.setattr("httpx.AsyncClient", lambda **_kwargs: FakeClient())
    route = await OSRMAdapter("https://router.example").get_route(
        Coordinates(1, 2), Coordinates(3, 4)
    )
    assert route.distance_km == 12.8
    assert route.estimated_duration_minutes == 31
    assert route.provider == "osrm"


@pytest.mark.asyncio
async def test_osrm_route_not_found_is_controlled(monkeypatch):
    class NotFoundResponse(FakeResponse):
        def json(self):
            return {"code": "NoRoute", "routes": []}

    class NotFoundClient(FakeClient):
        async def get(self, *_args, **_kwargs):
            return NotFoundResponse()

    monkeypatch.setattr("httpx.AsyncClient", lambda **_kwargs: NotFoundClient())
    with pytest.raises(DomainError, match="No drivable route"):
        await OSRMAdapter("https://router.example").get_route(Coordinates(1, 2), Coordinates(3, 4))


@pytest.mark.asyncio
async def test_osrm_retries_transient_server_failure():
    class RetryClient(FakeClient):
        def __init__(self):
            self.calls = 0

        async def get(self, *_args, **_kwargs):
            self.calls += 1
            if self.calls == 1:
                response = FakeResponse()
                response.status_code = 503
                return response
            return FakeResponse()

    client = RetryClient()
    route = await OSRMAdapter("https://router.example", retries=1, client=client).get_route(
        Coordinates(1, 2), Coordinates(3, 4)
    )
    assert route.distance_km == 12.8
    assert client.calls == 2
