"""RASHKAR Extra Income discovery, financial simulation, and farm plan persistence endpoints."""

from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

try:
    from cropnet.services.api.app.core.database import get_db
    from cropnet.services.api.app.core.security import CurrentUser, get_current_user
except ImportError:
    from app.core.database import get_db
    from app.core.security import CurrentUser, get_current_user

from ..adapters import (
    ensure_rashkar_seeded,
    get_active_crop_cycle,
    resolve_owned_farm_context,
)
from ..engines.income import IncomeEngine, get_opportunity_by_id
from ..models import (
    RashkarFarmerResourceProfileModel,
    RashkarIncomeOpportunityModel,
    RashkarIncomeScenarioModel,
    RashkarSavedIncomePlanModel,
)
from ..schemas.income import (
    DiscoveredOpportunity,
    EnterpriseFinancialAnalysis,
    FarmerResourceProfile,
    OpportunityComparisonItem,
    SavedIncomePlan,
)
from ..timezone import format_ist_iso, now_utc_naive, to_ist_iso


router = APIRouter(prefix="/income", tags=["RASHKAR Extra Income"])


class ScenarioCalculateRequest(BaseModel):
    """Payload to simulate a 12-month enterprise cash-flow scenario."""

    opportunity_id: str = Field(..., min_length=1, max_length=50)
    custom_budget_inr: Optional[float] = Field(default=None, ge=0.0)
    water_availability: Optional[str] = Field(default=None, max_length=50)
    available_labour_hours_day: Optional[float] = Field(default=None, ge=0.0, le=16.0)
    available_land_acres: Optional[float] = Field(default=None, ge=0.0)
    custom_assumptions: Optional[Dict[str, Any]] = None
    farm_id: Optional[str] = None


class CompareOpportunitiesRequest(BaseModel):
    """Payload for side-by-side enterprise comparison."""

    opportunity_ids: List[str] = Field(..., min_length=1)
    custom_budget_inr: float = Field(default=60000.0, ge=0.0)


class SaveIncomePlanRequest(BaseModel):
    """Payload to bookmark an extra-income enterprise plan for a farm."""

    opportunity_id: str = Field(..., min_length=1, max_length=50)
    chosen_budget_inr: float = Field(..., ge=0.0)
    notes: Optional[str] = None


def _serialize_opportunity_row(row: RashkarIncomeOpportunityModel) -> Dict[str, Any]:
    req_res = row.required_resources if isinstance(row.required_resources, dict) else {}
    catalog_obj = get_opportunity_by_id(row.opportunity_id)
    return {
        "opportunity_id": row.opportunity_id,
        "title": row.title,
        "category": row.category,
        "is_cost_saving": bool(row.is_cost_saving),
        "tagline": row.tagline or "",
        "min_investment_inr": row.min_investment_inr,
        "max_investment_inr": row.max_investment_inr,
        "working_capital_required_inr": row.working_capital_required_inr or 0.0,
        "required_resources": row.required_resources if row.required_resources is not None else [],
        "required_land_acres": req_res.get(
            "required_land_acres",
            catalog_obj.required_land_acres if catalog_obj else 0.0,
        ),
        "required_space_type": req_res.get(
            "required_space_type",
            catalog_obj.required_space_type if catalog_obj else "field",
        ),
        "water_requirement": req_res.get(
            "water_requirement",
            catalog_obj.water_requirement if catalog_obj else "none",
        ),
        "daily_labor_hours": req_res.get(
            "daily_labor_hours",
            catalog_obj.daily_labor_hours if catalog_obj else 0.5,
        ),
        "risk_level": row.risk_level or "moderate",
        "payback_period_months": row.payback_period_months,
        "potential_annual_profit_inr": row.potential_annual_profit_inr,
        "potential_annual_savings_inr": row.potential_annual_savings_inr or 0.0,
        "summary": row.summary,
        "market_commodity": row.market_commodity or "",
        "market_benchmark_price": row.market_benchmark_price or "",
        "market_source": row.market_source or "",
        "target_crops": row.target_crops or [],
        "key_assumptions": row.key_assumptions or [],
        "key_risks": row.key_risks or [],
        "source_attribution": row.source_attribution,
        "minimum_viable_unit_description": (
            catalog_obj.minimum_viable_unit_description if catalog_obj else ""
        ),
    }


def _profile_from_row(
    row: Optional[RashkarFarmerResourceProfileModel],
    farm_ctx: Dict[str, Any],
    active_crop_code: Optional[str],
    active_crop_stage: Optional[str],
) -> FarmerResourceProfile:
    if row is None:
        return FarmerResourceProfile(
            total_farm_acres=farm_ctx.get("total_area_acres"),
            current_crop_code=active_crop_code,
            current_crop_stage=active_crop_stage,
        )

    return FarmerResourceProfile(
        available_investment_inr=float(row.available_investment_inr or 0.0),
        monthly_operating_budget_inr=float(row.monthly_operating_budget_inr or 0.0),
        max_risk_capital_inr=row.max_risk_capital_inr,
        willing_to_borrow=bool(row.willing_to_borrow),
        total_farm_acres=(
            row.total_farm_acres
            if row.total_farm_acres is not None
            else farm_ctx.get("total_area_acres")
        ),
        cultivated_acres=row.cultivated_acres,
        available_land_acres=float(row.available_land_acres or 0.0),
        unused_land_acres=float(row.unused_land_acres or 0.0),
        field_bunds_available=(
            True if row.field_bunds_available is None else bool(row.field_bunds_available)
        ),
        has_animal_shed=bool(row.has_animal_shed),
        has_storage_room=bool(row.has_storage_room),
        has_shaded_space=bool(row.has_shaded_space),
        water_availability=row.water_availability or "seasonal_canal",
        water_months_available=list(row.water_months_available or []),
        family_labor_hours_day=float(
            2.0 if row.family_labor_hours_day is None else row.family_labor_hours_day
        ),
        hired_labor_possible=bool(row.hired_labor_possible),
        existing_livestock=row.existing_livestock or "none",
        existing_assets=list(row.existing_assets or []),
        crop_byproducts=list(row.crop_byproducts or []),
        byproduct_surplus_available=(
            True
            if row.byproduct_surplus_available is None
            else bool(row.byproduct_surplus_available)
        ),
        interests=list(row.interests or []),
        has_transport=bool(row.has_transport),
        has_fpo_access=bool(row.has_fpo_access),
        distance_to_apmc_km=row.distance_to_apmc_km,
        risk_tolerance=row.risk_tolerance or "moderate",
        category_preference=row.category_preference or "all",
        age_range=row.age_range or "36-45",
        work_preference=row.work_preference or "daily_physical",
        payback_horizon=row.payback_horizon or "within_6_months",
        family_management_role=row.family_management_role or "self",
        current_crop_code=row.current_crop_code or active_crop_code,
        current_crop_stage=row.current_crop_stage or active_crop_stage,
    )


def _assert_opportunity_exists(opportunity_id: str, db: Session) -> RashkarIncomeOpportunityModel:
    row = (
        db.query(RashkarIncomeOpportunityModel)
        .filter(
            RashkarIncomeOpportunityModel.opportunity_id == opportunity_id,
            RashkarIncomeOpportunityModel.is_active == True,  # noqa: E712
        )
        .first()
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Income opportunity '{opportunity_id}' not found.",
        )
    return row


def _row_to_saved_plan(row: RashkarSavedIncomePlanModel) -> SavedIncomePlan:
    created_str = (
        to_ist_iso(row.created_at_utc)
        if row.created_at_utc is not None
        else format_ist_iso()
    )
    return SavedIncomePlan(
        plan_id=row.plan_id,
        farmer_id=row.owner_id,
        farm_id=row.farm_id,
        opportunity_id=row.opportunity_id,
        opportunity_title=row.opportunity_title,
        category=row.category,
        chosen_budget_inr=row.chosen_budget_inr,
        projected_annual_profit_inr=row.projected_annual_profit_inr,
        projected_annual_savings_inr=row.projected_annual_savings_inr or 0.0,
        payback_months=row.payback_months,
        break_even_reached=bool(row.break_even_reached),
        notes=row.notes,
        created_at_utc=created_str,
    )


@router.get("/opportunities")
def list_income_opportunities(
    category: Optional[str] = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """List seeded RASHKAR extra-income opportunities with optional category filtering."""
    del current_user
    ensure_rashkar_seeded(db)

    query = db.query(RashkarIncomeOpportunityModel).filter(
        RashkarIncomeOpportunityModel.is_active == True  # noqa: E712
    )
    if category and category != "all":
        query = query.filter(RashkarIncomeOpportunityModel.category == category)

    rows = query.order_by(
        RashkarIncomeOpportunityModel.min_investment_inr.asc(),
        RashkarIncomeOpportunityModel.title.asc(),
    ).all()
    return [_serialize_opportunity_row(row) for row in rows]


@router.get("/opportunities/{opportunity_id}")
def get_income_opportunity_detail(
    opportunity_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Return full details for a single income opportunity."""
    del current_user
    ensure_rashkar_seeded(db)
    row = _assert_opportunity_exists(opportunity_id, db)
    return _serialize_opportunity_row(row)


@router.get("/farms/{farm_id}/profile", response_model=FarmerResourceProfile)
def get_farm_income_profile(
    farm_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FarmerResourceProfile:
    """Return persisted farmer resource profile for an owned farm without fabricating crops."""
    ensure_rashkar_seeded(db)
    farm_ctx = resolve_owned_farm_context(farm_id, current_user, db)
    fid = farm_ctx["farm_id"]

    row = (
        db.query(RashkarFarmerResourceProfileModel)
        .filter(RashkarFarmerResourceProfileModel.farm_id == fid)
        .first()
    )
    active_cycle = get_active_crop_cycle(fid, db)
    return _profile_from_row(
        row=row,
        farm_ctx=farm_ctx,
        active_crop_code=active_cycle.crop_code if active_cycle else None,
        active_crop_stage=active_cycle.current_stage_code if active_cycle else None,
    )


@router.put("/farms/{farm_id}/profile", response_model=FarmerResourceProfile)
def upsert_farm_income_profile(
    farm_id: str,
    payload: FarmerResourceProfile,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FarmerResourceProfile:
    """Create or update the owned farm's resource profile in Postgres/SQLite."""
    ensure_rashkar_seeded(db)
    farm_ctx = resolve_owned_farm_context(farm_id, current_user, db)
    fid = farm_ctx["farm_id"]
    now = now_utc_naive()

    row = (
        db.query(RashkarFarmerResourceProfileModel)
        .filter(RashkarFarmerResourceProfileModel.farm_id == fid)
        .first()
    )
    if row is None:
        row = RashkarFarmerResourceProfileModel(
            farm_id=fid,
            owner_id=farm_ctx["owner_id"],
        )
        db.add(row)
    else:
        row.owner_id = farm_ctx["owner_id"]

    profile_fields = payload.model_dump()
    for field_name, field_value in profile_fields.items():
        if hasattr(row, field_name):
            setattr(row, field_name, field_value)
    row.updated_at_utc = now

    db.commit()
    db.refresh(row)

    active_cycle = get_active_crop_cycle(fid, db)
    return _profile_from_row(
        row=row,
        farm_ctx=farm_ctx,
        active_crop_code=active_cycle.crop_code if active_cycle else None,
        active_crop_stage=active_cycle.current_stage_code if active_cycle else None,
    )


@router.post("/farms/{farm_id}/discover", response_model=List[DiscoveredOpportunity])
def discover_farm_opportunities(
    farm_id: str,
    profile_override: Optional[FarmerResourceProfile] = Body(default=None),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[DiscoveredOpportunity]:
    """Rank feasibility-scored income enterprises for an owned farm."""
    ensure_rashkar_seeded(db)
    farm_ctx = resolve_owned_farm_context(farm_id, current_user, db)
    fid = farm_ctx["farm_id"]

    if profile_override is not None:
        profile = profile_override
    else:
        row = (
            db.query(RashkarFarmerResourceProfileModel)
            .filter(RashkarFarmerResourceProfileModel.farm_id == fid)
            .first()
        )
        active_cycle = get_active_crop_cycle(fid, db)
        profile = _profile_from_row(
            row=row,
            farm_ctx=farm_ctx,
            active_crop_code=active_cycle.crop_code if active_cycle else None,
            active_crop_stage=active_cycle.current_stage_code if active_cycle else None,
        )

    return IncomeEngine.match_opportunities(profile)


def _persist_scenario(
    analysis: EnterpriseFinancialAnalysis,
    farm_id: str,
    owner_id: str,
    labour_hours: float,
    land_acres: float,
    custom_assumptions: Optional[Dict[str, Any]],
    db: Session,
) -> None:
    scenario_row = RashkarIncomeScenarioModel(
        scenario_id=analysis.scenario_id,
        owner_id=owner_id,
        farm_id=farm_id,
        opportunity_id=analysis.opportunity_id,
        custom_budget_inr=analysis.custom_budget_inr,
        available_labour_hours_day=labour_hours,
        available_land_acres=land_acres,
        custom_assumptions=custom_assumptions or {},
        calculated_capex_inr=analysis.calculated_capex_inr,
        calculated_opex_annual_inr=analysis.calculated_opex_annual_inr,
        calculated_gross_revenue_inr=analysis.calculated_gross_revenue_inr,
        calculated_net_profit_annual_inr=analysis.calculated_net_profit_annual_inr,
        calculated_break_even_months=analysis.calculated_break_even_months,
        sensitivity_analysis=analysis.sensitivity_analysis,
        monthly_cash_flows=analysis.monthly_cash_flows,
        generated_at_utc=now_utc_naive(),
    )
    db.add(scenario_row)
    db.commit()


@router.post("/farms/{farm_id}/calculate-scenario", response_model=EnterpriseFinancialAnalysis)
def calculate_and_persist_farm_scenario(
    farm_id: str,
    payload: ScenarioCalculateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EnterpriseFinancialAnalysis:
    """Simulate 3-scenario enterprise financials for an owned farm and persist the scenario."""
    ensure_rashkar_seeded(db)
    farm_ctx = resolve_owned_farm_context(farm_id, current_user, db)
    fid = farm_ctx["farm_id"]

    opp = _assert_opportunity_exists(payload.opportunity_id, db)
    profile_row = (
        db.query(RashkarFarmerResourceProfileModel)
        .filter(RashkarFarmerResourceProfileModel.farm_id == fid)
        .first()
    )

    budget = (
        float(payload.custom_budget_inr)
        if payload.custom_budget_inr is not None
        else float(
            profile_row.available_investment_inr
            if profile_row and profile_row.available_investment_inr is not None
            else opp.min_investment_inr
        )
    )
    water = (
        payload.water_availability
        or (profile_row.water_availability if profile_row else None)
        or "seasonal_canal"
    )
    labour = (
        float(payload.available_labour_hours_day)
        if payload.available_labour_hours_day is not None
        else float(profile_row.family_labor_hours_day if profile_row else 2.0)
    )
    land = (
        float(payload.available_land_acres)
        if payload.available_land_acres is not None
        else float(profile_row.available_land_acres if profile_row else 0.5)
    )

    analysis = IncomeEngine.calculate_enterprise_financials(
        opportunity_id=payload.opportunity_id,
        custom_budget_inr=budget,
        water_availability=water,
    )
    _persist_scenario(
        analysis=analysis,
        farm_id=fid,
        owner_id=farm_ctx["owner_id"],
        labour_hours=labour,
        land_acres=land,
        custom_assumptions=payload.custom_assumptions,
        db=db,
    )
    return analysis


@router.post("/calculate-scenario", response_model=EnterpriseFinancialAnalysis)
def calculate_income_scenario(
    payload: ScenarioCalculateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EnterpriseFinancialAnalysis:
    """Run enterprise financial simulation (and persist when an owned farm_id is provided)."""
    ensure_rashkar_seeded(db)
    opp = _assert_opportunity_exists(payload.opportunity_id, db)

    if payload.farm_id:
        farm_ctx = resolve_owned_farm_context(payload.farm_id, current_user, db)
        fid = farm_ctx["farm_id"]
        profile_row = (
            db.query(RashkarFarmerResourceProfileModel)
            .filter(RashkarFarmerResourceProfileModel.farm_id == fid)
            .first()
        )
        budget = (
            float(payload.custom_budget_inr)
            if payload.custom_budget_inr is not None
            else float(
                profile_row.available_investment_inr
                if profile_row and profile_row.available_investment_inr is not None
                else opp.min_investment_inr
            )
        )
        water = (
            payload.water_availability
            or (profile_row.water_availability if profile_row else None)
            or "seasonal_canal"
        )
        analysis = IncomeEngine.calculate_enterprise_financials(
            opportunity_id=payload.opportunity_id,
            custom_budget_inr=budget,
            water_availability=water,
        )
        _persist_scenario(
            analysis=analysis,
            farm_id=fid,
            owner_id=farm_ctx["owner_id"],
            labour_hours=float(
                payload.available_labour_hours_day
                if payload.available_labour_hours_day is not None
                else (profile_row.family_labor_hours_day if profile_row else 2.0)
            ),
            land_acres=float(
                payload.available_land_acres
                if payload.available_land_acres is not None
                else (profile_row.available_land_acres if profile_row else 0.5)
            ),
            custom_assumptions=payload.custom_assumptions,
            db=db,
        )
        return analysis

    budget = (
        float(payload.custom_budget_inr)
        if payload.custom_budget_inr is not None
        else float(opp.min_investment_inr)
    )
    water = payload.water_availability or "seasonal_canal"
    return IncomeEngine.calculate_enterprise_financials(
        opportunity_id=payload.opportunity_id,
        custom_budget_inr=budget,
        water_availability=water,
    )


@router.post("/compare-opportunities", response_model=List[OpportunityComparisonItem])
def compare_income_opportunities(
    payload: CompareOpportunitiesRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[OpportunityComparisonItem]:
    """Compare selected enterprise options side by side under a common capital budget."""
    del current_user
    ensure_rashkar_seeded(db)
    for oid in payload.opportunity_ids:
        _assert_opportunity_exists(oid, db)
    return IncomeEngine.compare_opportunities(
        opportunity_ids=payload.opportunity_ids,
        custom_budget=payload.custom_budget_inr,
    )


@router.get("/farms/{farm_id}/plans", response_model=List[SavedIncomePlan])
def list_farm_saved_plans(
    farm_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[SavedIncomePlan]:
    """List saved income plans scoped to an owned farm."""
    farm_ctx = resolve_owned_farm_context(farm_id, current_user, db)
    rows = (
        db.query(RashkarSavedIncomePlanModel)
        .filter(RashkarSavedIncomePlanModel.farm_id == farm_ctx["farm_id"])
        .order_by(RashkarSavedIncomePlanModel.created_at_utc.desc())
        .all()
    )
    return [_row_to_saved_plan(row) for row in rows]


@router.post(
    "/farms/{farm_id}/plans",
    response_model=SavedIncomePlan,
    status_code=status.HTTP_201_CREATED,
)
def save_farm_income_plan(
    farm_id: str,
    payload: SaveIncomePlanRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SavedIncomePlan:
    """Calculate financials and save a bookmarked enterprise income plan for an owned farm."""
    ensure_rashkar_seeded(db)
    farm_ctx = resolve_owned_farm_context(farm_id, current_user, db)
    fid = farm_ctx["farm_id"]

    opp = _assert_opportunity_exists(payload.opportunity_id, db)
    profile_row = (
        db.query(RashkarFarmerResourceProfileModel)
        .filter(RashkarFarmerResourceProfileModel.farm_id == fid)
        .first()
    )
    water = (
        profile_row.water_availability
        if profile_row and profile_row.water_availability
        else "seasonal_canal"
    )
    analysis = IncomeEngine.calculate_enterprise_financials(
        opportunity_id=payload.opportunity_id,
        custom_budget_inr=payload.chosen_budget_inr,
        water_availability=water,
    )

    plan_row = RashkarSavedIncomePlanModel(
        plan_id=f"plan_{uuid.uuid4().hex[:12]}",
        owner_id=farm_ctx["owner_id"],
        farm_id=fid,
        opportunity_id=opp.opportunity_id,
        opportunity_title=opp.title,
        category=opp.category,
        chosen_budget_inr=float(payload.chosen_budget_inr),
        projected_annual_profit_inr=float(analysis.calculated_net_profit_annual_inr),
        projected_annual_savings_inr=float(analysis.calculated_annual_savings_inr),
        payback_months=analysis.calculated_break_even_months,
        break_even_reached=bool(analysis.break_even_reached),
        notes=payload.notes,
        created_at_utc=now_utc_naive(),
    )
    db.add(plan_row)
    db.commit()
    db.refresh(plan_row)
    return _row_to_saved_plan(plan_row)


@router.delete("/farms/{farm_id}/plans/{plan_id}")
def delete_farm_saved_plan(
    farm_id: str,
    plan_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Delete a saved income plan belonging to the owned farm."""
    farm_ctx = resolve_owned_farm_context(farm_id, current_user, db)
    row = (
        db.query(RashkarSavedIncomePlanModel)
        .filter(
            RashkarSavedIncomePlanModel.plan_id == plan_id,
            RashkarSavedIncomePlanModel.farm_id == farm_ctx["farm_id"],
        )
        .first()
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Saved income plan '{plan_id}' not found for farm '{farm_id}'.",
        )
    db.delete(row)
    db.commit()
    return {
        "status": "deleted",
        "plan_id": plan_id,
        "farm_id": farm_ctx["farm_id"],
    }
