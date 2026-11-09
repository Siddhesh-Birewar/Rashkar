import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.db.session import get_db, SessionLocal
from backend.app.db.models.farm import FarmModel, FarmPlotModel, CropCycleModel
from backend.app.services.crop_heat_engine import CROP_SPECIES_PHYSIOLOGY, CropHeatEngine
from backend.app.schemas.crop_heat import CropHeatAssessmentRequest

client = TestClient(app)

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_backend_stage_definitions_for_all_supported_crops():
    """Verify all supported crops have complete, non-null stage definitions with valid thresholds."""
    assert len(CROP_SPECIES_PHYSIOLOGY) >= 4
    for crop_code, spec in CROP_SPECIES_PHYSIOLOGY.items():
        stages = spec.get("stages", [])
        assert len(stages) >= 3, f"Crop {crop_code} has insufficient growth stages ({len(stages)})"
        
        for s in stages:
            code = s.get("stage_code")
            name = s.get("stage_name")
            name_en = s.get("stage_name_en")
            crit_tmax = s.get("crit_tmax")
            
            assert code is not None and str(code).strip() != "", f"Crop {crop_code} has empty stage code"
            assert name is not None and str(name).strip() != "" and str(name).lower() != "null", f"Crop {crop_code} stage {code} has invalid stage_name"
            assert name_en is not None and str(name_en).strip() != "" and str(name_en).lower() != "null", f"Crop {crop_code} stage {code} has invalid stage_name_en"
            assert isinstance(crit_tmax, (int, float)) and 25.0 <= crit_tmax <= 50.0, f"Crop {crop_code} stage {code} has unrealistic crit_tmax {crit_tmax}"

def test_unsupported_crop_does_not_fabricate_stages(db: Session):
    """An unsupported crop with no stage data must NOT fabricate soybean stages."""
    # Create temporary farm with an unsupported crop code
    farm_id = "farm_unsupported_test"
    farm = db.query(FarmModel).filter(FarmModel.farm_id == farm_id).first()
    if not farm:
        farm = FarmModel(
            farm_id=farm_id,
            owner_id="farmer_demo_01",
            farm_name="Unsupported Crop Farm",
            district="Pune",
            taluka="Haveli",
            latitude=18.5,
            longitude=73.8,
            total_area_acres=2.0
        )
        db.add(farm)
        db.commit()
    
    plot = db.query(FarmPlotModel).filter(FarmPlotModel.farm_id == farm_id).first()
    if not plot:
        plot = FarmPlotModel(
            plot_id="plot_unsupported_test",
            farm_id=farm_id,
            plot_name="Plot Test",
            area_acres=2.0,
            irrigation_type="rainfed"
        )
        db.add(plot)
        db.commit()
        
    cycle = db.query(CropCycleModel).filter(CropCycleModel.plot_id == plot.plot_id).first()
    if not cycle:
        cycle = CropCycleModel(
            cycle_id="cycle_unsupported_test",
            plot_id=plot.plot_id,
            crop_code="dragonfruit", # exotic unsupported crop
            season="kharif",
            sowing_date=date(2026, 6, 1),
            is_active=True
        )
        db.add(cycle)
        db.commit()

    req = CropHeatAssessmentRequest(
        farm_id=farm_id,
        plot_id=plot.plot_id,
        forecast_tmax_c=36.0
    )
    res = CropHeatEngine.assess_crop_heat_risk(db=db, request=req)
    # Dragonfruit must not return soybean stages (pod formation, flowering, etc.)
    for s in res.supported_stages:
        assert "pod" not in s.get("stage_name", "").lower()
        assert "soybean" not in s.get("stage_name", "").lower()

def test_dynamic_stage_recalculation_changes_threshold_risk_and_interventions(db: Session):
    """Selecting different growth stages must dynamically update threshold, exposure hours, and interventions."""
    # Stage 1: Soybean Flowering (Crit Tmax 35.0°C)
    req_flowering = CropHeatAssessmentRequest(
        farm_id="farm_demo_pune_01",
        farmer_confirmed_stage="stage_flowering",
        forecast_tmax_c=37.0
    )
    res_flowering = CropHeatEngine.assess_crop_heat_risk(db=db, request=req_flowering)
    assert res_flowering.critical_tmax_threshold_c == 35.0
    assert res_flowering.overall_crop_heat_risk in ["critical", "high"]
    assert res_flowering.hours_above_critical > 0.0
    # Must have pollen/flower protection intervention
    flowering_titles = [i.title_en for i in res_flowering.recommended_interventions]
    assert any("pollen" in i.why_appropriate.lower() or "flower" in i.why_appropriate.lower() or "potassium" in i.title_en.lower() for i in res_flowering.recommended_interventions)

    # Stage 2: Soybean Maturity (Crit Tmax 42.0°C)
    req_maturity = CropHeatAssessmentRequest(
        farm_id="farm_demo_pune_01",
        farmer_confirmed_stage="stage_maturity",
        forecast_tmax_c=37.0
    )
    res_maturity = CropHeatEngine.assess_crop_heat_risk(db=db, request=req_maturity)
    assert res_maturity.critical_tmax_threshold_c == 42.0
    # Under 37°C ambient, 42°C critical threshold means 0.0 hours above critical
    assert res_maturity.hours_above_critical == 0.0
    assert res_maturity.overall_crop_heat_risk in ["moderate", "low"]
    # Must have maturity/harvest intervention, NOT flower abortion foliar spray
    maturity_titles = [i.title_en for i in res_maturity.recommended_interventions]
    assert any("harvest" in t.lower() or "shattering" in i.why_appropriate.lower() for t, i in zip(maturity_titles, res_maturity.recommended_interventions))

def test_season_expiry_suppresses_stage_interventions(db: Session):
    """When a crop season is expired and unconfirmed, stage-specific chemical interventions must be suppressed."""
    # Sowing date 250 days ago (expired for 105-day soybean)
    req = CropHeatAssessmentRequest(
        farm_id="farm_demo_pune_01",
        forecast_tmax_c=38.0
    )
    # Temporarily set sowing date to 250 days ago
    cycle = db.query(CropCycleModel).join(FarmPlotModel).filter(
        FarmPlotModel.farm_id == "farm_demo_pune_01",
        CropCycleModel.is_active == True
    ).first()
    orig_sowing = cycle.sowing_date
    orig_confirmed = cycle.current_stage_code
    try:
        cycle.sowing_date = date.today() - timedelta(days=250)
        cycle.current_stage_code = None
        db.commit()
        
        res = CropHeatEngine.assess_crop_heat_risk(db=db, request=req)
        assert res.is_season_expired is True
        assert res.season_status == "EXPIRED"
        # No flower or pod chemical interventions when expired
        for i in res.recommended_interventions:
            assert "flower abortion" not in i.why_appropriate.lower()
            assert "pod development" not in i.why_appropriate.lower()
    finally:
        cycle.sowing_date = orig_sowing
        cycle.current_stage_code = orig_confirmed
        db.commit()

def test_invalid_sowing_date_handled_safely(db: Session):
    """A crop cycle with future or missing sowing date must not crash the service."""
    req = CropHeatAssessmentRequest(
        farm_id="farm_demo_pune_01",
        forecast_tmax_c=34.0
    )
    cycle = db.query(CropCycleModel).join(FarmPlotModel).filter(
        FarmPlotModel.farm_id == "farm_demo_pune_01",
        CropCycleModel.is_active == True
    ).first()
    orig_sowing = cycle.sowing_date
    try:
        # Sowing date in the future
        cycle.sowing_date = date.today() + timedelta(days=30)
        db.commit()
        res = CropHeatEngine.assess_crop_heat_risk(db=db, request=req)
        assert res.days_after_sowing == 0
        assert res.assessment_id is not None
    finally:
        cycle.sowing_date = orig_sowing
        db.commit()

def test_farmer_confirmed_stage_persists(db: Session):
    """When a farmer confirms a growth stage, it persists in the crop cycle record."""
    cycle = db.query(CropCycleModel).join(FarmPlotModel).filter(
        FarmPlotModel.farm_id == "farm_demo_pune_01",
        CropCycleModel.is_active == True
    ).first()
    orig_stage = cycle.current_stage_code
    try:
        # Send confirmation for stage_vegetative
        req = CropHeatAssessmentRequest(
            farm_id="farm_demo_pune_01",
            farmer_confirmed_stage="stage_vegetative"
        )
        res = CropHeatEngine.assess_crop_heat_risk(db=db, request=req)
        assert res.farmer_confirmed_stage == "stage_vegetative"
        
        # Verify it persisted in DB
        db.refresh(cycle)
        assert cycle.current_stage_code in ["stage_vegetative", "VEGETATIVE"]
        
        # Subsequent request without farmer_confirmed_stage should read persisted stage
        req_subsequent = CropHeatAssessmentRequest(
            farm_id="farm_demo_pune_01"
        )
        res_subsequent = CropHeatEngine.assess_crop_heat_risk(db=db, request=req_subsequent)
        assert res_subsequent.growth_stage_code in ["stage_vegetative", "VEGETATIVE"]
    finally:
        cycle.current_stage_code = orig_stage
        db.commit()
