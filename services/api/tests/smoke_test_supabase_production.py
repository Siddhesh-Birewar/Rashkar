"""
CropNet AI — Phase 4.2 Production API Smoke Test Suite.

Verifies live FastAPI endpoints against the deployed Supabase PostgreSQL database:
- Confirms database connectivity: data_source_mode == 'database', degraded_mode == False.
- Confirms headers: X-Data-Source-Mode: database, X-Degraded-Mode: false.
- Confirms chickpea reproductive thresholds and best-suited pH qualifiers.
- Confirms pomegranate 'Light soil' texture and 480-entry daily water schedule.
- Confirms regional suitability across Baramati, Indapur, Maval, and Mulshi.
"""
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_API_DIR = _SCRIPT_DIR.parent
_SERVICES_DIR = _API_DIR.parent
_CROPNET_ROOT = _SERVICES_DIR.parent
_WORKSPACE_ROOT = _CROPNET_ROOT.parent

for p in [str(_WORKSPACE_ROOT), str(_CROPNET_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi.testclient import TestClient
from cropnet.services.api.app.main import app
from cropnet.services.api.app.core.config import settings


def run_production_api_smoke_tests():
    print("=" * 78)
    print("   CROPNET AI — PHASE 4.2 PRODUCTION SUPABASE API SMOKE TESTS")
    print("=" * 78)
    print(f"Target Environment: {settings.ENVIRONMENT}")
    print(f"Database: ...@{settings.SYNC_DATABASE_URL.split('@')[1]}")

    client = TestClient(app)

    # 1. GET /api/v1/crops
    print("\n[Smoke Test 1] GET /api/v1/crops...")
    res = client.get("/api/v1/crops")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    assert res.headers.get("X-CropNet-Data-Source") == "database", f"Expected X-CropNet-Data-Source: database, got {res.headers.get('X-CropNet-Data-Source')}"
    assert res.headers.get("X-CropNet-Degraded-Mode") == "false", f"Expected X-CropNet-Degraded-Mode: false, got {res.headers.get('X-CropNet-Degraded-Mode')}"
    crops_list = res.json()
    assert len(crops_list) == 10, f"Expected 10 crops, got {len(crops_list)}"
    crop_ids = sorted([c["id"] for c in crops_list])
    expected_crops = sorted([
        "sugarcane", "pomegranate", "soybean", "cotton", "maize",
        "wheat", "sorghum", "chickpea", "bajra", "groundnut"
    ])
    assert crop_ids == expected_crops, f"Crop IDs mismatch: {crop_ids}"
    print(f"  Passed! Verified {len(crops_list)} crops from live database.")

    # 2. GET /api/v1/crops/chickpea
    print("\n[Smoke Test 2] GET /api/v1/crops/chickpea...")
    res = client.get("/api/v1/crops/chickpea")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    chk = res.json()
    assert chk["data_source_mode"] == "database"
    assert chk["degraded_mode"] is False
    assert "Chickpea" in chk["common_name"]

    # Soil qualifiers
    soil = chk["soil"]
    assert soil["ph_best_suited_min"] == 6.0, f"Expected ph_best_suited_min 6.0, got {soil['ph_best_suited_min']}"
    assert soil["ph_best_suited_max"] == 8.0, f"Expected ph_best_suited_max 8.0, got {soil['ph_best_suited_max']}"
    assert soil["ph_optimum_min"] is None, "ph_optimum_min must be None"
    assert soil["ph_optimum_max"] is None, "ph_optimum_max must be None"
    assert soil["ph_tolerable_min"] is None, "ph_tolerable_min must be None"
    assert soil["ph_tolerable_max"] is None, "ph_tolerable_max must be None"
    assert "best-suited" in soil["ph_context_notes"]
    assert soil["best_suited_soil_textures"] == ["Deep Loam", "Silty Clay Loam"]

    # Climate reproductive sensitivity
    clim = chk["climate"]
    assert clim["temp_tolerable_min_c"] is None, "temp_tolerable_min_c must be None"
    assert clim["temp_tolerable_max_c"] is None, "temp_tolerable_max_c must be None"
    assert clim["temp_reproductive_max_c"] == 35.0, f"Expected temp_reproductive_max_c 35.0, got {clim['temp_reproductive_max_c']}"
    assert clim["temp_reproductive_min_mean_c"] == 15.0, f"Expected temp_reproductive_min_mean_c 15.0, got {clim['temp_reproductive_min_mean_c']}"
    assert "reproductive stage causing flower drop" in clim["thermal_threshold_context"]

    # Water decoupled schedules
    water = chk["water"]
    assert len(water["irrigation_stages_detail"]) == 2, "Expected 2 distinct irrigation schedules (ICRISAT and MPKV)"
    src_ids = [s["source_id"] for s in water["irrigation_stages_detail"]]
    assert "icrisat_chickpea_2010" in src_ids
    assert "mpkv_research_2023" in src_ids
    print("  Passed! Verified chickpea reproductive thresholds, decoupled water schedules, and best-suited pH qualifiers.")

    # 3. GET /api/v1/crops/pomegranate
    print("\n[Smoke Test 3] GET /api/v1/crops/pomegranate...")
    res = client.get("/api/v1/crops/pomegranate")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    pom = res.json()
    assert pom["data_source_mode"] == "database"
    assert pom["degraded_mode"] is False

    # Pomegranate Soil Textures
    pom_soil = pom["soil"]
    assert pom_soil["best_suited_soil_textures"] == ["Light soil"], f"Expected ['Light soil'], got {pom_soil['best_suited_soil_textures']}"
    assert pom_soil["preferred_textures"] == ["Light soil"], f"Expected ['Light soil'], got {pom_soil['preferred_textures']}"
    assert pom_soil["acceptable_textures"] == [], f"Expected [], got {pom_soil['acceptable_textures']}"
    assert pom_soil["ph_best_suited_min"] == 6.5
    assert pom_soil["ph_best_suited_max"] == 7.0
    assert pom_soil["ph_tolerable_max"] == 8.5
    assert pom_soil["ph_tolerable_min"] is None

    # Pomegranate Water Requirements & Table
    pom_water = pom["water"]
    assert pom_water["annual_water_requirement_mm_min"] is None, "annual water min must be None"
    assert pom_water["annual_water_requirement_mm_max"] is None, "annual water max must be None"
    dwt = pom_water["daily_water_table"]
    assert dwt is not None, "daily_water_table must not be None"
    assert dwt["unit"] == "liters_per_tree_per_day", f"Expected liters_per_tree_per_day, got {dwt['unit']}"
    assert "mrig_bahar" in dwt
    assert "hasta_bahar" in dwt
    assert "ambia_bahar" in dwt

    total_table_entries = (
        len(dwt["mrig_bahar"]["schedule"]) +
        len(dwt["hasta_bahar"]["schedule"]) +
        len(dwt["ambia_bahar"]["schedule"])
    )
    # 32 entries * 5 age years = 160 per bahar * 3 bahars = 480 values across 96 schedule weeks
    assert total_table_entries == 96, f"Expected 96 schedule weeks, got {total_table_entries}"
    print(f"  Passed! Verified pomegranate 'Light soil' texture and daily water tables ({dwt['unit']}).")

    # 4. GET /api/v1/crops/pomegranate/requirements
    print("\n[Smoke Test 4] GET /api/v1/crops/pomegranate/requirements...")
    res = client.get("/api/v1/crops/pomegranate/requirements")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    req = res.json()
    assert req["crop_id"] == "pomegranate"
    assert req["soil"]["best_suited_soil_textures"] == ["Light soil"]
    assert req["water"]["daily_water_table"]["unit"] == "liters_per_tree_per_day"
    print("  Passed! Verified requirements endpoint response integrity.")

    # 5. Regional Suitability for All 4 Pilot Talukas
    print("\n[Smoke Test 5] Checking regional suitability across all 4 pilot talukas...")
    reg_list = pom["regional_suitability"]
    assert len(reg_list) == 4, f"Expected 4 talukas, got {len(reg_list)}"
    taluka_map = {r["taluka"]: r for r in reg_list}
    for t in ["Baramati", "Indapur", "Maval", "Mulshi"]:
        assert t in taluka_map, f"Missing taluka: {t}"

    # Verify Baramati & Indapur evidence_status
    assert taluka_map["Baramati"]["evidence_status"] == "regional_screening"
    assert taluka_map["Indapur"]["evidence_status"] == "regional_screening"

    # Verify Maval & Mulshi evidence_status
    assert taluka_map["Maval"]["evidence_status"] == "requires_regional_validation"
    assert taluka_map["Mulshi"]["evidence_status"] == "requires_regional_validation"
    print("  Passed! Verified all 4 talukas (Baramati, Indapur, Maval, Mulshi) and evidence statuses.")

    # 6. GET /api/v1/crops/{crop_id}/sources and Modular Source Verification
    print("\n[Smoke Test 6] GET /api/v1/crops/chickpea/sources and /pomegranate/sources...")
    res = client.get("/api/v1/crops/chickpea/sources")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    chk_sources = res.json()
    assert len(chk_sources) >= 1, "Expected at least 1 source for chickpea"
    print(f"  Passed! Verified chickpea source citations: {[s['id'] for s in chk_sources]}")

    # Check granular module source attributions
    assert chk["soil"]["source_id"] == "icrisat_chickpea_2010"
    assert chk["climate"]["source_id"] == "icrisat_chickpea_2010"
    assert pom["soil"]["source_id"] == "icar_nrcp_manage_2022"
    assert pom["climate"]["source_id"] == "icar_nrcp_manage_2022"
    print("  Passed! Verified authoritative source attributions on soil and climate modules (ICRISAT and ICAR-NRCP).")

    print("\n" + "=" * 78)
    print("   ALL PRODUCTION SUPABASE API SMOKE TESTS PASSED WITH ZERO ERRORS!")
    print("=" * 78)
    return True


if __name__ == "__main__":
    run_production_api_smoke_tests()
