import pytest
from fastapi.testclient import TestClient

def test_get_income_opportunities_catalog(client: TestClient):
    response = client.get("/v1/income/opportunities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 8

    opp_ids = [opp["opportunity_id"] for opp in data]
    assert "OPP_COMPOST_COST_SAVING_01" in opp_ids
    assert "OPP_DIRECT_APMC_FPO_01" in opp_ids
    assert "OPP_SMALL_GOAT_2_PLUS_1" in opp_ids
    assert "OPP_OSMANABADI_GOAT_10_PLUS_1" in opp_ids
    assert "OPP_OYSTER_MUSHROOM_01" in opp_ids

    # Verify zero-cash compost item
    compost = next(o for o in data if o["opportunity_id"] == "OPP_COMPOST_COST_SAVING_01")
    assert compost["category"] == "zero_cash"
    assert compost["is_cost_saving"] is True
    assert compost["min_investment_inr"] == 0.0
    assert compost["potential_annual_savings_inr"] > 0
    assert len(compost["key_assumptions"]) > 0

def test_get_single_opportunity_endpoint(client: TestClient):
    response = client.get("/v1/income/opportunities/OPP_OYSTER_MUSHROOM_01")
    assert response.status_code == 200
    data = response.json()
    assert data["opportunity_id"] == "OPP_OYSTER_MUSHROOM_01"
    assert data["category"] == "moderate_enterprise"

def test_match_opportunities_zero_budget(client: TestClient):
    payload = {
        "available_investment_inr": 0.0,
        "monthly_operating_budget_inr": 0.0,
        "available_land_acres": 0.0,
        "unused_land_acres": 0.0,
        "water_availability": "rainfed_only",
        "family_labor_hours_day": 1.5,
        "crop_byproducts": ["soybean_straw", "cow_dung"]
    }
    response = client.post("/v1/income/match-opportunities", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0

    # Top opportunity should be zero cash
    top_opp = data[0]
    assert top_opp["opportunity"]["category"] == "zero_cash"
    assert top_opp["is_feasible"] is True

    # Commercial 10+1 goat must be infeasible
    goat = next(o for o in data if o["opportunity"]["opportunity_id"] == "OPP_OSMANABADI_GOAT_10_PLUS_1")
    assert goat["is_feasible"] is False
    assert goat["feasibility_status"] == "NOT_CURRENTLY_AFFORDABLE"
    assert goat["capital_gap_inr"] == 75000.0

def test_match_opportunities_fifteen_thousand_budget(client: TestClient):
    payload = {
        "available_investment_inr": 15000.0,
        "monthly_operating_budget_inr": 2000.0,
        "available_land_acres": 0.5,
        "unused_land_acres": 0.2,
        "field_bunds_available": True,
        "water_availability": "seasonal_canal",
        "family_labor_hours_day": 2.5
    }
    response = client.post("/v1/income/match-opportunities", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Commercial 10+1 goat requiring 75k must NOT be approved
    goat_commercial = next(o for o in data if o["opportunity"]["opportunity_id"] == "OPP_OSMANABADI_GOAT_10_PLUS_1")
    assert goat_commercial["is_feasible"] is False
    assert goat_commercial["capital_gap_inr"] == 60000.0

    # Bund drumstick costing 1.5k must be approved
    drumstick = next(o for o in data if o["opportunity"]["opportunity_id"] == "OPP_FIELD_BUND_DRUMSTICK_01")
    assert drumstick["is_feasible"] is True
    assert drumstick["capital_gap_inr"] == 0.0

def test_calculate_income_scenario_deterministic(client: TestClient):
    payload = {
        "opportunity_id": "OPP_OYSTER_MUSHROOM_01",
        "custom_budget_inr": 20000.0,
        "available_labour_hours_day": 2.0,
        "available_land_acres": 0.0
    }
    response = client.post("/v1/income/calculate-scenario", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["opportunity_id"] == "OPP_OYSTER_MUSHROOM_01"
    assert data["calculated_capex_inr"] == 18000.0
    assert data["calculated_net_profit_annual_inr"] > 0
    assert len(data["monthly_cash_flows"]) == 12
    assert "base" in data["scenarios"]
    assert "conservative" in data["scenarios"]
    assert "optimistic" in data["scenarios"]

def test_compare_selected_opportunities(client: TestClient):
    payload = {
        "opportunity_ids": ["OPP_COMPOST_COST_SAVING_01", "OPP_OYSTER_MUSHROOM_01"],
        "custom_budget_inr": 20000.0
    }
    response = client.post("/v1/income/compare-opportunities", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    mush = next(o for o in data if o["opportunity_id"] == "OPP_OYSTER_MUSHROOM_01")
    compost = next(o for o in data if o["opportunity_id"] == "OPP_COMPOST_COST_SAVING_01")
    assert mush["net_annual_profit_inr"] > 0
    assert compost["is_cost_saving"] is True
    assert compost["annual_money_saved_inr"] > 0

def test_farm_profile_and_saved_plan_lifecycle(client: TestClient):
    # Setup test farm
    farm_res = client.post("/v1/farms/", json={
        "owner_id": "farmer_test_income_01",
        "farm_name": "Baramati Test Farm",
        "district": "Pune",
        "taluka": "Baramati",
        "village": "Malegaon",
        "latitude": 18.15,
        "longitude": 74.58
    })
    assert farm_res.status_code == 200
    farm_id = farm_res.json()["farm_id"]

    # 1. Get prefilled profile
    prof_res = client.get(f"/v1/income/farms/{farm_id}/profile")
    assert prof_res.status_code == 200
    prof_data = prof_res.json()
    assert prof_data["available_investment_inr"] == 0.0

    # 2. Update profile
    prof_data["available_investment_inr"] = 10000.0
    prof_data["has_storage_room"] = True
    save_prof_res = client.put(f"/v1/income/farms/{farm_id}/profile", json=prof_data)
    assert save_prof_res.status_code == 200
    assert save_prof_res.json()["available_investment_inr"] == 10000.0

    # 3. Discover opportunities for farm
    disc_res = client.post(f"/v1/income/farms/{farm_id}/discover")
    assert disc_res.status_code == 200
    disc_data = disc_res.json()
    assert len(disc_data) > 0

    # 4. Save a plan
    plan_res = client.post(f"/v1/income/farms/{farm_id}/plans", json={
        "opportunity_id": "OPP_FIELD_BUND_DRUMSTICK_01",
        "chosen_budget_inr": 2500.0,
        "notes": "Plan to plant 25 moringa saplings along North boundary bund."
    })
    assert plan_res.status_code == 200
    plan_data = plan_res.json()
    assert plan_data["opportunity_id"] == "OPP_FIELD_BUND_DRUMSTICK_01"
    assert plan_data["projected_annual_profit_inr"] > 0

    # 5. List saved plans
    list_res = client.get(f"/v1/income/farms/{farm_id}/plans")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert len(list_data) >= 1
    assert list_data[0]["opportunity_id"] == "OPP_FIELD_BUND_DRUMSTICK_01"
