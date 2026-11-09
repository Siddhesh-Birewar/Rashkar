import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.app.db.session import get_db
from backend.app.db.models.income import (
    FarmerResourceProfileModel,
    IncomeOpportunityModel,
    IncomeScenarioModel,
    SavedIncomePlanModel
)
from backend.app.db.models.farm import FarmModel, FarmPlotModel, CropCycleModel
from backend.app.schemas.income import (
    OpportunityCatalogItem,
    FarmerResourceProfile,
    DiscoveredOpportunity,
    EnterpriseFinancialAnalysis,
    OpportunityComparisonItem,
    SavedIncomePlan
)
from backend.app.services.income_knowledge_catalog import (
    EXTENDED_OPPORTUNITY_CATALOG,
    get_opportunity_by_id
)
from backend.app.services.income_engine import IncomeEngine
from backend.app.core.timezone import now_utc

router = APIRouter()

class ScenarioCalculateRequest(BaseModel):
    opportunity_id: str
    custom_budget_inr: float = Field(default=0.0, ge=0.0)
    available_labour_hours_day: float = Field(default=2.0, ge=0.0, le=16.0)
    available_land_acres: float = Field(default=0.0, ge=0.0)
    water_availability: str = Field(default="seasonal_canal")
    custom_assumptions: Optional[Dict[str, Any]] = None

class CompareOpportunitiesRequest(BaseModel):
    opportunity_ids: List[str]
    custom_budget_inr: float = Field(default=25000.0, ge=0.0)

class SavePlanRequest(BaseModel):
    opportunity_id: str
    chosen_budget_inr: float = Field(default=0.0, ge=0.0)
    notes: Optional[str] = None

# -----------------------------------------------------------------------------
# 1. CATALOGUE ENDPOINTS
# -----------------------------------------------------------------------------
@router.get("/opportunities", response_model=List[OpportunityCatalogItem])
def get_opportunities(
    category: Optional[str] = Query(None, description="zero_cash, very_low_cost, moderate_enterprise, crop_diversification, group_external"),
    crop_code: Optional[str] = Query(None, description="Filter by crop context"),
    max_budget: Optional[float] = Query(None, description="Max budget in INR")
):
    """
    Retrieve full catalog of canonical diversification opportunities across all 5 tiers.
    """
    opps = EXTENDED_OPPORTUNITY_CATALOG
    if category and category != "all":
        opps = [o for o in opps if o.category == category]
    if crop_code and crop_code != "all":
        opps = [o for o in opps if not o.target_crops or "all" in o.target_crops or crop_code.lower() in [c.lower() for c in o.target_crops]]
    if max_budget is not None:
        opps = [o for o in opps if o.min_investment_inr <= max_budget]
    return opps

@router.get("/opportunities/{opportunity_id}", response_model=OpportunityCatalogItem)
def get_single_opportunity(opportunity_id: str):
    """
    Retrieve single opportunity definition by ID.
    """
    opp = get_opportunity_by_id(opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail=f"Opportunity with ID '{opportunity_id}' not found.")
    return opp

# -----------------------------------------------------------------------------
# 2. MATCHING & SIMULATION ENDPOINTS
# -----------------------------------------------------------------------------
@router.post("/match-opportunities", response_model=List[DiscoveredOpportunity])
def match_opportunities_to_farmer(profile: FarmerResourceProfile):
    """
    Evaluate farmer resource constraints and discover personalized opportunities
    prioritizing zero-cash and cost-saving options first.
    """
    return IncomeEngine.match_opportunities(profile)

@router.post("/calculate-scenario", response_model=EnterpriseFinancialAnalysis)
def calculate_income_scenario(request: ScenarioCalculateRequest):
    """
    Produce a rigorous 3-scenario financial simulation (Conservative, Base, Optimistic)
    with 12-month monthly cash flows, cumulative payback, and sensitivity analysis.
    """
    opp = get_opportunity_by_id(request.opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail=f"Opportunity with ID '{request.opportunity_id}' not found.")
    
    return IncomeEngine.calculate_enterprise_financials(
        opportunity_id=request.opportunity_id,
        custom_budget_inr=request.custom_budget_inr,
        water_availability=request.water_availability
    )

@router.post("/compare-opportunities", response_model=List[OpportunityComparisonItem])
def compare_selected_opportunities(request: CompareOpportunitiesRequest):
    """
    Produce a side-by-side comparison matrix for selected enterprise alternatives
    using the authoritative unified financial simulation service.
    """
    if not request.opportunity_ids:
        raise HTTPException(status_code=400, detail="Must provide at least one opportunity ID.")
    return IncomeEngine.compare_opportunities(request.opportunity_ids, request.custom_budget_inr)

# -----------------------------------------------------------------------------
# 3. FARM-SPECIFIC PROFILE & PLAN PERSISTENCE ENDPOINTS
# -----------------------------------------------------------------------------
@router.get("/farms/{farm_id}/profile", response_model=FarmerResourceProfile)
def get_farm_resource_profile(farm_id: str, db: Session = Depends(get_db)):
    """
    Retrieve or prefill a farmer's resource profile based on registered farm details.
    """
    profile_record = db.query(FarmerResourceProfileModel).filter(FarmerResourceProfileModel.farm_id == farm_id).first()
    if profile_record:
        return FarmerResourceProfile(
            available_investment_inr=profile_record.available_investment_inr,
            monthly_operating_budget_inr=profile_record.monthly_operating_budget_inr,
            max_risk_capital_inr=profile_record.max_risk_capital_inr,
            willing_to_borrow=profile_record.willing_to_borrow,
            total_farm_acres=profile_record.total_farm_acres,
            cultivated_acres=profile_record.cultivated_acres,
            available_land_acres=profile_record.available_land_acres,
            unused_land_acres=profile_record.unused_land_acres,
            field_bunds_available=profile_record.field_bunds_available,
            has_animal_shed=profile_record.has_animal_shed,
            has_storage_room=profile_record.has_storage_room,
            has_shaded_space=profile_record.has_shaded_space,
            water_availability=profile_record.water_availability,
            water_months_available=profile_record.water_months_available or [],
            family_labor_hours_day=profile_record.family_labor_hours_day,
            hired_labor_possible=profile_record.hired_labor_possible,
            existing_livestock=profile_record.existing_livestock,
            existing_assets=profile_record.existing_assets or [],
            crop_byproducts=profile_record.crop_byproducts or [],
            byproduct_surplus_available=profile_record.byproduct_surplus_available,
            interests=profile_record.interests or [],
            has_transport=profile_record.has_transport,
            has_fpo_access=profile_record.has_fpo_access,
            distance_to_apmc_km=profile_record.distance_to_apmc_km,
            risk_tolerance=profile_record.risk_tolerance,
            category_preference=profile_record.category_preference
        )

    # Prefill from existing FarmModel
    farm = db.query(FarmModel).filter(FarmModel.farm_id == farm_id).first()
    total_area = farm.total_area_acres if farm and farm.total_area_acres else 2.5
    
    # Check plot crops for byproduct prefilling
    plots = db.query(FarmPlotModel).filter(FarmPlotModel.farm_id == farm_id).all() if farm else []
    byproducts = []
    has_drip = False
    for p in plots:
        if p.irrigation_type and "drip" in p.irrigation_type.lower():
            has_drip = True
        cycles = db.query(CropCycleModel).filter(CropCycleModel.plot_id == p.plot_id).all()
        for c in cycles:
            if c.crop_code in ["soybean", "cotton", "jowar", "onion"]:
                byproducts.append(f"{c.crop_code}_straw")

    return FarmerResourceProfile(
        available_investment_inr=0.0,
        monthly_operating_budget_inr=0.0,
        total_farm_acres=total_area,
        cultivated_acres=total_area * 0.8,
        available_land_acres=round(total_area * 0.2, 2),
        unused_land_acres=round(total_area * 0.1, 2),
        field_bunds_available=True,
        water_availability="seasonal_canal",
        family_labor_hours_day=2.0,
        existing_assets=["drip"] if has_drip else ["tools"],
        crop_byproducts=list(set(byproducts)) if byproducts else ["crop_residue", "cow_dung"],
        byproduct_surplus_available=True,
        category_preference="all"
    )

@router.put("/farms/{farm_id}/profile", response_model=FarmerResourceProfile)
def save_farm_resource_profile(farm_id: str, profile: FarmerResourceProfile, db: Session = Depends(get_db)):
    """
    Save or update farmer resource profile.
    """
    farm = db.query(FarmModel).filter(FarmModel.farm_id == farm_id).first()
    farmer_id = farm.owner_id if farm else "farmer_demo_01"

    record = db.query(FarmerResourceProfileModel).filter(FarmerResourceProfileModel.farm_id == farm_id).first()
    if not record:
        record = FarmerResourceProfileModel(farm_id=farm_id, farmer_id=farmer_id)
        db.add(record)

    record.available_investment_inr = profile.available_investment_inr
    record.monthly_operating_budget_inr = profile.monthly_operating_budget_inr
    record.max_risk_capital_inr = profile.max_risk_capital_inr
    record.willing_to_borrow = profile.willing_to_borrow
    record.total_farm_acres = profile.total_farm_acres
    record.cultivated_acres = profile.cultivated_acres
    record.available_land_acres = profile.available_land_acres
    record.unused_land_acres = profile.unused_land_acres
    record.field_bunds_available = profile.field_bunds_available
    record.has_animal_shed = profile.has_animal_shed
    record.has_storage_room = profile.has_storage_room
    record.has_shaded_space = profile.has_shaded_space
    record.water_availability = profile.water_availability
    record.water_months_available = profile.water_months_available
    record.family_labor_hours_day = profile.family_labor_hours_day
    record.hired_labor_possible = profile.hired_labor_possible
    record.existing_livestock = profile.existing_livestock
    record.existing_assets = profile.existing_assets
    record.crop_byproducts = profile.crop_byproducts
    record.byproduct_surplus_available = profile.byproduct_surplus_available
    record.interests = profile.interests
    record.has_transport = profile.has_transport
    record.has_fpo_access = profile.has_fpo_access
    record.distance_to_apmc_km = profile.distance_to_apmc_km
    record.risk_tolerance = profile.risk_tolerance
    record.category_preference = profile.category_preference
    record.updated_at_utc = now_utc()

    db.commit()
    db.refresh(record)
    return profile

@router.post("/farms/{farm_id}/discover", response_model=List[DiscoveredOpportunity])
def discover_farm_opportunities(farm_id: str, profile_override: Optional[FarmerResourceProfile] = None, db: Session = Depends(get_db)):
    """
    Discover farm-grounded opportunities prioritizing zero-cash and cost-saving options.
    """
    profile = profile_override or get_farm_resource_profile(farm_id, db)
    return IncomeEngine.match_opportunities(profile)

@router.post("/farms/{farm_id}/plans", response_model=SavedIncomePlan)
def save_income_plan(farm_id: str, req: SavePlanRequest, db: Session = Depends(get_db)):
    """
    Save an opportunity scenario plan for the farm.
    """
    farm = db.query(FarmModel).filter(FarmModel.farm_id == farm_id).first()
    farmer_id = farm.owner_id if farm else "farmer_demo_01"

    opp = get_opportunity_by_id(req.opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")

    fin = IncomeEngine.calculate_enterprise_financials(req.opportunity_id, req.chosen_budget_inr)

    plan_id = f"plan_{uuid.uuid4().hex[:10]}"
    record = SavedIncomePlanModel(
        plan_id=plan_id,
        farmer_id=farmer_id,
        farm_id=farm_id,
        opportunity_id=opp.opportunity_id,
        opportunity_title=opp.title,
        category=opp.category,
        chosen_budget_inr=req.chosen_budget_inr,
        projected_annual_profit_inr=fin.calculated_net_profit_annual_inr,
        projected_annual_savings_inr=fin.calculated_annual_savings_inr,
        payback_months=fin.calculated_break_even_months,
        break_even_reached=fin.break_even_reached,
        notes=req.notes,
        created_at_utc=now_utc()
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return SavedIncomePlan(
        plan_id=record.plan_id,
        farmer_id=record.farmer_id,
        farm_id=record.farm_id,
        opportunity_id=record.opportunity_id,
        opportunity_title=record.opportunity_title,
        category=record.category,
        chosen_budget_inr=record.chosen_budget_inr,
        projected_annual_profit_inr=record.projected_annual_profit_inr,
        projected_annual_savings_inr=record.projected_annual_savings_inr,
        payback_months=record.payback_months,
        break_even_reached=record.break_even_reached,
        notes=record.notes,
        created_at_utc=record.created_at_utc.isoformat()
    )

@router.get("/farms/{farm_id}/plans", response_model=List[SavedIncomePlan])
def list_saved_income_plans(farm_id: str, db: Session = Depends(get_db)):
    """
    List all saved diversification plans for the given farm.
    """
    records = db.query(SavedIncomePlanModel).filter(SavedIncomePlanModel.farm_id == farm_id).order_by(SavedIncomePlanModel.created_at_utc.desc()).all()
    return [
        SavedIncomePlan(
            plan_id=r.plan_id,
            farmer_id=r.farmer_id,
            farm_id=r.farm_id,
            opportunity_id=r.opportunity_id,
            opportunity_title=r.opportunity_title,
            category=r.category,
            chosen_budget_inr=r.chosen_budget_inr,
            projected_annual_profit_inr=r.projected_annual_profit_inr,
            projected_annual_savings_inr=r.projected_annual_savings_inr,
            payback_months=r.payback_months,
            break_even_reached=r.break_even_reached,
            notes=r.notes,
            created_at_utc=r.created_at_utc.isoformat()
        )
        for r in records
    ]
