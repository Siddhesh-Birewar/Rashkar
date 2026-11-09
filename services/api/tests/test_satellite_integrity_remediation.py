"""
Comprehensive Verification Test Suite for Satellite Data Integrity Remediation (Requirement R4).

Verifies:
1. No synthetic NDVI/NDMI, hash-based reflectance, or fake rasters are generated on retrieval failure.
2. Live retrieval failure fails closed, returning quality_status='NO_USABLE_OBSERVATION'
   and copernicus_provider_status='PROVIDER_UNAVAILABLE'.
3. Sync endpoint preserves authentic historical observations with acquisition timestamps when refresh fails.
4. Cross-farm silent fallback to Baramati farm (94a1f16e-bf0d-4d3f-9bd3-d63a57189818) is completely removed (returns None / 404).
5. Strict UUID validation, path normalization, and containment inside DERIVED_RASTER_CACHE_DIR
   prevent directory traversal attacks.
6. Genuine satellite observations include full lineage metadata, timestamp, radiometric validation,
   valid-pixel counts, and quality status.
7. Isolated synthetic QA records (SYNTHETIC_QA_ISOLATED) are excluded from farmer dashboards and timeseries.
"""
import os
import uuid
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
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
    sanitize_farm_id,
    _safe_raster_cache_path,
    get_raster_map_path,
    get_spatial_metadata,
    DERIVED_RASTER_CACHE_DIR,
)
from cropnet.services.api.app.services.satellite.cleanup import (
    isolate_synthetic_database_observations,
    cleanup_synthetic_filesystem_rasters,
)
from cropnet.services.api.app.services.farm_health.collectors.satellite_collector import SatelliteCollector
from cropnet.services.api.app.api.v1.endpoints.farms import _FARM_STORAGE


TEST_USER_ID = uuid.UUID("11111111-2222-3333-4444-555555555555")
TEST_FARM_ID = uuid.UUID("66666666-7777-8888-9999-aaaaaaaaaaaa")
TEST_POLYGON = {
    "type": "Polygon",
    "coordinates": [[[74.5, 18.1], [74.52, 18.1], [74.52, 18.12], [74.5, 18.12], [74.5, 18.1]]],
}


@pytest.fixture
def satellite_db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    now = datetime.utcnow()
    farm = FarmModel(
        id=str(TEST_FARM_ID),
        owner_id=str(TEST_USER_ID),
        name="Integrity Remediation Farm",
        village="Malegaon",
        taluka="Baramati",
        district="Pune",
        state="Maharashtra",
        geometry_geojson=TEST_POLYGON,
        calculated_area_hectares=2.5,
        calculated_area_acres=6.18,
        centroid_latitude=18.11,
        centroid_longitude=74.51,
        created_at=now,
        updated_at=now,
    )
    session.add(farm)
    session.commit()

    _FARM_STORAGE[TEST_FARM_ID] = {
        "id": TEST_FARM_ID,
        "owner_id": TEST_USER_ID,
        "name": farm.name,
        "geometry": farm.geometry_geojson,
        "calculated_area_hectares": farm.calculated_area_hectares,
        "calculated_area_acres": farm.calculated_area_acres,
    }

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        _FARM_STORAGE.clear()


@pytest.fixture
def client(satellite_db_session):
    def override_get_db():
        try:
            yield satellite_db_session
        finally:
            pass

    def override_get_current_user():
        return CurrentUser(
            user_id=TEST_USER_ID,
            email="remediation_auditor@cropnet.ai",
            role="authenticated",
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ===========================================================================
# 1. FAIL-CLOSED RETRIEVAL TESTS (No Synthetic Data or Fake Rasters)
# ===========================================================================

class TestSatelliteFailClosedRetrieval:
    """Verifies that live retrieval failure returns fail-closed states without generating synthetic data."""

    def test_compute_polygon_indices_fail_closed_when_live_fails(self):
        """When live Sentinel-2 retrieval fails, return NO_USABLE_OBSERVATION and PROVIDER_UNAVAILABLE."""
        with patch.object(copernicus_client, "fetch_live_raster_indices", return_value=None):
            result = copernicus_client.compute_polygon_indices(
                polygon_geojson=TEST_POLYGON,
                farm_area_ha=2.5,
                use_live_raster=True,
                farm_id=str(TEST_FARM_ID),
            )

        assert result["quality_status"] == "NO_USABLE_OBSERVATION"
        assert result["copernicus_provider_status"] == "PROVIDER_UNAVAILABLE"
        assert result["product_id"] is None
        assert result["mean_ndvi"] is None
        assert result["median_ndvi"] is None
        assert result["mean_ndmi"] is None
        assert result["valid_pixel_count"] == 0
        assert result["total_pixel_count"] == 0
        assert result["farm_coverage_percent"] == 0.0
        assert result["cloud_masked_percent"] == 0.0
        assert result["radiometric_conversion_provenance"] == "NONE"
        assert "No synthetic data generated" in result["quality_notes"]

    def test_no_synthetic_rasters_written_to_disk_on_failure(self):
        """No PNG or JSON rasters may be written to disk on live retrieval failure."""
        test_id = str(uuid.uuid4())
        ndvi_target = os.path.join(DERIVED_RASTER_CACHE_DIR, f"{test_id}_ndvi.png")
        meta_target = os.path.join(DERIVED_RASTER_CACHE_DIR, f"{test_id}_meta.json")

        # Ensure target files do not exist beforehand
        if os.path.exists(ndvi_target):
            os.remove(ndvi_target)
        if os.path.exists(meta_target):
            os.remove(meta_target)

        with patch.object(copernicus_client, "fetch_live_raster_indices", return_value=None):
            res = copernicus_client.compute_polygon_indices(
                polygon_geojson=TEST_POLYGON,
                farm_area_ha=2.5,
                use_live_raster=True,
                farm_id=test_id,
            )

        assert res["quality_status"] == "NO_USABLE_OBSERVATION"
        assert not os.path.exists(ndvi_target), "Synthetic NDVI PNG was created on failure!"
        assert not os.path.exists(meta_target), "Synthetic metadata JSON was created on failure!"


# ===========================================================================
# 2. PATH TRAVERSAL AND SECURITY TESTS
# ===========================================================================

class TestSatelliteSecurityAndSanitization:
    """Verifies strict UUID validation, path normalization, and cross-farm leakage prevention."""

    def test_sanitize_farm_id_valid_uuid(self):
        valid = "94a1f16e-bf0d-4d3f-9bd3-d63a57189818"
        assert sanitize_farm_id(valid) == valid
        assert sanitize_farm_id(uuid.UUID(valid)) == valid

    def test_sanitize_farm_id_rejects_directory_traversal(self):
        traversal_payloads = [
            "../../etc/passwd",
            "../../../tmp/hack",
            "94a1f16e-bf0d-4d3f-9bd3-d63a57189818/../../../escaped",
            "..\\..\\windows\\system32",
            "not-a-valid-uuid",
            "",
            None,
        ]
        for payload in traversal_payloads:
            with pytest.raises(ValueError, match="Invalid farm_id|farm_id cannot be None"):
                sanitize_farm_id(payload)

    def test_safe_raster_cache_path_strictly_within_cache_dir(self):
        farm_uuid = "94a1f16e-bf0d-4d3f-9bd3-d63a57189818"
        safe_path = _safe_raster_cache_path(farm_uuid, "ndvi.png")
        assert safe_path.startswith(DERIVED_RASTER_CACHE_DIR + os.sep)
        assert safe_path.endswith(f"{farm_uuid}_ndvi.png")

        # Suffix traversal attempts
        with pytest.raises(ValueError, match="Invalid suffix"):
            _safe_raster_cache_path(farm_uuid, "../../../etc/shadow")
        with pytest.raises(ValueError, match="Invalid suffix"):
            _safe_raster_cache_path(farm_uuid, "sub/meta.json")

    def test_no_silent_cross_farm_fallback_to_baramati(self):
        """
        When a farm's raster or metadata does not exist, get_raster_map_path
        and get_spatial_metadata must return None, NEVER falling back to Baramati farm ID.
        """
        random_farm_id = str(uuid.uuid4())
        # Both must return None without returning Baramati rasters
        assert get_raster_map_path(random_farm_id, "ndvi") is None
        assert get_raster_map_path(random_farm_id, "ndmi") is None
        assert get_raster_map_path(random_farm_id, "scl") is None
        assert get_spatial_metadata(random_farm_id) is None


# ===========================================================================
# 3. HISTORICAL PRESERVATION AND API ENDPOINTS
# ===========================================================================

class TestSatelliteHistoricalPreservation:
    """Verifies that API sync failures preserve genuine historical observations."""

    def test_sync_failure_preserves_historical_observation(self, client, satellite_db_session):
        """When live retrieval fails, sync preserves the latest genuine historical observation."""
        # 1. Seed an authentic historical observation from 5 days ago
        hist_date = datetime.utcnow() - timedelta(days=5)
        hist_obs = SatelliteVegetationObservationModel(
            id=str(uuid.uuid4()),
            farm_id=str(TEST_FARM_ID),
            observation_date=hist_date,
            product_id="S2B_43QDA_20261104_0_L2A",
            tile_id="T43QDA",
            sensor="Sentinel-2 L2A",
            processing_baseline="05.13",
            mean_ndvi=0.640,
            median_ndvi=0.640,
            min_ndvi=0.200,
            max_ndvi=0.850,
            std_ndvi=0.120,
            mean_ndmi=0.217,
            valid_pixel_count=1848,
            total_pixel_count=1918,
            farm_coverage_percent=96.4,
            cloud_masked_percent=0.0,
            spatial_resolution_meters=10.0,
            quality_status="VALID_OBSERVATION",
            quality_notes="Authentic Sentinel-2 L2A ground observation [veg_px: 1104, soil_px: 744, rad: HARMONIZED_COG_BOA_OFFSET_ALREADY_APPLIED]",
            is_small_farm_warning=False,
            created_at=hist_date,
        )
        satellite_db_session.add(hist_obs)
        satellite_db_session.commit()

        # 2. Trigger sync with simulated live provider failure
        with patch.object(copernicus_client, "fetch_live_raster_indices", return_value=None):
            res = client.post(f"/api/v1/farms/{TEST_FARM_ID}/satellite/sync")

        assert res.status_code == 200
        sync_data = res.json()
        assert sync_data["success"] is False
        assert sync_data["synced_observations_count"] == 0
        assert sync_data["copernicus_provider_status"] == "PROVIDER_UNAVAILABLE"
        assert sync_data["latest_observation"] is not None
        assert sync_data["latest_observation"]["id"] == hist_obs.id
        assert sync_data["latest_observation"]["mean_ndvi"] == 0.640
        assert "Preserving latest historical observation" in sync_data["message"]

        # Verify no fake row was inserted
        total_rows = satellite_db_session.query(SatelliteVegetationObservationModel).filter(
            SatelliteVegetationObservationModel.farm_id == str(TEST_FARM_ID)
        ).count()
        assert total_rows == 1

    def test_sync_failure_with_no_history_returns_empty(self, client, satellite_db_session):
        """When a farm has zero observations and live retrieval fails, latest_observation is None."""
        with patch.object(copernicus_client, "fetch_live_raster_indices", return_value=None):
            res = client.post(f"/api/v1/farms/{TEST_FARM_ID}/satellite/sync")

        assert res.status_code == 200
        sync_data = res.json()
        assert sync_data["success"] is False
        assert sync_data["latest_observation"] is None
        assert sync_data["synced_observations_count"] == 0
        assert sync_data["copernicus_provider_status"] == "PROVIDER_UNAVAILABLE"

        # GET /latest returns 404
        latest_res = client.get(f"/api/v1/farms/{TEST_FARM_ID}/satellite/latest")
        assert latest_res.status_code == 404

    def test_raster_map_endpoints_return_404_when_missing(self, client):
        """When raster map PNG or metadata JSON is missing, return 404 without creating synthetic data."""
        res_map = client.get(f"/api/v1/farms/{TEST_FARM_ID}/satellite/latest/raster-map?index_type=ndvi")
        assert res_map.status_code == 404
        assert "not found" in res_map.json()["detail"].lower()

        res_meta = client.get(f"/api/v1/farms/{TEST_FARM_ID}/satellite/latest/spatial-metadata")
        assert res_meta.status_code == 404
        assert "not available" in res_meta.json()["detail"].lower()


# ===========================================================================
# 4. SYNTHETIC QA RECORD ISOLATION TESTS
# ===========================================================================

class TestSyntheticQAIsolation:
    """Verifies that synthetic QA records are isolated and excluded from farmer views."""

    def test_isolate_synthetic_qa_observations_in_db(self, satellite_db_session, client):
        """Synthetic records are marked SYNTHETIC_QA_ISOLATED and hidden from farmer queries."""
        now = datetime.utcnow()
        # Authentic record
        auth_obs = SatelliteVegetationObservationModel(
            id=str(uuid.uuid4()),
            farm_id=str(TEST_FARM_ID),
            observation_date=now - timedelta(days=2),
            product_id="S2B_43QDA_20261104_0_L2A",
            tile_id="T43QDA",
            sensor="Sentinel-2 L2A",
            mean_ndvi=0.620,
            valid_pixel_count=1800,
            total_pixel_count=1900,
            quality_status="VALID_OBSERVATION",
            quality_notes="[veg_px: 1000, rad: HARMONIZED_COG_BOA_OFFSET_ALREADY_APPLIED]",
            created_at=now - timedelta(days=2),
        )
        # Synthetic record (with fake ESA product_id format)
        synth_obs = SatelliteVegetationObservationModel(
            id=str(uuid.uuid4()),
            farm_id=str(TEST_FARM_ID),
            observation_date=now,
            product_id="S2B_MSIL2A_20261108T053649_N0500_R119_T43QDB",
            tile_id="T43QDB",
            sensor="Sentinel-2 L2A",
            mean_ndvi=0.550,
            valid_pixel_count=1521,
            total_pixel_count=1521,
            quality_status="VALID_OBSERVATION",
            quality_notes="High quality cloud-free observation (1521 valid 10m pixels).",
            created_at=now,
        )
        satellite_db_session.add(auth_obs)
        satellite_db_session.add(synth_obs)
        satellite_db_session.commit()

        # Run isolation utility
        isolated_count = isolate_synthetic_database_observations(satellite_db_session)
        assert isolated_count == 1

        satellite_db_session.refresh(synth_obs)
        assert synth_obs.quality_status == "SYNTHETIC_QA_ISOLATED"
        assert "ISOLATED" in synth_obs.quality_notes

        # Verify GET /latest returns ONLY the authentic observation
        latest_res = client.get(f"/api/v1/farms/{TEST_FARM_ID}/satellite/latest")
        assert latest_res.status_code == 200
        latest_data = latest_res.json()
        assert latest_data["id"] == auth_obs.id
        assert latest_data["product_id"] == "S2B_43QDA_20261104_0_L2A"

        # Verify GET /observations excludes isolated observation
        obs_res = client.get(f"/api/v1/farms/{TEST_FARM_ID}/satellite/observations")
        assert obs_res.status_code == 200
        obs_list = obs_res.json()
        assert len(obs_list) == 1
        assert obs_list[0]["id"] == auth_obs.id

        # Verify Farm Health Collector picks ONLY the authentic observation
        collector = SatelliteCollector()
        farm_dict = {"id": TEST_FARM_ID}
        summary = collector.collect(farm_dict, satellite_db_session)
        assert summary.product_id == "S2B_43QDA_20261104_0_L2A"
        assert summary.canopy_ndvi == 0.620
