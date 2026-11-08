import os
import pytest
from playwright.sync_api import sync_playwright

FRONTEND_URL = "http://127.0.0.1:8080"
BACKEND_BASE_URL = "http://127.0.0.1:8000"
SCREENSHOT_DIR = "docs/screenshots"

def setup_module():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def test_worker_heat_risk_dynamic_api():
    """Verify Worker Heat Risk returns dynamic, multi-workload WBGT calculations and triage guidance."""
    with sync_playwright() as p:
        request_context = p.request.new_context()
        
        # Test 1: Heavy work, unacclimatised, protective coveralls
        res_heavy_sun = request_context.post(
            f"{BACKEND_BASE_URL}/v1/heat-risk/worker-hazard",
            data={
                "latitude": 18.15,
                "longitude": 74.58,
                "taluka": "Baramati",
                "workload_category": "heavy",
                "clothing_type": "coveralls_protective",
                "is_acclimatised": False,
                "sun_exposure": "direct_sun",
                "exposure_duration_hours": 4.0
            }
        )
        assert res_heavy_sun.status == 200
        data_heavy_sun = res_heavy_sun.json()
        assert "current_wbgt_estimated_c" in data_heavy_sun
        assert "hourly_projections" in data_heavy_sun
        assert len(data_heavy_sun["hourly_projections"]) >= 6
        assert "emergency_triage" in data_heavy_sun
        assert "heat_exhaustion" in data_heavy_sun["emergency_triage"]
        assert "heat_stroke" in data_heavy_sun["emergency_triage"]
        
        # Test 2: Light work in full shade, acclimatised, standard work clothes
        res_light_shade = request_context.post(
            f"{BACKEND_BASE_URL}/v1/heat-risk/worker-hazard",
            data={
                "latitude": 18.15,
                "longitude": 74.58,
                "taluka": "Baramati",
                "workload_category": "light",
                "clothing_type": "standard_work_clothes",
                "is_acclimatised": True,
                "sun_exposure": "full_shade",
                "exposure_duration_hours": 4.0
            }
        )
        assert res_light_shade.status == 200
        data_light_shade = res_light_shade.json()
        
        # Protective coveralls CAV (+2°C) makes effective WBGT strictly higher
        assert data_heavy_sun["max_wbgt_effective_c"] > data_light_shade["max_wbgt_effective_c"]
        # Heavy unacclimatised threshold (23°C) is stricter than light acclimatised threshold (31°C)
        assert data_heavy_sun["screening_threshold_c"] < data_light_shade["screening_threshold_c"]
        # Mandatory disclaimer verification
        assert "wbgt values are cloud-modeled estimates" in data_heavy_sun["disclaimer"].lower()

def test_crop_heat_risk_dynamic_stage_recalculation():
    """Verify Crop Heat Risk provides biological parameters, GDD, 4-day outlook, and stage sensitivity."""
    with sync_playwright() as p:
        request_context = p.request.new_context()
        
        # Flowering stage
        res_flower = request_context.post(
            f"{BACKEND_BASE_URL}/v1/heat-risk/crop-heat",
            data={
                "farm_id": "farm_demo_pune_01",
                "farmer_confirmed_stage": "flowering"
            }
        )
        assert res_flower.status == 200
        data_flower = res_flower.json()
        
        # Thermal parameters
        assert "base_temp_c" in data_flower
        assert "optimal_temp_max_c" in data_flower
        assert "critical_tmax_threshold_c" in data_flower
        assert "cumulative_heat_units_gdd" in data_flower
        assert "warm_night_respiration_hazard" in data_flower
        
        # 4-day outlook
        assert "daily_outlook" in data_flower
        assert len(data_flower["daily_outlook"]) == 4
        assert "recommended_interventions" in data_flower
        assert len(data_flower["recommended_interventions"]) > 0
        assert "evidence_citation" in data_flower

def test_yield_intelligence_apy_and_soil_provenance():
    """Verify Yield Intelligence returns APY baseline, CropNet soil properties, 5 stress scores, and ML gating."""
    with sync_playwright() as p:
        request_context = p.request.new_context()
        
        res = request_context.get(f"{BACKEND_BASE_URL}/v1/yield-intelligence/farm_demo_pune_01/yield-risk")
        assert res.status == 200
        data = res.json()
        
        # 1. Historical APY yield analysis
        assert "yield_baseline" in data
        baseline = data["yield_baseline"]
        assert baseline["sample_seasons_count"] > 0
        assert baseline["historical_mean_t_ha"] is not None
        assert baseline["historical_p10_t_ha"] is not None
        assert baseline["historical_p90_t_ha"] is not None
        
        # 2. Soil suitability analysis
        assert "suitability_analysis" in data
        soil = data["suitability_analysis"]
        assert "soil_ph" in soil
        assert "soil_texture" in soil
        assert "organic_carbon_pct" in soil
        assert "available_water_capacity_mm_m" in soil
        assert "effective_rooting_depth_cm" in soil
        
        # 3. 5 Environmental stress dimensions
        assert "risks" in data
        risk_dims = [r["risk_dimension"] for r in data["risks"]]
        assert "weather_dry_spell" in risk_dims
        assert "excess_rainfall_waterlogging" in risk_dims
        assert "soil_constraint" in risk_dims
        assert "crop_heat_stress" in risk_dims
        assert "pest_disease_watch" in risk_dims
        
        # 4. ML Prediction Gate Safeguard
        assert data["ml_prediction_gate"]["prediction_status"] == "REQUIRES_FARM_HARVEST_LABELS"
        assert "disabled" in data["yield_baseline"]["disclaimer"].lower() or "safeguard" in data["ml_prediction_gate"]

def test_income_diversification_catalog_matching_and_scenarios():
    """Verify Income Diversification includes 9 canonical enterprises, interactive matching, and 3-scenario simulations."""
    with sync_playwright() as p:
        request_context = p.request.new_context()
        
        # 1. Catalog check
        catalog_res = request_context.get(f"{BACKEND_BASE_URL}/v1/income/opportunities")
        assert catalog_res.status == 200
        catalog = catalog_res.json()
        assert len(catalog) >= 9
        enterprise_ids = [e["opportunity_id"] for e in catalog]
        assert "OPP_OSMANABADI_GOAT_01" in enterprise_ids
        assert "OPP_BROILER_POULTRY_01" in enterprise_ids
        assert "OPP_DAIRY_COWS_01" in enterprise_ids
        assert "OPP_OYSTER_MUSHROOM_01" in enterprise_ids
        assert "OPP_APICULTURE_01" in enterprise_ids
        assert "OPP_VERMICOMPOST_01" in enterprise_ids
        
        # 2. Match with low capital (e.g. ₹20,000)
        low_cap_match = request_context.post(
            f"{BACKEND_BASE_URL}/v1/income/match-opportunities",
            data={
                "available_investment_inr": 20000,
                "working_capital_inr": 5000,
                "available_land_acres": 0.5,
                "unused_land_acres": 0.25,
                "water_availability": "seasonal_canal",
                "family_labor_hours_day": 2.5,
                "existing_livestock": "none",
                "has_storage_or_shed": False,
                "risk_tolerance": "moderate",
                "category_preference": "all"
            }
        )
        assert low_cap_match.status == 200
        scored = low_cap_match.json()
        assert len(scored) >= 9
        # Dairy Gir (requires higher investment) should have suitability reflecting capital barrier
        dairy_item = next(e for e in scored if e["opportunity"]["opportunity_id"] == "OPP_DAIRY_COWS_01")
        assert dairy_item["suitability_score_pct"] < 80
        assert any("capital" in r.lower() for r in dairy_item["reasons_why_unsuitable"])
        
        # 3. 3-Scenario Financial Simulation
        scenario_res = request_context.post(
            f"{BACKEND_BASE_URL}/v1/income/calculate-scenario",
            data={
                "opportunity_id": "OPP_OYSTER_MUSHROOM_01",
                "custom_budget_inr": 35000.0,
                "available_labour_hours_day": 3.0,
                "available_land_acres": 0.2,
                "water_availability": "perennial_well"
            }
        )
        assert scenario_res.status == 200
        scenario_data = scenario_res.json()
        assert "scenarios" in scenario_data
        scenarios = scenario_data["scenarios"]
        assert "conservative" in scenarios
        assert "base" in scenarios
        assert "optimistic" in scenarios
        assert len(scenarios["base"]["monthly_net_cash_flow_inr"]) == 12
        assert scenarios["optimistic"]["net_annual_profit_inr"] > scenarios["conservative"]["net_annual_profit_inr"]
        
        # 4. Compare opportunities
        compare_res = request_context.post(
            f"{BACKEND_BASE_URL}/v1/income/compare-opportunities",
            data={
                "opportunity_ids": ["OPP_OYSTER_MUSHROOM_01", "OPP_VERMICOMPOST_01", "OPP_APICULTURE_01"],
                "custom_budget_inr": 50000.0
            }
        )
        assert compare_res.status == 200
        compare_data = compare_res.json()
        assert len(compare_data) == 3

def test_frontend_full_browser_experience():
    """Verify that Flutter Web runs cleanly in Chromium, renders canvas, and saves visual proof."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()
        
        # Load web page
        page.goto(FRONTEND_URL, wait_until="networkidle", timeout=25000)
        page.wait_for_timeout(3500)
        
        # Capture home screen
        home_screenshot = os.path.join(SCREENSHOT_DIR, "feature_completion_home.png")
        page.screenshot(path=home_screenshot)
        assert os.path.exists(home_screenshot)
        assert os.path.getsize(home_screenshot) > 1000
        
        # Check title
        assert "Rashkar" in page.title() or "rashkar" in page.content().lower()
        
        context.close()
        browser.close()
