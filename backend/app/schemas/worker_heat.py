from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class WorkerHeatAssessmentRequest(BaseModel):
    latitude: float = Field(..., ge=8.0, le=37.0, description="Farm plot latitude")
    longitude: float = Field(..., ge=68.0, le=98.0, description="Farm plot longitude")
    taluka: str = Field(default="Baramati", description="Taluka name")
    workload_category: str = Field(
        default="moderate",
        description="Workload intensity: light, moderate, heavy, very_heavy"
    )
    clothing_type: str = Field(
        default="standard_work_clothes",
        description="standard_work_clothes (CAV 0), woven_double_layer (+3), coveralls_protective (+2), impermeable_vapor_barrier (+10)"
    )
    is_acclimatised: bool = Field(
        default=True,
        description="Whether workers are acclimatised to local outdoor temperatures"
    )
    sun_exposure: str = Field(
        default="direct_sun",
        description="direct_sun, partial_shade, or full_shade"
    )
    exposure_duration_hours: float = Field(
        default=4.0,
        ge=0.5,
        le=12.0,
        description="Approximate outdoor exposure duration in hours"
    )

class HourlyHeatRiskProjection(BaseModel):
    forecast_hour_offset: int
    valid_time_ist: str
    air_temp_c: float
    relative_humidity_pct: float
    wind_speed_ms: float
    solar_irradiance_wm2: float
    wbgt_estimated_c: float
    wbgt_effective_c: float
    hazard_level: str
    exceeds_screening_threshold: bool
    threshold_limit_c: float
    trend: str = "STEADY"
    work_rest_cycle: str = "Continuous Work"
    missing_data_warnings: Optional[str] = None

class WorkerHeatAssessmentResponse(BaseModel):
    session_id: str
    generated_at_ist: str
    time_horizon: str = "0_to_6_hours"
    recalculation_cadence_minutes: int = 30
    
    # Section 1: Current conditions & provenance
    farm_location_display: str
    weather_source_name: str
    weather_retrieval_time_ist: str
    forecast_issue_time_ist: str
    is_observed_or_forecast: str = "Forecast (Operational WMO NWP)"
    current_air_temp_c: float
    current_relative_humidity_pct: float
    current_dew_point_c: float
    current_wind_speed_ms: float
    current_wind_speed_kmh: float
    current_solar_radiation_wm2: float
    current_wbgt_estimated_c: float
    data_confidence: str = "HIGH"
    missing_variables_warning: Optional[str] = None
    
    # Section 2: Six-hour timeline & Peak analysis
    peak_risk_hour_ist: str
    peak_risk_reason: str
    hourly_projections: List[HourlyHeatRiskProjection]
    
    # Section 3: Work-condition assessment
    workload_category: str
    clothing_type: str
    clothing_cav_c: float
    is_acclimatised: bool
    sun_exposure: str
    exposure_duration_hours: float
    current_hazard_level: str
    max_hazard_level_in_window: str
    max_wbgt_effective_c: float
    screening_threshold_c: float
    
    # Section 4: Risk explanation & technical details
    category_selection_reason: str
    main_contributing_factors: List[str]
    workload_interaction_explanation: str
    methodology_reference: str
    technical_details: Dict[str, Any]
    
    # Section 5: Safety guidance & emergency
    disclaimer: str
    safety_cautions: List[str]
    hydration_guidance: Dict[str, Any]
    before_work_guidance: List[str]
    during_work_guidance: List[str]
    high_risk_actions: List[str]
    emergency_triage: Dict[str, Any]
    
    audit_logged: bool = True
