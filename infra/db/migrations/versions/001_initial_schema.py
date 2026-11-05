"""Initial schema baseline for CropNet AI

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-06 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Farms Table
    op.create_table(
        "farms",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("village", sa.String(length=100), nullable=True),
        sa.Column("taluka", sa.String(length=100), nullable=False),
        sa.Column("district", sa.String(length=100), nullable=False),
        sa.Column("state", sa.String(length=100), nullable=False),
        sa.Column("irrigation_type", sa.String(length=50), nullable=True),
        sa.Column("water_source", sa.String(length=50), nullable=True),
        sa.Column("geometry_geojson", sa.JSON(), nullable=False),
        sa.Column("calculated_area_hectares", sa.Float(), nullable=False),
        sa.Column("calculated_area_acres", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_farms_owner_id", "farms", ["owner_id"])
    op.create_index("ix_farms_taluka", "farms", ["taluka"])

    # 2. Soil Data Sources Table
    op.create_table(
        "soil_data_sources",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("organization", sa.String(length=150), nullable=False),
        sa.Column("portal_url", sa.String(length=255), nullable=True),
        sa.Column("dataset_version", sa.String(length=50), nullable=False),
        sa.Column("license", sa.String(length=100), nullable=False),
        sa.Column("attribution", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id")
    )

    # 3. Soil Map Layers Table
    op.create_table(
        "soil_map_layers",
        sa.Column("id", sa.String(length=100), nullable=False),
        sa.Column("source_id", sa.String(length=50), nullable=False),
        sa.Column("parameter_key", sa.String(length=50), nullable=False),
        sa.Column("layer_name", sa.String(length=100), nullable=False),
        sa.Column("spatial_resolution", sa.String(length=50), nullable=False),
        sa.Column("depth_interval", sa.String(length=50), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=False),
        sa.Column("vintage_year", sa.Integer(), nullable=True),
        sa.Column("has_uncertainty", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["soil_data_sources.id"]),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_soil_map_layers_parameter_key", "soil_map_layers", ["parameter_key"])

    # 4. Farm Soil Profiles Table
    op.create_table(
        "farm_soil_profiles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("farm_id", sa.String(length=36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=True),
        sa.Column("is_map_derived", sa.Boolean(), nullable=True),
        sa.Column("disclaimer", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"]),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_farm_soil_profiles_farm_id", "farm_soil_profiles", ["farm_id"])

    # 5. Soil Parameters Table
    op.create_table(
        "soil_parameters",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("profile_id", sa.String(length=36), nullable=False),
        sa.Column("parameter_key", sa.String(length=50), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(length=30), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("dataset_version", sa.String(length=50), nullable=False),
        sa.Column("depth_interval", sa.String(length=50), nullable=False),
        sa.Column("spatial_resolution", sa.String(length=50), nullable=False),
        sa.Column("vintage_year", sa.Integer(), nullable=True),
        sa.Column("uncertainty", sa.Float(), nullable=True),
        sa.Column("verification_status", sa.String(length=50), nullable=False),
        sa.Column("availability_status", sa.String(length=50), nullable=False),
        sa.Column("farm_coverage_percent", sa.Float(), nullable=True),
        sa.Column("scientific_note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["profile_id"], ["farm_soil_profiles.id"]),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_soil_parameters_parameter_key", "soil_parameters", ["parameter_key"])
    op.create_index("ix_soil_parameters_profile_id", "soil_parameters", ["profile_id"])


def downgrade() -> None:
    op.drop_table("soil_parameters")
    op.drop_table("farm_soil_profiles")
    op.drop_table("soil_map_layers")
    op.drop_table("soil_data_sources")
    op.drop_table("farms")
