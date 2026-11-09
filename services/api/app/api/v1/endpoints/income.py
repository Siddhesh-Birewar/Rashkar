from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from cropnet.services.api.app.core.database import get_db
from cropnet.services.api.app.schemas.income import (
    OpportunityCatalogItem,
    FarmerResourceProfile,
    ScoredOpportunity,
    EnterpriseFinancialAnalysis,
    OpportunityComparisonItem
)
from cropnet.services.api.app.services.income.engine import IncomeEngine, OPPORTUNITY_CATALOG

router = APIRouter()

class ScenarioCalculateRequest(BaseModel):
    opportunity_id: str
    custom_budget_inr: float = Field(..., gt=0, json_schema_extra={"example": 50000.0})
    available_labour_hours_day: float = Field(default=2.5, ge=0.5, le=14.0)
    available_land_acres: float = Field(default=0.5, ge=0.0)
    water_availability: str = Field(default="seasonal_canal")
    custom_assumptions: Optional[Dict[str, Any]] = None

class CompareOpportunitiesRequest(BaseModel):
    opportunity_ids: List[str]
    custom_budget_inr: float = Field(default=60000.0, gt=0)

@router.get("/opportunities", response_model=List[OpportunityCatalogItem])
def get_opportunities(
    category: Optional[str] = Query(None, description="Filter by category e.g. livestock, horticulture, byproduct_utilization, value_addition"),
    crop_code: Optional[str] = Query(None, description="Filter by crop context"),
    max_budget: Optional[float] = Query(None, description="Max budget in INR")
):
    """
    Retrieve full catalog of 9 canonical agro-enterprise diversification opportunities grounded in NABARD unit costs.
    """
    opps = OPPORTUNITY_CATALOG
    if category and category != "all":
        opps = [o for o in opps if o.category == category]
    if crop_code and crop_code != "all":
        opps = [o for o in opps if not o.target_crops or "all" in o.target_crops or crop_code.lower() in [c.lower() for c in o.target_crops]]
    if max_budget:
        opps = [o for o in opps if o.min_investment_inr <= max_budget]
    return opps

@router.post("/match-opportunities", response_model=List[ScoredOpportunity])
def match_opportunities_to_farmer(profile: FarmerResourceProfile):
    """
    Score and filter all enterprise opportunities against the farmer's actual resources:
    capital, land, water, family labor, risk tolerance, and category preference.
    Returns explicit reasons why each opportunity is suitable or unsuitable.
    """
    return IncomeEngine.match_opportunities(profile)

@router.post("/calculate-scenario", response_model=EnterpriseFinancialAnalysis)
def calculate_income_scenario(request: ScenarioCalculateRequest):
    """
    Produce a rigorous 3-scenario financial simulation (Conservative, Base, Optimistic)
    with 12-month monthly cash flows, break-even months, Agmarknet mandi benchmarks, and sensitivity analysis.
    """
    opp = next((o for o in OPPORTUNITY_CATALOG if o.opportunity_id == request.opportunity_id), None)
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
    Produce a side-by-side comparison matrix for selected enterprise alternatives.
    """
    if not request.opportunity_ids:
        raise HTTPException(status_code=400, detail="Must provide at least one opportunity ID.")
    return IncomeEngine.compare_opportunities(request.opportunity_ids, request.custom_budget_inr)
