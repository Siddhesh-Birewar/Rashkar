import pytest
from fastapi.testclient import TestClient

from cropnet.services.api.app.main import app
from cropnet.services.api.app.services.crop_knowledge.seed_data import CROPS_DATA

client = TestClient(app)

EXPECTED_CROP_IDS = [
    "sugarcane",
    "pomegranate",
    "soybean",
    "cotton",
    "maize",
    "wheat",
    "sorghum",
    "bajra",
    "chickpea",
    "groundnut"
]


def test_crop_catalog_list_and_category_season_filters():
    """
    Verify GET /api/v1/crops returns all 10 initial crops and supports category and season filters.
    """
    # 1. Full Catalogue Listing
    res = client.get("/api/v1/crops")
    assert res.status_code == 200
    crops = res.json()
    assert len(crops) >= 10
    retrieved_ids = [c["id"] for c in crops]
    for exp_id in EXPECTED_CROP_IDS:
        assert exp_id in retrieved_ids

    # 2. Filter by Category: 'Cereal'
    res_cereal = client.get("/api/v1/crops?category=Cereal")
    assert res_cereal.status_code == 200
    cereal_crops = res_cereal.json()
    cereal_ids = [c["id"] for c in cereal_crops]
    assert "wheat" in cereal_ids
    assert "maize" in cereal_ids
    assert "sorghum" in cereal_ids
    assert "bajra" in cereal_ids
    assert "sugarcane" not in cereal_ids

    # 3. Filter by Category: 'Horticulture'
    res_hort = client.get("/api/v1/crops?category=Horticulture")
    assert res_hort.status_code == 200
    hort_crops = res_hort.json()
    assert any(c["id"] == "pomegranate" for c in hort_crops)

    # 4. Filter by Season: 'Rabi'
    res_rabi = client.get("/api/v1/crops?season=Rabi")
    assert res_rabi.status_code == 200
    rabi_crops = res_rabi.json()
    rabi_ids = [c["id"] for c in rabi_crops]
    assert "wheat" in rabi_ids
    assert "chickpea" in rabi_ids
    assert "sorghum" in rabi_ids


def test_crop_detailed_profile_and_scientific_traceability():
    """
    Verify GET /api/v1/crops/{crop_id} returns complete agronomic criteria and MPKV/ICAR source citations.
    """
    res = client.get("/api/v1/crops/sugarcane")
    assert res.status_code == 200
    profile = res.json()

    # Basic Info
    assert profile["id"] == "sugarcane"
    assert profile["common_name"] == "Sugarcane"
    assert profile["scientific_name"] == "Saccharum officinarum L."
    assert profile["marathi_name"] == "ऊस"
    assert len(profile["recommended_varieties"]) >= 3
    assert any("Co 86032" in v for v in profile["recommended_varieties"])

    # Soil Requirements
    soil = profile["soil"]
    assert soil is not None
    assert "Clay" in soil["preferred_textures"] or "Deep Black Vertisol" in soil["preferred_textures"]
    assert 6.0 <= soil["ph_optimum_min"] <= soil["ph_optimum_max"] <= 8.5
    assert soil["min_soil_depth_cm"] >= 60.0
    assert "waterlogging" in soil["drainage_requirement"].lower()

    # Climate Requirements
    clim = profile["climate"]
    assert clim is not None
    assert 20.0 <= clim["temp_optimum_min_c"] < clim["temp_optimum_max_c"] <= 38.0
    assert clim["frost_sensitivity"] is not None

    # Seasonal Requirements
    seasons = profile["seasons"]
    assert len(seasons) >= 2
    season_names = [s["season_name"] for s in seasons]
    assert "Adsali" in season_names
    assert "Suru" in season_names or "Pre-seasonal" in season_names

    # Water Requirements
    water = profile["water"]
    assert water is not None
    assert water["annual_water_requirement_mm_min"] >= 1500.0
    assert water["rainfed_suitable"] is False
    assert len(water["critical_growth_stages"]) >= 2

    # Regional Suitability across Pilot Talukas
    regional = profile["regional_suitability"]
    assert len(regional) >= 4
    talukas = {r["taluka"]: r for r in regional}
    assert "Baramati" in talukas
    assert "Maval" in talukas
    assert "Indapur" in talukas
    assert "Mulshi" in talukas

    assert talukas["Baramati"]["suitability_status"] == "Highly Suitable"
    assert talukas["Mulshi"]["suitability_status"] in ["Unsuitable / High Disease Risk", "Marginal / High Input"]

    # Source Attribution
    sources = profile["sources"]
    assert len(sources) >= 1
    source_orgs = [s["organization"] for s in sources]
    assert any("MPKV" in o or "Mahatma Phule" in o or "ICAR" in o for o in source_orgs)


def test_all_10_crops_present_and_structured():
    """
    Ensure all 10 priority crops have valid profiles without missing mandatory modules.
    """
    for crop_id in EXPECTED_CROP_IDS:
        res = client.get(f"/api/v1/crops/{crop_id}")
        assert res.status_code == 200, f"Crop {crop_id} failed with {res.status_code}"
        data = res.json()
        assert data["soil"] is not None, f"Missing soil for {crop_id}"
        assert data["climate"] is not None, f"Missing climate for {crop_id}"
        assert len(data["seasons"]) > 0, f"Missing seasons for {crop_id}"
        assert data["water"] is not None, f"Missing water for {crop_id}"
        assert len(data["regional_suitability"]) >= 4, f"Missing pilot talukas for {crop_id}"


def test_crop_requirements_and_sources_endpoints():
    """
    Verify GET /api/v1/crops/{crop_id}/requirements and /sources endpoints.
    """
    # 1. Requirements Endpoint
    req_res = client.get("/api/v1/crops/pomegranate/requirements")
    assert req_res.status_code == 200
    req_data = req_res.json()
    assert req_data["crop_id"] == "pomegranate"
    assert req_data["soil"]["salinity_sensitivity"] is not None
    assert req_data["water"]["irrigation_dependency"] is not None

    # 2. Sources Endpoint
    src_res = client.get("/api/v1/crops/pomegranate/sources")
    assert src_res.status_code == 200
    src_data = src_res.json()
    assert len(src_data) >= 1
    assert any("NRCP" in s["organization"] or "Solapur" in s["organization"] or "MPKV" in s["organization"] for s in src_data)

    # 3. 404 on nonexistent crop
    non_res = client.get("/api/v1/crops/nonexistent_crop_99")
    assert non_res.status_code == 404


def test_maharashtra_seasons_calendar_endpoint():
    """
    Verify GET /api/v1/agriculture/seasons returns Kharif, Rabi, and Zaid definitions.
    """
    res = client.get("/api/v1/agriculture/seasons")
    assert res.status_code == 200
    seasons = res.json()
    assert len(seasons) == 3
    s_names = [s["season_name"] for s in seasons]
    assert "Kharif" in s_names
    assert "Rabi" in s_names
    assert any("Zaid" in name or "Summer" in name for name in s_names)


def test_strict_phase4_scientific_guardrails():
    """
    Verify that NO ML recommendations or yield predictions are exposed in Phase 4.
    """
    res = client.get("/api/v1/crops/wheat")
    data = res.json()
    assert "recommendation_score" not in data
    assert "predicted_yield_tons_ha" not in data
    assert "fertilizer_prescription" not in data
