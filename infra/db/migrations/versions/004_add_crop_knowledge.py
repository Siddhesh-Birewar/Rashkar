"""Add agricultural knowledge base and crop requirement tables

Revision ID: 004_add_crop_knowledge
Revises: 003_add_weather_tables
Create Date: 2026-11-06 02:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "004_add_crop_knowledge"
down_revision: Union[str, None] = "003_add_weather_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Agricultural Knowledge Sources Table
    op.create_table(
        "agricultural_knowledge_sources",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("organization", sa.String(length=150), nullable=False),
        sa.Column("publication_title", sa.String(length=255), nullable=False),
        sa.Column("publication_year", sa.Integer(), nullable=True),
        sa.Column("document_url_or_ref", sa.Text(), nullable=True),
        sa.Column("section_or_pages", sa.String(length=100), nullable=True),
        sa.Column("evidence_quality", sa.String(length=50), nullable=True),
        sa.Column("last_verified_date", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id")
    )

    # 2. Crop Catalog Master Table
    op.create_table(
        "crop_catalog",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("common_name", sa.String(length=100), nullable=False),
        sa.Column("scientific_name", sa.String(length=150), nullable=False),
        sa.Column("marathi_name", sa.String(length=100), nullable=True),
        sa.Column("hindi_name", sa.String(length=100), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("crop_type", sa.String(length=50), nullable=False),
        sa.Column("typical_duration_days_min", sa.Integer(), nullable=True),
        sa.Column("typical_duration_days_max", sa.Integer(), nullable=True),
        sa.Column("recommended_varieties", sa.JSON(), nullable=True),
        sa.Column("source_id", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["agricultural_knowledge_sources.id"]),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_crop_catalog_category", "crop_catalog", ["category"])

    # 3. Crop Soil Requirements Table
    op.create_table(
        "crop_soil_requirements",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("crop_id", sa.String(length=50), nullable=False),
        sa.Column("preferred_textures", sa.JSON(), nullable=False),
        sa.Column("acceptable_textures", sa.JSON(), nullable=False),
        sa.Column("ph_optimum_min", sa.Float(), nullable=False),
        sa.Column("ph_optimum_max", sa.Float(), nullable=False),
        sa.Column("ph_tolerable_min", sa.Float(), nullable=False),
        sa.Column("ph_tolerable_max", sa.Float(), nullable=False),
        sa.Column("drainage_requirement", sa.String(length=150), nullable=False),
        sa.Column("salinity_sensitivity", sa.String(length=150), nullable=False),
        sa.Column("min_soil_depth_cm", sa.Float(), nullable=False),
        sa.Column("optimum_organic_carbon_g_kg", sa.Float(), nullable=True),
        sa.Column("water_holding_capacity_pref", sa.String(length=100), nullable=True),
        sa.Column("source_id", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["crop_id"], ["crop_catalog.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["agricultural_knowledge_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("crop_id")
    )
    op.create_index("ix_crop_soil_requirements_crop_id", "crop_soil_requirements", ["crop_id"])

    # 4. Crop Climate Requirements Table
    op.create_table(
        "crop_climate_requirements",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("crop_id", sa.String(length=50), nullable=False),
        sa.Column("temp_optimum_min_c", sa.Float(), nullable=False),
        sa.Column("temp_optimum_max_c", sa.Float(), nullable=False),
        sa.Column("temp_tolerable_min_c", sa.Float(), nullable=False),
        sa.Column("temp_tolerable_max_c", sa.Float(), nullable=False),
        sa.Column("annual_rainfall_min_mm", sa.Float(), nullable=True),
        sa.Column("annual_rainfall_max_mm", sa.Float(), nullable=True),
        sa.Column("humidity_preference", sa.String(length=150), nullable=True),
        sa.Column("frost_sensitivity", sa.String(length=150), nullable=False),
        sa.Column("heat_sensitivity", sa.String(length=150), nullable=False),
        sa.Column("solar_radiation_requirement", sa.String(length=150), nullable=True),
        sa.Column("source_id", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["crop_id"], ["crop_catalog.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["agricultural_knowledge_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("crop_id")
    )
    op.create_index("ix_crop_climate_requirements_crop_id", "crop_climate_requirements", ["crop_id"])

    # 5. Crop Season Requirements Table
    op.create_table(
        "crop_season_requirements",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("crop_id", sa.String(length=50), nullable=False),
        sa.Column("season_name", sa.String(length=50), nullable=False),
        sa.Column("is_primary_season", sa.Boolean(), nullable=True),
        sa.Column("planting_window_maharashtra", sa.String(length=150), nullable=False),
        sa.Column("harvesting_window_maharashtra", sa.String(length=150), nullable=False),
        sa.Column("duration_days_min", sa.Integer(), nullable=False),
        sa.Column("duration_days_max", sa.Integer(), nullable=False),
        sa.Column("planting_calendar_by_region", sa.JSON(), nullable=True),
        sa.Column("source_id", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["crop_id"], ["crop_catalog.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["agricultural_knowledge_sources.id"]),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_crop_season_requirements_crop_id", "crop_season_requirements", ["crop_id"])
    op.create_index("ix_crop_season_requirements_season_name", "crop_season_requirements", ["season_name"])

    # 6. Crop Water Requirements Table
    op.create_table(
        "crop_water_requirements",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("crop_id", sa.String(length=50), nullable=False),
        sa.Column("annual_water_requirement_mm_min", sa.Float(), nullable=False),
        sa.Column("annual_water_requirement_mm_max", sa.Float(), nullable=False),
        sa.Column("rainfed_suitable", sa.Boolean(), nullable=False),
        sa.Column("irrigation_dependency", sa.String(length=50), nullable=False),
        sa.Column("critical_growth_stages", sa.JSON(), nullable=False),
        sa.Column("waterlogging_sensitivity", sa.String(length=150), nullable=False),
        sa.Column("drought_sensitivity", sa.String(length=150), nullable=False),
        sa.Column("source_id", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["crop_id"], ["crop_catalog.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["agricultural_knowledge_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("crop_id")
    )
    op.create_index("ix_crop_water_requirements_crop_id", "crop_water_requirements", ["crop_id"])

    # 7. Crop Regional Suitability Table
    op.create_table(
        "crop_regional_suitability",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("crop_id", sa.String(length=50), nullable=False),
        sa.Column("taluka", sa.String(length=100), nullable=False),
        sa.Column("district", sa.String(length=100), nullable=False),
        sa.Column("suitability_status", sa.String(length=60), nullable=False),
        sa.Column("agronomic_rationale", sa.Text(), nullable=False),
        sa.Column("limiting_factors", sa.JSON(), nullable=True),
        sa.Column("source_id", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["crop_id"], ["crop_catalog.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["agricultural_knowledge_sources.id"]),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_crop_regional_suitability_crop_id", "crop_regional_suitability", ["crop_id"])
    op.create_index("ix_crop_regional_suitability_taluka", "crop_regional_suitability", ["taluka"])


def downgrade() -> None:
    op.drop_table("crop_regional_suitability")
    op.drop_table("crop_water_requirements")
    op.drop_table("crop_season_requirements")
    op.drop_table("crop_climate_requirements")
    op.drop_table("crop_soil_requirements")
    op.drop_table("crop_catalog")
    op.drop_table("agricultural_knowledge_sources")
