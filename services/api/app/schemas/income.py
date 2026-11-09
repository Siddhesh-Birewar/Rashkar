from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# Opportunity Definition Schema
class OpportunityCatalogItem(BaseModel):
    opportunity_id: str
    title: str
    category: str  # livestock, byproduct_utilization, value_addition, horticulture, agroforestry
    tagline: str
    min_investment_inr: float
    max_investment_inr: float
    required_land_acres: float
    water_requirement: str  # high, moderate, low, very_low
    daily_labor_hours: float
    risk_level: str  # low, moderate, high
    payback_period_months: int
    potential_annual_profit_inr: float
    summary: str
    market_commodity: str
    market_benchmark_price: str
    market_source: str
    target_crops: List[str] = Field(default_factory=list)
    key_assumptions: List[str] = Field(default_factory=list)
    key_risks: List[str] = Field(default_factory=list)
    source_attribution: str = ""

# Farmer Resource Profile Schema
class FarmerResourceProfile(BaseModel):
    available_investment_inr: float = Field(default=50000.0, ge=5000.0)
    working_capital_inr: float = Field(default=15000.0, ge=0.0)
    available_land_acres: float = Field(default=0.5, ge=0.0)
    unused_land_acres: float = Field(default=0.25, ge=0.0)
    water_availability: str = Field(default="seasonal_canal", description="reliable_year_round, seasonal_canal, rainfed_limited")
    family_labor_hours_day: float = Field(default=2.5, ge=0.5, le=14.0)
    existing_livestock: str = Field(default="none", description="none, cows, goats, poultry")
    has_storage_or_shed: bool = Field(default=False)
    risk_tolerance: str = Field(default="moderate", description="conservative, moderate, aggressive")
    category_preference: str = Field(default="all", description="all, livestock, horticulture, byproduct_utilization, value_addition")

# Scored Opportunity Response
class ScoredOpportunity(BaseModel):
    opportunity: OpportunityCatalogItem
    suitability_score_pct: int
    is_suitable: bool
    suitability_verdict: str  # Highly Recommended, Suitable with Constraints, Capital Limited, Water Constrained
    reasons_why_suitable: List[str]
    reasons_why_unsuitable: List[str]

# Detailed Financial Model Response
class FinancialScenarioItem(BaseModel):
    name: str
    price_assumption: str
    cost_assumption: str
    gross_annual_revenue_inr: float
    annual_opex_inr: float
    net_annual_profit_inr: float
    break_even_months: float
    monthly_net_cash_flow_inr: List[float]

class EnterpriseFinancialAnalysis(BaseModel):
    opportunity_id: str
    opportunity_title: str
    category: str
    custom_budget_inr: float
    calculated_capex_inr: float
    working_capital_inr: float = 0.0
    total_initial_outlay_inr: float = 0.0
    calculated_gross_revenue_inr: float = 0.0
    calculated_opex_annual_inr: float = 0.0
    calculated_net_profit_annual_inr: float = 0.0
    calculated_break_even_months: float = 0.0
    assumptions_applied: List[str] = Field(default_factory=list)
    risks_to_monitor: List[str] = Field(default_factory=list)
    source_attribution: str = ""
    scenarios: Dict[str, FinancialScenarioItem] = Field(default_factory=dict)
    local_mandi_benchmark: Dict[str, Any] = Field(default_factory=dict)
    sensitivity_analysis: Dict[str, Any] = Field(default_factory=dict)
    nabard_source_citation: str = ""
    disclaimer: str = ""

class OpportunityComparisonItem(BaseModel):
    opportunity_id: str
    title: str
    category: str
    initial_investment_inr: float
    net_annual_profit_inr: float
    payback_months: float
    land_required_acres: float
    water_needs: str
    daily_labor_hours: float
    risk_level: str
    suitability_verdict: str
