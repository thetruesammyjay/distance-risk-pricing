from pathlib import Path

import pytest

from services.routing_service.locations import LocationCatalog, LocationCatalogError


DATASET_PATH = Path("data/FUTO Route Endpoint Coordinate Collection.csv")


def test_futo_location_catalog_preserves_real_coordinates_and_duplicate_labels():
    catalog = LocationCatalog.from_csv(DATASET_PATH)

    assert len(catalog.all()) == 18
    assert catalog.find_by_endpoint("FUTO Main Gate").coordinates.latitude == pytest.approx(5.4005546)
    assert catalog.find_by_endpoint("FUTO Back Gate").coordinates.longitude == pytest.approx(7.009140)
    assert len([location for location in catalog.all() if location.endpoint_name == "Roundabout"]) == 2


def test_missing_location_catalog_is_explicitly_rejected(tmp_path):
    with pytest.raises(LocationCatalogError, match="was not found"):
        LocationCatalog.from_csv(tmp_path / "missing.csv")
