import pytest
from fastapi.testclient import TestClient
from backend.app.schemas.soil import (
    SoilVerificationStatus,
    VerificationStatus,
    ParameterAvailability,
    CropNetSoilCardResponse,
)
from backend.app.services.cropnet_spatial_service import derive_usda_texture_class, SpatialSoilService
from backend.app.services.soil_providers.soilgrids import SoilGridsProvider

def test_soilgrids_provider_capabilities():
    provider = SoilGridsProvider()
    caps = provider.get_capabilities()
    assert caps.provider_name == "ISRIC SoilGrids"
    assert caps.spatial_resolution_or_scale == "250m"
    assert "ph" in caps.available_properties
    assert "soc" in caps.available_properties
    assert "clay_percent" in caps.available_properties
    assert "total_nitrogen" in caps.available_properties
    assert "Creative Commons" in caps.licensing

def test_derive_usda_texture_class():
    # Vertisol: high clay (>40%)
    assert derive_usda_texture_class(sand=20.0, silt=25.0, clay=55.0) == "Clay"
    # Sandy soil
    assert derive_usda_texture_class(sand=90.0, silt=5.0, clay=5.0) == "Sand"
    # Loam
    assert derive_usda_texture_class(sand=40.0, silt=40.0, clay=20.0) == "Loam"
    # None handling
    assert derive_usda_texture_class(None, None, None) is None

def test_spatial_soil_service_guarantees_unverified_npk_as_none():
    service = SpatialSoilService()
    profile = service.generate_farm_soil_profile_for_coords(
        farm_id="farm_demo_pune_01",
        lat=18.5204,
        lon=73.8567,
        taluka="Baramati",
        area_acres=3.5
    )
    assert profile.is_map_derived is True
    assert "not laboratory soil test results" in profile.disclaimer.lower()
    # Available NPK must remain strictly None / unmeasured
    assert profile.available_nitrogen.value is None
    assert profile.available_nitrogen.availability_status == ParameterAvailability.NOT_AVAILABLE
    assert profile.available_phosphorus.value is None
    assert profile.available_potassium.value is None
    # Primary soil properties have values and units
    assert profile.ph is not None
    assert profile.ph.unit in ["pH", "pH_scale"]
    assert profile.soil_texture_class is not None

def test_soil_endpoints_owner_isolation(client: TestClient):
    # Register a new farm with owner 'farmer_alice'
    reg_payload = {
        "farmer_name": "Alice Patil",
        "phone_number": "9811122233",
        "taluka": "Baramati",
        "district": "Pune",
        "village": "Malegaon",
        "farm_name": "Alice Organic Farm",
        "total_area_acres": 4.0,
        "latitude": 18.15,
        "longitude": 74.58,
        "crop_code": "sugarcane",
        "season": "kharif",
        "sowing_date": "2024-06-01"
    }
    res = client.post("/v1/farms/guided-registration", json=reg_payload)
    assert res.status_code == 200
    farm_id = res.json()["farm_id"]
    farmer_id = res.json()["farmer_id"]

    # Owner can access soil profile
    res_owner = client.get(
        f"/v1/soil/farms/{farm_id}/profile",
        headers={"X-Farmer-Id": farmer_id}
    )
    assert res_owner.status_code == 200
    profile_data = res_owner.json()
    assert profile_data["farm_id"] == farm_id
    assert profile_data["is_map_derived"] is True

    # Unauthorized third-party is blocked with 403 Forbidden
    res_imposter = client.get(
        f"/v1/soil/farms/{farm_id}/profile",
        headers={"X-Farmer-Id": "farmer_unauthorized_intruder"}
    )
    assert res_imposter.status_code == 403
    assert "permission" in res_imposter.json()["detail"].lower()

def test_get_soil_card_for_ui(client: TestClient):
    res = client.get("/v1/soil/farms/farm_demo_pune_01/card")
    assert res.status_code == 200
    data = res.json()
    assert data["farm_id"] == "farm_demo_pune_01"
    assert "texture_summary" in data
    assert "provenance_badge" in data
    assert data["provenance_badge"] == "Location-Based Estimate (SoilGrids 250m)"
    assert data["is_lab_measured"] is False
    assert "disclaimer" in data
    assert "indicators" in data
    assert len(data["indicators"]) >= 4
    # Available NPK notice
    assert "unmeasured_nutrients_notice" in data
    assert "physical lab test required" in data["unmeasured_nutrients_notice"].lower()

def test_soil_providers_and_layers_catalogue(client: TestClient):
    # Providers endpoint
    resp = client.get("/v1/soil/providers")
    assert resp.status_code == 200
    providers = resp.json()
    assert len(providers) >= 2
    names = [p["provider_name"] for p in providers]
    assert any("SoilGrids" in n for n in names)

    # Layers endpoint
    resp_layers = client.get("/v1/soil/layers")
    assert resp_layers.status_code == 200
    layers = resp_layers.json()
    keys = [l["parameter_key"] for l in layers]
    assert "ph" in keys
    assert "clay_percent" in keys
    assert "available_nitrogen" in keys
