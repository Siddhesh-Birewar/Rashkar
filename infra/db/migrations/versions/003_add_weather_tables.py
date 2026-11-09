"""Add weather snapshots and climate summaries tables

Revision ID: 003_add_weather_tables
Revises: 002_add_farm_centroid
Create Date: 2026-11-06 02:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003_add_weather_tables"
down_revision: Union[str, None] = "002_add_farm_centroid"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Farm Weather Snapshots Table
    op.create_table(
        "farm_weather_snapshots",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("farm_id", sa.String(length=36), nullable=False),
        sa.Column("snapshot_type", sa.String(length=30), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("observation_time", sa.DateTime(), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("feels_like", sa.Float(), nullable=True),
        sa.Column("temperature_min", sa.Float(), nullable=True),
        sa.Column("temperature_max", sa.Float(), nullable=True),
        sa.Column("humidity", sa.Float(), nullable=True),
        sa.Column("wind_speed", sa.Float(), nullable=True),
        sa.Column("wind_direction", sa.Float(), nullable=True),
        sa.Column("precipitation_mm", sa.Float(), nullable=True),
        sa.Column("weather_condition", sa.String(length=100), nullable=True),
        sa.Column("weather_description", sa.String(length=255), nullable=True),
        sa.Column("weather_icon", sa.String(length=50), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"]),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_farm_weather_snapshots_farm_id", "farm_weather_snapshots", ["farm_id"])
    op.create_index("ix_farm_weather_snapshots_snapshot_type", "farm_weather_snapshots", ["snapshot_type"])

    # 2. Farm Climate Summaries Table
    op.create_table(
        "farm_climate_summaries",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("farm_id", sa.String(length=36), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("period_description", sa.String(length=100), nullable=False),
        sa.Column("annual_rainfall_mm", sa.Float(), nullable=False),
        sa.Column("monsoon_rainfall_mm", sa.Float(), nullable=False),
        sa.Column("monsoon_share_percent", sa.Float(), nullable=False),
        sa.Column("mean_temperature_c", sa.Float(), nullable=False),
        sa.Column("min_temperature_c", sa.Float(), nullable=False),
        sa.Column("max_temperature_c", sa.Float(), nullable=False),
        sa.Column("rainfall_variability_index", sa.Float(), nullable=True),
        sa.Column("potential_water_stress_indicator", sa.String(length=150), nullable=True),
        sa.Column("monthly_rainfall_json", sa.JSON(), nullable=False),
        sa.Column("monthly_temperature_json", sa.JSON(), nullable=False),
        sa.Column("wet_season_months_json", sa.JSON(), nullable=False),
        sa.Column("dry_season_months_json", sa.JSON(), nullable=False),
        sa.Column("agricultural_seasons_json", sa.JSON(), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"]),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_farm_climate_summaries_farm_id", "farm_climate_summaries", ["farm_id"])


def downgrade() -> None:
    op.drop_table("farm_climate_summaries")
    op.drop_table("farm_weather_snapshots")
