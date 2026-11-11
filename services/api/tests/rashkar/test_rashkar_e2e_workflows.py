"""End-to-end authenticated workflow tests across RASHKAR Context, Heat, Yield, Soil, and Income APIs."""

from datetime import date, datetime, timedelta
import uuid
import pytest

from cropnet.services.api.app.models.soil_and_farm import (
    FarmSoilProfileModel,
    SoilParameterModel,
)
from cropnet.services.api.app.models.soil_reports import (
    SoilMeasurementModel,
    SoilTestReportModel,
)
from cropnet.services.api.app.models.weather import FarmClimateSummaryModel
from cropnet.services.api.app.rashkar.adapters import weather as weather_adapter
from cropnet.services.api.app.rashkar.models import RashkarIncomeScenarioModel
from cropnet.services.api.app.rashkar.timezone import now_ist


def _build_mock_open_meteo_payload() -> dict:
    """Build deterministic IST-aligned Open-Meteo hourly + daily response."""
    anchor = now_ist().replace(minute=0, second=0, microsecond=0)
    start_dt = anchor - timedelta(days=9)
    total_hours = 14 * 24

    h_times, h_temps, h_rh, h_wind, h_sw, h_dni, h_rain = [], [], [], [], [], [], []
    for idx in range(total_hours):
        dt = start_dt + timedelta(hours=idx)
        hr = dt.hour
        h_times.append(dt.strftime("%Y-%m-%dT%H:00"))
        # Peak heat in afternoon IST (13:00-16:00) triggering meaningful WBGT/VPD
        temp = 39.5 if 12 <= hr <= 16 else (26.0 if hr <= 6 or hr >= 21 else 33.5)
        rh = 38.0 if 12 <= hr <= 16 else 68.0
        wind_kmh = 10.8
        sw = 780.0 if 9 <= hr <= 16 else 0.0
        h_temps.append(temp)
        h_rh.append(rh)
        h_wind.append(wind_kmh)
        h_sw.append(sw)
        h_dni.append(sw * 0.8)
        h_rain.append(0.0)

    d_times, d_tmax, d_tmin, d_rain = [], [], [], []
    today = anchor.date()
    for offset in range(-9, 7):
        d = today + timedelta(days=offset)
        d_times.append(d.strftime("%Y-%m-%d"))
        d_tmax.append(40.2 if offset >= 0 else 38.0)
        d_tmin.append(25.0)
        d_rain.append(0.0)

    return {
        "elevation": 538.0,
        "hourly": {
            "time": h_times,
            "temperature_2m": h_temps,
            "relative_humidity_2m": h_rh,
            "wind_speed_10m": h_wind,
            "shortwave_radiation": h_sw,
            "direct_normal_irradiance": h_dni,
            "precipitation": h_rain,
        },
        "daily": {
            "time": d_times,
            "temperature_2m_max": d_tmax,
            "temperature_2m_min": d_tmin,
            "precipitation_sum": d_rain,
        },
    }


@pytest.fixture(autouse=True)
def _mock_open_meteo(monkeypatch):
    weather_adapter.clear_weather_cache()
    payload = _build_mock_open_meteo_payload()
    monkeypatch.setattr(
        weather_adapter,
        "fetch_open_meteo_forecast",
        lambda lat, lon, past_days=10, forecast_days=7: payload,
    )
    yield
    weather_adapter.clear_weather_cache()


def _create_baramati_farm(test_client, user_id: str, name: str = "Malegaon Farm") -> str:
    resp = test_client.post(
        "/api/v1/farms",
        json={
            "name": name,
            "taluka": "Baramati",
            "district": "Pune",
            "state": "Maharashtra",
            "village": "Malegaon",
            "irrigation_type": "drip",
            "water_source": "well",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [74.525, 18.175],
                        [74.535, 18.175],
                        [74.535, 18.185],
                        [74.525, 18.185],
                        [74.525, 18.175],
                    ]
                ],
            },
        },
        headers={"X-Dev-User-Id": user_id},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def test_e2e_crops_overview_pre_sowing_cycle_and_stage_lifecycle(test_client):
    user_id = str(uuid.uuid4())
    headers = {"X-Dev-User-Id": user_id}
    farm_id = _create_baramati_farm(test_client, user_id)

    # 1. Canonical crops + stages catalog
    crops_resp = test_client.get("/api/v1/rashkar/crops?include_stages=true", headers=headers)
    assert crops_resp.status_code == 200
    crops = crops_resp.json()
    assert len(crops) == 38
    soy = next(c for c in crops if c["crop_code"] == "soybean")
    assert soy["is_pioneer_pilot_crop"] is True
    assert len(soy["stages"]) == 4

    # 2. Initial overview has no active crop + live weather preview
    ov_before = test_client.get(f"/api/v1/rashkar/farms/{farm_id}/overview", headers=headers).json()
    assert ov_before["has_active_crop"] is False
    assert ov_before["active_crop_cycle"] is None
    assert ov_before["weather"]["status"] == "OK"
    assert ov_before["weather"]["current_air_temp_c"] is not None

    # 3. Pre-sowing yield preview does NOT persist a crop cycle
    preview = test_client.get(
        f"/api/v1/rashkar/yield/farms/{farm_id}/assessment?crop_code=soybean",
        headers=headers,
    )
    assert preview.status_code == 200
    prev_data = preview.json()
    assert prev_data["status"] == "OK"
    assert prev_data["crop_code"] == "soybean"
    assert prev_data["provenance"]["screening_mode"] == "PRE_SOWING_PREVIEW"

    cycles_still_empty = test_client.get(
        f"/api/v1/rashkar/farms/{farm_id}/crop-cycles", headers=headers
    ).json()
    assert cycles_still_empty == []

    # 4. Register Cotton, then activate Soybean -> Cotton becomes inactive
    sowing_str = (date.today() - timedelta(days=42)).isoformat()
    c1 = test_client.post(
        f"/api/v1/rashkar/farms/{farm_id}/crop-cycle",
        json={"crop_code": "cotton", "sowing_date": sowing_str, "season": "Kharif"},
        headers=headers,
    )
    assert c1.status_code == 201
    c1_data = c1.json()
    assert c1_data["current_stage_code"] is None
    assert c1_data["is_active"] is True

    c2 = test_client.post(
        f"/api/v1/rashkar/farms/{farm_id}/crop-cycle",
        json={"crop_code": "soybean", "sowing_date": sowing_str, "season": "Kharif", "planted_area_acres": 2.0},
        headers=headers,
    )
    assert c2.status_code == 201
    c2_id = c2.json()["id"]

    all_cycles = test_client.get(f"/api/v1/rashkar/farms/{farm_id}/crop-cycles", headers=headers).json()
    assert len(all_cycles) == 2
    assert sum(1 for c in all_cycles if c["is_active"]) == 1
    assert next(c for c in all_cycles if c["is_active"])["id"] == c2_id

    # 5. Confirm phenological stage & patch variety
    confirm = test_client.post(
        f"/api/v1/rashkar/farms/{farm_id}/crop-cycle/confirm-stage",
        json={"stage_code": "flowering"},
        headers=headers,
    )
    assert confirm.status_code == 200
    assert confirm.json()["current_stage_code"] == "flowering"
    assert confirm.json()["stage_source"] == "farmer_confirmed"
    assert confirm.json()["stage_confidence"] == 1.0

    patched = test_client.patch(
        f"/api/v1/rashkar/farms/{farm_id}/crop-cycle/{c2_id}",
        json={"variety_name": "JS-335"},
        headers=headers,
    )
    assert patched.status_code == 200
    assert patched.json()["variety_name"] == "JS-335"


def test_e2e_worker_heat_crop_heat_and_history_audit(test_client):
    user_id = str(uuid.uuid4())
    headers = {"X-Dev-User-Id": user_id}
    farm_id = _create_baramati_farm(test_client, user_id)

    test_client.post(
        f"/api/v1/rashkar/farms/{farm_id}/crop-cycle",
        json={
            "crop_code": "soybean",
            "sowing_date": (date.today() - timedelta(days=45)).isoformat(),
            "current_stage_code": "flowering",
        },
        headers=headers,
    )

    # Worker heat via farm_id (coordinates defaulted from owned farm)
    wh_resp = test_client.post(
        "/api/v1/rashkar/worker-heat/assess",
        json={
            "farm_id": farm_id,
            "workload_category": "heavy",
            "clothing_type": "standard_work_clothes",
            "is_acclimatised": True,
            "sun_exposure": "direct_sun",
        },
        headers=headers,
    )
    assert wh_resp.status_code == 200
    wh_data = wh_resp.json()
    assert wh_data["status"] == "OK"
    assert wh_data["current_wbgt_estimated_c"] is not None
    assert wh_data["audit_logged"] is True
    assert len(wh_data["hourly_projections"]) > 0

    wh_hist = test_client.get(
        f"/api/v1/rashkar/worker-heat/farms/{farm_id}/history", headers=headers
    )
    assert wh_hist.status_code == 200
    assert len(wh_hist.json()) == 1

    # Coordinate-only worker heat works cleanly without farm_id
    wh_coord = test_client.post(
        "/api/v1/rashkar/worker-heat/assess",
        json={"latitude": 18.18, "longitude": 74.53, "taluka": "Baramati"},
        headers=headers,
    )
    assert wh_coord.status_code == 200
    assert wh_coord.json()["status"] == "OK"

    # Crop heat assessment on owned farm
    ch_resp = test_client.post(
        "/api/v1/rashkar/crop-heat/assess",
        json={"farm_id": farm_id},
        headers=headers,
    )
    assert ch_resp.status_code == 200
    ch_data = ch_resp.json()
    assert ch_data["status"] == "OK"
    assert ch_data["crop_code"] == "soybean"
    assert ch_data["growth_stage_code"] == "R1_FLOWERING"
    assert ch_data["audit_logged"] is True
    assert len(ch_data["daily_outlook"]) > 0

    ch_hist = test_client.get(
        f"/api/v1/rashkar/crop-heat/farms/{farm_id}/history", headers=headers
    )
    assert ch_hist.status_code == 200
    assert len(ch_hist.json()) == 1
    assert ch_hist.json()[0]["crop_code"] == "soybean"


def test_e2e_soil_hierarchy_lab_over_map_over_unavailable_and_yield(
    test_client, isolated_test_session
):
    user_id = str(uuid.uuid4())
    headers = {"X-Dev-User-Id": user_id}
    farm_id = _create_baramati_farm(test_client, user_id)

    test_client.post(
        f"/api/v1/rashkar/farms/{farm_id}/crop-cycle",
        json={
            "crop_code": "soybean",
            "sowing_date": (date.today() - timedelta(days=40)).isoformat(),
            "current_stage_code": "flowering",
        },
        headers=headers,
    )

    # Tier 1: No soil data on file -> preserves None without synthesis
    yld_empty = test_client.get(
        f"/api/v1/rashkar/yield/farms/{farm_id}/assessment", headers=headers
    ).json()
    assert yld_empty["status"] == "OK"
    assert yld_empty["suitability_analysis"]["soil_ph"] is None
    assert "unavailable" in yld_empty["suitability_analysis"]["data_provenance"].lower()

    # Tier 2: CropNet Map-Derived Soil Profile + Climate Summary (with synthetic & unavailable rows filtered)
    profile = FarmSoilProfileModel(
        id=str(uuid.uuid4()),
        farm_id=farm_id,
        version=1,
        is_map_derived=True,
        disclaimer="ISRIC SoilGrids v2.0 map-derived estimate.",
    )
    isolated_test_session.add(profile)
    isolated_test_session.flush()
    isolated_test_session.add_all(
        [
            SoilParameterModel(
                id=str(uuid.uuid4()),
                profile_id=profile.id,
                parameter_key="ph",
                display_name="Soil pH",
                value=6.4,
                unit="pH",
                source="isric_soilgrids",
                dataset_version="2.0",
                depth_interval="0-30cm",
                spatial_resolution="250m",
                verification_status="MAP_ESTIMATE",
                availability_status="AVAILABLE",
            ),
            SoilParameterModel(
                id=str(uuid.uuid4()),
                profile_id=profile.id,
                parameter_key="soc",
                display_name="Organic Carbon",
                value=0.62,
                unit="%",
                source="isric_soilgrids",
                dataset_version="2.0",
                depth_interval="0-30cm",
                spatial_resolution="250m",
                verification_status="MAP_ESTIMATE",
                availability_status="AVAILABLE",
            ),
            SoilParameterModel(
                id=str(uuid.uuid4()),
                profile_id=profile.id,
                parameter_key="clay",
                display_name="Clay",
                value=45.0,
                unit="%",
                source="isric_soilgrids",
                dataset_version="2.0",
                depth_interval="0-30cm",
                spatial_resolution="250m",
                verification_status="MAP_ESTIMATE",
                availability_status="AVAILABLE",
            ),
            SoilParameterModel(
                id=str(uuid.uuid4()),
                profile_id=profile.id,
                parameter_key="sand",
                display_name="Sand",
                value=22.0,
                unit="%",
                source="isric_soilgrids",
                dataset_version="2.0",
                depth_interval="0-30cm",
                spatial_resolution="250m",
                verification_status="MAP_ESTIMATE",
                availability_status="AVAILABLE",
            ),
            SoilParameterModel(
                id=str(uuid.uuid4()),
                profile_id=profile.id,
                parameter_key="silt",
                display_name="Silt",
                value=33.0,
                unit="%",
                source="isric_soilgrids",
                dataset_version="2.0",
                depth_interval="0-30cm",
                spatial_resolution="250m",
                verification_status="MAP_ESTIMATE",
                availability_status="AVAILABLE",
            ),
            SoilParameterModel(
                id=str(uuid.uuid4()),
                profile_id=profile.id,
                parameter_key="cec",
                display_name="Fake Synthetic CEC",
                value=99.9,
                unit="cmol/kg",
                source="synthetic_fallback",
                dataset_version="0.0",
                depth_interval="0-30cm",
                spatial_resolution="250m",
                verification_status="SYNTHETIC_IGNORED",
                availability_status="AVAILABLE",
            ),
        ]
    )
    isolated_test_session.add(
        FarmClimateSummaryModel(
            id=str(uuid.uuid4()),
            farm_id=farm_id,
            source="NASA POWER",
            annual_rainfall_mm=710.0,
            monsoon_rainfall_mm=580.0,
            monsoon_share_percent=81.7,
            mean_temperature_c=26.5,
            min_temperature_c=14.0,
            max_temperature_c=40.5,
            monthly_rainfall_json={},
            monthly_temperature_json={},
            wet_season_months_json=[6, 7, 8, 9],
            dry_season_months_json=[12, 1, 2, 3],
        )
    )
    isolated_test_session.commit()

    ov_map = test_client.get(f"/api/v1/rashkar/farms/{farm_id}/overview", headers=headers).json()
    assert ov_map["soil"]["soil_ph"] == 6.4
    assert ov_map["soil"]["organic_carbon_pct"] == 0.62
    assert ov_map["soil"]["cation_exchange_capacity"] is None  # synthetic parameter ignored
    assert ov_map["soil"]["climate_normal_rainfall_mm"] == 710.0
    assert ov_map["soil"]["is_lab_measured"] is False

    # Tier 3: Confirmed Laboratory Soil Report overrides map pH while keeping map texture supplement
    report = SoilTestReportModel(
        id=str(uuid.uuid4()),
        user_id=user_id,
        farm_id=farm_id,
        original_filename="kvk_report.pdf",
        storage_path="/tmp/kvk_report.pdf",
        upload_timestamp=datetime.utcnow(),
        laboratory_name="Baramati KVK Soil Lab",
        extraction_status="EXTRACTED",
        review_status="CONFIRMED",
    )
    isolated_test_session.add(report)
    isolated_test_session.flush()
    isolated_test_session.add(
        SoilMeasurementModel(
            id=str(uuid.uuid4()),
            report_id=report.id,
            farm_id=farm_id,
            parameter_key="ph",
            original_parameter_name="Soil pH (1:2.5)",
            original_value=7.0,
            original_unit="pH",
            normalized_value=7.0,
            farmer_corrected_value=7.1,
            verification_status="FARMER_CORRECTED",
        )
    )
    isolated_test_session.commit()

    yld_lab = test_client.get(
        f"/api/v1/rashkar/yield/farms/{farm_id}/assessment", headers=headers
    ).json()
    assert yld_lab["suitability_analysis"]["soil_ph"] == 7.1
    assert "Baramati KVK Soil Lab" in yld_lab["suitability_analysis"]["data_provenance"]
    assert yld_lab["audit_logged"] is True

    # Verify baseline & yield history endpoints
    base_resp = test_client.get(
        "/api/v1/rashkar/yield/baseline?district=Pune&crop_code=soybean", headers=headers
    )
    assert base_resp.status_code == 200
    assert base_resp.json()["district"] == "Pune"
    assert base_resp.json()["sample_seasons_count"] > 0

    hist = test_client.get(f"/api/v1/rashkar/yield/farms/{farm_id}/history", headers=headers)
    assert hist.status_code == 200
    assert len(hist.json()) == 2


def test_e2e_income_profile_discover_scenario_compare_and_plans(
    test_client, isolated_test_session
):
    user_id = str(uuid.uuid4())
    headers = {"X-Dev-User-Id": user_id}
    farm_id = _create_baramati_farm(test_client, user_id)

    opps = test_client.get("/api/v1/rashkar/income/opportunities", headers=headers).json()
    assert len(opps) >= 5
    opp_ids = [o["opportunity_id"] for o in opps[:2]]

    detail = test_client.get(
        f"/api/v1/rashkar/income/opportunities/{opp_ids[0]}", headers=headers
    )
    assert detail.status_code == 200
    assert detail.json()["opportunity_id"] == opp_ids[0]

    # Profile PUT -> GET round-trip including Part A personal context fields
    prof_payload = {
        "available_investment_inr": 25000.0,
        "monthly_operating_budget_inr": 3000.0,
        "water_availability": "reliable_year_round",
        "family_labor_hours_day": 3.5,
        "age_range": "46-55",
        "work_preference": "manage_supervise",
        "payback_horizon": "6_to_12_months",
        "family_management_role": "multiple_family",
        "current_crop_code": "soybean",
        "current_crop_stage": "flowering",
    }
    put_prof = test_client.put(
        f"/api/v1/rashkar/income/farms/{farm_id}/profile",
        json=prof_payload,
        headers=headers,
    )
    assert put_prof.status_code == 200
    got_prof = test_client.get(
        f"/api/v1/rashkar/income/farms/{farm_id}/profile", headers=headers
    ).json()
    assert got_prof["age_range"] == "46-55"
    assert got_prof["work_preference"] == "manage_supervise"
    assert got_prof["payback_horizon"] == "6_to_12_months"
    assert got_prof["family_management_role"] == "multiple_family"
    assert got_prof["current_crop_code"] == "soybean"

    # Discover matched opportunities
    disc = test_client.post(
        f"/api/v1/rashkar/income/farms/{farm_id}/discover", headers=headers
    )
    assert disc.status_code == 200
    assert len(disc.json()) >= 1

    # Farm-scoped scenario persists to rashkar_income_scenarios
    scen = test_client.post(
        f"/api/v1/rashkar/income/farms/{farm_id}/calculate-scenario",
        json={"opportunity_id": opp_ids[0], "custom_budget_inr": 15000.0},
        headers=headers,
    )
    assert scen.status_code == 200
    scen_id = scen.json()["scenario_id"]
    persisted = (
        isolated_test_session.query(RashkarIncomeScenarioModel)
        .filter(RashkarIncomeScenarioModel.scenario_id == scen_id)
        .first()
    )
    assert persisted is not None
    assert persisted.farm_id == farm_id

    # Stateless scenario + side-by-side comparison
    stateless = test_client.post(
        "/api/v1/rashkar/income/calculate-scenario",
        json={"opportunity_id": opp_ids[0], "custom_budget_inr": 15000.0},
        headers=headers,
    )
    assert stateless.status_code == 200

    comp = test_client.post(
        "/api/v1/rashkar/income/compare-opportunities",
        json={"opportunity_ids": opp_ids, "custom_budget_inr": 25000.0},
        headers=headers,
    )
    assert comp.status_code == 200
    assert len(comp.json()) == 2

    # Save -> list -> overview count -> delete -> list empty
    saved = test_client.post(
        f"/api/v1/rashkar/income/farms/{farm_id}/plans",
        json={
            "opportunity_id": opp_ids[0],
            "chosen_budget_inr": 15000.0,
            "notes": "Start next month after soybean harvest",
        },
        headers=headers,
    )
    assert saved.status_code == 201
    plan_id = saved.json()["plan_id"]
    assert saved.json()["farmer_id"] == user_id

    plans_list = test_client.get(
        f"/api/v1/rashkar/income/farms/{farm_id}/plans", headers=headers
    ).json()
    assert len(plans_list) == 1
    assert plans_list[0]["plan_id"] == plan_id

    ov_after = test_client.get(f"/api/v1/rashkar/farms/{farm_id}/overview", headers=headers).json()
    assert ov_after["saved_income_plans_count"] == 1

    deleted = test_client.delete(
        f"/api/v1/rashkar/income/farms/{farm_id}/plans/{plan_id}", headers=headers
    )
    assert deleted.status_code == 200
    assert (
        test_client.get(
            f"/api/v1/rashkar/income/farms/{farm_id}/plans", headers=headers
        ).json()
        == []
    )
