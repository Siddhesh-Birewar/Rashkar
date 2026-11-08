from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.app.db.session import get_db
from backend.app.db.models.income import IncomeOpportunityModel, IncomeScenarioModel
from backend.app.core.timezone import now_utc

router = APIRouter()

class OpportunityResponse(BaseModel):
    opportunity_id: str
    title: str
    category: str
    target_crops: List[str]
    required_resources: List[str]
    min_investment_inr: float
    max_investment_inr: float
    payback_period_months: int
    potential_annual_profit_inr: float
    risk_level: str
    summary: str
    key_assumptions: List[str]
    key_risks: List[str]
    source_attribution: str

class ScenarioCalculateRequest(BaseModel):
    opportunity_id: str
    custom_budget_inr: float = Field(..., gt=0, json_schema_extra={"example": 25000.0})
    available_labour_hours_day: float = Field(default=2.0, ge=0.5, le=12.0)
    available_land_acres: float = Field(default=0.5, ge=0.0)
    custom_assumptions: Optional[Dict[str, Any]] = None

class ScenarioResponse(BaseModel):
    opportunity_id: str
    opportunity_title: str
    category: str
    custom_budget_inr: float
    calculated_capex_inr: float
    calculated_opex_annual_inr: float
    calculated_gross_revenue_inr: float
    calculated_net_profit_annual_inr: float
    calculated_break_even_months: float
    working_capital_inr: float = 0.0
    scenarios: Optional[Dict[str, Any]] = None
    sensitivity_analysis: Dict[str, Any]
    assumptions_applied: List[str]
    risks_to_monitor: List[str]
    source_attribution: str
    disclaimer: str

@router.get("/opportunities", response_model=List[OpportunityResponse])
def get_opportunities(
    category: Optional[str] = Query(None, description="Filter by category e.g. livestock, byproduct_utilization, value_addition"),
    crop_code: Optional[str] = Query(None, description="Filter by crop e.g. soybean, cotton"),
    max_budget: Optional[float] = Query(None, description="Max budget in INR"),
    db: Session = Depends(get_db)
):
    query = db.query(IncomeOpportunityModel).filter(IncomeOpportunityModel.is_active == True)
    if category:
        query = query.filter(IncomeOpportunityModel.category == category)
    if max_budget:
        query = query.filter(IncomeOpportunityModel.min_investment_inr <= max_budget)
    
    opps = query.all()
    if crop_code:
        c_clean = crop_code.lower()
        filtered = [o for o in opps if c_clean in [c.lower() for c in (o.target_crops or [])]]
        if filtered:
            opps = filtered
    
    return [
        OpportunityResponse(
            opportunity_id=o.opportunity_id,
            title=o.title,
            category=o.category,
            target_crops=o.target_crops or [],
            required_resources=o.required_resources or [],
            min_investment_inr=o.min_investment_inr,
            max_investment_inr=o.max_investment_inr,
            payback_period_months=o.payback_period_months,
            potential_annual_profit_inr=o.potential_annual_profit_inr,
            risk_level=o.risk_level,
            summary=o.summary,
            key_assumptions=o.key_assumptions or [],
            key_risks=o.key_risks or [],
            source_attribution=o.source_attribution
        )
        for o in opps
    ]

@router.post("/calculate-scenario", response_model=ScenarioResponse)
def calculate_income_scenario(request: ScenarioCalculateRequest, db: Session = Depends(get_db)):
    opp = db.query(IncomeOpportunityModel).filter(
        IncomeOpportunityModel.opportunity_id == request.opportunity_id
    ).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    budget = request.custom_budget_inr
    scale_factor = max(0.5, min(3.0, budget / opp.min_investment_inr))
    
    capex = round(budget, 2)
    working_capital = round(budget * 0.15, 2)
    opex_ratio = 0.25 if opp.risk_level == "low" else 0.35
    opex_annual = round(capex * opex_ratio, 2)
    
    # Base scenario
    gross_revenue = round(opp.potential_annual_profit_inr * scale_factor + opex_annual, 2)
    net_profit = round(gross_revenue - opex_annual, 2)
    monthly_net = max(1.0, net_profit / 12.0)
    break_even_months = round(capex / monthly_net, 1)

    # Conservative scenario (-15% revenue drop, +10% cost increase)
    cons_rev = round(gross_revenue * 0.85, 2)
    cons_opex = round(opex_annual * 1.10, 2)
    cons_profit = round(cons_rev - cons_opex, 2)
    cons_be = round(capex / max(1.0, cons_profit / 12.0), 1)

    # Optimistic scenario (+15% revenue expansion, -5% efficiency)
    opt_rev = round(gross_revenue * 1.15, 2)
    opt_opex = round(opex_annual * 0.95, 2)
    opt_profit = round(opt_rev - opt_opex, 2)
    opt_be = round(capex / max(1.0, opt_profit / 12.0), 1)

    # Sensitivity analysis (+10% costs, -10% revenue)
    stress_rev = gross_revenue * 0.90
    stress_opex = opex_annual * 1.10
    stress_profit = round(stress_rev - stress_opex, 2)

    return ScenarioResponse(
        opportunity_id=opp.opportunity_id,
        opportunity_title=opp.title,
        category=opp.category,
        custom_budget_inr=budget,
        calculated_capex_inr=capex,
        calculated_opex_annual_inr=opex_annual,
        calculated_gross_revenue_inr=gross_revenue,
        calculated_net_profit_annual_inr=net_profit,
        calculated_break_even_months=break_even_months,
        working_capital_inr=working_capital,
        scenarios={
            "conservative": {
                "label": "Conservative (-15% Market Realisation, +10% Input Cost)",
                "gross_revenue_inr": cons_rev,
                "opex_annual_inr": cons_opex,
                "net_profit_annual_inr": cons_profit,
                "break_even_months": cons_be
            },
            "base": {
                "label": "Base (Current NABARD / KVK Norms)",
                "gross_revenue_inr": gross_revenue,
                "opex_annual_inr": opex_annual,
                "net_profit_annual_inr": net_profit,
                "break_even_months": break_even_months
            },
            "optimistic": {
                "label": "Optimistic (+15% Premium Grade & Direct Marketing)",
                "gross_revenue_inr": opt_rev,
                "opex_annual_inr": opt_opex,
                "net_profit_annual_inr": opt_profit,
                "break_even_months": opt_be
            }
        },
        sensitivity_analysis={
            "base_case_annual_profit_inr": net_profit,
            "downside_10pct_market_drop_profit_inr": stress_profit,
            "variance_inr": round(net_profit - stress_profit, 2)
        },
        assumptions_applied=opp.key_assumptions or [],
        risks_to_monitor=opp.key_risks or [],
        source_attribution=opp.source_attribution,
        disclaimer="Transparent planning scenario only. Projections are based on KVK/ICAR regional benchmarks and do not guarantee market prices or revenue."
    )
