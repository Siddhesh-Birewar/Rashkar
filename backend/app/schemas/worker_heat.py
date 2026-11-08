from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

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
        description="standard_work_clothes (CAV 0), woven_double_layer (+3), coveralls_protective (+2)"
    )
    is_acclimatised: bool = Field(
        default=True,
        description="Whether workers are acclimatised to local outdoor temperatures (>2 weeks continuous exposure)"
    )
    sun_exposure: str = Field(
        default="direct_sun",
        description="direct_sun or full_shade"
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

class WorkerHeatAssessmentResponse(BaseModel):
    session_id: str
    generated_at_ist: str
    time_horizon: str = "0_to_6_hours"
    recalculation_cadence_minutes: int = 30
    workload_category: str
    clothing_cav_c: float
    is_acclimatised: bool
    sun_exposure: str
    current_hazard_level: str
    max_hazard_level_in_window: str
    max_wbgt_effective_c: float
    screening_threshold_c: float
    disclaimer: str
    safety_cautions: List[str]
    hydration_guidance: Dict[str, Any]
    hourly_projections: List[HourlyHeatRiskProjection]
    audit_logged: bool
