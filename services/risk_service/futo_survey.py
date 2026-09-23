from __future__ import annotations

import csv
import math
import re
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

from services.risk_service.service import (
    RiskComponents,
    RiskObservation,
)
from services.routing_service.locations import LocationCatalog

DEFAULT_PROFILE_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "processed"
    / "futo_route_risk_profile.csv"
)
DEFAULT_LOCATION_CATALOG_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "FUTO Route Endpoint Coordinate Collection.csv"
)
MODEL_VERSION = "futo-survey-composite-v1"
COORDINATE_TOLERANCE = 0.00001

SURVEY_TIME_BANDS = (
    ("7:00 AM - 10:00 AM", 7 * 60, 10 * 60),
    ("10:00 AM - 1:00 PM", 10 * 60, 13 * 60),
    ("1:00 PM - 4:00 PM", 13 * 60, 16 * 60),
    ("4:00 PM - 7:00 PM", 16 * 60, 19 * 60),
    ("7:00 PM - 10:00 PM", 19 * 60, 22 * 60),
)


@dataclass(frozen=True, slots=True)
class FutoRiskProfileEntry:
    route_id: str
    route_name: str
    time_band: str
    response_count: int
    risk_score: Decimal


class FutoSurveyRiskProvider:
    """Serve route/time risk estimates from the aggregated FUTO questionnaire."""

    def __init__(
        self,
        profile_path: str | Path = DEFAULT_PROFILE_PATH,
        *,
        location_catalog_path: str | Path = DEFAULT_LOCATION_CATALOG_PATH,
        timezone_name: str = "Africa/Lagos",
    ) -> None:
        try:
            self.timezone = ZoneInfo(timezone_name)
        except (KeyError, ValueError) as exc:
            raise ValueError(f"unknown FUTO survey timezone: {timezone_name}") from exc
        self.profile_path = Path(profile_path)
        self._profiles = _load_profile(self.profile_path)
        self._time_priors = _build_time_priors(self._profiles.values())
        catalog = LocationCatalog.from_csv(location_catalog_path)
        self._route_coordinates = _build_route_coordinates(self._profiles.values(), catalog)

    async def get_observation(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
        requested_at: datetime,
    ) -> RiskObservation:
        if requested_at.tzinfo is None:
            requested_at = requested_at.replace(tzinfo=UTC)
        time_band, time_selection = _select_time_band(requested_at.astimezone(self.timezone))
        route_id = _find_route_id(origin, destination, self._route_coordinates)
        entry = self._profiles.get((route_id, time_band)) if route_id else None
        route_selection = "exact surveyed route" if entry else "all surveyed routes time prior"
        if entry is None:
            entry = self._time_priors[time_band]

        return RiskObservation(
            components=RiskComponents(None, None, None, entry.risk_score),
            source_type="questionnaire",
            data_sources=(
                "FUTO road-risk assessment survey",
                f"{route_selection}: {entry.route_name}",
                f"survey time band: {time_band}",
                f"responses: {entry.response_count}",
                time_selection,
            ),
            model_version=MODEL_VERSION,
            composite_score=entry.risk_score,
        )

    async def health_check(self) -> bool:
        return bool(self._profiles and self._time_priors)


def _load_profile(path: Path) -> dict[tuple[str, str], FutoRiskProfileEntry]:
    if not path.is_file():
        raise ValueError(f"FUTO survey risk profile was not found: {path}")
    required = {
        "route_id",
        "route_name",
        "time_band",
        "response_count",
        "risk_score",
    }
    profiles: dict[tuple[str, str], FutoRiskProfileEntry] = {}
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            missing = sorted(required - frozenset(reader.fieldnames or ()))
            if missing:
                raise ValueError("FUTO survey risk profile is missing: " + ", ".join(missing))
            for row_number, row in enumerate(reader, start=2):
                route_id = _required_text(row, "route_id", row_number)
                route_name = _required_text(row, "route_name", row_number)
                time_band = _required_text(row, "time_band", row_number)
                response_count = int(_required_text(row, "response_count", row_number))
                risk_score = Decimal(_required_text(row, "risk_score", row_number))
                if response_count < 1 or not risk_score.is_finite() or not 0 <= risk_score <= 1:
                    raise ValueError(f"invalid FUTO survey risk profile row {row_number}")
                entry = FutoRiskProfileEntry(
                    route_id, route_name, time_band, response_count, risk_score
                )
                profiles[(route_id, time_band)] = entry
    except OSError as exc:
        raise ValueError(f"FUTO survey risk profile could not be read: {path}") from exc
    if not profiles:
        raise ValueError("FUTO survey risk profile contains no rows")
    return profiles


def _build_time_priors(
    entries: Iterable[FutoRiskProfileEntry],
) -> dict[str, FutoRiskProfileEntry]:
    totals: dict[str, tuple[int, Decimal]] = defaultdict(lambda: (0, Decimal("0")))
    for entry in entries:
        if not isinstance(entry, FutoRiskProfileEntry):
            raise ValueError("invalid FUTO survey risk profile entry")
        count, weighted_score = totals[entry.time_band]
        totals[entry.time_band] = (
            count + entry.response_count,
            weighted_score + entry.risk_score * entry.response_count,
        )
    result: dict[str, FutoRiskProfileEntry] = {}
    for time_band, _, _ in SURVEY_TIME_BANDS:
        count, weighted_score = totals.get(time_band, (0, Decimal("0")))
        if count < 1:
            raise ValueError(f"FUTO survey profile has no observations for {time_band}")
        result[time_band] = FutoRiskProfileEntry(
            route_id="__time_prior__",
            route_name="all surveyed routes",
            time_band=time_band,
            response_count=count,
            risk_score=(weighted_score / count).quantize(Decimal("0.0001")),
        )
    return result


def _build_route_coordinates(
    entries: Iterable[FutoRiskProfileEntry],
    catalog: LocationCatalog,
) -> dict[
    str,
    tuple[tuple[tuple[float, float], tuple[float, float]], ...],
]:
    endpoint_coordinates: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for location in catalog.all():
        endpoint_coordinates[_normalize_endpoint(location.endpoint_name)].append(
            (location.coordinates.latitude, location.coordinates.longitude)
        )

    route_coordinates: dict[
        str,
        tuple[tuple[tuple[float, float], tuple[float, float]], ...],
    ] = {}
    for entry in entries:
        if not isinstance(entry, FutoRiskProfileEntry) or entry.route_id in route_coordinates:
            continue
        origin_name, separator, destination_name = entry.route_name.partition(" to ")
        if not separator:
            continue
        origins = _coordinates_for_endpoint(origin_name, endpoint_coordinates)
        destinations = _coordinates_for_endpoint(destination_name, endpoint_coordinates)
        pairs = tuple((origin, destination) for origin in origins for destination in destinations)
        if pairs:
            route_coordinates[entry.route_id] = pairs
    return route_coordinates


def _coordinates_for_endpoint(
    endpoint_name: str,
    endpoint_coordinates: dict[str, list[tuple[float, float]]],
) -> list[tuple[float, float]]:
    key = _normalize_endpoint(endpoint_name)
    aliases = {key}
    if key == "school-roundabout":
        aliases.add("roundabout")
    coordinates: list[tuple[float, float]] = []
    for alias in aliases:
        coordinates.extend(endpoint_coordinates.get(alias, ()))
    return coordinates


def _find_route_id(
    origin: tuple[float, float],
    destination: tuple[float, float],
    route_coordinates: dict[
        str,
        tuple[tuple[tuple[float, float], tuple[float, float]], ...],
    ],
) -> str | None:
    matches = [
        route_id
        for route_id, coordinate_pairs in route_coordinates.items()
        if any(
            _close_coordinate(origin, route_origin)
            and _close_coordinate(destination, route_destination)
            for route_origin, route_destination in coordinate_pairs
        )
    ]
    return matches[0] if len(matches) == 1 else None


def _select_time_band(local_time: datetime) -> tuple[str, str]:
    minutes = local_time.hour * 60 + local_time.minute
    for time_band, start, end in SURVEY_TIME_BANDS:
        if start <= minutes < end:
            return time_band, "time selection: requested time within survey window"
    if minutes < SURVEY_TIME_BANDS[0][1]:
        return SURVEY_TIME_BANDS[0][0], "time selection: clamped before survey window"
    return SURVEY_TIME_BANDS[-1][0], "time selection: clamped after survey window"


def _close_coordinate(
    first: tuple[float, float], second: tuple[float, float]
) -> bool:
    return (
        math.isclose(first[0], second[0], abs_tol=COORDINATE_TOLERANCE)
        and math.isclose(first[1], second[1], abs_tol=COORDINATE_TOLERANCE)
    )


def _normalize_endpoint(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _required_text(row: dict[str, str], name: str, row_number: int) -> str:
    value = row.get(name)
    if value is None or not value.strip():
        raise ValueError(f"row {row_number} {name} is required")
    return value.strip()
