"""Income Diversification — catalogue, matching and financial simulation endpoints.

Ported from the Rashkar `yeild-and-heat-risk-feature` branch (7b5641e) and adapted
to CropNet. The source's DB-backed farm-profile / saved-plan routes require
Rashkar-only tables (farms plots, income plans) and are intentionally omitted;
this module exposes the self-contained income engine.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from cropnet.services.api.app.schemas.income import (
    OpportunityCatalogItem,
    FarmerResourceProfile,
    DiscoveredOpportunity,
    EnterpriseFinancialAnalysis,
    OpportunityComparisonItem,
)
from cropnet.services.api.app.services.income.catalog import (
    EXTENDED_OPPORTUNITY_CATALOG,
    get_opportunity_by_id,
)
from cropnet.services.api.app.services.income.engine import IncomeEngine

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


@router.get("/opportunities", response_model=List[OpportunityCatalogItem])
def get_opportunities(
    category: Optional[str] = Query(None, description="zero_cash, very_low_cost, moderate_enterprise, crop_diversification, group_external"),
    crop_code: Optional[str] = Query(None, description="Filter by crop context"),
    max_budget: Optional[float] = Query(None, description="Max budget in INR"),
):
    """Retrieve the canonical diversification opportunities across all 5 tiers."""
    opps = EXTENDED_OPPORTUNITY_CATALOG
    if category and category != "all":
        opps = [o for o in opps if o.category == category]
    if crop_code and crop_code != "all":
        opps = [
            o for o in opps
            if not o.target_crops or "all" in o.target_crops
            or crop_code.lower() in [c.lower() for c in o.target_crops]
        ]
    if max_budget is not None:
        opps = [o for o in opps if o.min_investment_inr <= max_budget]
    return opps


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityCatalogItem)
def get_single_opportunity(opportunity_id: str):
    """Retrieve a single opportunity definition by ID."""
    opp = get_opportunity_by_id(opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail=f"Opportunity with ID '{opportunity_id}' not found.")
    return opp


@router.post("/match-opportunities", response_model=List[DiscoveredOpportunity])
def match_opportunities_to_farmer(profile: FarmerResourceProfile):
    """Discover and rank opportunities against the farmer's resources."""
    return IncomeEngine.match_opportunities(profile)


@router.post("/calculate-scenario", response_model=EnterpriseFinancialAnalysis)
def calculate_income_scenario(request: ScenarioCalculateRequest):
    """3-scenario financial simulation with monthly cash flows and break-even."""
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
    """Side-by-side comparison of selected enterprises."""
    if not request.opportunity_ids:
        raise HTTPException(status_code=400, detail="Must provide at least one opportunity ID.")
    return IncomeEngine.compare_opportunities(request.opportunity_ids, request.custom_budget_inr)
