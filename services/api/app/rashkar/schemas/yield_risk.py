"""Pydantic response schemas for Yield Risk & DES APY baseline screening."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RiskItem(BaseModel):
    risk_dimension: str
    risk_level: str  # low, moderate, high, extreme
    time_horizon: str
    impact_severity: str
    confidence: str
    drivers: List[str] = Field(default_factory=list)
    evidence_provenance: List[Dict[str, Any]] = Field(default_factory=list)
    recommended_actions: List[Dict[str, Any]] = Field(default_factory=list)


class HistoricalYieldBaseline(BaseModel):
    status: str
    geographical_unit: str
    district: str
    crop_code: str
    season: str = "Kharif / Rabi"
    data_period: str
    sample_seasons_count: int
    historical_mean_t_ha: Optional[float] = None
    historical_median_t_ha: Optional[float] = None
    historical_p10_t_ha: Optional[float] = None
    historical_p25_t_ha: Optional[float] = None
    historical_p90_t_ha: Optional[float] = None
    min_recorded_t_ha: Optional[float] = None
    max_recorded_t_ha: Optional[float] = None
    historical_std_dev: Optional[float] = None
    disclaimer: str


class SoilSuitabilityAnalysis(BaseModel):
    soil_texture: Optional[str] = None
    soil_ph: Optional[float] = None
    ph_status: str = "Unavailable (Unsampled)"
    organic_carbon_pct: Optional[float] = None
    cation_exchange_capacity: Optional[float] = None
    available_water_capacity_mm_m: Optional[float] = None
    effective_rooting_depth_cm: Optional[float] = None
    climate_normal_rainfall_mm: Optional[float] = None
    suitability_verdict: str = "Unavailable — Soil profile metrics missing"
    data_provenance: str = "Unavailable"


class ActionableRecommendation(BaseModel):
    recommendation_id: str
    title: str
    description: str
    why_recommended: str
    supporting_data: str
    evidence_source: str
    urgency: str  # High, Medium, Preventative
    limitations: str


class YieldRiskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str = "OK"
    has_active_crop: bool = True
    needs_crop_registration: bool = False
    message: Optional[str] = None

    # Section 1: Farm and crop summary
    farm_id: str
    farm_name: str
    plot_id: str = "primary_farm_plot"
    crop_code: Optional[str] = None
    crop_name: Optional[str] = None
    sowing_date: Optional[str] = None
    days_after_sowing: Optional[int] = None
    total_area_acres: Optional[float] = None
    irrigation_type: Optional[str] = None
    location_display: str
    generated_at_utc: str
    timezone: str = "Asia/Kolkata"

    # Section 2: Historical yield analysis
    yield_baseline: Optional[HistoricalYieldBaseline] = None

    # Section 3: Crop suitability & edaphic profile
    suitability_analysis: Optional[SoilSuitabilityAnalysis] = None

    # Section 4: Environmental stress screening
    coverage: Dict[str, Any] = Field(default_factory=dict)
    crop_stage: Dict[str, Any] = Field(default_factory=dict)
    risks: List[RiskItem] = Field(default_factory=list)
    composite_risk_score: Optional[float] = None
    composite_risk_tier: Optional[str] = None

    # Section 5: Machine learning & farm harvest label gate
    ml_prediction_gate: Dict[str, Any] = Field(default_factory=dict)

    # Section 6: Actionable recommendations
    recommendations: List[ActionableRecommendation] = Field(default_factory=list)

    # Section 7: Farmer-friendly narrative explanation
    farmer_narrative_explanation: str = ""

    provenance: Optional[Dict[str, Any]] = None
    audit_logged: bool = False


__all__ = [
    "RiskItem",
    "HistoricalYieldBaseline",
    "SoilSuitabilityAnalysis",
    "ActionableRecommendation",
    "YieldRiskResponse",
]
