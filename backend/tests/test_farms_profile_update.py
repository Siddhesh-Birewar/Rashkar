import pytest
from datetime import date
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_farm_profile_update_e2e():
    # 1. Register initial farm
    reg_payload = {
        "farmer_name": "Kailas Jadhav",
        "phone_number": "9811223344",
        "district": "Pune",
        "taluka": "Baramati",
        "village": "Malegaon",
        "latitude": 18.151,
        "longitude": 74.577,
        "farm_name": "Jadhav Sheti",
        "crop_code": "soybean",
        "sowing_date": "2024-06-25",
        "total_area_acres": 3.0,
        "planted_area_acres": 2.5,
        "irrigation_type": "rainfed",
        "preferred_language": "en"
    }
    reg_resp = client.post("/v1/farms/guided-registration", json=reg_payload)
    assert reg_resp.status_code == 200
    initial_summary = reg_resp.json()
    farm_id = initial_summary["farm_id"]
    assert initial_summary["active_crop_code"] == "soybean"
    assert "Baramati" in initial_summary["location_display"]

    # 2. Update profile post-registration
    update_payload = {
        "farmer_name": "Kailas R. Jadhav",
        "phone_number": "9899887766",
        "farm_name": "Jadhav High-Tech Farm",
        "district": "Nashik",
        "taluka": "Niphad",
        "village": "Pimpalgaon",
        "latitude": 20.083,
        "longitude": 74.033,
        "total_area_acres": 5.0,
        "planted_area_acres": 4.5,
        "crop_code": "onion",
        "sowing_date": "2024-07-10",
        "irrigation_type": "drip",
        "preferred_language": "en"
    }
    put_resp = client.put(f"/v1/farms/{farm_id}/profile", json=update_payload)
    assert put_resp.status_code == 200
    updated_summary = put_resp.json()

    assert updated_summary["farmer_name"] == "Kailas R. Jadhav"
    assert "Niphad, Nashik" in updated_summary["location_display"]
    assert updated_summary["active_crop_code"] == "onion"
    assert updated_summary["planted_area_acres"] == 4.5
    assert updated_summary["irrigation_type"] == "drip"

    # 3. Verify persistence via independent GET
    get_resp = client.get(f"/v1/farms/{farm_id}/summary")
    assert get_resp.status_code == 200
    persisted = get_resp.json()
    assert persisted["farmer_name"] == "Kailas R. Jadhav"
    assert persisted["active_crop_code"] == "onion"
    assert "Niphad" in persisted["location_display"]

    # 4. Verify Yield Intelligence now calculates Nashik Onion baseline
    yield_resp = client.get(f"/v1/yield-intelligence/{farm_id}/yield-risk")
    assert yield_resp.status_code == 200
    yield_data = yield_resp.json()
    assert yield_data["crop_code"] == "onion"
    baseline = yield_data["yield_baseline"]
    assert "onion" in baseline["geographical_unit"].lower()
    # Onion historical APY average is ~12-16 t/ha
    assert baseline["historical_mean_t_ha"] > 5.0
