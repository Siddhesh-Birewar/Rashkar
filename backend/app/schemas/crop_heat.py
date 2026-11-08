from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class CropHeatAssessmentRequest(BaseModel):
    farm_id: str = Field(..., description="Unique farm identifier")
    plot_id: Optional[str] = Field(None, description="Optional plot identifier")
    forecast_tmax_c: Optional[float] = Field(None, description="Forecasted maximum day temperature (°C)")
    forecast_tmin_c: Optional[float] = Field(None, description="Forecasted minimum night temperature (°C)")
    forecast_sun_hours: Optional[float] = Field(None, description="Forecasted hours of direct sunlight")

class CropHeatIntervention(BaseModel):
    intervention_id: str
    title_en: str
    title_mr: str
    description_en: str
    description_mr: str
    evidence_citation: str

class CropHeatAssessmentResponse(BaseModel):
    assessment_id: str
    farm_id: str
    crop_code: str
    crop_common_name: str
    growth_stage_code: str
    growth_stage_name_en: str
    growth_stage_name_mr: str
    generated_at_ist: str
    tmax_forecast_c: float
    tmin_forecast_c: float
    critical_tmax_threshold_c: float
    critical_tmin_threshold_c: float
    daytime_heat_stress_level: str
    warm_night_respiration_hazard: bool
    overall_crop_heat_risk: str
    physiological_mechanism: str
    evidence_citation: str
    recommended_interventions: List[CropHeatIntervention]
    audit_logged: bool
