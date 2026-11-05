import uuid
import pytest
from fastapi.testclient import TestClient
from shapely.geometry import Polygon

from cropnet.services.api.app.main import app
from cropnet.services.api.app.services.soil_providers.soilgrids import SoilGridsProvider
from cropnet.services.api.app.services.soil_providers.openlandmap import OpenLandMapProvider
from cropnet.services.api.app.services.soil_providers.natmo import NATMOProvider
from cropnet.services.api.app.services.soil_providers.bhoomi import BhoomiProvider
from cropnet.services.api.app.services.spatial_extractor import calculate_polygon_area, SpatialSoilService
from cropnet.services.api.app.schemas.soil import VerificationStatus, ParameterAvailability

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Maval" in data["active_pilot_regions"]
    assert "Baramati" in data["active_pilot_regions"]
    assert data["soil_data_providers"]["isric_soilgrids"]["operational"] is True
    assert data["soil_data_providers"]["icar_nbsslup_bhoomi"]["operational"] is False


def test_provider_capabilities_reporting():
    response = client.get("/api/v1/soil/providers")
    assert response.status_code == 200
    providers = response.json()
    assert len(providers) >= 5

    provider_names = [p["provider_name"] for p in providers]
    assert any("SoilGrids" in name for name in provider_names)
    assert any("OpenLandMap" in name for name in provider_names)
    assert any("NATMO" in name for name in provider_names)
    assert any("BHOOMI" in name for name in provider_names)

    # Check SoilGrids capability metadata
    sg = next(p for p in providers if "SoilGrids" in p["provider_name"])
    assert sg["spatial_resolution_or_scale"] == "250m"
    assert sg["licensing"].startswith("Creative Commons")
    assert "0-5cm" in sg["supported_depth_intervals"]
    assert sg["provides_uncertainty"] is True

    # Check NATMO capability metadata
    natmo = next(p for p in providers if "NATMO" in p["provider_name"])
    assert natmo["is_operational"] is False

    # Check BHOOMI capability metadata
    bhoomi = next(p for p in providers if "BHOOMI" in p["provider_name"])
    assert bhoomi["requires_credentials"] is True


def test_farm_creation_and_geodesic_area_calculation():
    user1_id = str(uuid.uuid4())
    # Baramati farm polygon (approx 100m x 100m = ~1 hectare)
    farm_payload = {
        "name": "Baramati Pilot Plot 1",
        "taluka": "Baramati",
        "district": "Pune",
        "state": "Maharashtra",
        "village": "Malegaon",
        "irrigation_type": "irrigated",
        "water_source": "canal",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [74.530, 18.180],
                [74.531, 18.180],
                [74.531, 18.181],
                [74.530, 18.181],
                [74.530, 18.180]
            ]]
        }
    }

    response = client.post(
        "/api/v1/farms",
        json=farm_payload,
        headers={"X-Dev-User-Id": user1_id}
    )
    assert response.status_code == 201
    farm_data = response.json()
    assert farm_data["name"] == "Baramati Pilot Plot 1"
    assert farm_data["owner_id"] == user1_id
    assert farm_data["calculated_area_hectares"] > 0
    assert farm_data["calculated_area_acres"] > 0
    # ~1.1 to ~1.3 hectares for this 0.001 deg box in Maharashtra
    assert 1.0 <= farm_data["calculated_area_hectares"] <= 1.5

    farm_id = farm_data["id"]

    # Test user isolation: user2 cannot read user1's farm
    user2_id = str(uuid.uuid4())
    unauthorized_response = client.get(
        f"/api/v1/farms/{farm_id}",
        headers={"X-Dev-User-Id": user2_id}
    )
    assert unauthorized_response.status_code == 403

    # Authorized user can read the farm
    authorized_response = client.get(
        f"/api/v1/farms/{farm_id}",
        headers={"X-Dev-User-Id": user1_id}
    )
    assert authorized_response.status_code == 200


def test_soilgrids_polygon_extraction_and_provenance():
    # Test Maval pilot farm polygon
    maval_poly = Polygon([
        (73.675, 18.755),
        (73.685, 18.755),
        (73.685, 18.765),
        (73.675, 18.765),
        (73.675, 18.755)
    ])

    service = SpatialSoilService()
    profile = service.generate_farm_soil_profile(
        farm_id="test-maval-farm",
        polygon=maval_poly,
        taluka="Maval"
    )

    assert profile.is_map_derived is True
    assert "NOT a physical laboratory soil test" in profile.disclaimer

    # Check pH
    assert profile.ph is not None
    assert profile.ph.value is not None
    assert 5.5 <= profile.ph.value <= 8.5
    assert profile.ph.unit == "pH"
    assert profile.ph.source == "ISRIC SoilGrids"
    assert profile.ph.dataset_version == "2.0.0"
    assert profile.ph.depth_interval == "0-5cm"

    # Check Total Nitrogen (verify it carries scientific warning)
    assert profile.total_nitrogen is not None
    assert profile.total_nitrogen.value is not None
    assert "NOT available mineral nitrogen" in profile.total_nitrogen.scientific_note

    # Check that available NPK are strictly NOT fabricated
    assert profile.available_nitrogen.value is None
    assert profile.available_nitrogen.verification_status == VerificationStatus.NOT_AVAILABLE
    assert profile.available_nitrogen.availability_status == ParameterAvailability.NOT_AVAILABLE

    assert profile.available_phosphorus.value is None
    assert profile.available_phosphorus.verification_status == VerificationStatus.NOT_AVAILABLE

    assert profile.available_potassium.value is None
    assert profile.available_potassium.verification_status == VerificationStatus.NOT_AVAILABLE


def test_pilot_coverage_matrix_endpoint():
    response = client.get("/api/v1/soil/pilot-coverage")
    assert response.status_code == 200
    data = response.json()
    talukas = [r["taluka"] for r in data["pilot_regions"]]
    assert "Maval" in talukas
    assert "Mulshi" in talukas
    assert "Baramati" in talukas
    assert "Indapur" in talukas
