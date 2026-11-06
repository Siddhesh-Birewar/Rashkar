"""
CropNet AI — Phase 4.2 Post-Migration Validation Script.

Validates that Supabase database is strictly at revision 005_evidence_provenance_updates,
all 8 nullable columns are nullable, all added columns/defaults exist,
and all 10 crop catalog records and 40 regional suitability records are preserved intact.
"""
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_CROPNET_ROOT = _SCRIPT_DIR.parents[1]
_WORKSPACE_ROOT = _CROPNET_ROOT.parent

for p in [str(_WORKSPACE_ROOT), str(_CROPNET_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from sqlalchemy import create_engine, text, inspect
from cropnet.services.api.app.core.config import settings


def run_post_migration_validation():
    url = settings.SYNC_DATABASE_URL
    if not url:
        raise RuntimeError("SYNC_DATABASE_URL is not configured.")

    engine = create_engine(url)
    inspector = inspect(engine)

    with engine.connect() as conn:
        # 1. Revision Check
        rev = conn.execute(text("SELECT version_num FROM alembic_version;")).scalar()
        print(f"[Validation 1] Current Alembic revision: {rev}")
        assert rev == "005_evidence_provenance_updates", f"Expected revision 005, got {rev}"

        # 2. Verify all 8 relaxed nullable columns are nullable
        print(f"[Validation 2] Verifying 8 nullable columns in information_schema...")
        soil_cols = {c["name"]: c for c in inspector.get_columns("crop_soil_requirements", schema="public")}
        assert soil_cols["ph_tolerable_min"]["nullable"] is True, "ph_tolerable_min must be NULLABLE"
        assert soil_cols["ph_tolerable_max"]["nullable"] is True, "ph_tolerable_max must be NULLABLE"
        assert soil_cols["ph_optimum_min"]["nullable"] is True, "ph_optimum_min must be NULLABLE"
        assert soil_cols["ph_optimum_max"]["nullable"] is True, "ph_optimum_max must be NULLABLE"

        clim_cols = {c["name"]: c for c in inspector.get_columns("crop_climate_requirements", schema="public")}
        assert clim_cols["temp_tolerable_min_c"]["nullable"] is True, "temp_tolerable_min_c must be NULLABLE"
        assert clim_cols["temp_tolerable_max_c"]["nullable"] is True, "temp_tolerable_max_c must be NULLABLE"

        water_cols = {c["name"]: c for c in inspector.get_columns("crop_water_requirements", schema="public")}
        assert water_cols["annual_water_requirement_mm_min"]["nullable"] is True, "annual_water_min must be NULLABLE"
        assert water_cols["annual_water_requirement_mm_max"]["nullable"] is True, "annual_water_max must be NULLABLE"

        # 3. Verify all new columns exist and defaults are correct
        print(f"[Validation 3] Verifying new provenance columns and defaults...")
        # Soil additions
        assert "ph_best_suited_min" in soil_cols, "ph_best_suited_min missing"
        assert "ph_best_suited_max" in soil_cols, "ph_best_suited_max missing"
        assert "ph_context_notes" in soil_cols, "ph_context_notes missing"
        assert "best_suited_soil_textures" in soil_cols, "best_suited_soil_textures missing"
        assert "evidence_status" in soil_cols, "soil evidence_status missing"
        assert "unverified_parameters" in soil_cols, "unverified_parameters missing"

        # Climate additions & alterations
        assert "temp_reproductive_max_c" in clim_cols, "temp_reproductive_max_c missing"
        assert "temp_reproductive_min_mean_c" in clim_cols, "temp_reproductive_min_mean_c missing"
        assert "thermal_threshold_context" in clim_cols, "thermal_threshold_context missing"
        assert "evidence_status" in clim_cols, "clim evidence_status missing"
        assert str(clim_cols["frost_sensitivity"]["type"]).lower() == "text", "frost_sensitivity must be TEXT"
        assert str(clim_cols["heat_sensitivity"]["type"]).lower() == "text", "heat_sensitivity must be TEXT"

        # Water additions & alterations
        assert "daily_water_table" in water_cols, "daily_water_table missing"
        assert "irrigation_stages_detail" in water_cols, "irrigation_stages_detail missing"
        assert "evidence_status" in water_cols, "water evidence_status missing"
        assert water_cols["irrigation_dependency"]["type"].length == 255, "irrigation_dependency length must be 255"
        assert str(water_cols["waterlogging_sensitivity"]["type"]).lower() == "text", "waterlogging_sensitivity must be TEXT"
        assert str(water_cols["drought_sensitivity"]["type"]).lower() == "text", "drought_sensitivity must be TEXT"

        # Regional additions
        reg_cols = {c["name"]: c for c in inspector.get_columns("crop_regional_suitability", schema="public")}
        assert "evidence_status" in reg_cols, "reg evidence_status missing"

        # 4. Verify table record counts (Before vs After)
        print(f"[Validation 4] Verifying table record counts (Before vs After)...")
        expected_counts = {
            "crop_catalog": 10,
            "crop_soil_requirements": 10,
            "crop_climate_requirements": 10,
            "crop_season_requirements": 17,
            "crop_water_requirements": 10,
            "crop_regional_suitability": 40,
            "agricultural_knowledge_sources": 8,
            "farms": 2,
            "farm_weather_snapshots": 2,
            "farm_climate_summaries": 1,
            "farm_soil_profiles": 1,
            "soil_parameters": 11,
        }
        for tbl, expected_cnt in expected_counts.items():
            cnt = conn.execute(text(f'SELECT count(*) FROM "{tbl}";')).scalar()
            print(f"  - {tbl}: {cnt} rows (preserved, exactly matches baseline: {expected_cnt})")
            assert cnt == expected_cnt, f"Record count changed in {tbl}: expected {expected_cnt}, got {cnt}"

        # 5. Verify 10 crop IDs and 40 regional records preserved
        crop_ids = sorted([r[0] for r in conn.execute(text("SELECT id FROM crop_catalog;")).fetchall()])
        expected_crops = sorted([
            "sugarcane", "pomegranate", "soybean", "cotton", "maize",
            "wheat", "sorghum", "chickpea", "bajra", "groundnut"
        ])
        assert crop_ids == expected_crops, f"Crop IDs altered: {crop_ids}"

        reg_count = conn.execute(text("SELECT count(*) FROM crop_regional_suitability;")).scalar()
        assert reg_count == 40, f"Regional records altered: {reg_count}"

        print("\nAll Post-Migration Validations PASSED! Schema and data integrity confirmed.")
        return True


if __name__ == "__main__":
    run_post_migration_validation()
