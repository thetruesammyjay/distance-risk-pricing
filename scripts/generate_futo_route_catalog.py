from __future__ import annotations

import argparse
import csv
import os
import time
from pathlib import Path
from urllib.parse import quote

import httpx
from dotenv import load_dotenv

from ml.src.futo_survey import load_futo_survey
from ml.src.route_catalog import ROUTE_CATALOG_COLUMNS

DEFAULT_INPUT = Path(
    "data/raw/FUTO Road Risk Assessment Survey for Dynamic Transportation Pricing.csv"
)
DEFAULT_OUTPUT = Path("data/external/futo_route_catalog_candidates.csv")
TOMTOM_GEOCODE_BASE = "https://api.tomtom.com/search/2/geocode"
OSRM_ROUTE_BASE = "https://router.project-osrm.org/route/v1/driving"
FUTO_CONTEXT = "Federal University of Technology Owerri, Imo State, Nigeria"
CANDIDATE_COLUMNS = (
    *ROUTE_CATALOG_COLUMNS,
    "origin_query",
    "destination_query",
    "origin_match",
    "destination_match",
    "notes",
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate reviewable FUTO route metadata candidates from geocoding and OSRM."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--delay-seconds",
        type=float,
        default=0.2,
        help="delay between TomTom geocoder requests (default: 0.2)",
    )
    args = parser.parse_args()
    if args.delay_seconds < 0:
        parser.error("--delay-seconds cannot be negative")

    load_dotenv()
    api_key = os.getenv("FUTO_GEOCODING_API_KEY", "").strip()
    if not api_key:
        parser.error(
            "FUTO_GEOCODING_API_KEY is required; use a TomTom key with Geocoding API access"
        )

    dataset = load_futo_survey(args.input, strict=True)
    routes = sorted(
        {(observation.route_id, observation.route_name) for observation in dataset.observations}
    )
    if args.output.resolve() == args.input.resolve():
        parser.error("output must not overwrite the raw input file")

    with httpx.Client(timeout=20.0) as client:
        rows = [
            _generate_candidate(
                client,
                route_id,
                route_name,
                api_key,
                args.delay_seconds,
            )
            for route_id, route_name in routes
        ]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CANDIDATE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    unresolved = sum(
        not row["origin_latitude"]
        or not row["origin_longitude"]
        or not row["destination_latitude"]
        or not row["destination_longitude"]
        for row in rows
    )
    print(f"routes={len(rows)}")
    print(f"unresolved_routes={unresolved}")
    print(f"output={args.output}")
    print("verification_status=needs_review")
    return 0


def _generate_candidate(
    client: httpx.Client,
    route_id: str,
    route_name: str,
    api_key: str,
    delay_seconds: float,
) -> dict[str, str | float]:
    origin_name, separator, destination_name = route_name.partition(" to ")
    if not separator:
        return _empty_candidate(route_id, route_name, "route name does not contain ' to '")

    origin_query = f"{origin_name}, {FUTO_CONTEXT}"
    destination_query = f"{destination_name}, {FUTO_CONTEXT}"
    origin = _geocode(client, origin_query, api_key)
    time.sleep(delay_seconds)
    destination = _geocode(client, destination_query, api_key)
    row: dict[str, str | float] = {
        "route_id": route_id,
        "route_name": route_name,
        "origin_latitude": origin["latitude"],
        "origin_longitude": origin["longitude"],
        "destination_latitude": destination["latitude"],
        "destination_longitude": destination["longitude"],
        "distance_km": "",
        "duration_minutes": "",
        "source": "TomTom Geocoding API + OSRM candidate; manual verification required",
        "source_url": (
            f"{TOMTOM_GEOCODE_BASE}/{quote(origin_query, safe='')}.json; "
            f"{TOMTOM_GEOCODE_BASE}/{quote(destination_query, safe='')}.json"
        ),
        "verification_status": "needs_review",
        "origin_query": origin_query,
        "destination_query": destination_query,
        "origin_match": origin["match"],
        "destination_match": destination["match"],
        "notes": "; ".join(item for item in (origin["notes"], destination["notes"]) if item),
    }
    if origin["latitude"] != "" and destination["latitude"] != "":
        route = _route(
            client,
            float(origin["longitude"]),
            float(origin["latitude"]),
            float(destination["longitude"]),
            float(destination["latitude"]),
        )
        row["distance_km"] = route["distance_km"]
        row["duration_minutes"] = route["duration_minutes"]
        row["source_url"] = (
            f"{row['source_url']}; "
            f"{OSRM_ROUTE_BASE}/{float(origin['longitude'])},{float(origin['latitude'])};"
            f"{float(destination['longitude'])},{float(destination['latitude'])}"
        )
        row["notes"] = "; ".join(item for item in (str(row["notes"]), route["notes"]) if item)
    else:
        row["notes"] = "; ".join(
            item
            for item in (str(row["notes"]), "OSRM skipped because an endpoint was unresolved")
            if item
        )
    return row


def _geocode(client: httpx.Client, query: str, api_key: str) -> dict[str, str | float]:
    url = f"{TOMTOM_GEOCODE_BASE}/{quote(query, safe='')}.json"
    try:
        response = client.get(url, params={"key": api_key, "limit": 5, "countrySet": "NG"})
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            return {
                "latitude": "",
                "longitude": "",
                "match": "",
                "notes": "geocoder returned an invalid response",
            }
        results = payload.get("results", [])
        if not isinstance(results, list) or not results:
            return {
                "latitude": "",
                "longitude": "",
                "match": "",
                "notes": "geocoder returned no result",
            }
        first = results[0]
        position = first.get("position", {})
        latitude, longitude = position.get("lat"), position.get("lon")
        if not isinstance(latitude, int | float) or not isinstance(longitude, int | float):
            return {
                "latitude": "",
                "longitude": "",
                "match": "",
                "notes": "geocoder result had no usable position",
            }
        address = first.get("address", {})
        match = address.get("freeformAddress", "") if isinstance(address, dict) else ""
        notes = f"{len(results)} geocoder result(s); first result requires review"
        return {
            "latitude": float(latitude),
            "longitude": float(longitude),
            "match": str(match),
            "notes": notes,
        }
    except (httpx.HTTPError, ValueError, TypeError, KeyError, IndexError) as exc:
        return {
            "latitude": "",
            "longitude": "",
            "match": "",
            "notes": f"geocoder error: {type(exc).__name__}",
        }


def _route(
    client: httpx.Client,
    origin_lon: float,
    origin_lat: float,
    destination_lon: float,
    destination_lat: float,
) -> dict[str, str | float]:
    url = f"{OSRM_ROUTE_BASE}/{origin_lon},{origin_lat};{destination_lon},{destination_lat}"
    try:
        response = client.get(url, params={"overview": "false"})
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            return {
                "distance_km": "",
                "duration_minutes": "",
                "notes": "OSRM returned an invalid response",
            }
        routes = payload.get("routes", [])
        if payload.get("code") != "Ok" or not routes:
            return {"distance_km": "", "duration_minutes": "", "notes": "OSRM returned no route"}
        route = routes[0]
        return {
            "distance_km": round(float(route["distance"]) / 1000, 4),
            "duration_minutes": round(float(route["duration"]) / 60, 2),
            "notes": "OSRM route distance/duration candidate; review route geometry",
        }
    except (httpx.HTTPError, ValueError, TypeError, KeyError, IndexError) as exc:
        return {
            "distance_km": "",
            "duration_minutes": "",
            "notes": f"OSRM error: {type(exc).__name__}",
        }


def _empty_candidate(route_id: str, route_name: str, notes: str) -> dict[str, str]:
    row = {column: "" for column in CANDIDATE_COLUMNS}
    row.update(
        {
            "route_id": route_id,
            "route_name": route_name,
            "verification_status": "needs_review",
            "notes": notes,
        }
    )
    return row


if __name__ == "__main__":
    raise SystemExit(main())
