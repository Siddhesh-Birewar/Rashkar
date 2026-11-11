"""Pydantic request and response schemas for Crop Heat Stress assessments."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CropHeatAssessmentRequest(BaseModel):
    farm_id: Optional[str] = Field(default=None, description="Unique farm identifier")
    plot_id: Optional[str] = Field(default=None, description="Optional plot identifier")
    crop_code: Optional[str] = Field(
        default=None,
        description="Optional explicit crop code override when not using persisted cycle",
    )
    farmer_confirmed_stage: Optional[str] = Field(
        default=None,
        description="Farmer confirmed/corrected growth stage",
    )
    forecast_tmax_c: Optional[float] = Field(
        default=None,
        description="Forecasted maximum day temperature (°C)",
    )
    forecast_tmin_c: Optional[float] = Field(
        default=None,
        description="Forecasted minimum night temperature (°C)",
    )
    forecast_sun_hours: Optional[float] = Field(
        default=None,
        description="Forecasted hours of direct sunlight",
    )


class CropHeatIntervention(BaseModel):
    intervention_id: str
    title_en: str
    title_mr: str
    description_en: str
    description_mr: str
    why_appropriate: str
    evidence_citation: str
    source_page_or_table: Optional[str] = "Package of Practices, Table 3.1"
    agronomist_reviewer: Optional[str] = "ICAR-SAU Agrometeorological Review Panel"
    application_method: Optional[str] = "Foliar / Soil Application"
    application_dose: Optional[str] = "Specified dose per hectare"
    infrastructure_requirements: Optional[str] = (
        "Drip / Sprinkler / Knapsack Sprayer"
    )
    trigger_condition: Optional[str] = "Assessed Heat Stress Condition"
    evidence_status: str = "VERIFIED_PUBLISHED"
    category: str = "VERIFIED_AGRONOMIC"


class DailyCropHeatOutlook(BaseModel):
    date: str
    day_label: str
    tmax_c: float
    tmin_c: float
    hours_above_critical: float
    risk_category: str
    explanation: str


class CropHeatAssessmentResponse(BaseModel):
    status: str = "OK"
    has_active_crop: bool = True
    needs_crop_registration: bool = False
    message: Optional[str] = None

    assessment_id: str
    farm_id: str
    farm_name: str
    plot_name: str = "Registered Farm Plot"
    crop_code: Optional[str] = None
    crop_common_name: Optional[str] = None
    crop_variety: Optional[str] = None
    sowing_date: Optional[str] = None
    days_after_sowing: Optional[int] = None
    crop_area_acres: Optional[float] = None
    irrigation_status: Optional[str] = None
    soil_texture: Optional[str] = None
    soil_provenance_label: str = "Soil data unavailable (unsampled farm coordinate)"
    is_soil_synthetic: bool = False

    # Season status
    is_season_expired: bool = False
    season_status: str = "ACTIVE"
    requires_season_update: bool = False
    season_expiry_message: Optional[str] = None

    # Section 1: Growth stage & overrides
    growth_stage_code: Optional[str] = None
    growth_stage_name_en: Optional[str] = None
    growth_stage_name_mr: Optional[str] = None
    stage_source: Optional[str] = None
    supported_stages: List[Dict[str, Any]] = Field(default_factory=list)
    farmer_confirmed_stage: Optional[str] = None

    # Section 2: Crop Thermal Analysis
    base_temp_c: Optional[float] = None
    optimal_temp_min_c: Optional[float] = None
    optimal_temp_max_c: Optional[float] = None
    critical_tmax_threshold_c: Optional[float] = None
    critical_tmin_threshold_c: Optional[float] = None
    tmax_forecast_c: Optional[float] = None
    tmin_forecast_c: Optional[float] = None
    peak_vpd_kpa: Optional[float] = None
    hours_above_critical: Optional[float] = None
    consecutive_hot_days: Optional[int] = None
    daytime_exposure_hours: Optional[float] = None
    warm_night_respiration_hazard: Optional[bool] = None
    warm_night_penalty_score: Optional[float] = None
    cumulative_heat_units_gdd: Optional[float] = None
    overall_stress_score: Optional[float] = None
    evidence_citation: str = ""
    evidence_status: str = "VERIFIED_PUBLISHED"
    institution_attribution: Optional[str] = (
        "ICAR-CRIDA / State Agricultural Universities (SAU)"
    )
    thermal_analysis: Optional[Dict[str, Any]] = None
    personalized_crop_vulnerability_score: Optional[Dict[str, Any]] = None
    topographic_downscaling: Optional[Dict[str, Any]] = None

    # Section 3: Multi-day outlook
    daily_outlook: List[DailyCropHeatOutlook] = Field(default_factory=list)
    four_day_outlook: Optional[List[DailyCropHeatOutlook]] = None

    # Section 4: Agronomic risk explanation
    generated_at_ist: str
    daytime_heat_stress_level: Optional[str] = None
    overall_crop_heat_risk: Optional[str] = None
    physiological_mechanism: Optional[str] = None
    stage_biological_vulnerability: Optional[str] = None

    # Section 5: Field recommendations
    recommended_interventions: List[CropHeatIntervention] = Field(default_factory=list)
    field_recommendations: List[CropHeatIntervention] = Field(default_factory=list)

    # Section 6: Historical trends & provenance
    assessment_history: List[Dict[str, Any]] = Field(default_factory=list)
    provenance: Optional[Dict[str, Any]] = None
    audit_logged: bool = False


__all__ = [
    "CropHeatAssessmentRequest",
    "CropHeatIntervention",
    "DailyCropHeatOutlook",
    "CropHeatAssessmentResponse",
]
