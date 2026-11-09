import uuid
import pytest
from fastapi.testclient import TestClient
from shapely.geometry import Polygon

from cropnet.services.api.app.main import app
from cropnet.services.api.app.services.spatial_extractor import (
    derive_usda_texture_class,
    SpatialSoilService
)

client = TestClient(app)


def test_usda_texture_classification_logic():
    """
    Verify USDA Soil Texture Classification function across key soil types.
    """
    # 1. Baramati Vertisol (Smectite / Montmorillonitic heavy clay)
    # Clay: 42%, Sand: 28%, Silt: 30% -> Clay
    assert derive_usda_texture_class(sand=28.0, silt=30.0, clay=42.0) == "Clay"

    # 2. Maval Red Lateritic Gravelly Clay Loam
    # Clay: 35%, Sand: 35%, Silt: 30% -> Clay Loam
    assert derive_usda_texture_class(sand=35.0, silt=30.0, clay=35.0) == "Clay Loam"

    # 3. Alluvial Loam
    # Clay: 18%, Sand: 42%, Silt: 40% -> Loam
    assert derive_usda_texture_class(sand=42.0, silt=40.0, clay=18.0) == "Loam"

    # 4. Sandy Soil
    # Clay: 5%, Sand: 90%, Silt: 5% -> Sand
    assert derive_usda_texture_class(sand=90.0, silt=5.0, clay=5.0) == "Sand"

    # 5. Silt Loam
    # Clay: 15%, Sand: 20%, Silt: 65% -> Silt Loam
    assert derive_usda_texture_class(sand=20.0, silt=65.0, clay=15.0) == "Silt Loam"

    # 6. Missing parameters return None safely
    assert derive_usda_texture_class(sand=None, silt=30.0, clay=40.0) is None
    assert derive_usda_texture_class(sand=30.0, silt=None, clay=40.0) is None
    assert derive_usda_texture_class(sand=30.0, silt=30.0, clay=None) is None


def test_farm_soil_analysis_lifecycle_and_caching():
    """
    End-to-end test for Phase 2:
    1. Register a farm with real polygon in Baramati.
    2. Check GET /soil returns 404 before analysis.
    3. Run POST /soil/analyse (triggers SpatialSoilService & SoilGrids WCS).
    4. Verify derived USDA texture class, spatial representativeness, and scientific guardrails.
    5. Verify strict NPK restriction (Available N, P, K must be null).
    6. Verify caching (subsequent POST without force_refresh returns cached profile).
    7. Verify GET /soil and GET /soil/history.
    8. Verify multi-tenant security isolation (User 2 blocked with 403).
    """
    user1_id = str(uuid.uuid4())
    user2_id = str(uuid.uuid4())

    # 1. Register Farm in Baramati (agricultural parcel: ~1.2 ha < 6.25 ha)
    farm_payload = {
        "name": "Baramati Pilot Grape Vineyard",
        "taluka": "Baramati",
        "district": "Pune",
        "state": "Maharashtra",
        "village": "Malegaon Khurd",
        "irrigation_type": "irrigated",
        "water_source": "well",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [74.528, 18.178],
                [74.532, 18.178],
                [74.532, 18.182],
                [74.528, 18.182],
                [74.528, 18.178]
            ]]
        }
    }

    create_res = client.post(
        "/api/v1/farms",
        json=farm_payload,
        headers={"X-Dev-User-Id": user1_id}
    )
    assert create_res.status_code == 201
    farm = create_res.json()
    farm_id = farm["id"]
    area_ha = farm["calculated_area_hectares"]

    # 2. GET /soil before analysis should return 404
    get_before = client.get(
        f"/api/v1/farms/{farm_id}/soil",
        headers={"X-Dev-User-Id": user1_id}
    )
    assert get_before.status_code == 404

    # 3. Trigger Soil Analysis for Farm
    analyse_res = client.post(
        f"/api/v1/farms/{farm_id}/soil/analyse",
        json={"force_refresh": False, "depth": "0-5cm"},
        headers={"X-Dev-User-Id": user1_id}
    )
    assert analyse_res.status_code == 200
    profile = analyse_res.json()
    profile_id = profile["profile_id"]

    # 4. Verify Scientific Results & Metadata
    assert profile["farm_id"] == farm_id
    assert profile["source_dataset"] == "ISRIC SoilGrids 2.0"
    assert profile["spatial_resolution"] == "250m"
    assert profile["depth_interval"] == "0-5cm"
    assert profile["is_map_derived"] is True
    assert "estimates derived from geospatial soil datasets" in profile["disclaimer"].lower()

    # Verify spatial representativeness warning for small parcel (< 6.25 ha)
    if area_ha < 6.25:
        assert profile["spatial_representativeness_warning"] is not None
        assert "smaller than the 250m raster" in profile["spatial_representativeness_warning"]

    # Verify Physical Properties & Texture Class
    assert profile["ph"] is not None
    assert profile["organic_carbon"] is not None
    assert profile["sand_percent"] is not None
    assert profile["silt_percent"] is not None
    assert profile["clay_percent"] is not None
    assert profile["soil_texture_class"] in [
        "Clay", "Clay Loam", "Silty Clay", "Sandy Clay", "Loam", "Sandy Clay Loam"
    ]

    # Verify Total Nitrogen has explicit non-available warning
    assert profile["total_nitrogen"] is not None
    assert "NOT available mineral nitrogen" in profile["total_nitrogen"]["scientific_note"]

    # 5. SCIENTIFIC RESTRICTIONS: Available N, P, K MUST BE NULL
    assert profile["available_nitrogen"]["value"] is None
    assert profile["available_nitrogen"]["verification_status"] == "not_available"
    assert profile["available_phosphorus"]["value"] is None
    assert profile["available_phosphorus"]["verification_status"] == "not_available"
    assert profile["available_potassium"]["value"] is None
    assert profile["available_potassium"]["verification_status"] == "not_available"

    # 6. Verify Caching: Second call without force_refresh returns the exact same profile_id instantly
    cache_res = client.post(
        f"/api/v1/farms/{farm_id}/soil/analyse",
        json={"force_refresh": False, "depth": "0-5cm"},
        headers={"X-Dev-User-Id": user1_id}
    )
    assert cache_res.status_code == 200
    cached_profile = cache_res.json()
    assert cached_profile["profile_id"] == profile_id

    # 7. GET /api/v1/farms/{farm_id}/soil retrieves latest profile
    get_res = client.get(
        f"/api/v1/farms/{farm_id}/soil",
        headers={"X-Dev-User-Id": user1_id}
    )
    assert get_res.status_code == 200
    retrieved_profile = get_res.json()
    assert retrieved_profile["profile_id"] == profile_id
    assert retrieved_profile["soil_texture_class"] == profile["soil_texture_class"]

    # 8. GET /api/v1/farms/{farm_id}/soil/history returns list
    hist_res = client.get(
        f"/api/v1/farms/{farm_id}/soil/history",
        headers={"X-Dev-User-Id": user1_id}
    )
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert len(history) >= 1
    assert any(h["profile_id"] == profile_id for h in history)

    # 9. Multi-Tenant Authorization Security: User 2 cannot access or analyse User 1's farm
    u2_analyse = client.post(
        f"/api/v1/farms/{farm_id}/soil/analyse",
        json={"force_refresh": False},
        headers={"X-Dev-User-Id": user2_id}
    )
    assert u2_analyse.status_code == 403

    u2_get = client.get(
        f"/api/v1/farms/{farm_id}/soil",
        headers={"X-Dev-User-Id": user2_id}
    )
    assert u2_get.status_code == 403

    u2_hist = client.get(
        f"/api/v1/farms/{farm_id}/soil/history",
        headers={"X-Dev-User-Id": user2_id}
    )
    assert u2_hist.status_code == 403


def test_soil_layers_catalogue_endpoint():
    """
    Verify GET /api/v1/soil/layers returns supported layer metadata.
    """
    res = client.get("/api/v1/soil/layers")
    assert res.status_code == 200
    layers = res.json()
    assert len(layers) >= 7

    layer_keys = [l["parameter_key"] for l in layers]
    assert "ph" in layer_keys
    assert "soc" in layer_keys
    assert "sand_percent" in layer_keys
    assert "clay_percent" in layer_keys
    assert "soil_texture_class" in layer_keys
    assert "total_nitrogen" in layer_keys
    assert "available_nitrogen" in layer_keys

    # Check that derived texture class is marked
    texture_layer = next(l for l in layers if l["parameter_key"] == "soil_texture_class")
    assert texture_layer["is_derived"] is True

    # Check that available nitrogen reflects lab requirement
    avail_n_layer = next(l for l in layers if l["parameter_key"] == "available_nitrogen")
    assert "Physical Test Required" in avail_n_layer["source"]
