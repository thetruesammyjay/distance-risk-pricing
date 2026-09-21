from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ml.src.futo_survey import FutoSurveyObservation

ROUTE_CATALOG_COLUMNS = (
    "route_id",
    "route_name",
    "origin_latitude",
    "origin_longitude",
    "destination_latitude",
    "destination_longitude",
    "distance_km",
    "duration_minutes",
    "source",
    "source_url",
    "verification_status",
)


@dataclass(frozen=True, slots=True)
class FutoRouteMetadata:
    route_id: str
    route_name: str
    origin_latitude: float
    origin_longitude: float
    destination_latitude: float
    destination_longitude: float
    distance_km: float
    duration_minutes: float
    source: str
    source_url: str
    verification_status: str = "verified"

    def __post_init__(self) -> None:
        if not self.route_id.strip() or not self.route_name.strip():
            raise ValueError("route_id and route_name are required")
        for value, name, minimum, maximum in (
            (self.origin_latitude, "origin_latitude", -90, 90),
            (self.destination_latitude, "destination_latitude", -90, 90),
            (self.origin_longitude, "origin_longitude", -180, 180),
            (self.destination_longitude, "destination_longitude", -180, 180),
        ):
            if not minimum <= value <= maximum:
                raise ValueError(f"{name} must be between {minimum} and {maximum}")
        if self.distance_km < 0 or self.duration_minutes <= 0:
            raise ValueError(
                "distance_km must be non-negative and duration_minutes must be positive"
            )
        if not self.source.strip() or not self.source_url.strip():
            raise ValueError("source and source_url are required")
        if self.verification_status != "verified":
            raise ValueError("route metadata must be marked verified before training")


class RouteCatalogValidationError(ValueError):
    """Raised when route metadata is incomplete or not verified."""


def load_route_catalog(path: str | Path, *, strict: bool = True) -> dict[str, FutoRouteMetadata]:
    source_path = Path(path)
    with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = sorted(set(ROUTE_CATALOG_COLUMNS) - set(reader.fieldnames or ()))
        if missing:
            raise RouteCatalogValidationError(
                f"route catalog is missing required columns: {', '.join(missing)}"
            )
        catalog: dict[str, FutoRouteMetadata] = {}
        errors: list[str] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                metadata = _parse_row(row)
                if metadata.route_id in catalog:
                    raise ValueError(f"duplicate route_id: {metadata.route_id}")
                catalog[metadata.route_id] = metadata
            except (KeyError, TypeError, ValueError) as exc:
                errors.append(f"row {row_number}: {exc}")
    if strict and errors:
        raise RouteCatalogValidationError("; ".join(errors))
    return catalog


def validate_catalog_covers_observations(
    observations: tuple[FutoSurveyObservation, ...] | list[FutoSurveyObservation],
    catalog: dict[str, FutoRouteMetadata],
) -> None:
    missing = sorted({observation.route_id for observation in observations} - set(catalog))
    if missing:
        raise RouteCatalogValidationError(
            f"route catalog is missing FUTO routes: {', '.join(missing)}"
        )


def write_catalog_template(route_names: tuple[tuple[str, str], ...], path: str | Path) -> None:
    """Create a blank metadata template; it deliberately contains no estimates."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ROUTE_CATALOG_COLUMNS)
        writer.writeheader()
        for route_id, route_name in route_names:
            writer.writerow(
                {
                    "route_id": route_id,
                    "route_name": route_name,
                    "origin_latitude": "",
                    "origin_longitude": "",
                    "destination_latitude": "",
                    "destination_longitude": "",
                    "distance_km": "",
                    "duration_minutes": "",
                    "source": "",
                    "source_url": "",
                    "verification_status": "needs_review",
                }
            )


def _parse_row(row: dict[str, Any]) -> FutoRouteMetadata:
    return FutoRouteMetadata(
        route_id=_text(row, "route_id"),
        route_name=_text(row, "route_name"),
        origin_latitude=_float(row, "origin_latitude"),
        origin_longitude=_float(row, "origin_longitude"),
        destination_latitude=_float(row, "destination_latitude"),
        destination_longitude=_float(row, "destination_longitude"),
        distance_km=_float(row, "distance_km"),
        duration_minutes=_float(row, "duration_minutes"),
        source=_text(row, "source"),
        source_url=_text(row, "source_url"),
        verification_status=_text(row, "verification_status"),
    )


def _text(row: dict[str, Any], name: str) -> str:
    value = row[name]
    if value is None or not str(value).strip():
        raise ValueError(f"{name} is required")
    return str(value).strip()


def _float(row: dict[str, Any], name: str) -> float:
    return float(_text(row, name))
