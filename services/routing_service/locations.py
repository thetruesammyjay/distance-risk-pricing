from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass
from pathlib import Path

from services.routing_service.models import Coordinates

DEFAULT_LOCATION_CATALOG_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "FUTO Route Endpoint Coordinate Collection.csv"
)
REQUIRED_COLUMNS = frozenset(
    {"Timestamp", "endpoint_name", "latitude", "longitude", "source", "source_url", "notes"}
)


@dataclass(frozen=True, slots=True)
class Location:
    location_id: str
    endpoint_name: str
    coordinates: Coordinates
    collected_at: str
    source: str
    source_url: str
    notes: str


class LocationCatalogError(ValueError):
    """Raised when the configured FUTO endpoint catalog is missing or invalid."""


class LocationCatalog:
    def __init__(self, locations: tuple[Location, ...]) -> None:
        if not locations:
            raise LocationCatalogError("the FUTO endpoint catalog contains no locations")
        self._locations = locations

    @classmethod
    def from_csv(cls, path: str | Path = DEFAULT_LOCATION_CATALOG_PATH) -> LocationCatalog:
        source_path = Path(path)
        if not source_path.is_file():
            raise LocationCatalogError(f"location catalog was not found: {source_path}")

        try:
            with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                columns = frozenset(reader.fieldnames or ())
                missing = sorted(REQUIRED_COLUMNS - columns)
                if missing:
                    raise LocationCatalogError(
                        "location catalog is missing required columns: " + ", ".join(missing)
                    )
                locations = tuple(
                    _parse_location(row, row_number)
                    for row_number, row in enumerate(reader, start=2)
                )
        except OSError as exc:
            raise LocationCatalogError(f"location catalog could not be read: {source_path}") from exc

        return cls(locations)

    def all(self) -> tuple[Location, ...]:
        return self._locations

    def find_by_endpoint(self, endpoint_name: str) -> Location:
        for location in self._locations:
            if location.endpoint_name == endpoint_name:
                return location
        raise LocationCatalogError(f"endpoint is not present in the location catalog: {endpoint_name}")


def _parse_location(row: dict[str, str], row_number: int) -> Location:
    endpoint_name = _required_text(row, "endpoint_name", row_number)
    collected_at = _required_text(row, "Timestamp", row_number)
    source = _required_text(row, "source", row_number)
    source_url = _required_text(row, "source_url", row_number)
    notes = str(row.get("notes", "")).strip()
    try:
        latitude = float(_required_text(row, "latitude", row_number))
        longitude = float(_required_text(row, "longitude", row_number))
        coordinates = Coordinates(latitude, longitude)
    except (TypeError, ValueError) as exc:
        raise LocationCatalogError(f"row {row_number} has invalid coordinates") from exc
    if not math.isfinite(coordinates.latitude) or not math.isfinite(coordinates.longitude):
        raise LocationCatalogError(f"row {row_number} has non-finite coordinates")
    if not source_url.startswith(("http://", "https://")):
        raise LocationCatalogError(f"row {row_number} source_url must use HTTP or HTTPS")
    return Location(
        location_id=f"{_slug(endpoint_name)}-{row_number - 1}",
        endpoint_name=endpoint_name,
        coordinates=coordinates,
        collected_at=collected_at,
        source=source,
        source_url=source_url,
        notes=notes,
    )


def _required_text(row: dict[str, str], name: str, row_number: int) -> str:
    value = row.get(name)
    if value is None or not value.strip():
        raise LocationCatalogError(f"row {row_number} {name} is required")
    return value.strip()


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "location"
