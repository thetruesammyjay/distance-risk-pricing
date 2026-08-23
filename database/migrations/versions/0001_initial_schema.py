"""Create the initial fare quote schema."""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fare_quotes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("origin_latitude", sa.Numeric(10, 7), nullable=False),
        sa.Column("origin_longitude", sa.Numeric(10, 7), nullable=False),
        sa.Column("destination_latitude", sa.Numeric(10, 7), nullable=False),
        sa.Column("destination_longitude", sa.Numeric(10, 7), nullable=False),
        sa.Column("distance_km", sa.Numeric(12, 3), nullable=False),
        sa.Column("estimated_duration_minutes", sa.Integer(), nullable=False),
        sa.Column("risk_score", sa.Numeric(6, 4), nullable=False),
        sa.Column("risk_classification", sa.String(length=32), nullable=False),
        sa.Column("demand_multiplier", sa.Numeric(8, 4), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("base_fare", sa.Numeric(12, 2), nullable=False),
        sa.Column("distance_component", sa.Numeric(12, 2), nullable=False),
        sa.Column("risk_adjustment", sa.Numeric(12, 2), nullable=False),
        sa.Column("demand_adjustment", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_fare", sa.Numeric(12, 2), nullable=False),
        sa.Column("formula_mode", sa.String(length=32), nullable=False),
        sa.Column("formula_version", sa.String(length=32), nullable=False),
        sa.Column("pricing_coefficient_version", sa.String(length=64), nullable=False),
        sa.Column("risk_source_summary", sa.Text(), nullable=False),
        sa.Column("demand_source_type", sa.String(length=32), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("fare_quotes")
