"""
CropNet AI — Phase 4.2 Database Preflight Check.

Verifies that the target Supabase database is strictly at revision 004_add_crop_knowledge
with no schema drift or missing Phase 4 tables before applying migration 005.
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


def run_database_preflight():
    url = settings.SYNC_DATABASE_URL
    if not url:
        raise RuntimeError("SYNC_DATABASE_URL is not configured.")

    engine = create_engine(url)
    inspector = inspect(engine)

    with engine.connect() as conn:
        # 1. Revision Check
        rev = conn.execute(text("SELECT version_num FROM alembic_version;")).scalar()
        print(f"[Preflight 1] Alembic revision: {rev}")
        if rev != "004_add_crop_knowledge":
            raise RuntimeError(
                f"STOP: Database revision is '{rev}', expected '004_add_crop_knowledge'. Schema drift or out-of-order migration detected."
            )

        # 2. Table Existence Check
        public_tables = set(inspector.get_table_names(schema="public"))
        expected_phase4_tables = [
            "crop_catalog",
            "crop_soil_requirements",
            "crop_climate_requirements",
            "crop_season_requirements",
            "crop_water_requirements",
            "crop_regional_suitability",
            "agricultural_knowledge_sources",
        ]
        print(f"[Preflight 2] Checking Phase 4 tables...")
        for tbl in expected_phase4_tables:
            if tbl not in public_tables:
                raise RuntimeError(f"STOP: Expected Phase 4 table '{tbl}' is missing from database!")
            print(f"  - Table '{tbl}' verified.")

        # 3. Column & Constraint Verification for 004 baseline
        print(f"[Preflight 3] Verifying 004 column baseline...")
        soil_cols = {c["name"]: c for c in inspector.get_columns("crop_soil_requirements", schema="public")}
        assert soil_cols["ph_tolerable_min"]["nullable"] is False, "004 baseline expects ph_tolerable_min NOT NULL"
        assert soil_cols["ph_optimum_min"]["nullable"] is False, "004 baseline expects ph_optimum_min NOT NULL"
        assert "ph_best_suited_min" not in soil_cols, "ph_best_suited_min must not exist prior to migration 005"

        clim_cols = {c["name"]: c for c in inspector.get_columns("crop_climate_requirements", schema="public")}
        assert clim_cols["temp_tolerable_max_c"]["nullable"] is False, "004 baseline expects temp_tolerable_max_c NOT NULL"
        assert "temp_reproductive_max_c" not in clim_cols, "temp_reproductive_max_c must not exist prior to migration 005"

        water_cols = {c["name"]: c for c in inspector.get_columns("crop_water_requirements", schema="public")}
        assert water_cols["annual_water_requirement_mm_min"]["nullable"] is False, "004 baseline expects water min NOT NULL"
        assert "daily_water_table" not in water_cols, "daily_water_table must not exist prior to migration 005"

        # 4. Record Count Verification
        print(f"[Preflight 4] Verifying table record counts...")
        expected_counts = {
            "crop_catalog": 10,
            "crop_soil_requirements": 10,
            "crop_climate_requirements": 10,
            "crop_season_requirements": 17,
            "crop_water_requirements": 10,
            "crop_regional_suitability": 40,
            "agricultural_knowledge_sources": 8,
        }
        for tbl, expected_cnt in expected_counts.items():
            actual_cnt = conn.execute(text(f'SELECT count(*) FROM "{tbl}";')).scalar()
            print(f"  - {tbl}: {actual_cnt} rows (expected: {expected_cnt})")
            if actual_cnt != expected_cnt:
                raise RuntimeError(
                    f"STOP: Row count mismatch in '{tbl}': got {actual_cnt}, expected {expected_cnt}!"
                )

        print("\nAll Database Preflight Checks PASSED! Database is ready for migration 005.")
        return True


if __name__ == "__main__":
    run_database_preflight()
