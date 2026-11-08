import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_full_maharashtra_districts_and_crops_catalog():
    # 1. Verify 36 districts
    resp = client.get("/v1/geo/districts")
    assert resp.status_code == 200
    districts = resp.json()
    district_names = [d["district_name"] for d in districts]
    assert len(district_names) == 36
    assert "Solapur" in district_names
    assert "Nashik" in district_names
    assert "Ahmednagar" in district_names
    assert "Nagpur" in district_names

    # 2. Verify talukas for Solapur
    resp_talukas = client.get("/v1/geo/talukas?district=Solapur")
    assert resp_talukas.status_code == 200
    talukas = resp_talukas.json()
    assert len(talukas) >= 11
    pandharpur = next(t for t in talukas if t["taluka_name"] == "Pandharpur")
    assert 17.0 < pandharpur["latitude"] < 18.5
    assert 75.0 < pandharpur["longitude"] < 76.0

    # 3. Verify crops catalog
    resp_crops = client.get("/v1/geo/crops")
    assert resp_crops.status_code == 200
    crops = resp_crops.json()
    assert len(crops) >= 30
    crop_codes = [c["crop_code"] for c in crops]
    assert "jowar" in crop_codes
    assert "onion" in crop_codes
    assert "cotton" in crop_codes
    assert "sugarcane" in crop_codes

def test_solapur_jowar_dynamic_registration_and_yield_intelligence():
    # 1. Guided registration for a new farmer in Solapur
    payload = {
        "farmer_name": "Tukaram Shinde",
        "phone_number": "9876543210",
        "district": "Solapur",
        "taluka": "Pandharpur",
        "village": "Bhatumbare",
        "latitude": 17.678,
        "longitude": 75.328,
        "farm_name": "Shinde Sheti Farm",
        "crop_code": "jowar",
        "sowing_date": "2024-07-05",
        "total_area_acres": 4.0,
        "planted_area_acres": 3.5,
        "irrigation_type": "rainfed",
        "preferred_language": "en"
    }
    reg_resp = client.post("/v1/farms/guided-registration", json=payload)
    assert reg_resp.status_code == 200
    farm_summary = reg_resp.json()
    farm_id = farm_summary["farm_id"]
    farmer_id = farm_summary["farmer_id"]

    assert farm_summary["farmer_name"] == "Tukaram Shinde"
    assert "Pandharpur, Solapur" in farm_summary["location_display"]
    assert farm_summary["active_crop_code"] == "jowar"

    # 2. Verify dynamic soil profile assigned for Solapur
    assert farm_summary["soil_summary"] is not None
    assert farm_summary["soil_summary"]["clay_pct"] >= 40.0  # Deep black vertisol of Deccan

    # 3. Verify Yield Intelligence baseline is computed from real APY data for Solapur Jowar
    yield_resp = client.get(f"/v1/yield-intelligence/{farm_id}/yield-risk")
    assert yield_resp.status_code == 200
    yield_data = yield_resp.json()

    assert yield_data["crop_code"] == "jowar"
    assert yield_data["farm_id"] == farm_id
    baseline = yield_data["yield_baseline"]
    assert "solapur" in baseline["geographical_unit"].lower()
    # Solapur Jowar historical APY average is ~0.53 t/ha (rainfed Deccan sorghum)
    assert 0.3 <= baseline["historical_mean_t_ha"] <= 1.2
    assert baseline["sample_seasons_count"] >= 20

    # 4. Verify Income Opportunities for Jowar include Osmanabadi Goat Rearing
    inc_resp = client.get("/v1/income/opportunities?crop_code=jowar")
    assert inc_resp.status_code == 200
    opps = inc_resp.json()
    opp_ids = [o["opportunity_id"] for o in opps]
    assert "OPP_OSMANABADI_GOAT_01" in opp_ids

    # 5. Verify Assistant grounded chat for this farm
    chat_resp = client.post("/v1/assistant/chat", json={
        "farmer_id": farmer_id,
        "farm_id": farm_id,
        "message": "Why is my crop at risk today?",
        "provider_override": "none"
    })
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    assert "Tukaram" in chat_data["reply"]
    assert "Pandharpur" in chat_data["reply"]
