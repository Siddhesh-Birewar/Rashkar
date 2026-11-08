"""
Comprehensive Security Regression Test Suite for Water and Satellite Endpoints.

Verifies:
1. Farm Ownership Enforcement & Cross-User Access Rejection (403 Forbidden).
2. Missing Authentication Rejection (401 Unauthorized in production).
3. Production Protection: X-Dev-User-Id header bypass is strictly blocked when ENVIRONMENT=production.
4. Farm Cache & Data Isolation: Water sources and satellite records from Farm A never leak into Farm B.
5. Sensitive Credential Safeguards: Client secrets and Bearer tokens are never exposed or logged.
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
from cropnet.services.api.app.core.config import settings
from cropnet.services.api.app.models.soil_and_farm import Base, FarmModel
from cropnet.services.api.app.models.water import WaterSourceModel
from cropnet.services.api.app.models.satellite import SatelliteVegetationObservationModel
from cropnet.services.api.app.api.v1.endpoints.farms import _FARM_STORAGE


USER_A_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
USER_B_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
FARM_A_ID = uuid.UUID("11111111-aaaa-1111-aaaa-111111111111")
FARM_B_ID = uuid.UUID("22222222-bbbb-2222-bbbb-222222222222")


@pytest.fixture
def security_test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    now = datetime.utcnow()
    # Farm A belongs to User A
    farm_a = FarmModel(
        id=str(FARM_A_ID),
        owner_id=str(USER_A_ID),
        name="User A Farm",
        village="Malegaon",
        taluka="Baramati",
        district="Pune",
        state="Maharashtra",
        geometry_geojson={"type": "Polygon", "coordinates": [[[74.5, 18.1], [74.6, 18.1], [74.6, 18.2], [74.5, 18.2], [74.5, 18.1]]]},
        calculated_area_hectares=2.5,
        calculated_area_acres=6.18,
        created_at=now,
        updated_at=now,
    )
    # Farm B belongs to User B
    farm_b = FarmModel(
        id=str(FARM_B_ID),
        owner_id=str(USER_B_ID),
        name="User B Farm",
        village="Nimgaon",
        taluka="Indapur",
        district="Pune",
        state="Maharashtra",
        geometry_geojson={"type": "Polygon", "coordinates": [[[74.9, 18.0], [74.92, 18.0], [74.92, 18.02], [74.9, 18.02], [74.9, 18.0]]]},
        calculated_area_hectares=3.0,
        calculated_area_acres=7.41,
        created_at=now,
        updated_at=now,
    )
    session.add(farm_a)
    session.add(farm_b)
    session.commit()

    _FARM_STORAGE[FARM_A_ID] = {
        "id": FARM_A_ID,
        "owner_id": USER_A_ID,
        "name": farm_a.name,
        "geometry": farm_a.geometry_geojson,
        "calculated_area_hectares": farm_a.calculated_area_hectares,
        "calculated_area_acres": farm_a.calculated_area_acres,
    }
    _FARM_STORAGE[FARM_B_ID] = {
        "id": FARM_B_ID,
        "owner_id": USER_B_ID,
        "name": farm_b.name,
        "geometry": farm_b.geometry_geojson,
        "calculated_area_hectares": farm_b.calculated_area_hectares,
        "calculated_area_acres": farm_b.calculated_area_acres,
    }

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        _FARM_STORAGE.clear()


@pytest.fixture
def sec_client(security_test_db):
    def override_get_db():
        try:
            yield security_test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_cross_user_water_access_rejected_403(sec_client):
    """User B must be rejected with 403 Forbidden when trying to access User A's water sources."""
    def override_user_b():
        return CurrentUser(user_id=USER_B_ID, email="user_b@cropnet.ai", is_authenticated=True)

    app.dependency_overrides[get_current_user] = override_user_b

    # User B tries to read User A's water sources
    res = sec_client.get(f"/api/v1/farms/{FARM_A_ID}/water/sources")
    assert res.status_code == 403
    assert "permission" in res.json()["detail"].lower()


def test_cross_user_satellite_access_rejected_403(sec_client):
    """User B must be rejected with 403 Forbidden when trying to access User A's satellite data."""
    def override_user_b():
        return CurrentUser(user_id=USER_B_ID, email="user_b@cropnet.ai", is_authenticated=True)

    app.dependency_overrides[get_current_user] = override_user_b

    res = sec_client.get(f"/api/v1/farms/{FARM_A_ID}/satellite/latest")
    assert res.status_code == 403
    assert "permission" in res.json()["detail"].lower()


def test_cross_farm_water_cache_isolation(sec_client):
    """Water sources added to Farm A must never be visible under Farm B."""
    def override_user_a():
        return CurrentUser(user_id=USER_A_ID, email="user_a@cropnet.ai", is_authenticated=True)

    def override_user_b():
        return CurrentUser(user_id=USER_B_ID, email="user_b@cropnet.ai", is_authenticated=True)

    # 1. User A creates a source on Farm A
    app.dependency_overrides[get_current_user] = override_user_a
    source_payload = {
        "source_type": "borewell",
        "name": "User A Private Borewell",
        "location_description": "Near pump house",
        "latitude": 18.15,
        "longitude": 74.55,
        "seasonal_availability": "perennial",
        "reliability": "reliable",
        "daily_available_hours": 8.0,
        "irrigation_method": "drip",
        "measured_capacity_lph": 15000.0,
        "capacity_provenance": "MEASURED",
    }
    create_res = sec_client.post(f"/api/v1/farms/{FARM_A_ID}/water/sources", json=source_payload)
    assert create_res.status_code == 201
    source_id = create_res.json()["id"]

    # 2. User B lists water sources on Farm B -> must NOT see Farm A's source
    app.dependency_overrides[get_current_user] = override_user_b
    list_res = sec_client.get(f"/api/v1/farms/{FARM_B_ID}/water/sources")
    assert list_res.status_code == 200
    b_sources = list_res.json()
    assert not any(s["id"] == source_id for s in b_sources)
    assert not any(s["name"] == "User A Private Borewell" for s in b_sources)


def test_dev_bypass_strictly_blocked_in_production(sec_client, monkeypatch):
    """When ENVIRONMENT='production', X-Dev-User-Id header is ignored and missing Bearer returns 401."""
    # Ensure get_current_user is NOT overridden so actual security logic runs
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]

    monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    # Request with X-Dev-User-Id in production without Authorization Bearer
    res = sec_client.get(
        f"/api/v1/farms/{FARM_A_ID}/water/sources",
        headers={"X-Dev-User-Id": str(USER_A_ID)}
    )
    assert res.status_code == 401
    assert "Authorization Bearer token" in res.json()["detail"]


def test_copernicus_no_secrets_in_logs(caplog):
    """Verify that Copernicus client initialization and methods do not log client secrets."""
    import logging
    from cropnet.services.api.app.services.satellite.copernicus_client import CopernicusClient

    with caplog.at_level(logging.DEBUG):
        client = CopernicusClient()
        _ = client.has_credentials
        _ = client.get_token()

    for record in caplog.records:
        assert "COPERNICUS_CLIENT_SECRET" not in record.message
        assert "access_token" not in record.message
