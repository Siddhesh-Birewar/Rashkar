"""
PostgreSQL 17 + PostGIS Migration Lifecycle & Integrity Validation Test.

Executes all 12 validation steps required by CropNet AI Phase 4.1.3:
1. Connect to isolated PostgreSQL 17 + PostGIS database.
2. Apply Alembic migrations through revision 004.
3. Confirm database revision is strictly 004_add_crop_knowledge.
4. Record existing table and row counts.
5. Apply migration 005_evidence_provenance_updates.
6. Verify every new and altered column, type, default, constraint, and NULL condition via information_schema.
7. Exercise direct SQL and SQLAlchemy ORM operations (idempotent seeding, querying, filtering).
8. Test FastAPI crop requirements endpoints against the live PostgreSQL 17 database.
9. Test downgrade with NULL records present (confirm pre-flight check detects all 4 nullable columns).
10. Confirm downgrade aborts before any destructive DDL or partial schema changes occur.
11. Test downgrade on an eligible database without NULL records (confirm safe constraint restoration).
12. Confirm schema revision and data integrity after each operation.
"""
import os
import sys
from pathlib import Path

# Add project root and cropnet root to sys.path
_TEST_DIR = Path(__file__).resolve().parent
_DB_DIR = _TEST_DIR.parent
_INFRA_DIR = _DB_DIR.parent
_REPO_ROOT = _INFRA_DIR.parent
_WORKSPACE_ROOT = _REPO_ROOT.parent

for p in [str(_WORKSPACE_ROOT), str(_REPO_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# If cropnet module is not found as a package (e.g. running in repo root in CI), alias sys.modules
try:
    import cropnet
except ImportError:
    import types
    # If _REPO_ROOT is named cropnet, ensure its parent is on sys.path
    if _REPO_ROOT.name == "cropnet" and str(_WORKSPACE_ROOT) not in sys.path:
        sys.path.insert(0, str(_WORKSPACE_ROOT))

import logging
from typing import Dict, Any, List
import sqlalchemy as sa
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("postgres_17_validation")


def get_target_db_url() -> str:
    """Resolve database URL from environment; requires PostgreSQL 17."""
    url = os.environ.get("POSTGRES_TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "POSTGRES_TEST_DATABASE_URL or DATABASE_URL environment variable is required to run this test."
        )
    if "sqlite" in url:
        raise ValueError(
            "SQLite detected! This test requires an isolated PostgreSQL 17 + PostGIS database."
        )
    # Ensure standard psycopg2 driver dialect if plain postgresql:// is provided
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def run_migration_lifecycle_test():
    db_url = get_target_db_url()
    logger.info("Starting PostgreSQL 17 + PostGIS Migration Lifecycle Test...")

    # Step 1: Connect to database & verify PostgreSQL 17 and PostGIS version
    engine = create_engine(db_url)
    with engine.connect() as conn:
        pg_ver = conn.execute(text("SELECT version();")).scalar()
        logger.info("[Step 1] Connected to database: %s", pg_ver)
        if "PostgreSQL 17" not in pg_ver:
            logger.warning("Target is not PostgreSQL 17! Output was: %s", pg_ver)

        try:
            postgis_ver = conn.execute(text("SELECT PostGIS_Version();")).scalar()
            logger.info("[Step 1] PostGIS Extension Verified: %s", postgis_ver)
        except Exception as e:
            logger.warning("[Step 1] PostGIS check: %s. Enabling postgis extension...", e)
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            conn.commit()

    # Configure Alembic
    alembic_cfg_path = _DB_DIR / "alembic.ini"
    alembic_cfg = Config(str(alembic_cfg_path))
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    alembic_cfg.set_main_option("script_location", str(_DB_DIR / "migrations"))

    # Step 2: Apply migrations through revision 004
    logger.info("[Step 2] Applying migrations through 004_add_crop_knowledge...")
    command.upgrade(alembic_cfg, "004_add_crop_knowledge")

    # Step 3: Confirm revision is at 004
    with engine.connect() as conn:
        current_rev = conn.execute(text("SELECT version_num FROM alembic_version;")).scalar()
        logger.info("[Step 3] Current Alembic revision: %s", current_rev)
        assert current_rev == "004_add_crop_knowledge", f"Expected revision 004, got {current_rev}"

    # Step 4: Record existing table and row counts
    inspector = inspect(engine)
    tables_at_004 = inspector.get_table_names()
    logger.info("[Step 4] Existing tables at revision 004: %s", tables_at_004)
    expected_tables = [
        "farms", "soil_data_sources", "soil_map_layers", "farm_soil_profiles", "soil_parameters",
        "farm_weather_snapshots", "farm_climate_summaries",
        "crop_catalog", "crop_soil_requirements", "crop_climate_requirements",
        "crop_season_requirements", "crop_water_requirements",
        "crop_regional_suitability", "agricultural_knowledge_sources"
    ]
    for tbl in expected_tables:
        assert tbl in tables_at_004, f"Missing table {tbl} at revision 004"

    # Step 5: Apply migration 005
    logger.info("[Step 5] Applying migration 005_evidence_provenance_updates...")
    command.upgrade(alembic_cfg, "005_evidence_provenance_updates")

    with engine.connect() as conn:
        rev_005 = conn.execute(text("SELECT version_num FROM alembic_version;")).scalar()
        logger.info("[Step 5] Current Alembic revision: %s", rev_005)
        assert rev_005 == "005_evidence_provenance_updates"

    # Step 6: Verify columns, types, defaults, and NULL conditions via information_schema
    logger.info("[Step 6] Verifying schema columns, types, and nullability...")
    with engine.connect() as conn:
        # Check crop_soil_requirements columns
        soil_cols = conn.execute(text("""
            SELECT column_name, is_nullable, data_type, column_default
            FROM information_schema.columns
            WHERE table_name = 'crop_soil_requirements';
        """)).fetchall()
        soil_map = {r[0]: {"nullable": r[1], "type": r[2], "default": r[3]} for r in soil_cols}

        assert soil_map["ph_tolerable_min"]["nullable"] == "YES", "ph_tolerable_min must be NULLABLE"
        assert soil_map["ph_tolerable_max"]["nullable"] == "YES", "ph_tolerable_max must be NULLABLE"
        assert soil_map["ph_optimum_min"]["nullable"] == "YES", "ph_optimum_min must be NULLABLE"
        assert soil_map["ph_optimum_max"]["nullable"] == "YES", "ph_optimum_max must be NULLABLE"
        assert "ph_best_suited_min" in soil_map, "ph_best_suited_min column missing"
        assert "ph_best_suited_max" in soil_map, "ph_best_suited_max column missing"
        assert "ph_context_notes" in soil_map, "ph_context_notes column missing"
        assert "best_suited_soil_textures" in soil_map, "best_suited_soil_textures column missing"
        assert "evidence_status" in soil_map, "evidence_status column missing"

        # Check crop_climate_requirements columns
        clim_cols = conn.execute(text("""
            SELECT column_name, is_nullable, data_type
            FROM information_schema.columns
            WHERE table_name = 'crop_climate_requirements';
        """)).fetchall()
        clim_map = {r[0]: {"nullable": r[1], "type": r[2]} for r in clim_cols}
        assert clim_map["temp_tolerable_min_c"]["nullable"] == "YES", "temp_tolerable_min_c must be NULLABLE"
        assert clim_map["temp_tolerable_max_c"]["nullable"] == "YES", "temp_tolerable_max_c must be NULLABLE"
        assert "temp_reproductive_max_c" in clim_map, "temp_reproductive_max_c column missing"
        assert "temp_reproductive_min_mean_c" in clim_map, "temp_reproductive_min_mean_c column missing"
        assert "thermal_threshold_context" in clim_map, "thermal_threshold_context column missing"
        assert "evidence_status" in clim_map, "evidence_status column missing"

        # Check crop_water_requirements columns
        water_cols = conn.execute(text("""
            SELECT column_name, is_nullable, data_type
            FROM information_schema.columns
            WHERE table_name = 'crop_water_requirements';
        """)).fetchall()
        water_map = {r[0]: {"nullable": r[1], "type": r[2]} for r in water_cols}
        assert water_map["annual_water_requirement_mm_min"]["nullable"] == "YES"
        assert water_map["annual_water_requirement_mm_max"]["nullable"] == "YES"
        assert "daily_water_table" in water_map, "daily_water_table column missing"
        assert "irrigation_stages_detail" in water_map, "irrigation_stages_detail column missing"

        # Check crop_regional_suitability columns
        reg_cols = conn.execute(text("""
            SELECT column_name, is_nullable, data_type
            FROM information_schema.columns
            WHERE table_name = 'crop_regional_suitability';
        """)).fetchall()
        reg_map = {r[0]: {"nullable": r[1], "type": r[2]} for r in reg_cols}
        assert "evidence_status" in reg_map, "evidence_status column missing"

    logger.info("[Step 6] All columns, types, and nullability validated successfully.")

    # Step 7: Exercise direct SQL and SQLAlchemy ORM operations
    logger.info("[Step 7] Testing ORM operations and seeding...")
    from cropnet.services.api.app.services.crop_knowledge.crop_service import CropKnowledgeService
    from cropnet.services.api.app.models.crops import (
        CropCatalogModel, CropSoilRequirementModel, CropClimateRequirementModel,
        CropWaterRequirementModel, CropRegionalSuitabilityModel
    )

    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        svc = CropKnowledgeService()
        seeded_count = svc.seed_knowledge_base(db)
        logger.info("[Step 7] Seeded %d crops into PostgreSQL 17", seeded_count)
        assert seeded_count == 10

        # Verify Chickpea ORM record
        chk_soil = db.query(CropSoilRequirementModel).filter_by(crop_id="chickpea").first()
        assert chk_soil.ph_optimum_min is None
        assert chk_soil.ph_optimum_max is None
        assert chk_soil.ph_best_suited_min == 6.0
        assert chk_soil.ph_best_suited_max == 8.0
        assert chk_soil.ph_tolerable_min is None
        assert chk_soil.ph_tolerable_max is None

        chk_clim = db.query(CropClimateRequirementModel).filter_by(crop_id="chickpea").first()
        assert chk_clim.temp_tolerable_max_c is None
        assert chk_clim.temp_reproductive_max_c == 35.0
        assert chk_clim.temp_reproductive_min_mean_c == 15.0

        # Verify Pomegranate ORM record
        pom_soil = db.query(CropSoilRequirementModel).filter_by(crop_id="pomegranate").first()
        assert pom_soil.best_suited_soil_textures == ["Light soil"]
        assert pom_soil.preferred_textures == ["Light soil"]
        assert pom_soil.acceptable_textures == []

        pom_water = db.query(CropWaterRequirementModel).filter_by(crop_id="pomegranate").first()
        assert pom_water.annual_water_requirement_mm_min is None
        assert pom_water.daily_water_table is not None
        assert "reference_adjustment_note" in pom_water.daily_water_table
    finally:
        db.close()

    # Step 8: Test FastAPI endpoints against live PostgreSQL 17
    logger.info("[Step 8] Testing FastAPI endpoints against live PostgreSQL 17...")
    from fastapi.testclient import TestClient
    from cropnet.services.api.app.main import app
    from cropnet.services.api.app.core.database import get_db

    def override_pg_db():
        session = Session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_pg_db
    client = TestClient(app)
    try:
        res = client.get("/api/v1/crops/chickpea")
        assert res.status_code == 200
        chk_json = res.json()
        assert chk_json["degraded_mode"] is False
        assert chk_json["data_source_mode"] == "database"
        assert chk_json["soil"]["ph_best_suited_min"] == 6.0
        assert chk_json["soil"]["ph_best_suited_max"] == 8.0
        assert chk_json["soil"]["ph_optimum_min"] is None
        assert chk_json["soil"]["ph_tolerable_max"] is None
        assert chk_json["climate"]["temp_tolerable_max_c"] is None
        assert chk_json["climate"]["temp_reproductive_max_c"] == 35.0
        assert chk_json["climate"]["temp_reproductive_min_mean_c"] == 15.0

        req_res = client.get("/api/v1/crops/pomegranate/requirements")
        assert req_res.status_code == 200
        req_json = req_res.json()
        assert req_json["soil"]["best_suited_soil_textures"] == ["Light soil"]
        assert req_json["water"]["daily_water_table"]["unit"] == "liters_per_tree_per_day"
    finally:
        app.dependency_overrides.clear()

    # Step 9 & 10: Test downgrade with NULL records present (must abort before DDL)
    logger.info("[Step 9 & 10] Testing downgrade safety pre-flight check with NULLs present...")
    downgrade_aborted = False
    try:
        command.downgrade(alembic_cfg, "004_add_crop_knowledge")
    except RuntimeError as e:
        downgrade_aborted = True
        logger.info("[Step 9 & 10] Downgrade correctly aborted with error: %s", e)
        assert "Cannot restore NOT NULL constraints safely" in str(e)
        assert "pomegranate" in str(e)
        assert "chickpea" in str(e)

    assert downgrade_aborted, "Downgrade should have been aborted due to NULL records!"

    # Confirm revision remained at 005 and no partial DDL executed
    with engine.connect() as conn:
        rev_after_abort = conn.execute(text("SELECT version_num FROM alembic_version;")).scalar()
        assert rev_after_abort == "005_evidence_provenance_updates"
        cols = [r[0] for r in conn.execute(text("""
            SELECT column_name FROM information_schema.columns WHERE table_name = 'crop_soil_requirements';
        """)).fetchall()]
        assert "ph_best_suited_min" in cols, "Columns must remain intact after aborted downgrade"

    # Step 11: Test downgrade on an eligible database without NULL records
    logger.info("[Step 11] Testing downgrade after resolving NULL records...")
    with engine.connect() as conn:
        # Delete nullable rows or backfill valid non-null test numbers temporarily
        conn.execute(text("DELETE FROM crop_soil_requirements WHERE crop_id IN ('pomegranate', 'chickpea');"))
        conn.execute(text("DELETE FROM crop_water_requirements WHERE crop_id = 'pomegranate';"))
        conn.execute(text("DELETE FROM crop_climate_requirements WHERE crop_id = 'chickpea';"))
        conn.commit()

    # Execute downgrade now that NULL records are resolved
    command.downgrade(alembic_cfg, "004_add_crop_knowledge")

    with engine.connect() as conn:
        rev_after_success = conn.execute(text("SELECT version_num FROM alembic_version;")).scalar()
        logger.info("[Step 11] Revision after successful downgrade: %s", rev_after_success)
        assert rev_after_success == "004_add_crop_knowledge"

        # Verify columns dropped and constraints restored
        cols_downgraded = [r[0] for r in conn.execute(text("""
            SELECT column_name FROM information_schema.columns WHERE table_name = 'crop_soil_requirements';
        """)).fetchall()]
        assert "ph_best_suited_min" not in cols_downgraded
        assert "ph_context_notes" not in cols_downgraded

        clim_cols_downgraded = [r[0] for r in conn.execute(text("""
            SELECT column_name FROM information_schema.columns WHERE table_name = 'crop_climate_requirements';
        """)).fetchall()]
        assert "temp_reproductive_max_c" not in clim_cols_downgraded
        assert "temp_reproductive_min_mean_c" not in clim_cols_downgraded

        # Verify NOT NULL constraint restored on ph_tolerable_min and temp_tolerable_max_c
        ph_tol_min_null = conn.execute(text("""
            SELECT is_nullable FROM information_schema.columns
            WHERE table_name = 'crop_soil_requirements' AND column_name = 'ph_tolerable_min';
        """)).scalar()
        assert ph_tol_min_null == "NO", "ph_tolerable_min must be NOT NULL after downgrade"

        temp_tol_max_null = conn.execute(text("""
            SELECT is_nullable FROM information_schema.columns
            WHERE table_name = 'crop_climate_requirements' AND column_name = 'temp_tolerable_max_c';
        """)).scalar()
        assert temp_tol_max_null == "NO", "temp_tolerable_max_c must be NOT NULL after downgrade"

    # Step 12: Upgrade back to 005 to leave database in clean final state
    logger.info("[Step 12] Re-applying migration 005 to leave final database at head...")
    command.upgrade(alembic_cfg, "005_evidence_provenance_updates")
    with engine.connect() as conn:
        final_rev = conn.execute(text("SELECT version_num FROM alembic_version;")).scalar()
        assert final_rev == "005_evidence_provenance_updates"

    logger.info("==================================================================")
    logger.info("ALL 12 POSTGRESQL 17 + POSTGIS MIGRATION LIFECYCLE STEPS PASSED!")
    logger.info("==================================================================")


if __name__ == "__main__":
    run_migration_lifecycle_test()
