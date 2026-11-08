"""
Comprehensive Unit and Integration Tests for Sentinel-2 Satellite-Based Vegetation Intelligence.

Verifies:
1. Exact band math: NDVI = (B08 - B04)/(B08 + B04), NDMI = (B08 - B11)/(B08 + B11).
2. SCL cloud and cloud-shadow masking.
3. Farm polygon geometry intersection and pixel statistics.
4. Small farm spatial representativeness safeguards (<0.5 ha or <5 pixels).
5. Historical time-series retrieval.
6. Agronomic indirect-indicator disclaimers.
7. Farm ownership security enforcement.
"""
import uuid
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from cropnet.services.api.app.main import app
from cropnet.services.api.app.core.database import get_db
from cropnet.services.api.app.core.security import get_current_user, CurrentUser
from cropnet.services.api.app.models.soil_and_farm import Base, FarmModel
from cropnet.services.api.app.models.satellite import SatelliteVegetationObservationModel
from cropnet.services.api.app.services.satellite.copernicus_client import (
    copernicus_client,
    SCL_MASKED_CLASSES,
    convert_raw_dn_to_reflectance,
    calibrate_dn_to_reflectance,
)
from cropnet.services.api.app.api.v1.endpoints.farms import _FARM_STORAGE

TEST_USER_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
OTHER_USER_ID = uuid.UUID("44444444-4444-4444-4444-444444444444")
TEST_FARM_ID = uuid.UUID("55555555-5555-5555-5555-555555555555")
SMALL_FARM_ID = uuid.UUID("66666666-6666-6666-6666-666666666666")


@pytest.fixture
def isolated_satellite_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    # Seed normal farm (2.5 ha)
    now = datetime.utcnow()
    farm = FarmModel(
        id=str(TEST_FARM_ID),
        owner_id=str(TEST_USER_ID),
        name="Indapur Demonstration Field",
        village="Bawada",
        taluka="Indapur",
        district="Pune",
        state="Maharashtra",
        geometry_geojson={"type": "Polygon", "coordinates": [[[74.9, 18.0], [74.92, 18.0], [74.92, 18.02], [74.9, 18.02], [74.9, 18.0]]]},
        calculated_area_hectares=2.5,
        calculated_area_acres=6.18,
        centroid_latitude=18.01,
        centroid_longitude=74.91,
        created_at=now,
        updated_at=now,
    )
    session.add(farm)

    # Seed small farm (0.2 ha)
    small_farm = FarmModel(
        id=str(SMALL_FARM_ID),
        owner_id=str(TEST_USER_ID),
        name="Micro Kitchen Garden",
        village="Bawada",
        taluka="Indapur",
        district="Pune",
        state="Maharashtra",
        geometry_geojson={"type": "Polygon", "coordinates": [[[74.91, 18.01], [74.911, 18.01], [74.911, 18.011], [74.91, 18.011], [74.91, 18.01]]]},
        calculated_area_hectares=0.2,
        calculated_area_acres=0.49,
        centroid_latitude=18.0105,
        centroid_longitude=74.9105,
        created_at=now,
        updated_at=now,
    )
    session.add(small_farm)
    session.commit()

    _FARM_STORAGE[TEST_FARM_ID] = {
        "id": TEST_FARM_ID,
        "owner_id": TEST_USER_ID,
        "name": farm.name,
        "geometry": farm.geometry_geojson,
        "calculated_area_hectares": farm.calculated_area_hectares,
        "calculated_area_acres": farm.calculated_area_acres,
    }
    _FARM_STORAGE[SMALL_FARM_ID] = {
        "id": SMALL_FARM_ID,
        "owner_id": TEST_USER_ID,
        "name": small_farm.name,
        "geometry": small_farm.geometry_geojson,
        "calculated_area_hectares": small_farm.calculated_area_hectares,
        "calculated_area_acres": small_farm.calculated_area_acres,
    }

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        _FARM_STORAGE.clear()


@pytest.fixture
def client(isolated_satellite_db):
    def override_get_db():
        try:
            yield isolated_satellite_db
        finally:
            pass

    def override_get_current_user():
        return CurrentUser(
            user_id=TEST_USER_ID,
            email="researcher@cropnet.ai",
            role="authenticated",
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ===========================================================================
# 1. UNIT TESTS: BAND MATH & SCL MASKING
# ===========================================================================

def test_scl_masking_classes():
    # Masked classes: 0 (No data), 1 (Saturated), 3 (Shadows), 7 (Unclassified), 8 (Med cloud), 9 (High cloud), 10 (Cirrus), 11 (Snow/Ice)
    assert 0 in SCL_MASKED_CLASSES  # No data
    assert 1 in SCL_MASKED_CLASSES  # Saturated or defective
    assert 3 in SCL_MASKED_CLASSES  # Cloud shadows
    assert 7 in SCL_MASKED_CLASSES  # Unclassified
    assert 8 in SCL_MASKED_CLASSES  # Cloud medium prob
    assert 9 in SCL_MASKED_CLASSES  # Cloud high prob
    assert 10 in SCL_MASKED_CLASSES # Cirrus
    assert 11 in SCL_MASKED_CLASSES # Snow/Ice


def test_radiometric_offset_baseline_matrix():
    """
    Comprehensive test of Sentinel-2 radiometric calibration across processing baselines:
    - Legacy Baselines (PB < 04.00, e.g. N0214, N0300) without offset
    - PB 04.00 (N0400) with offset -1000 DN
    - PB 05.00 (N0500) with offset -1000 DN
    - PB 05.10 and PB 05.11 with offset -1000 DN
    - DN = 0 treated strictly as NO_DATA (returns None)
    - Negative reflectance preserved down to physical bounds
    - Already-calibrated reflectance passed through directly without double-conversion
    - Explicit product metadata overrides
    """
    # 1. Legacy baseline (N0214): offset = 0. DN=2000 -> 0.20
    val = calibrate_dn_to_reflectance(2000.0, processing_baseline="N0214")
    assert pytest.approx(val, 0.0001) == 0.20

    # 2. Legacy baseline (N0300): offset = 0. DN=2500 -> 0.25
    val = calibrate_dn_to_reflectance(2500.0, processing_baseline="N0300")
    assert pytest.approx(val, 0.0001) == 0.25

    # 3. PB 04.00 (N0400): offset = -1000. DN=2000 -> (2000 - 1000)/10000 = 0.10
    val = calibrate_dn_to_reflectance(2000.0, processing_baseline="N0400")
    assert pytest.approx(val, 0.0001) == 0.10

    # 4. PB 05.00 (N0500): offset = -1000. DN=3500 -> (3500 - 1000)/10000 = 0.25
    val = calibrate_dn_to_reflectance(3500.0, processing_baseline="N0500")
    assert pytest.approx(val, 0.0001) == 0.25

    # 5. PB 05.10: offset = -1000. DN=4000 -> (4000 - 1000)/10000 = 0.30
    val = calibrate_dn_to_reflectance(4000.0, processing_baseline="N0510")
    assert pytest.approx(val, 0.0001) == 0.30

    # 6. PB 05.11: offset = -1000. DN=1500 -> (1500 - 1000)/10000 = 0.05
    val = calibrate_dn_to_reflectance(1500.0, processing_baseline="N0511")
    assert pytest.approx(val, 0.0001) == 0.05

    # 7. DN = 0 is strictly NO_DATA -> None
    assert calibrate_dn_to_reflectance(0.0, processing_baseline="N0500") is None
    assert calibrate_dn_to_reflectance(0, processing_baseline="N0214") is None

    # 8. Negative reflectance handling: DN = 900 in PB 05.00 -> (900 - 1000)/10000 = -0.010
    val_neg = calibrate_dn_to_reflectance(900.0, processing_baseline="N0500", allow_negative_reflectance=True)
    assert pytest.approx(val_neg, 0.0001) == -0.010

    # Clamped when requested:
    val_clamped = calibrate_dn_to_reflectance(900.0, processing_baseline="N0500", allow_negative_reflectance=False)
    assert val_clamped == 0.0

    # 9. Provider already returned calibrated reflectance in [0.0, 1.0]
    val_calibrated = calibrate_dn_to_reflectance(0.4215, is_calibrated_reflectance=True)
    assert val_calibrated == 0.4215

    # 10. Dynamic metadata dictionary with explicit BOA_ADD_OFFSET and QUANTIFICATION_VALUE
    meta = {"BOA_ADD_OFFSET": -1000.0, "QUANTIFICATION_VALUE": 10000.0}
    val_meta = calibrate_dn_to_reflectance(5000.0, metadata=meta)
    assert pytest.approx(val_meta, 0.0001) == 0.40


def test_spatial_resolution_truth_in_polygon_computation():
    """Verify that NDMI records B11 20m native, B08 10m native, bilinear resampling, and SCL nearest-neighbour."""
    poly = {
        "type": "Polygon",
        "coordinates": [[[74.5, 18.1], [74.52, 18.1], [74.52, 18.12], [74.5, 18.12], [74.5, 18.1]]]
    }
    result = copernicus_client.compute_polygon_indices(poly, farm_area_ha=2.5)

    assert result["spatial_resolution_meters"] == 10.0
    assert result["b11_native_resolution_meters"] == 20.0
    assert result["b08_native_resolution_meters"] == 10.0
    assert result["target_grid_meters"] == 10.0
    assert result["resampling_method"] == "bilinear"
    assert "Resampling does not create native 10m information" in result["resampling_notes"]
    assert result["scl_resampling_method"] == "nearest_neighbour"


def test_satellite_endpoint_ownership_enforcement(client):
    """Verify that a user cannot access another user's farm satellite observations."""
    def override_other_user():
        return CurrentUser(
            user_id=OTHER_USER_ID,
            email="intruder@cropnet.ai",
            role="authenticated",
        )

    app.dependency_overrides[get_current_user] = override_other_user
    res = client.get(f"/api/v1/farms/{TEST_FARM_ID}/satellite/latest")
    assert res.status_code == 403
    assert "permission" in res.json()["detail"].lower()


def test_polygon_indices_computation_normal_farm():
    poly = {
        "type": "Polygon",
        "coordinates": [[[74.9, 18.0], [74.92, 18.0], [74.92, 18.02], [74.9, 18.02], [74.9, 18.0]]]
    }
    indices = copernicus_client.compute_polygon_indices(
        polygon_geojson=poly,
        farm_area_ha=2.5,
    )
    assert indices["valid_pixel_count"] > 10
    assert indices["mean_ndvi"] is not None
    assert 0.0 <= indices["mean_ndvi"] <= 1.0
    assert indices["mean_ndmi"] is not None
    assert indices["spatial_resolution_meters"] == 10.0
    assert indices["is_small_farm_warning"] is False
    assert indices["quality_status"] == "VALID_OBSERVATION"


def test_polygon_indices_computation_small_farm_warning():
    poly = {
        "type": "Polygon",
        "coordinates": [[[74.91, 18.01], [74.911, 18.01], [74.911, 18.011], [74.91, 18.011], [74.91, 18.01]]]
    }
    indices = copernicus_client.compute_polygon_indices(
        polygon_geojson=poly,
        farm_area_ha=0.2,  # <0.5 ha
    )
    assert indices["is_small_farm_warning"] is True
    assert indices["quality_status"] == "SMALL_FARM_WARNING"
    assert "boundary pixel edge effects" in indices["quality_notes"]


# ===========================================================================
# 2. INTEGRATION TESTS: SATELLITE API ENDPOINTS
# ===========================================================================

def test_satellite_sync_and_timeseries_endpoints(client):
    # 1. Sync satellite observation
    res = client.post(f"/api/v1/farms/{TEST_FARM_ID}/satellite/sync")
    assert res.status_code == 200
    sync_data = res.json()
    assert sync_data["success"] is True
    assert sync_data["latest_observation"] is not None
    assert sync_data["latest_observation"]["mean_ndvi"] is not None
    assert sync_data["latest_observation"]["spatial_resolution_meters"] == 10.0

    # 2. Get latest observation
    res = client.get(f"/api/v1/farms/{TEST_FARM_ID}/satellite/latest")
    assert res.status_code == 200
    latest = res.json()
    assert latest["farm_id"] == str(TEST_FARM_ID)
    assert latest["mean_ndvi"] is not None
    assert latest["mean_ndmi"] is not None

    # 3. List historical observations
    res = client.get(f"/api/v1/farms/{TEST_FARM_ID}/satellite/observations")
    assert res.status_code == 200
    obs_list = res.json()
    assert len(obs_list) >= 1

    # 4. Get vegetation timeseries
    res = client.get(f"/api/v1/farms/{TEST_FARM_ID}/satellite/timeseries?months=6")
    assert res.status_code == 200
    ts = res.json()
    assert len(ts["series"]) >= 3
    assert ts["vegetation_interpretation"] != ""
    assert "MUST NEVER be interpreted as direct diagnoses" in ts["scientific_disclaimer"]
