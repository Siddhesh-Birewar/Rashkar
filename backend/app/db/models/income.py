from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Float, Integer, ForeignKey, JSON, Boolean
from backend.app.db.session import Base
from backend.app.core.timezone import now_utc

class FarmerResourceProfileModel(Base):
    """
    Persisted farmer resource profile used to personalize income opportunities.
    """
    __tablename__ = "farmer_resource_profiles"

    farm_id = Column(String(50), primary_key=True, index=True)
    farmer_id = Column(String(50), nullable=False, index=True)
    available_investment_inr = Column(Float, default=0.0)
    monthly_operating_budget_inr = Column(Float, default=0.0)
    max_risk_capital_inr = Column(Float, nullable=True)
    willing_to_borrow = Column(Boolean, default=False)
    
    total_farm_acres = Column(Float, nullable=True)
    cultivated_acres = Column(Float, nullable=True)
    available_land_acres = Column(Float, default=0.0)
    unused_land_acres = Column(Float, default=0.0)
    field_bunds_available = Column(Boolean, default=True)
    
    has_animal_shed = Column(Boolean, default=False)
    has_storage_room = Column(Boolean, default=False)
    has_shaded_space = Column(Boolean, default=False)
    
    water_availability = Column(String(50), default="seasonal_canal")
    water_months_available = Column(JSON, default=list)
    
    family_labor_hours_day = Column(Float, default=2.0)
    hired_labor_possible = Column(Boolean, default=False)
    
    existing_livestock = Column(String(50), default="none")
    existing_assets = Column(JSON, default=list)
    crop_byproducts = Column(JSON, default=list)
    byproduct_surplus_available = Column(Boolean, default=True)
    
    interests = Column(JSON, default=list)
    has_transport = Column(Boolean, default=False)
    has_fpo_access = Column(Boolean, default=False)
    distance_to_apmc_km = Column(Float, nullable=True)
    
    risk_tolerance = Column(String(20), default="moderate")
    category_preference = Column(String(50), default="all")
    updated_at_utc = Column(DateTime, default=now_utc, onupdate=now_utc)

class IncomeOpportunityModel(Base):
    """
    Curated catalogue of agro-allied, value-addition and diversification opportunities
    grounded in Maharashtra agro-climatic conditions.
    """
    __tablename__ = "income_opportunities"

    opportunity_id = Column(String(50), primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    category = Column(String(50), nullable=False)  # zero_cash, very_low_cost, moderate_enterprise, crop_diversification, group_external
    is_cost_saving = Column(Boolean, default=False)
    tagline = Column(String(200), default="")
    target_crops = Column(JSON, default=list)  # Associated crops e.g. ["cotton", "soybean", "sugarcane"]
    required_resources = Column(JSON, default=list)  # e.g. ["land", "water", "shed", "crop_residue"]
    min_investment_inr = Column(Float, nullable=False, default=0.0)
    max_investment_inr = Column(Float, nullable=False, default=0.0)
    working_capital_required_inr = Column(Float, default=0.0)
    payback_period_months = Column(Integer, nullable=False, default=1)
    potential_annual_profit_inr = Column(Float, nullable=False, default=0.0)
    potential_annual_savings_inr = Column(Float, default=0.0)
    risk_level = Column(String(20), default="moderate")  # low, moderate, high
    summary = Column(Text, nullable=False)
    market_commodity = Column(String(100), default="")
    market_benchmark_price = Column(String(100), default="")
    market_source = Column(String(150), default="")
    key_assumptions = Column(JSON, default=list)
    key_risks = Column(JSON, default=list)
    source_attribution = Column(String(200), nullable=False)  # e.g., "KVK Baramati / ICAR-NIASM"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=now_utc)

class IncomeScenarioModel(Base):
    """
    Farmer-specific editable financial scenario calculation.
    Deterministic, transparent, reproducible.
    """
    __tablename__ = "income_scenarios"

    scenario_id = Column(String(50), primary_key=True, index=True)
    farmer_id = Column(String(50), nullable=False, index=True)
    farm_id = Column(String(50), nullable=False, index=True)
    opportunity_id = Column(String(50), ForeignKey("income_opportunities.opportunity_id"), nullable=False)
    custom_budget_inr = Column(Float, nullable=False)
    available_labour_hours_day = Column(Float, default=2.0)
    available_land_acres = Column(Float, default=0.5)
    custom_assumptions = Column(JSON, default=dict)
    calculated_capex_inr = Column(Float, nullable=False)
    calculated_opex_annual_inr = Column(Float, nullable=False)
    calculated_gross_revenue_inr = Column(Float, nullable=False)
    calculated_net_profit_annual_inr = Column(Float, nullable=False)
    calculated_break_even_months = Column(Float, nullable=True)
    sensitivity_analysis = Column(JSON, default=dict)
    monthly_cash_flows = Column(JSON, default=list)
    generated_at_utc = Column(DateTime, default=now_utc)

class SavedIncomePlanModel(Base):
    """
    Saved opportunity plans for farmers.
    """
    __tablename__ = "saved_income_plans"

    plan_id = Column(String(50), primary_key=True, index=True)
    farmer_id = Column(String(50), nullable=False, index=True)
    farm_id = Column(String(50), nullable=False, index=True)
    opportunity_id = Column(String(50), nullable=False)
    opportunity_title = Column(String(150), nullable=False)
    category = Column(String(50), nullable=False)
    chosen_budget_inr = Column(Float, nullable=False)
    projected_annual_profit_inr = Column(Float, nullable=False)
    projected_annual_savings_inr = Column(Float, default=0.0)
    payback_months = Column(Float, nullable=True)
    break_even_reached = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at_utc = Column(DateTime, default=now_utc)
