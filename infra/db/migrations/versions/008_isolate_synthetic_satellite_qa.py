"""Isolate pre-Phase 6.2 synthetic satellite QA observations

Revision ID: 008_isolate_synthetic_satellite_qa
Revises: 007_water_and_satellite
Create Date: 2026-11-09 11:30:00.000000

Remediates Requirement R4:
Isolates fabricated/synthetic satellite QA observations from farmer-facing views:
- Marks records matching '%T053649_N0500_R119_T43QDB' or synthetic 40x40 pixel counts as 'SYNTHETIC_QA_ISOLATED'.
- Updates quality_notes to record isolation audit provenance.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "008_isolate_synthetic_satellite_qa"
down_revision: Union[str, None] = "007_water_and_satellite"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "satellite_vegetation_observations" in existing_tables:
        op.execute(
            sa.text(
                """
                UPDATE satellite_vegetation_observations
                SET quality_status = 'SYNTHETIC_QA_ISOLATED',
                    quality_notes = COALESCE(quality_notes, '') || ' [ISOLATED: Pre-Phase 6.2 synthetic QA simulation record isolated from production views]'
                WHERE product_id LIKE '%T053649_N0500_R119_T43QDB'
                   OR (farm_id = '94a1f16e-bf0d-4d3f-9bd3-d63a57189818' AND total_pixel_count = 1521);
                """
            )
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "satellite_vegetation_observations" in existing_tables:
        op.execute(
            sa.text(
                """
                UPDATE satellite_vegetation_observations
                SET quality_status = 'VALID_OBSERVATION'
                WHERE quality_status = 'SYNTHETIC_QA_ISOLATED';
                """
            )
        )
