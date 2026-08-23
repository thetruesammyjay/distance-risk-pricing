"""Use PostgreSQL NUMERIC columns for exact fare and risk values."""

from alembic import op
import sqlalchemy as sa

revision = "0002_numeric_values"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


NUMERIC_COLUMNS = {
    "origin_latitude": sa.Numeric(10, 7),
    "origin_longitude": sa.Numeric(10, 7),
    "destination_latitude": sa.Numeric(10, 7),
    "destination_longitude": sa.Numeric(10, 7),
    "distance_km": sa.Numeric(12, 3),
    "risk_score": sa.Numeric(6, 4),
    "demand_multiplier": sa.Numeric(8, 4),
    "base_fare": sa.Numeric(12, 2),
    "distance_component": sa.Numeric(12, 2),
    "risk_adjustment": sa.Numeric(12, 2),
    "demand_adjustment": sa.Numeric(12, 2),
    "total_fare": sa.Numeric(12, 2),
}


def upgrade() -> None:
    for name, type_ in NUMERIC_COLUMNS.items():
        op.alter_column(
            "fare_quotes",
            name,
            existing_type=sa.Float(),
            type_=type_,
            postgresql_using=f"{name}::numeric",
        )


def downgrade() -> None:
    for name, type_ in NUMERIC_COLUMNS.items():
        op.alter_column(
            "fare_quotes",
            name,
            existing_type=type_,
            type_=sa.Float(),
            postgresql_using=f"{name}::double precision",
        )

