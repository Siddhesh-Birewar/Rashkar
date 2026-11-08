import pytest
from fastapi.testclient import TestClient

def test_complete_farmer_journey_e2e(client: TestClient):
    # =========================================================================
    # Step 1: Farmer Registration & Guided Onboarding
    # =========================================================================
    registration_payload = {
        "farmer_name": "Dattatraya Shinde",
        "phone_number": "9822012345",
        "taluka": "Indapur",
        "district": "Pune",
        "village": "Bawada",
        "farm_name": "Shinde Krishi Sheti",
        "total_area_acres": 5.0,
        "latitude": 18.115,
        "longitude": 75.025,
        "crop_code": "soybean",
        "season": "kharif",
        "sowing_date": "2024-06-20",
        "irrigation_type": "canal",
        "planted_area_acres": 4.0
    }
    reg_res = client.post("/v1/farms/guided-registration", json=registration_payload)
    assert reg_res.status_code == 200, f"Registration failed: {reg_res.text}"
    farm_summary = reg_res.json()
    farm_id = farm_summary["farm_id"]
    farmer_id = farm_summary["farmer_id"]
    assert farm_id is not None
    assert farm_summary["farmer_name"] == "Dattatraya Shinde"
    assert "Indapur" in farm_summary["location_display"]
    assert farm_summary["active_crop_code"] == "soybean"

    # =========================================================================
    # Step 2: Query "Farm at a Glance" Summary
    # =========================================================================
    summary_res = client.get(f"/v1/farms/{farm_id}/summary")
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["farm_id"] == farm_id
    assert summary["weather_summary"] is not None
    assert "temperature_c" in summary["weather_summary"]
    assert summary["soil_summary"] is not None
    assert "clay_pct" in summary["soil_summary"]

    # =========================================================================
    # Step 3: Yield Intelligence Assessment
    # =========================================================================
    yield_res = client.get(f"/v1/yield-intelligence/{farm_id}/yield-risk")
    assert yield_res.status_code == 200
    yield_data = yield_res.json()
    assert yield_data["crop_code"] == "soybean"
    assert "risks" in yield_data
    assert len(yield_data["risks"]) > 0
    assert "yield_baseline" in yield_data
    assert yield_data["coverage"]["crop_status"] == "supported_rules_and_baselines"

    # =========================================================================
    # Step 4: Worker Heat Risk Assessment (0-6h Liljegren WBGT)
    # =========================================================================
    worker_heat_payload = {
        "latitude": 18.115,
        "longitude": 75.025,
        "taluka": "Indapur",
        "workload_category": "heavy",
        "clothing_type": "standard_work_clothes",
        "is_acclimatised": True,
        "sun_exposure": "direct_sun"
    }
    worker_res = client.post("/v1/heat-risk/worker-hazard", json=worker_heat_payload)
    assert worker_res.status_code == 200
    worker_data = worker_res.json()
    assert worker_data["time_horizon"] == "0_to_6_hours"
    assert len(worker_data["hourly_projections"]) == 7
    assert worker_data["screening_threshold_c"] == 26.0

    # =========================================================================
    # Step 5: Crop Heat Risk Assessment
    # =========================================================================
    crop_heat_payload = {
        "farm_id": farm_id,
        "forecast_tmax_c": 38.5,
        "forecast_tmin_c": 24.5
    }
    crop_heat_res = client.post("/v1/heat-risk/crop-heat", json=crop_heat_payload)
    assert crop_heat_res.status_code == 200
    crop_heat_data = crop_heat_res.json()
    assert crop_heat_data["crop_code"] == "soybean"
    assert crop_heat_data["critical_tmax_threshold_c"] is not None
    assert "evidence_citation" in crop_heat_data

    # =========================================================================
    # Step 6: Income Diversification Opportunities & Scenario Simulation
    # =========================================================================
    opps_res = client.get("/v1/income/opportunities")
    assert opps_res.status_code == 200
    opps = opps_res.json()
    assert len(opps) > 0
    selected_opp = opps[0]["opportunity_id"]

    sim_payload = {
        "opportunity_id": selected_opp,
        "custom_budget_inr": 30000.0,
        "available_labour_hours_day": 2.5,
        "available_land_acres": 0.5
    }
    sim_res = client.post("/v1/income/calculate-scenario", json=sim_payload)
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert sim_data["calculated_capex_inr"] == 30000.0
    assert sim_data["calculated_net_profit_annual_inr"] > 0
    assert sim_data["calculated_break_even_months"] > 0

    # =========================================================================
    # Step 7: Grounded AI Assistant Chat
    # =========================================================================
    chat_payload = {
        "farmer_id": farmer_id,
        "farm_id": farm_id,
        "message": "What is the heat risk and advice for my soybean crop today?"
    }
    chat_res = client.post("/v1/assistant/chat", json=chat_payload)
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert len(chat_data["reply"]) > 0
    assert len(chat_data["citations"]) > 0

    # =========================================================================
    # Step 8: Crop Loss Evidence Documentation & Review Workflow
    # =========================================================================
    loss_payload = {
        "farmer_id": farmer_id,
        "farm_id": farm_id,
        "crop_code": "soybean",
        "season": "kharif",
        "event_date": "2024-07-25",
        "peril_type": "inundation",
        "damage_estimate_pct": 50.0,
        "affected_area_acres": 3.0,
        "photo_urls": [],
        "is_draft": False
    }
    loss_res = client.post("/v1/pmfby/cases", json=loss_payload)
    assert loss_res.status_code == 200
    loss_data = loss_res.json()
    case_id = loss_data["case_id"]
    assert loss_data["dossier_status"] == "evidence_submitted"

    # Human agronomist reviews case in reviewer queue
    review_res = client.post(
        f"/v1/pmfby/cases/{case_id}/review",
        json={
            "reviewer_id": "agronomist_indapur_kvk",
            "decision": "verified_loss",
            "rationale": "Excessive moisture and drainage block verified with rainfall baseline.",
            "recommended_compensation_basis": "Mid-season localized adversity PMFBY provision"
        }
    )
    assert review_res.status_code == 200
    reviewed_case = review_res.json()
    assert reviewed_case["dossier_status"] == "review_completed"
    assert reviewed_case["reviewer_decision"] == "verified_loss"
