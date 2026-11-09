"""Evidence provenance and scientific knowledge base updates

Revision ID: 005_evidence_provenance_updates
Revises: 004_add_crop_knowledge
Create Date: 2026-11-06 23:30:00.000000

Downgrade Safety Limitation:
---------------------------
This migration relaxes NOT NULL constraints on crop_soil_requirements.ph_tolerable_min
and crop_water_requirements.annual_water_requirement_mm_min/max to prevent fabricating
unsupported agronomic values (e.g. for Pomegranate and Chickpea where lower limits are unverified).
Under CropNet scientific integrity rules, fabricating synthetic backfill data to satisfy
NOT NULL constraints is strictly prohibited. Consequently, downgrade() performs a pre-flight
check for NULL records and will abort with an actionable error if NULLs are present, preventing
database crashes or data loss.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "005_evidence_provenance_updates"
down_revision: Union[str, None] = "004_add_crop_knowledge"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update crop_soil_requirements
    # Make pH bounds nullable (for crops where lower/upper tolerable limits or universal optimums are unverified)
    op.alter_column(
        "crop_soil_requirements",
        "ph_tolerable_min",
        existing_type=sa.Float(),
        nullable=True
    )
    op.alter_column(
        "crop_soil_requirements",
        "ph_tolerable_max",
        existing_type=sa.Float(),
        nullable=True
    )
    op.alter_column(
        "crop_soil_requirements",
        "ph_optimum_min",
        existing_type=sa.Float(),
        nullable=True
    )
    op.alter_column(
        "crop_soil_requirements",
        "ph_optimum_max",
        existing_type=sa.Float(),
        nullable=True
    )
    op.add_column(
        "crop_soil_requirements",
        sa.Column("ph_best_suited_min", sa.Float(), nullable=True)
    )
    op.add_column(
        "crop_soil_requirements",
        sa.Column("ph_best_suited_max", sa.Float(), nullable=True)
    )
    op.add_column(
        "crop_soil_requirements",
        sa.Column("evidence_status", sa.String(length=50), nullable=True, server_default="derived")
    )
    op.add_column(
        "crop_soil_requirements",
        sa.Column("unverified_parameters", sa.JSON(), nullable=True)
    )
    op.add_column(
        "crop_soil_requirements",
        sa.Column("ph_context_notes", sa.Text(), nullable=True)
    )
    op.add_column(
        "crop_soil_requirements",
        sa.Column("best_suited_soil_textures", sa.JSON(), nullable=True)
    )

    # 2. Update crop_climate_requirements
    op.alter_column(
        "crop_climate_requirements",
        "temp_tolerable_min_c",
        existing_type=sa.Float(),
        nullable=True
    )
    op.alter_column(
        "crop_climate_requirements",
        "temp_tolerable_max_c",
        existing_type=sa.Float(),
        nullable=True
    )
    op.alter_column(
        "crop_climate_requirements",
        "frost_sensitivity",
        existing_type=sa.String(length=150),
        type_=sa.Text(),
        existing_nullable=False,
    )
    op.alter_column(
        "crop_climate_requirements",
        "heat_sensitivity",
        existing_type=sa.String(length=150),
        type_=sa.Text(),
        existing_nullable=False,
    )
    op.add_column(
        "crop_climate_requirements",
        sa.Column("temp_reproductive_max_c", sa.Float(), nullable=True)
    )
    op.add_column(
        "crop_climate_requirements",
        sa.Column("temp_reproductive_min_mean_c", sa.Float(), nullable=True)
    )
    op.add_column(
        "crop_climate_requirements",
        sa.Column("evidence_status", sa.String(length=50), nullable=True, server_default="derived")
    )
    op.add_column(
        "crop_climate_requirements",
        sa.Column("thermal_threshold_context", sa.Text(), nullable=True)
    )

    # 3. Update crop_water_requirements
    # Make annual water requirement bounds nullable (where aggregate mm is unsupported, e.g. pomegranate)
    op.alter_column(
        "crop_water_requirements",
        "annual_water_requirement_mm_min",
        existing_type=sa.Float(),
        nullable=True
    )
    op.alter_column(
        "crop_water_requirements",
        "annual_water_requirement_mm_max",
        existing_type=sa.Float(),
        nullable=True
    )
    op.alter_column(
        "crop_water_requirements",
        "irrigation_dependency",
        existing_type=sa.String(length=50),
        type_=sa.String(length=255),
        existing_nullable=False,
    )
    op.alter_column(
        "crop_water_requirements",
        "waterlogging_sensitivity",
        existing_type=sa.String(length=150),
        type_=sa.Text(),
        existing_nullable=False,
    )
    op.alter_column(
        "crop_water_requirements",
        "drought_sensitivity",
        existing_type=sa.String(length=150),
        type_=sa.Text(),
        existing_nullable=False,
    )
    op.add_column(
        "crop_water_requirements",
        sa.Column("daily_water_table", sa.JSON(), nullable=True)
    )
    op.add_column(
        "crop_water_requirements",
        sa.Column("irrigation_stages_detail", sa.JSON(), nullable=True)
    )
    op.add_column(
        "crop_water_requirements",
        sa.Column("evidence_status", sa.String(length=50), nullable=True, server_default="derived")
    )

    # 4. Update crop_regional_suitability
    op.add_column(
        "crop_regional_suitability",
        sa.Column("evidence_status", sa.String(length=50), nullable=True, server_default="regional_screening")
    )


def downgrade() -> None:
    # Pre-flight check: Verify if newly stored NULL values prevent safe constraint restoration
    conn = op.get_bind()

    null_ph_tol_min_crops = []
    null_ph_tol_max_crops = []
    null_ph_opt_min_crops = []
    null_ph_opt_max_crops = []
    null_water_min_crops = []
    null_water_max_crops = []
    null_temp_tol_min_crops = []
    null_temp_tol_max_crops = []
    try:
        null_ph_tol_min_crops = [
            row[0] for row in conn.execute(
                sa.text("SELECT crop_id FROM crop_soil_requirements WHERE ph_tolerable_min IS NULL")
            ).fetchall()
        ]
        null_ph_tol_max_crops = [
            row[0] for row in conn.execute(
                sa.text("SELECT crop_id FROM crop_soil_requirements WHERE ph_tolerable_max IS NULL")
            ).fetchall()
        ]
        null_ph_opt_min_crops = [
            row[0] for row in conn.execute(
                sa.text("SELECT crop_id FROM crop_soil_requirements WHERE ph_optimum_min IS NULL")
            ).fetchall()
        ]
        null_ph_opt_max_crops = [
            row[0] for row in conn.execute(
                sa.text("SELECT crop_id FROM crop_soil_requirements WHERE ph_optimum_max IS NULL")
            ).fetchall()
        ]
        null_water_min_crops = [
            row[0] for row in conn.execute(
                sa.text("SELECT crop_id FROM crop_water_requirements WHERE annual_water_requirement_mm_min IS NULL")
            ).fetchall()
        ]
        null_water_max_crops = [
            row[0] for row in conn.execute(
                sa.text("SELECT crop_id FROM crop_water_requirements WHERE annual_water_requirement_mm_max IS NULL")
            ).fetchall()
        ]
        null_temp_tol_min_crops = [
            row[0] for row in conn.execute(
                sa.text("SELECT crop_id FROM crop_climate_requirements WHERE temp_tolerable_min_c IS NULL")
            ).fetchall()
        ]
        null_temp_tol_max_crops = [
            row[0] for row in conn.execute(
                sa.text("SELECT crop_id FROM crop_climate_requirements WHERE temp_tolerable_max_c IS NULL")
            ).fetchall()
        ]
    except Exception:
        # If tables do not exist or dialect differs, proceed with standard downgrade operations
        pass

    if (null_ph_tol_min_crops or null_ph_tol_max_crops or
            null_ph_opt_min_crops or null_ph_opt_max_crops or
            null_water_min_crops or null_water_max_crops or
            null_temp_tol_min_crops or null_temp_tol_max_crops):
        details = []
        if null_ph_tol_min_crops:
            details.append(f"crop_soil_requirements.ph_tolerable_min (crops: {null_ph_tol_min_crops})")
        if null_ph_tol_max_crops:
            details.append(f"crop_soil_requirements.ph_tolerable_max (crops: {null_ph_tol_max_crops})")
        if null_ph_opt_min_crops:
            details.append(f"crop_soil_requirements.ph_optimum_min (crops: {null_ph_opt_min_crops})")
        if null_ph_opt_max_crops:
            details.append(f"crop_soil_requirements.ph_optimum_max (crops: {null_ph_opt_max_crops})")
        if null_water_min_crops:
            details.append(f"crop_water_requirements.annual_water_requirement_mm_min (crops: {null_water_min_crops})")
        if null_water_max_crops:
            details.append(f"crop_water_requirements.annual_water_requirement_mm_max (crops: {null_water_max_crops})")
        if null_temp_tol_min_crops:
            details.append(f"crop_climate_requirements.temp_tolerable_min_c (crops: {null_temp_tol_min_crops})")
        if null_temp_tol_max_crops:
            details.append(f"crop_climate_requirements.temp_tolerable_max_c (crops: {null_temp_tol_max_crops})")

        raise RuntimeError(
            f"Downgrade aborted: Cannot restore NOT NULL constraints safely without data loss. "
            f"Detected NULL values across target columns: {'; '.join(details)}. "
            f"Per CropNet scientific integrity guidelines, fabricating synthetic backfill values is strictly prohibited. "
            f"Please verify or restore verified agronomic values prior to executing downgrade."
        )

    # 4. Downgrade crop_regional_suitability
    op.drop_column("crop_regional_suitability", "evidence_status")

    # 3. Downgrade crop_water_requirements
    op.drop_column("crop_water_requirements", "evidence_status")
    op.drop_column("crop_water_requirements", "irrigation_stages_detail")
    op.drop_column("crop_water_requirements", "daily_water_table")
    op.alter_column(
        "crop_water_requirements",
        "drought_sensitivity",
        existing_type=sa.Text(),
        type_=sa.String(length=150),
        postgresql_using="SUBSTRING(drought_sensitivity FROM 1 FOR 150)",
        existing_nullable=False,
    )
    op.alter_column(
        "crop_water_requirements",
        "waterlogging_sensitivity",
        existing_type=sa.Text(),
        type_=sa.String(length=150),
        postgresql_using="SUBSTRING(waterlogging_sensitivity FROM 1 FOR 150)",
        existing_nullable=False,
    )
    op.alter_column(
        "crop_water_requirements",
        "irrigation_dependency",
        existing_type=sa.String(length=255),
        type_=sa.String(length=50),
        postgresql_using="SUBSTRING(irrigation_dependency FROM 1 FOR 50)",
        existing_nullable=False,
    )
    op.alter_column(
        "crop_water_requirements",
        "annual_water_requirement_mm_max",
        existing_type=sa.Float(),
        nullable=False
    )
    op.alter_column(
        "crop_water_requirements",
        "annual_water_requirement_mm_min",
        existing_type=sa.Float(),
        nullable=False
    )

    # 2. Downgrade crop_climate_requirements
    op.drop_column("crop_climate_requirements", "thermal_threshold_context")
    op.drop_column("crop_climate_requirements", "evidence_status")
    op.drop_column("crop_climate_requirements", "temp_reproductive_min_mean_c")
    op.drop_column("crop_climate_requirements", "temp_reproductive_max_c")
    op.alter_column(
        "crop_climate_requirements",
        "heat_sensitivity",
        existing_type=sa.Text(),
        type_=sa.String(length=150),
        postgresql_using="SUBSTRING(heat_sensitivity FROM 1 FOR 150)",
        existing_nullable=False,
    )
    op.alter_column(
        "crop_climate_requirements",
        "frost_sensitivity",
        existing_type=sa.Text(),
        type_=sa.String(length=150),
        postgresql_using="SUBSTRING(frost_sensitivity FROM 1 FOR 150)",
        existing_nullable=False,
    )
    op.alter_column(
        "crop_climate_requirements",
        "temp_tolerable_max_c",
        existing_type=sa.Float(),
        nullable=False
    )
    op.alter_column(
        "crop_climate_requirements",
        "temp_tolerable_min_c",
        existing_type=sa.Float(),
        nullable=False
    )

    # 1. Downgrade crop_soil_requirements
    op.drop_column("crop_soil_requirements", "best_suited_soil_textures")
    op.drop_column("crop_soil_requirements", "ph_context_notes")
    op.drop_column("crop_soil_requirements", "unverified_parameters")
    op.drop_column("crop_soil_requirements", "evidence_status")
    op.drop_column("crop_soil_requirements", "ph_best_suited_max")
    op.drop_column("crop_soil_requirements", "ph_best_suited_min")
    op.alter_column(
        "crop_soil_requirements",
        "ph_optimum_max",
        existing_type=sa.Float(),
        nullable=False
    )
    op.alter_column(
        "crop_soil_requirements",
        "ph_optimum_min",
        existing_type=sa.Float(),
        nullable=False
    )
    op.alter_column(
        "crop_soil_requirements",
        "ph_tolerable_max",
        existing_type=sa.Float(),
        nullable=False
    )
    op.alter_column(
        "crop_soil_requirements",
        "ph_tolerable_min",
        existing_type=sa.Float(),
        nullable=False
    )
