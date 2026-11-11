"""Income Diversification — canonical catalogue, matching, financial simulation, and plan persistence.

Provides comprehensive agricultural enterprise diversification advisory (Crops, Floriculture,
Poultry, Fishery, Livestock, Small Space, Farm Resource Monetization, Value Addition).
"""
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from cropnet.services.api.app.api.v1.endpoints.farms import _get_farm_and_verify_owner
from cropnet.services.api.app.core.database import get_db
from cropnet.services.api.app.core.security import CurrentUser, get_current_user
from cropnet.services.api.app.rashkar.models import (
    RashkarFarmerResourceProfileModel,
    RashkarSavedIncomePlanModel,
    now_utc_naive,
)
from cropnet.services.api.app.schemas.income import (
    CompareOpportunitiesPostRequest,
    DetailedOpportunityItem,
    DiscoveredOpportunity,
    EnterpriseFinancialAnalysis,
    FarmerResourceProfile,
    FarmResourceProfileUpdateRequest,
    FinancialScenarioSimulateRequest,
    FinancialScenarioSimulateResponse,
    OpportunityCatalogItem,
    OpportunityCategoryItem,
    OpportunityComparisonItem,
    SaveFarmPlanRequest,
)
from cropnet.services.api.app.services.income.catalog import (
    ALL_OPPORTUNITIES_LIST,
    EXTENDED_OPPORTUNITY_CATALOG,
    get_opportunity_by_id,
)
from cropnet.services.api.app.services.income.data_loader import (
    convert_raw_to_catalog_item,
    get_all_categories,
    get_all_raw_opportunities,
    get_raw_opportunity_by_id,
)
from cropnet.services.api.app.services.income.engine import IncomeEngine
from cropnet.services.api.app.services.income.enhanced_engine import EnhancedIncomeEngine

router = APIRouter()


# -----------------------------------------------------------------------------
# Legacy / Backward Compatible Request Schemas
# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
# 1. Opportunity Catalogue & Category Endpoints
# -----------------------------------------------------------------------------
@router.get("/categories", response_model=List[OpportunityCategoryItem])
def get_categories():
    """Returns the 8 canonical income diversification categories with opportunity counts."""
    cats = get_all_categories()
    raw_opps = get_all_raw_opportunities()
    
    # Compute counts per category
    counts: Dict[str, int] = {}
    for o in raw_opps:
        k = o.get("category", "")
        counts[k] = counts.get(k, 0) + 1

    return [
        OpportunityCategoryItem(
            key=c["key"],
            name=c["name"],
            tagline=c["tagline"],
            count=counts.get(c["key"], 0),
        )
        for c in cats
    ]


@router.get("/catalog", response_model=List[DetailedOpportunityItem])
def get_detailed_catalog(
    category: Optional[str] = Query(None, description="Category filter (e.g. CROP_DIVERSIFICATION, POULTRY)"),
    max_budget: Optional[float] = Query(None, description="Max budget in INR"),
    min_land: Optional[float] = Query(None, description="Max land required in acres"),
    water: Optional[str] = Query(None, description="Max water requirement (none, low, moderate, high)"),
    search: Optional[str] = Query(None, description="Search keyword in title or description"),
):
    """Retrieve all rich diversification opportunities with optional filters."""
    # Match against dummy empty profile to generate baseline DetailedOpportunityItems
    baseline_items = EnhancedIncomeEngine.match_opportunities_for_farm(
        {"calculated_area_acres": 5.0, "water_source": "reliable_year_round"},
        {"available_investment_inr": 100000.0, "available_diversification_acres": 1.0},
    )

    filtered = baseline_items
    if category and category.lower() != "all":
        filtered = [o for o in filtered if o.category.upper() == category.upper()]
    if max_budget is not None:
        filtered = [o for o in filtered if o.setup_investment_range.get("min_inr", 0) <= max_budget]
    if min_land is not None:
        filtered = [o for o in filtered if o.suitable_land_acres <= min_land]
    if water and water.lower() != "all":
        water_levels = {"none": 0, "very_low": 1, "low": 2, "moderate": 3, "high": 4}
        max_lvl = water_levels.get(water.lower(), 4)
        filtered = [o for o in filtered if water_levels.get(o.water_requirement.lower(), 2) <= max_lvl]
    if search:
        s = search.lower().strip()
        filtered = [
            o for o in filtered
            if s in o.name.lower() or s in o.farmer_friendly_description.lower() or s in o.business_model.lower()
        ]

    return filtered


@router.get("/details/{opportunity_id}", response_model=DetailedOpportunityItem)
def get_opportunity_details(opportunity_id: str):
    """Retrieve full structured operational details for a specific enterprise."""
    raw = get_raw_opportunity_by_id(opportunity_id)
    if not raw:
        raise HTTPException(status_code=404, detail=f"Opportunity '{opportunity_id}' not found.")

    items = EnhancedIncomeEngine.match_opportunities_for_farm(
        {"calculated_area_acres": 2.0},
        {"available_investment_inr": 50000.0},
    )
    for item in items:
        if item.opportunity_id == opportunity_id:
            return item

    raise HTTPException(status_code=404, detail=f"Opportunity '{opportunity_id}' not found.")


# -----------------------------------------------------------------------------
# 2. Farm-Specific Matching & Resource Profile Endpoints
# -----------------------------------------------------------------------------
@router.get("/farms/{farm_id}/match", response_model=List[DetailedOpportunityItem])
def match_opportunities_for_farm_get(
    farm_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Evaluates farm context against diversification opportunities using deterministic agricultural rules."""
    try:
        farm_uuid = uuid.UUID(farm_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid farm ID format")

    farm = _get_farm_and_verify_owner(farm_uuid, current_user, db)

    # Check for stored resource profile in DB
    prof_row = (
        db.query(RashkarFarmerResourceProfileModel)
        .filter(
            RashkarFarmerResourceProfileModel.farm_id == str(farm_uuid),
            RashkarFarmerResourceProfileModel.owner_id == str(current_user.user_id),
        )
        .first()
    )

    profile_dict: Dict[str, Any] = {}
    if prof_row:
        profile_dict = {
            "available_diversification_acres": prof_row.available_land_acres,
            "available_investment_inr": prof_row.available_investment_inr,
            "monthly_operating_budget_inr": prof_row.monthly_operating_budget_inr,
            "water_source": prof_row.water_availability,
            "family_labor_hours_day": prof_row.family_labor_hours_day,
            "has_animal_shed": prof_row.has_animal_shed,
            "has_storage_room": prof_row.has_storage_room,
            "has_farm_pond": "pond" in str(prof_row.water_availability).lower(),
            "existing_equipment": prof_row.existing_assets or [],
            "existing_livestock": [prof_row.existing_livestock] if prof_row.existing_livestock else [],
        }

    return EnhancedIncomeEngine.match_opportunities_for_farm(farm, profile_dict)


@router.post("/farms/{farm_id}/match", response_model=List[DetailedOpportunityItem])
def match_opportunities_for_farm_post(
    farm_id: str,
    overrides: FarmResourceProfileUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Evaluates farm context with farmer-specified resource overrides (land, budget, water, etc.)."""
    try:
        farm_uuid = uuid.UUID(farm_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid farm ID format")

    farm = _get_farm_and_verify_owner(farm_uuid, current_user, db)
    profile_dict = overrides.model_dump()
    return EnhancedIncomeEngine.match_opportunities_for_farm(farm, profile_dict)


@router.get("/farms/{farm_id}/profile", response_model=Dict[str, Any])
def get_farm_resource_profile(
    farm_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns stored farmer resource profile or auto-populates defaults from registered farm."""
    try:
        farm_uuid = uuid.UUID(farm_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid farm ID format")

    farm = _get_farm_and_verify_owner(farm_uuid, current_user, db)

    prof_row = (
        db.query(RashkarFarmerResourceProfileModel)
        .filter(
            RashkarFarmerResourceProfileModel.farm_id == str(farm_uuid),
            RashkarFarmerResourceProfileModel.owner_id == str(current_user.user_id),
        )
        .first()
    )

    total_acres = float(farm.get("calculated_area_acres") or farm.get("area_acres") or 2.0)
    if prof_row:
        return {
            "farm_id": str(farm_uuid),
            "farm_name": farm.get("name"),
            "total_farm_acres": total_acres,
            "available_diversification_acres": prof_row.available_land_acres,
            "available_investment_inr": prof_row.available_investment_inr,
            "monthly_operating_budget_inr": prof_row.monthly_operating_budget_inr,
            "water_source": prof_row.water_availability,
            "family_labor_hours_day": prof_row.family_labor_hours_day,
            "has_animal_shed": prof_row.has_animal_shed,
            "has_storage_room": prof_row.has_storage_room,
            "has_farm_pond": "pond" in str(prof_row.water_availability).lower(),
            "existing_equipment": prof_row.existing_assets or [],
            "existing_livestock": [prof_row.existing_livestock] if prof_row.existing_livestock else [],
            "preferred_category": prof_row.category_preference,
        }

    # Default profile derived from registered farm
    return {
        "farm_id": str(farm_uuid),
        "farm_name": farm.get("name"),
        "total_farm_acres": total_acres,
        "available_diversification_acres": min(0.5, total_acres),
        "available_investment_inr": 0.0,
        "monthly_operating_budget_inr": 0.0,
        "water_source": farm.get("water_source") or "seasonal_canal",
        "family_labor_hours_day": 2.0,
        "has_animal_shed": False,
        "has_storage_room": False,
        "has_farm_pond": False,
        "existing_equipment": ["knapsack_sprayer"],
        "existing_livestock": [],
        "preferred_category": "all",
    }


@router.post("/farms/{farm_id}/profile", response_model=Dict[str, Any])
def save_farm_resource_profile(
    farm_id: str,
    profile_data: FarmResourceProfileUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Persists or updates the farmer's diversification resource profile."""
    try:
        farm_uuid = uuid.UUID(farm_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid farm ID format")

    farm = _get_farm_and_verify_owner(farm_uuid, current_user, db)

    prof_row = (
        db.query(RashkarFarmerResourceProfileModel)
        .filter(
            RashkarFarmerResourceProfileModel.farm_id == str(farm_uuid),
            RashkarFarmerResourceProfileModel.owner_id == str(current_user.user_id),
        )
        .first()
    )

    if not prof_row:
        prof_row = RashkarFarmerResourceProfileModel(
            farm_id=str(farm_uuid),
            owner_id=str(current_user.user_id),
        )
        db.add(prof_row)

    prof_row.available_land_acres = profile_data.available_diversification_acres
    prof_row.available_investment_inr = profile_data.available_investment_inr
    prof_row.monthly_operating_budget_inr = profile_data.monthly_operating_budget_inr
    prof_row.water_availability = profile_data.water_source
    prof_row.family_labor_hours_day = profile_data.family_labor_hours_day
    prof_row.has_animal_shed = profile_data.has_animal_shed
    prof_row.has_storage_room = profile_data.has_storage_room
    prof_row.existing_assets = profile_data.existing_equipment
    prof_row.existing_livestock = profile_data.existing_livestock[0] if profile_data.existing_livestock else "none"
    prof_row.category_preference = profile_data.preferred_category or "all"
    prof_row.updated_at_utc = now_utc_naive()

    db.commit()
    db.refresh(prof_row)

    return {"status": "SUCCESS", "message": "Farm resource profile updated successfully."}


# -----------------------------------------------------------------------------
# 3. Financial Simulation & Comparison Endpoints
# -----------------------------------------------------------------------------
@router.post("/simulate", response_model=FinancialScenarioSimulateResponse)
def simulate_scenario(request: FinancialScenarioSimulateRequest):
    """Simulates financial outcomes across LOW, BASE, and HIGH scenarios with editable parameters."""
    return EnhancedIncomeEngine.simulate_financial_scenario(request)


@router.post("/compare", response_model=List[Dict[str, Any]])
def compare_opportunities_endpoint(request: CompareOpportunitiesPostRequest):
    """Produces side-by-side comparison matrix for 2 or 3 selected enterprises."""
    if not request.opportunity_ids:
        raise HTTPException(status_code=400, detail="Must provide at least one opportunity ID.")
    return EnhancedIncomeEngine.compare_selected_opportunities(
        request.opportunity_ids,
        request.allocated_acres,
        request.available_budget_inr,
    )


# -----------------------------------------------------------------------------
# 4. Saved Farm Business Plans Endpoints
# -----------------------------------------------------------------------------
@router.get("/farms/{farm_id}/plans", response_model=List[Dict[str, Any]])
def get_saved_farm_plans(
    farm_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves all saved diversification business plans for this farm."""
    try:
        farm_uuid = uuid.UUID(farm_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid farm ID format")

    _get_farm_and_verify_owner(farm_uuid, current_user, db)

    rows = (
        db.query(RashkarSavedIncomePlanModel)
        .filter(
            RashkarSavedIncomePlanModel.farm_id == str(farm_uuid),
            RashkarSavedIncomePlanModel.owner_id == str(current_user.user_id),
        )
        .order_by(RashkarSavedIncomePlanModel.created_at_utc.desc())
        .all()
    )

    return [
        {
            "plan_id": r.plan_id,
            "opportunity_id": r.opportunity_id,
            "opportunity_title": r.opportunity_title,
            "category": r.category,
            "chosen_budget_inr": r.chosen_budget_inr,
            "projected_operating_surplus_inr": r.projected_annual_profit_inr,
            "payback_months": r.payback_months,
            "break_even_reached": r.break_even_reached,
            "notes": r.notes,
            "created_at_utc": r.created_at_utc.isoformat() if r.created_at_utc else "",
        }
        for r in rows
    ]


@router.post("/farms/{farm_id}/plans", response_model=Dict[str, Any])
def save_farm_plan(
    farm_id: str,
    plan_data: SaveFarmPlanRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Saves a personalized business plan scenario to the farm record."""
    try:
        farm_uuid = uuid.UUID(farm_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid farm ID format")

    _get_farm_and_verify_owner(farm_uuid, current_user, db)

    raw = get_raw_opportunity_by_id(plan_data.opportunity_id)
    title = raw.get("name", "Agricultural Enterprise") if raw else plan_data.opportunity_id
    cat = raw.get("category", "CROP_DIVERSIFICATION") if raw else "CROP_DIVERSIFICATION"

    plan_id = f"plan_{uuid.uuid4().hex[:12]}"
    new_plan = RashkarSavedIncomePlanModel(
        plan_id=plan_id,
        owner_id=str(current_user.user_id),
        farm_id=str(farm_uuid),
        opportunity_id=plan_data.opportunity_id,
        opportunity_title=title,
        category=cat,
        chosen_budget_inr=plan_data.custom_budget_inr,
        projected_annual_profit_inr=plan_data.projected_operating_surplus_inr,
        projected_annual_savings_inr=0.0,
        payback_months=12.0 if plan_data.projected_operating_surplus_inr > 0 else None,
        break_even_reached=plan_data.projected_operating_surplus_inr > 0,
        notes=plan_data.notes or f"Scale: {plan_data.allocated_scale} {plan_data.scale_unit} ({plan_data.scenario_mode} scenario)",
        created_at_utc=now_utc_naive(),
    )

    db.add(new_plan)
    db.commit()

    return {"status": "SUCCESS", "plan_id": plan_id, "message": "Business plan saved successfully."}


@router.delete("/farms/{farm_id}/plans/{plan_id}", response_model=Dict[str, Any])
def delete_farm_plan(
    farm_id: str,
    plan_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deletes a saved business plan."""
    try:
        farm_uuid = uuid.UUID(farm_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid farm ID format")

    _get_farm_and_verify_owner(farm_uuid, current_user, db)

    plan = (
        db.query(RashkarSavedIncomePlanModel)
        .filter(
            RashkarSavedIncomePlanModel.plan_id == plan_id,
            RashkarSavedIncomePlanModel.farm_id == str(farm_uuid),
            RashkarSavedIncomePlanModel.owner_id == str(current_user.user_id),
        )
        .first()
    )

    if not plan:
        raise HTTPException(status_code=404, detail="Saved plan not found.")

    db.delete(plan)
    db.commit()

    return {"status": "SUCCESS", "message": "Plan deleted successfully."}


# -----------------------------------------------------------------------------
# 5. Backward Compatible Legacy Endpoints (Maintained)
# -----------------------------------------------------------------------------
@router.get("/opportunities", response_model=List[OpportunityCatalogItem])
def get_opportunities(
    category: Optional[str] = Query(None),
    crop_code: Optional[str] = Query(None),
    max_budget: Optional[float] = Query(None),
):
    """Legacy endpoint: returns canonical diversification opportunities."""
    opps = ALL_OPPORTUNITIES_LIST
    if category and category != "all":
        opps = [o for o in opps if o.category.lower() == category.lower()]
    if crop_code and crop_code != "all":
        opps = [
            o for o in opps
            if not o.target_crops or "all" in o.target_crops or crop_code.lower() in [c.lower() for c in o.target_crops]
        ]
    if max_budget is not None:
        opps = [o for o in opps if o.min_investment_inr <= max_budget]
    return opps


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityCatalogItem)
def get_single_opportunity(opportunity_id: str):
    """Legacy endpoint: retrieve opportunity definition by ID."""
    opp = get_opportunity_by_id(opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail=f"Opportunity with ID '{opportunity_id}' not found.")
    return opp


@router.post("/match-opportunities", response_model=List[DiscoveredOpportunity])
def match_opportunities_to_farmer(profile: FarmerResourceProfile):
    """Legacy endpoint: discover and rank opportunities against farmer resources."""
    return IncomeEngine.match_opportunities(profile)


@router.post("/calculate-scenario", response_model=EnterpriseFinancialAnalysis)
def calculate_income_scenario(request: ScenarioCalculateRequest):
    """Legacy endpoint: 3-scenario financial simulation with monthly cash flows."""
    opp = get_opportunity_by_id(request.opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail=f"Opportunity with ID '{request.opportunity_id}' not found.")
    return IncomeEngine.calculate_enterprise_financials(
        opportunity_id=request.opportunity_id,
        custom_budget_inr=request.custom_budget_inr,
        water_availability=request.water_availability,
    )


@router.post("/compare-opportunities", response_model=List[OpportunityComparisonItem])
def compare_selected_opportunities(request: CompareOpportunitiesRequest):
    """Legacy endpoint: side-by-side comparison of selected enterprises."""
    if not request.opportunity_ids:
        raise HTTPException(status_code=400, detail="Must provide at least one opportunity ID.")
    return IncomeEngine.compare_opportunities(request.opportunity_ids, request.custom_budget_inr)
