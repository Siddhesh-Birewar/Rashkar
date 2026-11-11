"""Pydantic request and response schemas for Worker Heat & WBGT risk screening."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WorkerHeatAssessmentRequest(BaseModel):
    farm_id: Optional[str] = Field(
        default=None,
        description="Optional canonical CropNet farm UUID for farm-context and audit scoping",
    )
    latitude: float = Field(..., ge=8.0, le=37.0, description="Farm plot latitude")
    longitude: float = Field(..., ge=68.0, le=98.0, description="Farm plot longitude")
    taluka: Optional[str] = Field(default=None, description="Taluka or locality name")
    workload_category: str = Field(
        default="moderate",
        description="Workload intensity: light, moderate, heavy, very_heavy",
    )
    clothing_type: str = Field(
        default="standard_work_clothes",
        description=(
            "standard_work_clothes (CAV 0), woven_double_layer (+3), "
            "coveralls_protective (+2), impermeable_vapor_barrier (+10)"
        ),
    )
    is_acclimatised: bool = Field(
        default=True,
        description="Whether workers are acclimatised to local outdoor temperatures",
    )
    sun_exposure: str = Field(
        default="direct_sun",
        description="direct_sun, partial_shade, or full_shade",
    )
    exposure_duration_hours: float = Field(
        default=4.0,
        ge=0.5,
        le=12.0,
        description="Approximate outdoor exposure duration in hours",
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
    heat_index_c: Optional[float] = None
    utci_c: Optional[float] = None
    hazard_level: str
    exceeds_screening_threshold: bool
    threshold_limit_c: float
    trend: str = "STEADY"
    work_rest_cycle: str = "Continuous Work"
    missing_data_warnings: Optional[str] = None


class WorkerHeatAssessmentResponse(BaseModel):
    status: str = "OK"
    error_message: Optional[str] = None

    session_id: str
    generated_at_ist: str
    time_horizon: str = "0_to_6_hours"
    recalculation_cadence_minutes: int = 30

    # Section 1: Current conditions & provenance
    farm_location_display: str
    weather_source_name: str
    weather_retrieval_time_ist: str
    forecast_issue_time_ist: str
    valid_time_ist: str = "Next 6 Hours"
    spatial_resolution: str = "0.1° (~11 km grid resolution)"
    grid_coordinates: str = ""
    is_observed_or_forecast: str = "Forecast (Operational WMO NWP)"
    current_air_temp_c: Optional[float] = None
    current_relative_humidity_pct: Optional[float] = None
    current_dew_point_c: Optional[float] = None
    current_wind_speed_ms: Optional[float] = None
    current_wind_speed_kmh: Optional[float] = None
    current_solar_radiation_wm2: Optional[float] = None
    current_wbgt_estimated_c: Optional[float] = None
    current_heat_index_c: Optional[float] = None
    current_utci_c: Optional[float] = None
    personalized_heat_strain_score: Optional[Dict[str, Any]] = None
    topographic_downscaling: Optional[Dict[str, Any]] = None
    ml_forecast_metadata: Optional[Dict[str, Any]] = None
    next_assessment_refresh_ist: Optional[str] = None
    data_confidence: str = "HIGH"
    missing_variables: List[str] = Field(default_factory=list)
    missing_variables_warning: Optional[str] = None

    # Section 2: Six-hour timeline & Peak analysis
    peak_risk_hour_ist: Optional[str] = None
    peak_risk_reason: Optional[str] = None
    hourly_projections: List[HourlyHeatRiskProjection] = Field(default_factory=list)

    # Section 3: Work-condition assessment
    workload_category: str
    clothing_type: str
    clothing_cav_c: float
    is_acclimatised: bool
    sun_exposure: str
    exposure_duration_hours: float
    planned_shift_duration_hours: float = 4.0
    forecast_coverage_hours: int = 6
    shift_exceeds_forecast_coverage: bool = False
    coverage_limitation_warning: Optional[str] = None
    current_hazard_level: str = "UNAVAILABLE"
    max_hazard_level_in_window: str = "UNAVAILABLE"
    max_wbgt_effective_c: Optional[float] = None
    screening_threshold_c: float
    threshold_comparison_message: str = ""
    threshold_difference_c: float = 0.0
    threshold_comparison_state: str = "BELOW"

    # Section 4: Risk explanation & technical details
    category_selection_reason: str = ""
    main_contributing_factors: List[str] = Field(default_factory=list)
    workload_interaction_explanation: str = ""
    methodology_reference: str
    methodology_standards_version: str = (
        "ACGIH 2023 TLVs & ISO 7243:2017 screening action limits"
    )
    threshold_meaning_explanation: str = ""
    safety_guarantee_disclaimer: str = ""
    technical_details: Dict[str, Any] = Field(default_factory=dict)

    # Section 5: Safety guidance & emergency
    disclaimer: str
    safety_cautions: List[str] = Field(default_factory=list)
    hydration_guidance: Dict[str, Any] = Field(default_factory=dict)
    before_work_guidance: List[str] = Field(default_factory=list)
    during_work_guidance: List[str] = Field(default_factory=list)
    high_risk_actions: List[str] = Field(default_factory=list)
    emergency_triage: Dict[str, Any] = Field(default_factory=dict)
    local_emergency_contacts: Dict[str, str] = Field(default_factory=dict)

    provenance: Optional[Dict[str, Any]] = None
    audit_logged: bool = False


__all__ = [
    "WorkerHeatAssessmentRequest",
    "HourlyHeatRiskProjection",
    "WorkerHeatAssessmentResponse",
]
