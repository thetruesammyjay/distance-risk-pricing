from datetime import UTC, datetime

from fastapi.testclient import TestClient

from services.api_gateway.app.main import app, fare_service
from services.routing_service.models import RouteResult


class StubRouting:
    async def estimate(self, origin, destination):
        return RouteResult(
            12.8, 31, {"type": "LineString", "coordinates": []}, origin, destination, "stub"
        )


def payload():
    return {
        "origin": {"latitude": 5.3921, "longitude": 7.0337},
        "destination": {"latitude": 5.4865, "longitude": 7.0259},
        "requested_at": datetime.now(UTC).isoformat(),
    }


def test_health_and_request_id():
    response = TestClient(app).get("/health", headers={"X-Request-ID": "test-request"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-request"
    assert response.json()["status"] == "ok"


def test_invalid_coordinates_use_error_envelope():
    invalid = payload()
    invalid["origin"]["latitude"] = 100
    response = TestClient(app).post("/api/v1/fares/estimate", json=invalid)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_naive_timestamp_is_rejected():
    invalid = payload()
    invalid["requested_at"] = "2026-08-23T18:30:00"
    response = TestClient(app).post("/api/v1/fares/estimate", json=invalid)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_fare_estimate_is_persisted_in_dev_repository(monkeypatch):
    monkeypatch.setattr(fare_service, "routing", StubRouting())
    client = TestClient(app)
    response = client.post("/api/v1/fares/estimate", json=payload())
    assert response.status_code == 200
    quote = response.json()
    assert quote["quote_id"]
    assert quote["risk"]["data_sources"] == ["simulated development scenario"]
    assert quote["demand"]["source_type"] == "simulated"
    retrieved = client.get(f"/api/v1/fares/{quote['quote_id']}")
    assert retrieved.status_code == 200
    assert retrieved.json()["fare"]["total"] == quote["fare"]["total"]


def test_missing_quote_returns_not_found():
    response = TestClient(app).get("/api/v1/fares/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "QUOTE_NOT_FOUND"
