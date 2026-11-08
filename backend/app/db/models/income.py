from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Float, Integer, ForeignKey, JSON, Boolean
from backend.app.db.session import Base
from backend.app.core.timezone import now_utc

class IncomeOpportunityModel(Base):
    """
    Curated catalogue of agro-allied, value-addition and diversification opportunities
    grounded in Maharashtra agro-climatic conditions.
    """
    __tablename__ = "income_opportunities"

    opportunity_id = Column(String(50), primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    category = Column(String(50), nullable=False)  # livestock, value_addition, agroforestry, horticulture, byproduct
    target_crops = Column(JSON, default=list)  # Associated crops e.g. ["cotton", "soybean", "sugarcane"]
    required_resources = Column(JSON, default=list)  # e.g. ["land", "water", "shed", "crop_residue"]
    min_investment_inr = Column(Float, nullable=False)
    max_investment_inr = Column(Float, nullable=False)
    payback_period_months = Column(Integer, nullable=False)
    potential_annual_profit_inr = Column(Float, nullable=False)
    risk_level = Column(String(20), default="moderate")  # low, moderate, high
    summary = Column(Text, nullable=False)
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
    calculated_break_even_months = Column(Float, nullable=False)
    sensitivity_analysis = Column(JSON, default=dict)
    generated_at_utc = Column(DateTime, default=now_utc)
