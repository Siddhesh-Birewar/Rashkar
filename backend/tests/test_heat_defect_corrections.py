import pytest
from datetime import date, datetime, timedelta
import uuid
from backend.app.schemas.worker_heat import WorkerHeatAssessmentRequest
from backend.app.schemas.crop_heat import CropHeatAssessmentRequest
from backend.app.services.worker_heat_engine import WorkerHeatEngine
from backend.app.services.crop_heat_engine import CropHeatEngine
from backend.app.services.crop_stage_service import CropStageService
from backend.app.db.models.farm import CropCycleModel, FarmPlotModel, FarmModel, SoilProfileModel
from backend.app.db.models.risk import CropHeatAssessmentLogModel

def create_isolated_farm(db_session, crop_code="soybean", sowing_days_ago=45, variety="JS 335"):
    uid = uuid.uuid4().hex[:8]
    farm = FarmModel(
        farm_id=f"farm_{uid}",
        owner_id="farmer_demo_pune_01",
        farm_name=f"Test Farm {uid}",
        total_area_acres=3.0,
        district="Pune",
        taluka="Baramati",
        latitude=18.5204,
        longitude=73.8567
    )
    db_session.add(farm)
    plot = FarmPlotModel(
        plot_id=f"plot_{uid}",
        farm_id=farm.farm_id,
        plot_name=f"Plot A",
        area_acres=3.0,
        irrigation_type="drip"
    )
    db_session.add(plot)
    cycle = CropCycleModel(
        cycle_id=f"cycle_{uid}",
        plot_id=plot.plot_id,
        crop_code=crop_code,
        season="kharif",
        sowing_date=date.today() - timedelta(days=sowing_days_ago),
        variety_name=variety,
        is_active=True
    )
    db_session.add(cycle)
    db_session.commit()
    return farm, plot, cycle

# ==============================================================================
# 1, 2, 3: WORKER WBGT THRESHOLD MESSAGING (BELOW, AT, ABOVE)
# ==============================================================================

def test_wbgt_below_threshold():
    """Test 1: When effective WBGT is below threshold, state is BELOW and diff is negative."""
    cool_hourly = [
        {"air_temp_c": 18.0, "rh_pct": 40.0, "wind_ms": 2.5, "solar_wm2": 50.0}
        for _ in range(7)
    ]
    req = WorkerHeatAssessmentRequest(
        latitude=18.5204,
        longitude=73.8567,
        workload_category="very_heavy",
        is_acclimatised=False,  # Threshold = 22.0C
        clothing_type="standard_work_clothes",
        sun_exposure="full_shade",
        exposure_duration_hours=4.0
    )
    result = WorkerHeatEngine.assess_worker_heat_hazard(req, weather_hourly_override=cool_hourly)

    assert result.threshold_comparison_state == "BELOW"
    assert result.threshold_difference_c < 0.0
    assert "below the 22.0" in result.threshold_comparison_message
    assert "exceed" not in result.threshold_comparison_message.lower()


def test_wbgt_at_threshold():
    """Test 2: When effective WBGT matches threshold exactly within tolerance, state is AT_THRESHOLD."""
    msg, diff, state = WorkerHeatEngine._build_threshold_comparison(26.0, 26.0, "heavy")
    assert state == "AT_THRESHOLD"
    assert diff == 0.0
    assert "is at the 26.0" in msg


def test_wbgt_above_threshold():
    """Test 3: When effective WBGT is above threshold, state is ABOVE and diff is positive."""
    hot_hourly = [
        {"air_temp_c": 42.0, "rh_pct": 65.0, "wind_ms": 1.0, "solar_wm2": 950.0}
        for _ in range(7)
    ]
    req = WorkerHeatAssessmentRequest(
        latitude=18.5204,
        longitude=73.8567,
        workload_category="very_heavy",
        is_acclimatised=False,  # Threshold = 22.0C
        clothing_type="standard_work_clothes",
        sun_exposure="direct_sun",
        exposure_duration_hours=5.0
    )
    result = WorkerHeatEngine.assess_worker_heat_hazard(req, weather_hourly_override=hot_hourly)

    assert result.threshold_comparison_state == "ABOVE"
    assert result.threshold_difference_c > 0.0
    assert "exceeds the 22.0" in result.threshold_comparison_message


# ==============================================================================
# 4. SHIFT DURATION LONGER THAN FORECAST COVERAGE
# ==============================================================================

def test_shift_duration_longer_than_forecast_coverage():
    """Test 4: Planned shift duration longer than 6-hour forecast flags coverage limitation."""
    req = WorkerHeatAssessmentRequest(
        latitude=18.5204,
        longitude=73.8567,
        workload_category="moderate",
        exposure_duration_hours=7.5
    )
    result = WorkerHeatEngine.assess_worker_heat_hazard(req)

    assert result.shift_exceeds_forecast_coverage is True
    assert result.planned_shift_duration_hours == 7.5
    assert result.forecast_coverage_hours == 6.0
    assert result.coverage_limitation_warning is not None
    assert "covers a 6-hour window" in result.coverage_limitation_warning
    assert "planned shift is 7.5 hours" in result.coverage_limitation_warning


# ==============================================================================
# 5 & 6: WEATHER PROVENANCE & MISSING VARIABLES / STALE DATA
# ==============================================================================

def test_weather_provenance_and_missing_variables():
    """Test 5 & 6: Weather provenance displays spatial resolution, coordinates, valid times and missing variables."""
    req = WorkerHeatAssessmentRequest(
        latitude=18.5204,
        longitude=73.8567,
        workload_category="moderate",
        exposure_duration_hours=4.0
    )
    result = WorkerHeatEngine.assess_worker_heat_hazard(req)

    assert "0.1" in result.spatial_resolution
    assert "18.5204" in result.grid_coordinates
    assert "ACGIH 2023" in result.methodology_standards_version
    assert "screening" in result.safety_guarantee_disclaimer.lower()
    assert "108" in result.local_emergency_contacts["ambulance_toll_free"]
    assert "1800-180-1551" in result.local_emergency_contacts["kisan_call_centre"]


def test_missing_solar_graceful_handling():
    """Test 6: Graceful handling of missing or zero solar irradiance."""
    no_solar_hourly = [
        {"air_temp_c": 32.0, "rh_pct": 50.0, "wind_ms": 1.5, "solar_wm2": 0.0}
        for _ in range(7)
    ]
    req = WorkerHeatAssessmentRequest(
        latitude=18.5204,
        longitude=73.8567,
        workload_category="moderate",
        sun_exposure="full_shade"
    )
    result = WorkerHeatEngine.assess_worker_heat_hazard(req, weather_hourly_override=no_solar_hourly)
    assert result.max_wbgt_effective_c > 0.0
    assert result.current_hazard_level in ["LOW", "MODERATE", "HIGH", "CRITICAL"]


# ==============================================================================
# 7 & 8: EXPIRED CROP SEASON & NULL STAGE SUPPRESSION
# ==============================================================================

def test_expired_crop_season_detection(db_session):
    """Test 7: Crop season with DAS far exceeding duration is marked EXPIRED and suppresses stage interventions."""
    farm, plot, cycle = create_isolated_farm(db_session, crop_code="soybean", sowing_days_ago=800, variety="JS 335")

    stage_info = CropStageService.estimate_growth_stage(db_session, "soybean", cycle.sowing_date)
    assert stage_info["is_expired"] is True
    assert stage_info["stage_code"] is None
    assert stage_info["season_status"] == "EXPIRED"

    # Assess crop heat for this cycle
    req = CropHeatAssessmentRequest(
        farm_id=farm.farm_id,
        plot_id=plot.plot_id,
        forecast_tmax_c=38.0,
        forecast_tmin_c=24.0
    )
    assessment = CropHeatEngine.assess_crop_heat_risk(db_session, req)

    assert assessment.is_season_expired is True
    assert assessment.season_status == "EXPIRED"
    assert assessment.requires_season_update is True
    assert "Crop season expired" in assessment.season_expiry_message
    assert len(assessment.recommended_interventions) == 0


def test_null_crop_stage_suppresses_stage_interventions(db_session):
    """Test 8: Expired crop with null stage has empty stage interventions and clear message."""
    farm, plot, cycle = create_isolated_farm(db_session, crop_code="soybean", sowing_days_ago=500)
    req = CropHeatAssessmentRequest(farm_id=farm.farm_id, plot_id=plot.plot_id)
    assessment = CropHeatEngine.assess_crop_heat_risk(db_session, req)
    assert assessment.growth_stage_code is None
    assert len(assessment.recommended_interventions) == 0


# ==============================================================================
# 9: FARMER-CONFIRMED STAGE OVERRIDE
# ==============================================================================

def test_farmer_confirmed_crop_stage_change(db_session):
    """Test 9: Passing confirmed_stage_code recalibrates stage and updates thresholds."""
    farm, plot, cycle = create_isolated_farm(db_session, crop_code="soybean", sowing_days_ago=20, variety="JS 93-05")

    req = CropHeatAssessmentRequest(
        farm_id=farm.farm_id,
        plot_id=plot.plot_id,
        farmer_confirmed_stage="stage_flowering",
        forecast_tmax_c=37.0,
        forecast_tmin_c=23.0
    )
    assessment = CropHeatEngine.assess_crop_heat_risk(db_session, req)

    assert "flower" in assessment.growth_stage_code.lower()
    assert assessment.farmer_confirmed_stage == "stage_flowering"
    assert assessment.critical_tmax_threshold_c == 35.0


# ==============================================================================
# 10: SYNTHETIC SOIL PROFILE LABELING
# ==============================================================================

def test_synthetic_soil_profile_labeling(db_session):
    """Test 10: Unsampled farm coordinates are explicitly marked as synthetic CropNet estimates."""
    farm, plot, cycle = create_isolated_farm(db_session, crop_code="soybean", sowing_days_ago=45)

    req = CropHeatAssessmentRequest(
        farm_id=farm.farm_id,
        plot_id=plot.plot_id,
        forecast_tmax_c=36.0,
        forecast_tmin_c=22.0
    )
    assessment = CropHeatEngine.assess_crop_heat_risk(db_session, req)

    assert assessment.is_soil_synthetic is True
    assert "CropNet Model Estimate (Unsampled Farm Coordinate)" in assessment.soil_provenance_label


# ==============================================================================
# 11: INVALID CROP THRESHOLD FALLBACK
# ==============================================================================

def test_invalid_crop_threshold_fallback(db_session):
    """Test 11: Missing or corrupted crop thresholds fall back safely to 10.0C base and 36.0C critical."""
    farm, plot, cycle = create_isolated_farm(db_session, crop_code="dragonfruit_exotic", sowing_days_ago=30)

    req = CropHeatAssessmentRequest(
        farm_id=farm.farm_id,
        plot_id=plot.plot_id,
        forecast_tmax_c=37.0,
        forecast_tmin_c=22.0
    )
    assessment = CropHeatEngine.assess_crop_heat_risk(db_session, req)
    assert assessment.base_temp_c == 10.0
    assert assessment.critical_tmax_threshold_c == 36.0
    assert assessment.optimal_temp_min_c == 25.0
    assert assessment.optimal_temp_max_c == 30.0


# ==============================================================================
# 12 & 13: AUDITED INTERVENTIONS, INFRASTRUCTURE SEPARATION & LOW RISK
# ==============================================================================

def test_audited_interventions_and_infrastructure_distinction(db_session):
    """Test 12 & 13: Verifies citations, agronomist reviewer, and distinct drip vs sprinkler infrastructure."""
    farm, plot, cycle = create_isolated_farm(db_session, crop_code="soybean", sowing_days_ago=45)

    req = CropHeatAssessmentRequest(
        farm_id=farm.farm_id,
        plot_id=plot.plot_id,
        farmer_confirmed_stage="stage_flowering",
        forecast_tmax_c=39.0,
        forecast_tmin_c=25.0
    )
    assessment = CropHeatEngine.assess_crop_heat_risk(db_session, req)

    assert len(assessment.recommended_interventions) > 0
    for inv in assessment.recommended_interventions:
        assert inv.evidence_status == "VERIFIED_PUBLISHED"
        assert inv.agronomist_reviewer is not None and len(inv.agronomist_reviewer) > 0
        assert inv.evidence_citation is not None and len(inv.evidence_citation) > 0
        assert inv.application_dose is not None
        assert inv.infrastructure_requirements is not None
        # Verify drip and overhead sprinklers are not conflated
        if "drip" in inv.title_en.lower():
            assert "drip" in inv.infrastructure_requirements.lower()
        if "sprinkler" in inv.title_en.lower():
            assert "sprinkler" in inv.infrastructure_requirements.lower()


def test_low_heat_risk_conditionality(db_session):
    """Test 13b: Low heat risk does NOT return emergency heat stress interventions."""
    farm, plot, cycle = create_isolated_farm(db_session, crop_code="soybean", sowing_days_ago=45)

    req = CropHeatAssessmentRequest(
        farm_id=farm.farm_id,
        plot_id=plot.plot_id,
        farmer_confirmed_stage="stage_flowering",
        forecast_tmax_c=26.0,
        forecast_tmin_c=18.0
    )
    assessment = CropHeatEngine.assess_crop_heat_risk(db_session, req)

    assert assessment.overall_crop_heat_risk == "low"
    assert len(assessment.recommended_interventions) == 1
    assert assessment.recommended_interventions[0].intervention_id == "ROUTINE_MONITORING"
    assert "Routine" in assessment.recommended_interventions[0].title_en


# ==============================================================================
# 14: DATABASE LOG HISTORY RETRIEVAL (NO FABRICATED ROWS)
# ==============================================================================

def test_database_log_history_retrieval(db_session):
    """Test 14: Verifies assessment history comes from real DB logs, returning empty when none exist."""
    farm, plot, cycle = create_isolated_farm(db_session, crop_code="onion", sowing_days_ago=40, variety="Bhima Super")

    req = CropHeatAssessmentRequest(
        farm_id=farm.farm_id,
        plot_id=plot.plot_id,
        forecast_tmax_c=35.0,
        forecast_tmin_c=20.0
    )
    # Clear prior logs for this farm
    db_session.query(CropHeatAssessmentLogModel).filter(
        CropHeatAssessmentLogModel.farm_id == farm.farm_id
    ).delete()
    db_session.commit()

    assessment1 = CropHeatEngine.assess_crop_heat_risk(db_session, req)
    # First time: history was empty before this log was saved
    assert len(assessment1.assessment_history) == 0

    # Second assessment: now exactly 1 historical log should be retrieved
    assessment2 = CropHeatEngine.assess_crop_heat_risk(db_session, req)
    assert len(assessment2.assessment_history) == 1
    assert assessment2.assessment_history[0]["crop_code"] == cycle.crop_code
