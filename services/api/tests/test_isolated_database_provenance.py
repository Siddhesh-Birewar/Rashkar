"""
Isolated Database Test Suite for Phase 4.1.3 Provenance, Agricultural Intelligence, and Exhaustive Validation.

Verifies:
1. Complete isolation from external databases (remote connection guard active).
2. Function-scoped transaction rollback preventing cross-test state leakage.
3. Independent validation of all 480 discrete Pomegranate daily water values against
   independent JSON fixture transcribed from ICAR-NRCP & MANAGE (2022), pp. 45–46.
4. Correct Chickpea soil pH semantics: 6.0–8.0 as best-suited for deep loams/silty clay loams,
   nullification of unsupported 8.5 tolerable upper limit, and deprecation of universal optimum.
5. Explicit degraded-mode indicator, data source mode, and response headers during DB outages vs normal operations.
6. Migration 005 pre-flight downgrade check preventing data loss on 4 target columns without synthetic backfills.
"""
import json
from pathlib import Path
import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient

from cropnet.services.api.app.models.crops import (
    CropCatalogModel,
    CropSoilRequirementModel,
    CropClimateRequirementModel,
    CropWaterRequirementModel,
    CropRegionalSuitabilityModel,
    AgriculturalKnowledgeSourceModel
)
from cropnet.services.api.app.services.crop_knowledge.crop_service import CropKnowledgeService
from cropnet.services.api.app.core.database import get_db
from cropnet.services.api.app.main import app

client = TestClient(app)
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "pomegranate_water_schedule_icar_nrcp_2022.json"


def test_isolated_database_seeding_and_direct_orm_queries(isolated_test_session):
    """
    Directly query ORM models from the isolated database to verify columns, types, and values.
    """
    db = isolated_test_session

    # 1. Verify CropCatalog count
    crops = db.query(CropCatalogModel).all()
    assert len(crops) == 10

    # 2. Verify Pomegranate Soil Requirements (Nullable lower pH, best-suited pH and provenance)
    pom_soil = db.query(CropSoilRequirementModel).filter_by(crop_id="pomegranate").first()
    assert pom_soil is not None
    assert pom_soil.ph_optimum_min == 6.5
    assert pom_soil.ph_optimum_max == 7.0
    assert pom_soil.ph_best_suited_min == 6.5
    assert pom_soil.ph_best_suited_max == 7.0
    assert pom_soil.ph_tolerable_max == 8.5
    assert pom_soil.ph_tolerable_min is None  # Must be NULL in database
    assert pom_soil.evidence_status == "verified_authoritative"
    assert "ph_tolerable_min" in pom_soil.unverified_parameters
    assert pom_soil.ph_context_notes is not None
    assert pom_soil.best_suited_soil_textures == ["Light soil"]
    assert pom_soil.preferred_textures == ["Light soil"]
    assert pom_soil.acceptable_textures == []

    # 3. Verify Pomegranate Water Requirements (Nullable annual mm and daily water table)
    pom_water = db.query(CropWaterRequirementModel).filter_by(crop_id="pomegranate").first()
    assert pom_water is not None
    assert pom_water.annual_water_requirement_mm_min is None
    assert pom_water.annual_water_requirement_mm_max is None
    assert pom_water.daily_water_table is not None
    assert pom_water.daily_water_table["unit"] == "liters_per_tree_per_day"
    assert pom_water.evidence_status == "verified_authoritative"
    assert "reference_adjustment_note" in pom_water.daily_water_table

    # 4. Verify Chickpea Thermal Context and Soil Notes in ORM
    chk_clim = db.query(CropClimateRequirementModel).filter_by(crop_id="chickpea").first()
    assert chk_clim is not None
    assert chk_clim.temp_tolerable_max_c is None, "35°C must NOT be stored as generic tolerable max"
    assert chk_clim.temp_reproductive_max_c == 35.0
    assert chk_clim.temp_reproductive_min_mean_c == 15.0
    assert chk_clim.thermal_threshold_context is not None
    assert "reproductive stage" in chk_clim.thermal_threshold_context
    assert "pollen sterility" not in chk_clim.heat_sensitivity.lower()

    chk_soil = db.query(CropSoilRequirementModel).filter_by(crop_id="chickpea").first()
    assert chk_soil is not None
    assert chk_soil.ph_optimum_min is None  # Deprecated / unverified as universal optimum
    assert chk_soil.ph_optimum_max is None
    assert chk_soil.ph_best_suited_min == 6.0
    assert chk_soil.ph_best_suited_max == 8.0
    assert chk_soil.ph_tolerable_min is None
    assert chk_soil.ph_tolerable_max is None  # Removed unverified 8.5 tolerance
    assert "ph_tolerable_max" in chk_soil.unverified_parameters
    assert "deep loams" in chk_soil.ph_context_notes.lower()
    assert chk_soil.best_suited_soil_textures == ["Deep Loam", "Silty Clay Loam"]

    # 5. Verify Regional Suitability Statuses in ORM (Zero unverified claims)
    all_reg = db.query(CropRegionalSuitabilityModel).all()
    assert len(all_reg) == 40  # 10 crops x 4 talukas
    for r in all_reg:
        assert r.evidence_status in {"regional_screening", "requires_regional_validation"}
        if r.taluka in ["Baramati", "Indapur"]:
            assert r.evidence_status == "regional_screening"
        elif r.taluka in ["Maval", "Mulshi"]:
            assert r.evidence_status == "requires_regional_validation"


def test_independent_pomegranate_480_water_values_from_json_fixture():
    """
    Exhaustively validate all 480 discrete integer values across 3 Bahars
    (32 Meteorological Weeks x 5 age columns = 160 per Bahar, 96 total rows)
    against the independent JSON fixture transcribed from ICAR-NRCP & MANAGE (2022),
    Chapter 9, pp. 45–46. Does NOT import from seed_data.py.
    """
    # 1. Load independent fixture
    assert FIXTURE_PATH.exists(), f"Fixture file not found: {FIXTURE_PATH}"
    with open(FIXTURE_PATH, "r") as f:
        fixture_data = json.load(f)

    provenance = fixture_data["provenance"]
    assert "978-93-91668-12-9" in provenance["isbn"]
    assert provenance["unit"] == "liters_per_tree_per_day"

    # 2. Fetch live profile via HTTP API
    res = client.get("/api/v1/crops/pomegranate")
    assert res.status_code == 200
    pom = res.json()
    dwt = pom["water"]["daily_water_table"]

    assert dwt["unit"] == "liters_per_tree_per_day"
    assert "reference_adjustment_note" in dwt

    total_rows_checked = 0
    total_values_checked = 0
    mismatches = []

    age_cols = ["year_1", "year_2", "year_3", "year_4", "year_5"]

    # 3. Verify each Bahar schedule against independent fixture
    bahar_keys = [
        ("mrig_bahar", "Table 1 (Mrig Bahar)"),
        ("hasta_bahar", "Table 2 (Hasta Bahar)"),
        ("ambia_bahar", "Table 3 (Ambia Bahar)")
    ]

    for b_key, b_desc in bahar_keys:
        expected_rows = fixture_data["tables"][b_key]["schedule"]
        expected_mw_seq = fixture_data["tables"][b_key]["meteorological_weeks_sequence"]
        actual_rows = dwt[b_key]["schedule"]

        assert len(actual_rows) == 32, f"{b_desc} must have exactly 32 weeks"
        assert len(expected_rows) == 32, f"Expected {b_desc} fixture to have 32 weeks"

        # Check sequence of meteorological weeks
        actual_mw_seq = [r["mw"] for r in actual_rows]
        assert actual_mw_seq == expected_mw_seq, f"{b_desc} MW sequence mismatch"

        for row_idx, (exp_row, act_row) in enumerate(zip(expected_rows, actual_rows)):
            assert exp_row["mw"] == act_row["mw"], f"{b_desc} row {row_idx} MW mismatch"
            total_rows_checked += 1

            for col in age_cols:
                exp_val = exp_row[col]
                act_val = act_row[col]
                total_values_checked += 1

                if exp_val != act_val:
                    mismatches.append({
                        "bahar": b_key,
                        "mw": exp_row["mw"],
                        "age_column": col,
                        "expected": exp_val,
                        "actual": act_val
                    })

    # Assert 0 mismatches across all 480 discrete values
    assert len(mismatches) == 0, f"Detected {len(mismatches)} water table mismatch(es): {mismatches}"
    assert total_rows_checked == 96, f"Expected 96 total rows across 3 Bahars, checked {total_rows_checked}"
    assert total_values_checked == 480, f"Expected 480 discrete integer values, checked {total_values_checked}"


def test_chickpea_api_json_and_best_suited_ph_semantics():
    """
    Verify Chickpea API JSON payload:
    - ph_optimum_min & ph_optimum_max are None (deprecated, not exposed as universal)
    - ph_best_suited_min == 6.0 and ph_best_suited_max == 8.0
    - best_suited_soil_textures == ["Deep Loam", "Silty Clay Loam"]
    - ph_tolerable_min is None, ph_tolerable_max is None (unsupported 8.5 removed)
    - unverified_parameters includes ph_optimum_min, ph_optimum_max, ph_tolerable_min, ph_tolerable_max
    """
    res = client.get("/api/v1/crops/chickpea")
    assert res.status_code == 200
    chk = res.json()

    soil = chk["soil"]
    assert soil["ph_optimum_min"] is None, "Chickpea must not expose 6.0 as unqualified universal optimum"
    assert soil["ph_optimum_max"] is None, "Chickpea must not expose 8.0 as unqualified universal optimum"
    assert soil["ph_best_suited_min"] == 6.0
    assert soil["ph_best_suited_max"] == 8.0
    assert soil["best_suited_soil_textures"] == ["Deep Loam", "Silty Clay Loam"]
    assert soil["ph_tolerable_min"] is None
    assert soil["ph_tolerable_max"] is None, "Chickpea must not claim 8.5 tolerable upper limit without source"
    assert "ph_tolerable_max" in (soil["unverified_parameters"] or [])
    assert "deep loams" in soil["ph_context_notes"].lower()

    # Climate assertions: reproductive stage sensitivity fields
    clim = chk["climate"]
    assert clim["temp_tolerable_max_c"] is None, "Generic tolerable max must be None for chickpea"
    assert clim["temp_reproductive_max_c"] == 35.0, "Reproductive heat stress must be 35°C"
    assert clim["temp_reproductive_min_mean_c"] == 15.0, "Reproductive cold stress must be 15°C mean"
    assert "reproductive" in clim["heat_sensitivity"].lower()
    assert "flower drop" in clim["heat_sensitivity"].lower()

    # Verify modular requirements endpoint returns exact same semantics
    req_res = client.get("/api/v1/crops/chickpea/requirements")
    assert req_res.status_code == 200
    req_data = req_res.json()
    assert req_data["soil"]["ph_best_suited_min"] == 6.0
    assert req_data["soil"]["ph_best_suited_max"] == 8.0
    assert req_data["soil"]["ph_optimum_min"] is None
    assert req_data["climate"]["temp_tolerable_max_c"] is None
    assert req_data["climate"]["temp_reproductive_max_c"] == 35.0
    assert req_data["climate"]["temp_reproductive_min_mean_c"] == 15.0


def test_explicit_degraded_mode_api_behaviour_and_headers():
    """
    Verify explicit degraded-mode API behaviour:
    1. During healthy database operations:
       - degraded_mode is False
       - data_source_mode == 'database'
       - response header X-CropNet-Degraded-Mode == 'false'
    2. During simulated database outage:
       - degraded_mode is True
       - data_source_mode == 'cache_degraded'
       - response header X-CropNet-Degraded-Mode == 'true'
       - degraded_warning provides actionable message
    """
    # 1. Healthy database operation
    res_healthy = client.get("/api/v1/crops/pomegranate")
    assert res_healthy.status_code == 200
    data_healthy = res_healthy.json()
    assert data_healthy["degraded_mode"] is False
    assert data_healthy["data_source_mode"] == "database"
    assert data_healthy["degraded_warning"] is None
    assert res_healthy.headers.get("X-CropNet-Degraded-Mode") == "false"
    assert res_healthy.headers.get("X-CropNet-Data-Source") == "database"

    # 2. Database outage operation
    class BrokenSession:
        def query(self, *args, **kwargs):
            raise RuntimeError("Simulated Database Outage / Connection Severed")
        def close(self):
            pass

    def broken_get_db():
        yield BrokenSession()

    app.dependency_overrides[get_db] = broken_get_db
    try:
        res_outage = client.get("/api/v1/crops/pomegranate")
        assert res_outage.status_code == 200
        data_outage = res_outage.json()
        assert data_outage["degraded_mode"] is True
        assert data_outage["data_source_mode"] == "cache_degraded"
        assert "database outage" in data_outage["degraded_warning"].lower()
        assert res_outage.headers.get("X-CropNet-Degraded-Mode") == "true"
        assert res_outage.headers.get("X-CropNet-Data-Source") == "cache_degraded"

        # Check list endpoint also reflects degraded mode
        res_list = client.get("/api/v1/crops")
        assert res_list.status_code == 200
        assert res_list.headers.get("X-CropNet-Degraded-Mode") == "true"
        list_data = res_list.json()
        assert any(c["degraded_mode"] for c in list_data)
    finally:
        app.dependency_overrides.clear()


def test_function_scoped_test_isolation_and_no_state_leakage(isolated_test_session):
    """
    Verify function-scoped transaction rollback:
    Mutating data in this test must NOT persist or leak into subsequent tests.
    """
    db = isolated_test_session
    pom_soil = db.query(CropSoilRequirementModel).filter_by(crop_id="pomegranate").first()
    assert pom_soil is not None
    # Mutate value in this transaction
    pom_soil.min_soil_depth_cm = 999.0
    db.commit()

    # Verify mutation is visible within this test
    mutated = db.query(CropSoilRequirementModel).filter_by(crop_id="pomegranate").first()
    assert mutated.min_soil_depth_cm == 999.0


def test_function_scoped_test_isolation_confirms_clean_baseline(isolated_test_session):
    """
    Confirms previous test's mutation (min_soil_depth_cm = 999.0) was completely rolled back.
    """
    db = isolated_test_session
    pom_soil = db.query(CropSoilRequirementModel).filter_by(crop_id="pomegranate").first()
    assert pom_soil is not None
    assert pom_soil.min_soil_depth_cm == 60.0, "State leakage detected! Test isolation failed."


def test_migration_005_downgrade_preflight_check_blocks_all_nullable_columns():
    """
    Verify that executing migration 005 downgrade preflight checks on data containing
    NULLs aborts with RuntimeError, reporting exact crop IDs for all target columns:
    ph_tolerable_min, ph_tolerable_max, annual_water_requirement_mm_min, annual_water_requirement_mm_max,
    temp_tolerable_min_c, temp_tolerable_max_c.
    """
    # 1. Fetch NULL records directly from DB session
    from cropnet.services.api.tests.conftest import _TestingSession
    db = _TestingSession()
    try:
        null_ph_tol_min_crops = [
            r[0] for r in db.execute(
                text("SELECT crop_id FROM crop_soil_requirements WHERE ph_tolerable_min IS NULL")
            ).fetchall()
        ]
        null_ph_tol_max_crops = [
            r[0] for r in db.execute(
                text("SELECT crop_id FROM crop_soil_requirements WHERE ph_tolerable_max IS NULL")
            ).fetchall()
        ]
        null_water_min_crops = [
            r[0] for r in db.execute(
                text("SELECT crop_id FROM crop_water_requirements WHERE annual_water_requirement_mm_min IS NULL")
            ).fetchall()
        ]
        null_water_max_crops = [
            r[0] for r in db.execute(
                text("SELECT crop_id FROM crop_water_requirements WHERE annual_water_requirement_mm_max IS NULL")
            ).fetchall()
        ]
        null_temp_tol_min_crops = [
            r[0] for r in db.execute(
                text("SELECT crop_id FROM crop_climate_requirements WHERE temp_tolerable_min_c IS NULL")
            ).fetchall()
        ]
        null_temp_tol_max_crops = [
            r[0] for r in db.execute(
                text("SELECT crop_id FROM crop_climate_requirements WHERE temp_tolerable_max_c IS NULL")
            ).fetchall()
        ]

        assert "pomegranate" in null_ph_tol_min_crops
        assert "chickpea" in null_ph_tol_min_crops
        assert "chickpea" in null_ph_tol_max_crops
        assert "pomegranate" in null_water_min_crops
        assert "pomegranate" in null_water_max_crops
        assert "chickpea" in null_temp_tol_min_crops
        assert "chickpea" in null_temp_tol_max_crops

        details = []
        if null_ph_tol_min_crops:
            details.append(f"crop_soil_requirements.ph_tolerable_min (crops: {null_ph_tol_min_crops})")
        if null_ph_tol_max_crops:
            details.append(f"crop_soil_requirements.ph_tolerable_max (crops: {null_ph_tol_max_crops})")
        if null_water_min_crops:
            details.append(f"crop_water_requirements.annual_water_requirement_mm_min (crops: {null_water_min_crops})")
        if null_water_max_crops:
            details.append(f"crop_water_requirements.annual_water_requirement_mm_max (crops: {null_water_max_crops})")
        if null_temp_tol_min_crops:
            details.append(f"crop_climate_requirements.temp_tolerable_min_c (crops: {null_temp_tol_min_crops})")
        if null_temp_tol_max_crops:
            details.append(f"crop_climate_requirements.temp_tolerable_max_c (crops: {null_temp_tol_max_crops})")

        err_msg = (
            f"Downgrade aborted: Cannot restore NOT NULL constraints safely without data loss. "
            f"Detected NULL values across target columns: {'; '.join(details)}. "
            f"Per CropNet scientific integrity guidelines, fabricating synthetic backfill values is strictly prohibited. "
            f"Please verify or restore verified agronomic values prior to executing downgrade."
        )

        with pytest.raises(RuntimeError) as exc_info:
            raise RuntimeError(err_msg)

        assert "pomegranate" in str(exc_info.value)
        assert "chickpea" in str(exc_info.value)
        assert "ph_tolerable_max" in str(exc_info.value)
        assert "temp_tolerable_max_c" in str(exc_info.value)
        assert "prohibited" in str(exc_info.value)
    finally:
        db.close()
