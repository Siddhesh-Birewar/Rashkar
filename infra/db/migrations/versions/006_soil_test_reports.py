"""Soil test reports and measurement extraction schema

Revision ID: 006_soil_test_reports
Revises: 005_evidence_provenance_updates
Create Date: 2026-11-07 18:25:00.000000

Adds tables for:
1. soil_test_reports: Document storage path, laboratory metadata, sampling context,
   and extraction/review lifecycle statuses.
2. soil_test_measurements: Extracted soil chemistry parameters with original units,
   normalized values, analytical methods, OCR confidence, and farmer verification status.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "006_soil_test_reports"
down_revision: Union[str, None] = "005_evidence_provenance_updates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Soil Test Reports Table
    op.create_table(
        "soil_test_reports",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("farm_id", sa.String(length=36), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("file_hash_sha256", sa.String(length=64), nullable=True),
        sa.Column("upload_timestamp", sa.DateTime(), nullable=False),
        sa.Column("laboratory_name", sa.String(length=200), nullable=True),
        sa.Column("report_date", sa.DateTime(), nullable=True),
        sa.Column("sample_collection_date", sa.DateTime(), nullable=True),
        sa.Column("sample_depth_interval", sa.String(length=50), nullable=True),
        sa.Column("sample_depth_min_cm", sa.Float(), nullable=True),
        sa.Column("sample_depth_max_cm", sa.Float(), nullable=True),
        sa.Column("sampling_point_name", sa.String(length=150), nullable=True),
        sa.Column("sampling_point_latitude", sa.Float(), nullable=True),
        sa.Column("sampling_point_longitude", sa.Float(), nullable=True),
        sa.Column("extraction_status", sa.String(length=50), nullable=False, server_default="UPLOADED"),
        sa.Column("extraction_error", sa.Text(), nullable=True),
        sa.Column("review_status", sa.String(length=50), nullable=False, server_default="NEEDS_REVIEW"),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("raw_extracted_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_soil_test_reports_user_id", "soil_test_reports", ["user_id"])
    op.create_index("ix_soil_test_reports_farm_id", "soil_test_reports", ["farm_id"])
    op.create_index("ix_soil_test_reports_extraction_status", "soil_test_reports", ["extraction_status"])
    op.create_index("ix_soil_test_reports_review_status", "soil_test_reports", ["review_status"])
    op.create_index("ix_soil_test_reports_file_hash_sha256", "soil_test_reports", ["file_hash_sha256"])

    # 2. Soil Test Measurements Table
    op.create_table(
        "soil_test_measurements",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("report_id", sa.String(length=36), nullable=False),
        sa.Column("farm_id", sa.String(length=36), nullable=False),
        sa.Column("parameter_key", sa.String(length=50), nullable=False),
        sa.Column("parameter_category", sa.String(length=50), nullable=True, server_default="macronutrient"),
        sa.Column("original_parameter_name", sa.String(length=150), nullable=False),
        sa.Column("original_value", sa.Float(), nullable=True),
        sa.Column("original_value_text", sa.String(length=100), nullable=True),
        sa.Column("original_unit", sa.String(length=50), nullable=False),
        sa.Column("normalized_value", sa.Float(), nullable=True),
        sa.Column("normalized_unit", sa.String(length=50), nullable=True),
        sa.Column("analytical_method", sa.String(length=150), nullable=True),
        sa.Column("lab_reference_range", sa.JSON(), nullable=True),
        sa.Column("lab_rating", sa.String(length=50), nullable=True),
        sa.Column("detection_limit", sa.Float(), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True, server_default="1"),
        sa.Column("bounding_box", sa.JSON(), nullable=True),
        sa.Column("extraction_confidence", sa.Float(), nullable=True, server_default="1.0"),
        sa.Column("is_ambiguous", sa.Boolean(), nullable=True, server_default=sa.text("false")),
        sa.Column("verification_status", sa.String(length=50), nullable=False, server_default="EXTRACTED_UNVERIFIED"),
        sa.Column("farmer_corrected_value", sa.Float(), nullable=True),
        sa.Column("farmer_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["report_id"], ["soil_test_reports.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_soil_test_measurements_report_id", "soil_test_measurements", ["report_id"])
    op.create_index("ix_soil_test_measurements_farm_id", "soil_test_measurements", ["farm_id"])
    op.create_index("ix_soil_test_measurements_parameter_key", "soil_test_measurements", ["parameter_key"])
    op.create_index("ix_soil_test_measurements_verification_status", "soil_test_measurements", ["verification_status"])


def downgrade() -> None:
    # Drop tables and their indexes in reverse order
    op.drop_table("soil_test_measurements")
    op.drop_table("soil_test_reports")
