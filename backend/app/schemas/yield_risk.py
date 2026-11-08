from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict

class RiskItem(BaseModel):
    risk_dimension: str
    risk_level: str  # low, moderate, high, extreme
    time_horizon: str
    impact_severity: str
    confidence: str
    drivers: List[str]
    evidence_provenance: List[Dict[str, Any]]
    recommended_actions: List[Dict[str, Any]]

class HistoricalYieldBaseline(BaseModel):
    status: str
    geographical_unit: str
    district: str
    crop_code: str
    season: str = "Kharif / Rabi"
    data_period: str
    sample_seasons_count: int
    historical_mean_t_ha: Optional[float]
    historical_median_t_ha: Optional[float]
    historical_p10_t_ha: Optional[float]
    historical_p90_t_ha: Optional[float]
    min_recorded_t_ha: Optional[float]
    max_recorded_t_ha: Optional[float]
    historical_std_dev: Optional[float]
    disclaimer: str

class SoilSuitabilityAnalysis(BaseModel):
    soil_texture: str
    soil_ph: float
    ph_status: str
    organic_carbon_pct: float
    cation_exchange_capacity: float
    available_water_capacity_mm_m: float
    effective_rooting_depth_cm: float
    climate_normal_rainfall_mm: float
    suitability_verdict: str
    data_provenance: str

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

    # Section 1: Farm and crop summary
    farm_id: str
    farm_name: str
    plot_id: str
    crop_code: str
    crop_name: str
    sowing_date: str
    days_after_sowing: int
    total_area_acres: float
    irrigation_type: str
    location_display: str
    generated_at_utc: str
    timezone: str = "Asia/Kolkata"
    
    # Section 2: Historical yield analysis
    yield_baseline: HistoricalYieldBaseline
    
    # Section 3: Crop suitability & edaphic profile
    suitability_analysis: SoilSuitabilityAnalysis
    
    # Section 4: Environmental stress screening
    coverage: Dict[str, Any]
    crop_stage: Dict[str, Any]
    risks: List[RiskItem]
    
    # Section 5: Machine learning & farm harvest label gate
    ml_prediction_gate: Dict[str, Any]
    
    # Section 6: Actionable recommendations
    recommendations: List[ActionableRecommendation]
    
    # Section 7: Farmer-friendly narrative explanation
    farmer_narrative_explanation: str
