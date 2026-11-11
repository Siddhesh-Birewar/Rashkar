from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# -----------------------------------------------------------------------------
# 1. Farmer Resource Profile Schema
# -----------------------------------------------------------------------------
class FarmerResourceProfile(BaseModel):
    available_investment_inr: float = Field(default=0.0, ge=0.0, description="Cash available for upfront setup")
    monthly_operating_budget_inr: float = Field(default=0.0, ge=0.0, description="Monthly cash available for recurring inputs")
    max_risk_capital_inr: Optional[float] = Field(default=None, description="Maximum amount comfortable risking")
    willing_to_borrow: bool = Field(default=False, description="Whether farmer considers institutional credit / KCC")
    
    total_farm_acres: Optional[float] = Field(default=None, ge=0.0)
    cultivated_acres: Optional[float] = Field(default=None, ge=0.0)
    available_land_acres: float = Field(default=0.0, ge=0.0, description="Spare uncultivated land")
    unused_land_acres: float = Field(default=0.0, ge=0.0, description="Spare parcel area")
    field_bunds_available: bool = Field(default=True, description="Usable perimeter / field bund area")
    
    has_animal_shed: bool = Field(default=False)
    has_storage_room: bool = Field(default=False)
    has_shaded_space: bool = Field(default=False)
    
    water_availability: str = Field(
        default="seasonal_canal",
        description="reliable_year_round, seasonal_canal, limited, rainfed_only, none, unknown"
    )
    water_months_available: List[int] = Field(default_factory=list, description="Calendar months 1-12 with available water")
    
    family_labor_hours_day: float = Field(default=2.0, ge=0.0, le=16.0, description="Family labor hours dedicated to diversification")
    hired_labor_possible: bool = Field(default=False)
    
    existing_livestock: str = Field(default="none", description="none, indigenous_cows, crossbred_cows, goats, desi_poultry, other")
    existing_assets: List[str] = Field(default_factory=list, description="tractor, pump, drip, sprinkler, tools, transport, electricity, vermicompost_pit")
    
    crop_byproducts: List[str] = Field(default_factory=list, description="soybean_straw, cotton_stalks, jowar_stover, onion_cull, cow_dung, none")
    byproduct_surplus_available: bool = Field(default=True, description="Surplus residue after primary livestock feeding and mulching")
    
    interests: List[str] = Field(default_factory=list, description="livestock, nursery, composting, food_processing, selling_produce, beekeeping, mushrooms, open_to_suggestions")
    has_transport: bool = Field(default=False, description="Ability to self-transport produce to local APMC / market")
    has_fpo_access: bool = Field(default=False, description="Active membership in local Farmer Producer Company or primary cooperative")
    distance_to_apmc_km: Optional[float] = Field(default=None, ge=0.0)
    
    risk_tolerance: str = Field(default="moderate", description="conservative, moderate, aggressive")
    category_preference: str = Field(default="all", description="all, zero_cash, very_low_cost, moderate_enterprise, crop_diversification, group_external")

    # Farmer Age & Personal Circumstances (Part A)
    age_range: Optional[str] = Field(
        default="36-45",
        description="under_25, 25-35, 36-45, 46-55, 56-65, above_65, prefer_not_to_say"
    )
    work_preference: Optional[str] = Field(
        default="daily_physical",
        description="daily_physical, light_physical, manage_supervise, family_help, hire_labor, low_attention"
    )
    payback_horizon: Optional[str] = Field(
        default="within_6_months",
        description="few_weeks, 3_to_6_months, 6_to_12_months, more_than_year"
    )
    family_management_role: Optional[str] = Field(
        default="self",
        description="self, family_member, multiple_family, hired_labor, fpo_group"
    )
    current_crop_code: Optional[str] = Field(default=None, description="Active standing crop code")
    current_crop_stage: Optional[str] = Field(default=None, description="Current growth stage code")

    @property
    def is_zero_budget(self) -> bool:
        return self.available_investment_inr <= 0.0 and self.monthly_operating_budget_inr <= 0.0


# -----------------------------------------------------------------------------
# 2. Opportunity Catalogue Item Schema
# -----------------------------------------------------------------------------
class OpportunityCatalogItem(BaseModel):
    opportunity_id: str
    title: str
    category: str  # zero_cash, very_low_cost, moderate_enterprise, crop_diversification, group_external
    is_cost_saving: bool = False
    tagline: str
    min_investment_inr: float = 0.0
    max_investment_inr: float = 0.0
    working_capital_required_inr: float = 0.0
    required_land_acres: float = 0.0
    required_space_type: str = "field"  # field, bund, shed, room, yard, none
    water_requirement: str = "none"  # none, very_low, low, moderate, high
    daily_labor_hours: float = 0.5
    risk_level: str = "low"  # low, moderate, high
    payback_period_months: int = 1
    potential_annual_profit_inr: float = 0.0
    potential_annual_savings_inr: float = 0.0
    summary: str = ""
    market_commodity: str = ""
    market_benchmark_price: str = ""
    market_source: str = ""
    market_verified: bool = True
    target_crops: List[str] = Field(default_factory=list)
    key_assumptions: List[str] = Field(default_factory=list)
    key_risks: List[str] = Field(default_factory=list)
    source_attribution: str = ""
    minimum_viable_unit_description: str = ""
    production_cycle_days: int = 30
    revenue_delay_months: int = 1


# -----------------------------------------------------------------------------
# 3. Discovered Opportunity (Personalized Result)
# -----------------------------------------------------------------------------
class DiscoveredOpportunity(BaseModel):
    opportunity: OpportunityCatalogItem
    feasibility_status: str  # USES_EXISTING_RESOURCES, FEASIBLE_NOW, NOT_CURRENTLY_AFFORDABLE, NEEDS_MORE_WATER_OR_LABOR, EQUIPMENT_NOT_OWNED, NOT_SUITABLE_CURRENTLY
    suitability_score: int  # 0 to 100 based on weighted criteria
    is_feasible: bool
    capital_gap_inr: float = 0.0
    matching_resources: List[str] = Field(default_factory=list)
    missing_requirements: List[str] = Field(default_factory=list)
    primary_benefit_label: str = ""
    evidence_source: str = ""
    estimated_annual_profit_inr: float = 0.0
    estimated_annual_savings_inr: float = 0.0
    payback_months: float = 1.0
    market_benchmark_summary: str = ""
    tripartite_return: Optional[dict] = None
    # 5 Clean Farmer Categories (Part D.13 & E.14)
    feasibility_category: str = "CAN_TRY_WITH_WHAT_YOU_HAVE"  # CAN_TRY_WITH_WHAT_YOU_HAVE, CAN_TRY_WITH_SMALL_ADDITIONAL_AMOUNT, NEEDS_MORE_MONEY, NEEDS_MORE_INFORMATION, NOT_SUITABLE_CURRENTLY
    farmer_summary_qa: Optional[Dict[str, Any]] = None  # 6 standard plain-language questions
    # Backward compatibility with earlier frontend models
    suitability_score_pct: Optional[int] = None
    is_suitable: Optional[bool] = None
    suitability_verdict: Optional[str] = None
    reasons_why_suitable: List[str] = Field(default_factory=list)
    reasons_why_unsuitable: List[str] = Field(default_factory=list)


# Backward compatibility alias
ScoredOpportunity = DiscoveredOpportunity


# -----------------------------------------------------------------------------
# 4. Multi-Scenario Financial Projections
# -----------------------------------------------------------------------------
class FinancialScenarioItem(BaseModel):
    name: str
    price_assumption: str
    cost_assumption: str
    gross_annual_revenue_inr: float
    annual_money_saved_inr: float = 0.0
    annual_opex_inr: float
    cash_operating_surplus_inr: float = 0.0
    imputed_family_labor_cost_inr: float = 0.0
    economic_profit_inr: float = 0.0
    net_annual_profit_inr: float
    break_even_months: Optional[float] = None
    break_even_reached: bool = True
    monthly_net_cash_flow_inr: List[float] = Field(default_factory=list)


class EnterpriseFinancialAnalysis(BaseModel):
    scenario_id: str
    opportunity_id: str
    opportunity_title: str
    category: str
    is_cost_saving: bool = False
    custom_budget_inr: float
    calculated_capex_inr: float
    working_capital_inr: float = 0.0
    total_initial_outlay_inr: float = 0.0
    calculated_gross_revenue_inr: float = 0.0
    calculated_annual_savings_inr: float = 0.0
    calculated_opex_annual_inr: float = 0.0
    cash_operating_surplus_inr: float = 0.0
    imputed_family_labor_cost_inr: float = 0.0
    economic_profit_inr: float = 0.0
    calculated_net_profit_annual_inr: float = 0.0
    calculated_break_even_months: Optional[float] = None
    break_even_reached: bool = True
    monthly_cash_flows: List[float] = Field(default_factory=list)
    assumptions_applied: List[str] = Field(default_factory=list)
    risks_to_monitor: List[str] = Field(default_factory=list)
    source_attribution: str = ""
    scenarios: Dict[str, FinancialScenarioItem] = Field(default_factory=dict)
    local_mandi_benchmark: Dict[str, Any] = Field(default_factory=dict)
    sensitivity_analysis: Dict[str, Any] = Field(default_factory=dict)
    nabard_source_citation: str = ""
    disclaimer: str = ""


# -----------------------------------------------------------------------------
# 5. Side-by-Side Comparison
# -----------------------------------------------------------------------------
class OpportunityComparisonItem(BaseModel):
    opportunity_id: str
    title: str
    category: str
    is_cost_saving: bool = False
    initial_investment_inr: float
    net_annual_profit_inr: float
    annual_money_saved_inr: float = 0.0
    payback_months: Optional[float] = None
    break_even_reached: bool = True
    land_required_acres: float
    water_needs: str
    daily_labor_hours: float
    risk_level: str
    suitability_verdict: str


# -----------------------------------------------------------------------------
# 6. Saved Farmer Plan
# -----------------------------------------------------------------------------
class SavedIncomePlan(BaseModel):
    plan_id: str
    farmer_id: str
    farm_id: str
    opportunity_id: str
    opportunity_title: str
    category: str
    chosen_budget_inr: float
    projected_annual_profit_inr: float
    projected_annual_savings_inr: float = 0.0
    payback_months: Optional[float] = None
    break_even_reached: bool = True
    notes: Optional[str] = None
    created_at_utc: str


# -----------------------------------------------------------------------------
# 7. Extended Farm Income Diversification Schemas
# -----------------------------------------------------------------------------
class FeasibilityStatus(str):
    GOOD_POTENTIAL_FIT = "GOOD_POTENTIAL_FIT"
    POTENTIALLY_SUITABLE = "POTENTIALLY_SUITABLE"
    MORE_INFORMATION_REQUIRED = "MORE_INFORMATION_REQUIRED"
    NOT_SUITABLE = "NOT_SUITABLE"


class DetailedOpportunityItem(BaseModel):
    opportunity_id: str
    name: str
    category: str
    category_name: str = ""
    farmer_friendly_description: str
    business_model: str
    suitable_geography: str
    suitable_land_acres: float = 0.0
    unit_of_operation: str
    minimum_scale: float = 0.0
    typical_scale: float = 1.0
    water_requirement: str = "none"
    soil_climate_considerations: str = ""
    initial_setup_requirements: str = ""
    recurring_requirements: str = ""
    equipment_and_infrastructure: str = ""
    setup_investment_range: Dict[str, float] = Field(default_factory=dict)
    recurring_operating_cost_range: Dict[str, float] = Field(default_factory=dict)
    production_yield_assumptions: Dict[str, Any] = Field(default_factory=dict)
    expected_sales_revenue_assumptions: Dict[str, Any] = Field(default_factory=dict)
    estimated_operating_surplus: Dict[str, float] = Field(default_factory=dict)
    time_to_first_income_months: float = 1.0
    production_cycle_days: int = 30
    labour_requirements: Dict[str, Any] = Field(default_factory=dict)
    electricity_requirements: str = "none"
    market_access_requirements: str = "local_village"
    major_risks: List[str] = Field(default_factory=list)
    permissions_or_registrations: List[str] = Field(default_factory=list)
    source_references: List[str] = Field(default_factory=list)
    reference_geography: str = "Maharashtra"
    last_verified_date: str = "2026-11-01"
    confidence_classification: str = "NABARD_MODEL_PROJECT"
    # Personalized Matching additions
    feasibility_status: str = "POTENTIALLY_SUITABLE"
    why_recommended: List[str] = Field(default_factory=list)
    supporting_resources: List[str] = Field(default_factory=list)
    missing_requirements: List[str] = Field(default_factory=list)
    what_to_arrange: List[str] = Field(default_factory=list)
    risks_to_consider: List[str] = Field(default_factory=list)


class OpportunityCategoryItem(BaseModel):
    key: str
    name: str
    tagline: str
    count: int = 0


class FarmResourceProfileUpdateRequest(BaseModel):
    available_diversification_acres: float = Field(default=0.5, ge=0.0)
    available_investment_inr: float = Field(default=0.0, ge=0.0)
    monthly_operating_budget_inr: float = Field(default=0.0, ge=0.0)
    water_source: str = Field(default="seasonal_canal")
    has_electricity: bool = Field(default=True)
    electricity_type: str = Field(default="single_phase")
    family_labor_hours_day: float = Field(default=2.0, ge=0.0, le=16.0)
    has_animal_shed: bool = Field(default=False)
    has_storage_room: bool = Field(default=False)
    has_farm_pond: bool = Field(default=False)
    existing_equipment: List[str] = Field(default_factory=list)
    existing_livestock: List[str] = Field(default_factory=list)
    market_access_type: str = Field(default="taluka_apmc")
    preferred_category: Optional[str] = None


class FinancialScenarioSimulateRequest(BaseModel):
    opportunity_id: str
    allocated_scale: float = Field(default=1.0, gt=0.0)
    custom_setup_investment_inr: Optional[float] = Field(default=None, ge=0.0)
    custom_annual_opex_inr: Optional[float] = Field(default=None, ge=0.0)
    custom_yield: Optional[float] = Field(default=None, ge=0.0)
    custom_sale_price: Optional[float] = Field(default=None, ge=0.0)
    scenario_mode: str = Field(default="BASE", description="LOW, BASE, HIGH")


class FinancialScenarioSimulateResponse(BaseModel):
    opportunity_id: str
    opportunity_name: str
    category: str
    scale_unit: str
    allocated_scale: float
    initial_setup_investment_inr: float
    recurring_operating_expenses_inr: float
    expected_gross_revenue_inr: float
    estimated_operating_surplus_inr: float
    break_even_estimate: str
    estimated_payback_months: Optional[float] = None
    scenario_mode: str
    scenarios: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    assumptions_applied: List[str] = Field(default_factory=list)
    key_risks: List[str] = Field(default_factory=list)
    source_attribution: str = ""
    disclaimer: str = ""


class CompareOpportunitiesPostRequest(BaseModel):
    opportunity_ids: List[str]
    allocated_acres: float = Field(default=0.5, ge=0.0)
    available_budget_inr: float = Field(default=50000.0, ge=0.0)


class SaveFarmPlanRequest(BaseModel):
    opportunity_id: str
    allocated_scale: float = Field(default=1.0, gt=0.0)
    scale_unit: str = "acre"
    custom_budget_inr: float = Field(default=0.0, ge=0.0)
    projected_operating_surplus_inr: float = Field(default=0.0)
    scenario_mode: str = Field(default="BASE")
    notes: Optional[str] = None

