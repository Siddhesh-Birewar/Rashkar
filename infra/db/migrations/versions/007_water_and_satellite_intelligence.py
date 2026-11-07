"""Water intelligence and satellite vegetation observation schema

Revision ID: 007_water_and_satellite
Revises: 006_soil_test_reports
Create Date: 2026-11-08 04:30:00.000000

Adds tables for:
1. water_sources: Farm irrigation water sources (borewell, open well, canal, etc.) with availability and capacity.
2. water_test_reports: Laboratory water test document metadata and review lifecycle.
3. water_measurements: Discrete chemical/physical water parameters (pH, EC, TDS, Na, Ca, Mg, Cl, HCO3, CO3, SO4, B, NO3).
4. satellite_vegetation_observations: Copernicus Sentinel-2 Level-2A surface reflectance canopy metrics (NDVI, NDMI, SCL masking).
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "007_water_and_satellite"
down_revision: Union[str, None] = "006_soil_test_reports"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Water Sources Table
    op.create_table(
        "water_sources",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("farm_id", sa.String(36), sa.ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("location_description", sa.String(255), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("seasonal_availability", sa.String(50), nullable=False, server_default="perennial"),
        sa.Column("reliability", sa.String(50), nullable=False, server_default="reliable"),
        sa.Column("daily_available_hours", sa.Float(), nullable=True),
        sa.Column("irrigation_method", sa.String(50), nullable=False, server_default="drip"),
        sa.Column("measured_capacity_lph", sa.Float(), nullable=True),
        sa.Column("capacity_provenance", sa.String(50), nullable=False, server_default="FARMER_REPORTED"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # 2. Water Test Reports Table
    op.create_table(
        "water_test_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False, index=True),
        sa.Column("farm_id", sa.String(36), sa.ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("water_source_id", sa.String(36), sa.ForeignKey("water_sources.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("storage_path", sa.String(500), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("file_hash_sha256", sa.String(64), nullable=True, index=True),
        sa.Column("upload_timestamp", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("laboratory_name", sa.String(200), nullable=True),
        sa.Column("lab_number", sa.String(100), nullable=True),
        sa.Column("report_date", sa.DateTime(), nullable=True),
        sa.Column("sample_collection_date", sa.DateTime(), nullable=True),
        sa.Column("sampling_location", sa.String(150), nullable=True),
        sa.Column("extraction_status", sa.String(50), nullable=False, server_default="UPLOADED", index=True),
        sa.Column("extraction_error", sa.Text(), nullable=True),
        sa.Column("review_status", sa.String(50), nullable=False, server_default="NEEDS_REVIEW", index=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("raw_extracted_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # 3. Water Measurements Table
    op.create_table(
        "water_measurements",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("report_id", sa.String(36), sa.ForeignKey("water_test_reports.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("farm_id", sa.String(36), sa.ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("water_source_id", sa.String(36), sa.ForeignKey("water_sources.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("parameter_key", sa.String(50), nullable=False, index=True),
        sa.Column("original_parameter_name", sa.String(150), nullable=False),
        sa.Column("original_value", sa.Float(), nullable=True),
        sa.Column("original_value_text", sa.String(100), nullable=True),
        sa.Column("original_unit", sa.String(50), nullable=False),
        sa.Column("normalized_value", sa.Float(), nullable=True),
        sa.Column("normalized_unit", sa.String(50), nullable=True),
        sa.Column("analytical_method", sa.String(150), nullable=True),
        sa.Column("detection_limit", sa.Float(), nullable=True),
        sa.Column("provenance", sa.String(50), nullable=False, server_default="LAB_REPORT"),
        sa.Column("verification_status", sa.String(50), nullable=False, server_default="EXTRACTED_UNVERIFIED", index=True),
        sa.Column("farmer_corrected_value", sa.Float(), nullable=True),
        sa.Column("farmer_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # 4. Satellite Vegetation Observations Table
    op.create_table(
        "satellite_vegetation_observations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("farm_id", sa.String(36), sa.ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("observation_date", sa.DateTime(), nullable=False, index=True),
        sa.Column("product_id", sa.String(120), nullable=False),
        sa.Column("tile_id", sa.String(50), nullable=True),
        sa.Column("sensor", sa.String(30), nullable=False, server_default="Sentinel-2 L2A"),
        sa.Column("processing_baseline", sa.String(30), nullable=True, server_default="N0500"),
        sa.Column("mean_ndvi", sa.Float(), nullable=True),
        sa.Column("median_ndvi", sa.Float(), nullable=True),
        sa.Column("min_ndvi", sa.Float(), nullable=True),
        sa.Column("max_ndvi", sa.Float(), nullable=True),
        sa.Column("std_ndvi", sa.Float(), nullable=True),
        sa.Column("mean_ndmi", sa.Float(), nullable=True),
        sa.Column("valid_pixel_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_pixel_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("farm_coverage_percent", sa.Float(), nullable=False, server_default="100.0"),
        sa.Column("cloud_masked_percent", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("spatial_resolution_meters", sa.Float(), nullable=False, server_default="10.0"),
        sa.Column("quality_status", sa.String(50), nullable=False, server_default="VALID_OBSERVATION", index=True),
        sa.Column("quality_notes", sa.Text(), nullable=True),
        sa.Column("is_small_farm_warning", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("satellite_vegetation_observations")
    op.drop_table("water_measurements")
    op.drop_table("water_test_reports")
    op.drop_table("water_sources")
