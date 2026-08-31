from datetime import UTC, datetime

from fastapi.testclient import TestClient

from services.api_gateway.app.config import Settings
from services.api_gateway.app.dependencies import build_fare_service
from services.api_gateway.app.main import create_app
from services.routing_service.models import RouteResult

test_settings = Settings(database_url=None)
fare_service = build_fare_service(test_settings)
app = create_app(test_settings, service=fare_service)


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


def test_ready_and_metrics_endpoints():
    client = TestClient(app)
    ready_response = client.get("/ready")
    assert ready_response.status_code == 200
    assert ready_response.json()["checks"]["repository"] is True
    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    assert "http_requests_total" in metrics_response.text


def test_api_key_authentication_can_be_enabled():
    secured = create_app(
        Settings(api_auth_enabled=True, api_key="a" * 32),
        service=fare_service,
    )
    client = TestClient(secured)
    assert client.get("/api/v1/fares/00000000-0000-0000-0000-000000000000").status_code == 401
    response = client.get(
        "/api/v1/fares/00000000-0000-0000-0000-000000000000",
        headers={"X-API-Key": "a" * 32},
    )
    assert response.status_code == 404


def test_rate_limit_returns_retryable_error():
    limited = create_app(Settings(rate_limit_requests=1), service=fare_service)
    client = TestClient(limited)
    assert client.get("/api/v1/fares/00000000-0000-0000-0000-000000000000").status_code == 404
    response = client.get("/api/v1/fares/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"


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
