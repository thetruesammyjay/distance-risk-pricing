from scripts.generate_futo_route_catalog import _generate_candidate


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.payload


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def get(self, url: str, params: dict) -> FakeResponse:
        self.calls.append((url, params))
        if "api.tomtom.com" in url:
            place = "FUTO Main Gate" if len(self.calls) == 1 else "FUTO Back Gate"
            return FakeResponse(
                {
                    "results": [
                        {
                            "position": {
                                "lat": 5.39 if len(self.calls) == 1 else 5.40,
                                "lon": 7.03,
                            },
                            "address": {"freeformAddress": place},
                        }
                    ]
                }
            )
        return FakeResponse(
            {
                "code": "Ok",
                "routes": [{"distance": 2500, "duration": 480}],
            }
        )


def test_generator_creates_unverified_candidate_without_exposing_key():
    client = FakeClient()

    row = _generate_candidate(
        client,
        "route-1",
        "FUTO Main Gate to FUTO Back Gate",
        "secret-key",
        0,
    )

    assert row["verification_status"] == "needs_review"
    assert row["origin_latitude"] == 5.39
    assert row["destination_latitude"] == 5.40
    assert row["distance_km"] == 2.5
    assert row["duration_minutes"] == 8.0
    assert "secret-key" not in str(row)
    assert len(client.calls) == 3
