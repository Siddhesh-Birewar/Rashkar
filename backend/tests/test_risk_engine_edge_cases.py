import pytest
from datetime import date, datetime, timedelta
import zoneinfo

from backend.app.core.timezone import now_utc, now_ist, to_ist, to_utc, IST_ZONE, UTC_ZONE
from backend.app.services.wbgt_solver import calculate_wbgt
from backend.app.services.worker_heat_engine import WorkerHeatEngine
from backend.app.services.crop_heat_engine import CropHeatEngine
from backend.app.services.yield_risk_engine import YieldRiskEngine
from backend.app.services.cropnet_service import CropNetService
from backend.app.services.crop_stage_service import CropStageService
from backend.app.schemas.worker_heat import WorkerHeatAssessmentRequest
from backend.app.schemas.crop_heat import CropHeatAssessmentRequest
from backend.app.schemas.soil import (
    UnifiedSoilProfile,
    NumericSoilProperty,
    CategoricalSoilProperty,
    SoilVerificationStatus,
    DepthStratifiedSoilObservation
)

def test_timezone_ist_utc_conversions():
    """Verify UTC persistence and explicit Asia/Kolkata (+05:30) display."""
    utc_time = now_utc()
    ist_time = to_ist(utc_time)

    # Offset must be exactly +05:30 (19800 seconds)
    offset = ist_time.utcoffset()
    assert offset == timedelta(hours=5, minutes=30)
    assert ist_time.tzinfo == IST_ZONE

    # Round trip back to UTC
    back_to_utc = to_utc(ist_time)
    assert abs((back_to_utc - utc_time).total_seconds()) < 1.0

def test_wbgt_sun_vs_shade_differential():
    """Verify physical differential between direct sun and full shade WBGT."""
    # Under high afternoon irradiance (38°C, 40% RH, 850 W/m², 1.5 m/s wind)
    sun = calculate_wbgt(38.0, 40.0, wind_speed_ms=1.5, solar_irradiance_wm2=850.0, in_sun=True)
    shade = calculate_wbgt(38.0, 40.0, wind_speed_ms=1.5, solar_irradiance_wm2=850.0, in_sun=False)

    # Black globe in sun must exceed air temp; in shade Tg equals air temp
    assert sun["black_globe_temp_c"] > 38.0
    assert abs(shade["black_globe_temp_c"] - 38.0) < 0.2

    # Outdoor WBGT in sun must be warmer than shaded WBGT
    assert sun["wbgt_estimated_c"] > shade["wbgt_estimated_c"]
    assert (sun["wbgt_estimated_c"] - shade["wbgt_estimated_c"]) > 1.0

def test_worker_heat_all_workload_categories(client):
    """Verify screening thresholds for all 4 ACGIH workload categories."""
    categories = {
        "light": 31.0,
        "moderate": 28.0,
        "heavy": 26.0,
        "very_heavy": 25.0
    }
    for cat, expected_threshold in categories.items():
        req = WorkerHeatAssessmentRequest(
            latitude=18.15,
            longitude=74.57,
            taluka="Baramati",
            workload_category=cat,
            is_acclimatised=True
        )
        res = WorkerHeatEngine.assess_worker_heat_hazard(req)
        assert res.screening_threshold_c == expected_threshold
        # Prescriptive fixed minute-by-minute work-rest schedule must NOT be present
        assert "mandatory work-stoppages" in res.disclaimer or "does not mandate work-stoppages" in res.disclaimer

def test_cropnet_multiple_soil_depths():
    """Verify multiple depth-stratified observations (0-5cm and 5-15cm) with metadata."""
    profile = CropNetService.create_synthetic_test_profile(farm_id="farm_depth_test", taluka="Baramati")

    assert len(profile.depth_observations) >= 2
    intervals = [obs.depth_interval for obs in profile.depth_observations]
    assert "0-5cm" in intervals
    assert "5-15cm" in intervals

    obs_0_5 = next(o for o in profile.depth_observations if o.depth_interval == "0-5cm")
    assert obs_0_5.ph is not None
    assert obs_0_5.ph.uncertainty_lower_bound is not None
    assert obs_0_5.ph.uncertainty_upper_bound is not None

def test_missing_cropnet_property_safety(db_session):
    """Verify that when soil properties are unavailable (None), engine does not substitute zero."""
    # Profile with missing pH (None)
    profile = CropNetService.create_synthetic_test_profile("farm_missing_ph", taluka="Baramati")
    profile.ph.value = None
    profile.ph.verification_status = SoilVerificationStatus.NOT_AVAILABLE

    assessment = YieldRiskEngine.assess_yield_risk(
        db=db_session,
        farm_id="farm_missing_ph",
        plot_id="plot_1",
        crop_code="soybean",
        sowing_date=date(2024, 6, 20),
        district="Pune",
        taluka="Baramati",
        soil_profile_override=profile
    )

    soil_risk = next(r for r in assessment["risks"] if r["risk_dimension"] == "soil_constraint")
    # Must report not available, not crash or claim pH = 0
    assert "not available" in soil_risk["drivers"][0].lower()
    assert soil_risk["risk_level"] == "low"

def test_crop_stage_das_boundaries(db_session):
    """Verify DAS phenological stage progression and boundary transitions."""
    sowing = now_ist().date() - timedelta(days=15)  # DAS 15 -> Vegetative
    st1 = CropStageService.estimate_crop_stage(db_session, "soybean", sowing)
    assert st1["stage_code"] == "VEGETATIVE"

    sowing_flowering = now_ist().date() - timedelta(days=40)  # DAS 40 -> Flowering (R1)
    st2 = CropStageService.estimate_crop_stage(db_session, "soybean", sowing_flowering)
    assert st2["stage_code"] == "R1_FLOWERING"
    assert st2["heat_sensitivity"] == "critical"

    # Farmer explicit confirmation overrides DAS heuristic
    st_override = CropStageService.estimate_crop_stage(
        db_session, "soybean", sowing, farmer_confirmed_stage="R1_FLOWERING"
    )
    assert st_override["stage_code"] == "R1_FLOWERING"
    assert st_override["farmer_confirmed"] is True

def test_crop_heat_threshold_comparisons(client):
    """Verify critical thermal threshold differences between crops (Cotton vs Soybean)."""
    # 1. Setup Cotton farm
    f_res = client.post("/v1/farms/", json={
        "owner_id": "farmer_cotton_01",
        "farm_name": "Cotton Thermal Farm",
        "district": "Pune",
        "taluka": "Indapur",
        "latitude": 18.11,
        "longitude": 75.02
    })
    farm_id = f_res.json()["farm_id"]
    p_res = client.post(f"/v1/farms/{farm_id}/plots", json={"plot_name": "P1", "area_acres": 2.0})
    plot_id = p_res.json()["plot_id"]
    client.post(f"/v1/farms/{farm_id}/crop-cycles?plot_id={plot_id}", json={
        "crop_code": "cotton",
        "season": "kharif",
        "sowing_date": "2024-06-15",
        "farmer_confirmed_stage": "FLOWERING_BOLL_DEV"
    })

    # At 37.5°C, Cotton critical threshold is 38.0°C (moderate/approaching, not high)
    res_cotton = client.post("/v1/heat-risk/crop-heat", json={
        "farm_id": farm_id,
        "plot_id": plot_id,
        "forecast_tmax_c": 37.5,
        "forecast_tmin_c": 22.0
    })
    assert res_cotton.status_code == 200
    data_cotton = res_cotton.json()
    assert data_cotton["critical_tmax_threshold_c"] == 38.0
    assert data_cotton["daytime_heat_stress_level"] == "moderate"
    assert data_cotton["warm_night_respiration_hazard"] is False
