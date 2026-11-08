import pytest
from fastapi.testclient import TestClient

def test_get_income_opportunities(client: TestClient):
    response = client.get("/v1/income/opportunities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3

    opp_ids = [opp["opportunity_id"] for opp in data]
    assert "OPP_VERMICOMPOST_01" in opp_ids
    assert "OPP_OSMANABADI_GOAT_01" in opp_ids
    assert "OPP_SOLAR_DRYER_01" in opp_ids

    # Verify key fields
    vermi = next(o for o in data if o["opportunity_id"] == "OPP_VERMICOMPOST_01")
    assert vermi["category"] == "byproduct_utilization"
    assert "soybean" in vermi["target_crops"]
    assert vermi["min_investment_inr"] <= vermi["max_investment_inr"]
    assert len(vermi["key_assumptions"]) > 0
    assert len(vermi["key_risks"]) > 0
    assert "ICAR" in vermi["source_attribution"] or "KVK" in vermi["source_attribution"] or "MPKV" in vermi["source_attribution"]

def test_filter_income_opportunities_by_crop(client: TestClient):
    response = client.get("/v1/income/opportunities?crop_code=onion")
    assert response.status_code == 200
    data = response.json()
    opp_ids = [opp["opportunity_id"] for opp in data]
    assert "OPP_SOLAR_DRYER_01" in opp_ids

def test_calculate_income_scenario_deterministic(client: TestClient):
    payload = {
        "opportunity_id": "OPP_VERMICOMPOST_01",
        "custom_budget_inr": 35000.0,
        "available_labour_hours_day": 2.0,
        "available_land_acres": 0.5
    }
    response = client.post("/v1/income/calculate-scenario", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["opportunity_id"] == "OPP_VERMICOMPOST_01"
    assert data["calculated_capex_inr"] == 35000.0
    assert data["calculated_gross_revenue_inr"] > 0
    assert data["calculated_opex_annual_inr"] > 0
    assert data["calculated_net_profit_annual_inr"] > 0
    assert data["calculated_break_even_months"] > 0
    assert isinstance(data["assumptions_applied"], list)
    assert len(data["assumptions_applied"]) > 0
    assert isinstance(data["risks_to_monitor"], list)
    assert len(data["risks_to_monitor"]) > 0
    assert data["source_attribution"] != ""

def test_calculate_scenario_invalid_opportunity(client: TestClient):
    payload = {
        "opportunity_id": "NON_EXISTENT_OPP",
        "custom_budget_inr": 20000.0
    }
    response = client.post("/v1/income/calculate-scenario", json=payload)
    assert response.status_code == 404
