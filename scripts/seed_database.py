"""Seed a Neon database with clearly labelled synthetic demo quotes.

This script never creates research observations. It is intended for a staging
or demo database only and refuses APP_ENV=production unless the caller opts in
explicitly with --allow-synthetic.
"""

from __future__ import annotations

import argparse
import os
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from dotenv import load_dotenv
from sqlalchemy import select

from database.models import FareQuoteModel
from database.session import create_session_factory
from services.routing_service.locations import LocationCatalog


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allow-synthetic",
        action="store_true",
        help="Allow synthetic demo rows when APP_ENV=production; not suitable for research data.",
    )
    parser.add_argument("--count", type=int, default=3)
    args = parser.parse_args()
    load_dotenv()
    if args.count < 1 or args.count > 20:
        raise SystemExit("--count must be between 1 and 20")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL must be set")
    if os.getenv("APP_ENV", "development").lower() == "production" and not args.allow_synthetic:
        raise SystemExit("Refusing synthetic seed data in production; use a staging database.")

    factory = create_session_factory(database_url)
    with factory() as session:
        existing = session.scalar(
            select(FareQuoteModel.id).where(
                FareQuoteModel.risk_source_summary == "synthetic demo seed"
            )
        )
        if existing:
            print("Synthetic demo quotes already exist; nothing to seed.")
            return
        for index in range(args.count):
            session.add(_demo_quote(index))
        session.commit()
    print(f"Seeded {args.count} synthetic demo quote(s).")


def _demo_quote(index: int) -> FareQuoteModel:
    now = datetime.now(UTC) - timedelta(minutes=index)
    quote_id = str(uuid4())
    catalog = LocationCatalog.from_csv()
    origin_location = catalog.find_by_endpoint("FUTO Main Gate")
    destination_location = catalog.find_by_endpoint("FUTO Back Gate")
    origin = {
        "latitude": origin_location.coordinates.latitude,
        "longitude": origin_location.coordinates.longitude,
    }
    destination = {
        "latitude": destination_location.coordinates.latitude,
        "longitude": destination_location.coordinates.longitude,
    }
    risk_score = Decimal("0.5800")
    payload = {
        "quote_id": quote_id,
        "created_at": now.isoformat(),
        "requested_at": now.isoformat(),
        "origin": origin,
        "destination": destination,
        "route": {
            "distance_km": 12.8,
            "estimated_duration_minutes": 31,
            "geometry": None,
            "provider": "synthetic-demo",
        },
        "risk": {
            "score": float(risk_score),
            "classification": "High",
            "components": {"accident": 0.4, "road": 0.5, "security": 0.6},
            "components_available": ["accident", "road", "security"],
            "components_missing": [],
            "weight_strategy": "configured_components",
            "source_type": "simulated",
            "data_sources": ["synthetic demo seed"],
            "model_version": "synthetic-demo-v1",
        },
        "demand": {
            "requests": 42,
            "available_drivers": 28,
            "multiplier": 1.5,
            "source_type": "simulated",
        },
        "fare": {
            "currency": "NGN",
            "base_fare": 500,
            "distance_component": 1920,
            "risk_adjustment": 74.24,
            "demand_adjustment": 1.5,
            "total": 2495.74,
            "formula_mode": "additive",
            "formula_version": "v1",
            "coefficient_version": "prototype-v1",
        },
    }
    return FareQuoteModel(
        id=quote_id,
        created_at=now,
        requested_at=now,
        origin_latitude=origin["latitude"],
        origin_longitude=origin["longitude"],
        destination_latitude=destination["latitude"],
        destination_longitude=destination["longitude"],
        distance_km=12.8,
        estimated_duration_minutes=31,
        risk_score=risk_score,
        risk_classification="High",
        demand_multiplier=1.5,
        currency="NGN",
        base_fare=500,
        distance_component=1920,
        risk_adjustment=74.24,
        demand_adjustment=1.5,
        total_fare=2495.74,
        formula_mode="additive",
        formula_version="v1",
        pricing_coefficient_version="prototype-v1",
        risk_source_summary="synthetic demo seed",
        demand_source_type="simulated",
        payload=payload,
    )


if __name__ == "__main__":
    main()
