from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class FareQuoteModel(Base):
    __tablename__ = "fare_quotes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    origin_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    origin_longitude: Mapped[float] = mapped_column(Float, nullable=False)
    destination_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    destination_longitude: Mapped[float] = mapped_column(Float, nullable=False)
    distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_classification: Mapped[str] = mapped_column(String(32), nullable=False)
    demand_multiplier: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    base_fare: Mapped[float] = mapped_column(Float, nullable=False)
    distance_component: Mapped[float] = mapped_column(Float, nullable=False)
    risk_adjustment: Mapped[float] = mapped_column(Float, nullable=False)
    demand_adjustment: Mapped[float] = mapped_column(Float, nullable=False)
    total_fare: Mapped[float] = mapped_column(Float, nullable=False)
    formula_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    formula_version: Mapped[str] = mapped_column(String(32), nullable=False)
    pricing_coefficient_version: Mapped[str] = mapped_column(String(64), nullable=False)
    risk_source_summary: Mapped[str] = mapped_column(Text, nullable=False)
    demand_source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
