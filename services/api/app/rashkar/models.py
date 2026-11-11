"""SQLAlchemy ORM models for the strictly additive RASHKAR tables (`rashkar_*`).

All models inherit CropNet's `Base` so they bind to the same SQLAlchemy metadata
and reference CropNet's canonical `farms.id` (`String(36)`) with cascade delete.
"""

import uuid
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)

try:
    from cropnet.services.api.app.models.soil_and_farm import Base
except ImportError:
    from app.models.soil_and_farm import Base

from .timezone import now_utc_naive


def _new_uuid() -> str:
    return str(uuid.uuid4())


class RashkarCropCycleModel(Base):
    """Registered crop cycle linked to a canonical CropNet farm."""

    __tablename__ = "rashkar_crop_cycles"

    id = Column(String(36), primary_key=True, index=True, default=_new_uuid)
    farm_id = Column(
        String(36),
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    owner_id = Column(String(36), nullable=False, index=True)
    crop_code = Column(String(50), nullable=False, index=True)
    variety_name = Column(String(100), nullable=True)
    sowing_date = Column(Date, nullable=True)
    season = Column(String(30), nullable=True)
    planted_area_acres = Column(Float, nullable=True)
    irrigation_type = Column(String(50), nullable=True)
    current_stage_code = Column(String(50), nullable=True)
    stage_source = Column(String(30), default="estimated_from_das", nullable=False)
    stage_confidence = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at_utc = Column(DateTime, default=now_utc_naive, nullable=False)
    updated_at_utc = Column(
        DateTime,
        default=now_utc_naive,
        onupdate=now_utc_naive,
        nullable=False,
    )


class RashkarCanonicalCropModel(Base):
    """Canonical crop master catalogue (38 Maharashtra crops & APY aliases)."""

    __tablename__ = "rashkar_canonical_crops"

    crop_code = Column(String(50), primary_key=True, index=True)
    common_name_en = Column(String(100), nullable=False)
    common_name_mr = Column(String(100), nullable=False)
    botanical_name = Column(String(150), nullable=False)
    crop_category = Column(String(50), nullable=False)
    standard_season = Column(String(50), nullable=False)
    is_pioneer_pilot_crop = Column(Boolean, default=False, nullable=False)
    support_level = Column(String(50), default="data_limited", nullable=False)
    apy_alias_list = Column(JSON, default=list, nullable=False)


class RashkarCropStageModel(Base):
    """Phenological growth stages keyed by canonical crop."""

    __tablename__ = "rashkar_crop_stages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    crop_code = Column(
        String(50),
        ForeignKey("rashkar_canonical_crops.crop_code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stage_code = Column(String(50), nullable=False, index=True)
    stage_name_en = Column(String(100), nullable=False)
    stage_name_mr = Column(String(100), nullable=False)
    sequence_order = Column(Integer, nullable=False)
    typical_das_start = Column(Integer, nullable=False)
    typical_das_end = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)


class RashkarAgronomicThresholdModel(Base):
    """Evidence-backed temperature and VPD thresholds per crop and growth stage."""

    __tablename__ = "rashkar_agronomic_thresholds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    crop_code = Column(
        String(50),
        ForeignKey("rashkar_canonical_crops.crop_code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stage_code = Column(String(50), nullable=False, index=True)
    tmin_ideal_low = Column(Float, nullable=True)
    tmax_ideal_high = Column(Float, nullable=True)
    tmax_stress_trigger = Column(Float, nullable=True)
    tmax_critical_damage = Column(Float, nullable=True)
    tmin_cold_trigger = Column(Float, nullable=True)
    vpd_stress_trigger_kpa = Column(Float, nullable=True)
    critical_heat_duration_hrs = Column(Integer, nullable=True, default=1)
    evidence_tier = Column(String(50), nullable=False)
    source_citation = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at_utc = Column(DateTime, default=now_utc_naive, nullable=False)


class RashkarAdvisoryCatalogueModel(Base):
    """Verified bilingual agronomic interventions mapped to crops/stages/severities."""

    __tablename__ = "rashkar_advisory_catalogue"

    advisory_id = Column(String(50), primary_key=True, index=True)
    domain = Column(String(50), nullable=False, index=True)
    target_crop_code = Column(String(50), nullable=False, index=True)
    target_stage_code = Column(String(50), nullable=True, index=True)
    trigger_severity = Column(String(50), nullable=False)
    title_en = Column(String(200), nullable=False)
    title_mr = Column(String(200), nullable=False)
    action_steps_en = Column(JSON, default=list, nullable=False)
    action_steps_mr = Column(JSON, default=list, nullable=False)
    do_not_do_warning = Column(Text, nullable=True)
    cost_class = Column(String(50), nullable=True)
    lead_time_required_hours = Column(Integer, nullable=True)
    source_attribution = Column(Text, nullable=False)
    is_verified_agronomist = Column(Boolean, default=True, nullable=False)


class RashkarWorkerHazardAuditLogModel(Base):
    """Audit trail of worker heat hazard calculations and applied WBGT thresholds."""

    __tablename__ = "rashkar_worker_hazard_audit_logs"

    id = Column(String(36), primary_key=True, index=True, default=_new_uuid)
    farm_id = Column(
        String(36),
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    owner_id = Column(String(36), nullable=True, index=True)
    request_timestamp_utc = Column(DateTime, default=now_utc_naive, nullable=False)
    forecast_target_timestamp_utc = Column(DateTime, nullable=False)
    weather_provider = Column(String(100), nullable=False)
    air_temp_c = Column(Float, nullable=False)
    relative_humidity_pct = Column(Float, nullable=False)
    wind_speed_kmh = Column(Float, nullable=False)
    solar_radiation_wm2 = Column(Float, nullable=False)
    calculated_wbgt_c = Column(Float, nullable=False)
    calculated_heat_index_c = Column(Float, nullable=True)
    risk_tier = Column(String(50), nullable=False)
    workload_class = Column(String(50), nullable=False)
    acclimatization_status = Column(Boolean, default=True, nullable=False)
    applied_threshold_wbgt_c = Column(Float, nullable=False)
    provenance_summary = Column(JSON, default=dict, nullable=False)
    advisory_issued_ids = Column(JSON, default=list, nullable=False)


class RashkarCropHeatLogModel(Base):
    """Audit trail of crop heat stress assessments for an active farm crop cycle."""

    __tablename__ = "rashkar_crop_heat_logs"

    id = Column(String(36), primary_key=True, index=True, default=_new_uuid)
    farm_id = Column(
        String(36),
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    owner_id = Column(String(36), nullable=False, index=True)
    crop_code = Column(String(50), nullable=False, index=True)
    stage_code = Column(String(50), nullable=True)
    stage_source = Column(String(50), nullable=True)
    assessed_at_utc = Column(DateTime, default=now_utc_naive, nullable=False)
    peak_tmax_c = Column(Float, nullable=False)
    peak_vpd_kpa = Column(Float, nullable=True)
    overall_stress_score = Column(Float, nullable=False)
    stress_tier = Column(String(50), nullable=False)
    weather_source = Column(String(100), nullable=False)
    provenance_summary = Column(JSON, default=dict, nullable=False)


class RashkarYieldAssessmentLogModel(Base):
    """Audit trail of yield baseline and biophysical stress screening assessments."""

    __tablename__ = "rashkar_yield_assessment_logs"

    id = Column(String(36), primary_key=True, index=True, default=_new_uuid)
    farm_id = Column(
        String(36),
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    owner_id = Column(String(36), nullable=False, index=True)
    crop_code = Column(String(50), nullable=False, index=True)
    district = Column(String(100), nullable=False)
    assessed_at_utc = Column(DateTime, default=now_utc_naive, nullable=False)
    benchmark_tier = Column(String(50), nullable=False)
    apy_mean_t_ha = Column(Float, nullable=True)
    apy_median_t_ha = Column(Float, nullable=True)
    apy_sample_count = Column(Integer, default=0, nullable=False)
    composite_risk_score = Column(Float, nullable=False)
    composite_risk_tier = Column(String(50), nullable=False)
    prediction_lock_status = Column(String(50), nullable=False)
    provenance_summary = Column(JSON, default=dict, nullable=False)


class RashkarFarmerResourceProfileModel(Base):
    """Persisted farmer resource and preference profile for Extra Income planning."""

    __tablename__ = "rashkar_farmer_resource_profiles"

    farm_id = Column(
        String(36),
        ForeignKey("farms.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    owner_id = Column(String(36), nullable=False, index=True)
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

    age_range = Column(String(30), nullable=True, default="36-45")
    work_preference = Column(String(50), nullable=True, default="daily_physical")
    payback_horizon = Column(String(50), nullable=True, default="within_6_months")
    family_management_role = Column(String(50), nullable=True, default="self")
    current_crop_code = Column(String(50), nullable=True)
    current_crop_stage = Column(String(50), nullable=True)

    updated_at_utc = Column(DateTime, default=now_utc_naive, onupdate=now_utc_naive)

    @property
    def farmer_id(self) -> str:
        return self.owner_id


class RashkarIncomeOpportunityModel(Base):
    """Curated catalogue of agro-allied and value-addition income opportunities."""

    __tablename__ = "rashkar_income_opportunities"

    opportunity_id = Column(String(50), primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    category = Column(String(50), nullable=False)
    is_cost_saving = Column(Boolean, default=False)
    tagline = Column(String(200), default="")
    target_crops = Column(JSON, default=list)
    required_resources = Column(JSON, default=list)
    min_investment_inr = Column(Float, nullable=False, default=0.0)
    max_investment_inr = Column(Float, nullable=False, default=0.0)
    working_capital_required_inr = Column(Float, default=0.0)
    payback_period_months = Column(Integer, nullable=False, default=1)
    potential_annual_profit_inr = Column(Float, nullable=False, default=0.0)
    potential_annual_savings_inr = Column(Float, default=0.0)
    risk_level = Column(String(20), default="moderate")
    summary = Column(Text, nullable=False)
    market_commodity = Column(String(100), default="")
    market_benchmark_price = Column(String(100), default="")
    market_source = Column(String(150), default="")
    key_assumptions = Column(JSON, default=list)
    key_risks = Column(JSON, default=list)
    source_attribution = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=now_utc_naive)


class RashkarIncomeScenarioModel(Base):
    """Editable deterministic financial scenario linked to a farm and opportunity."""

    __tablename__ = "rashkar_income_scenarios"

    scenario_id = Column(String(50), primary_key=True, index=True)
    owner_id = Column(String(36), nullable=False, index=True)
    farm_id = Column(
        String(36),
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    opportunity_id = Column(
        String(50),
        ForeignKey("rashkar_income_opportunities.opportunity_id", ondelete="CASCADE"),
        nullable=False,
    )
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
    generated_at_utc = Column(DateTime, default=now_utc_naive)

    @property
    def farmer_id(self) -> str:
        return self.owner_id


class RashkarSavedIncomePlanModel(Base):
    """Saved farmer income opportunity plans linked to a farm."""

    __tablename__ = "rashkar_saved_income_plans"

    plan_id = Column(String(50), primary_key=True, index=True)
    owner_id = Column(String(36), nullable=False, index=True)
    farm_id = Column(
        String(36),
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    opportunity_id = Column(String(50), nullable=False)
    opportunity_title = Column(String(150), nullable=False)
    category = Column(String(50), nullable=False)
    chosen_budget_inr = Column(Float, nullable=False)
    projected_annual_profit_inr = Column(Float, nullable=False)
    projected_annual_savings_inr = Column(Float, default=0.0)
    payback_months = Column(Float, nullable=True)
    break_even_reached = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at_utc = Column(DateTime, default=now_utc_naive)

    @property
    def farmer_id(self) -> str:
        return self.owner_id


__all__ = [
    "RashkarCropCycleModel",
    "RashkarCanonicalCropModel",
    "RashkarCropStageModel",
    "RashkarAgronomicThresholdModel",
    "RashkarAdvisoryCatalogueModel",
    "RashkarWorkerHazardAuditLogModel",
    "RashkarCropHeatLogModel",
    "RashkarYieldAssessmentLogModel",
    "RashkarFarmerResourceProfileModel",
    "RashkarIncomeOpportunityModel",
    "RashkarIncomeScenarioModel",
    "RashkarSavedIncomePlanModel",
]
