"""Heat Risk — Pydantic schemas for crop and worker heat-stress assessment."""
from typing import Optional
from pydantic import BaseModel, Field


class CropHeatRequest(BaseModel):
    crop_code: str = Field(..., description="Crop code, e.g. soybean, cotton, jowar, onion")
    forecast_tmax_c: float = Field(..., ge=-10.0, le=60.0)
    forecast_tmin_c: float = Field(..., ge=-20.0, le=45.0)
    growth_stage: Optional[str] = Field(None, description="Optional stage_code to override DAS selection")
    days_after_sowing: Optional[int] = Field(None, ge=0, le=400)
    forecast_sun_hours: Optional[float] = Field(None, ge=0.0, le=16.0)


class CropHeatResponse(BaseModel):
    crop_code: str
    growth_stage_code: str
    growth_stage_name: str
    critical_tmax_c: float
    critical_tmin_c: float
    forecast_tmax_c: float
    forecast_tmin_c: float
    hours_above_critical: float
    warm_night_hazard: bool
    warm_night_penalty: float
    cumulative_gdd: float
    risk_category: str
    risk_label: str
    explanation: str
    evidence_citation: str
    methodology_note: str


class WorkerHeatRequest(BaseModel):
    air_temp_c: float = Field(..., ge=-10.0, le=60.0)
    relative_humidity_pct: float = Field(..., ge=0.0, le=100.0)
    wind_speed_ms: float = Field(1.5, ge=0.0, le=30.0)
    solar_irradiance_wm2: float = Field(600.0, ge=0.0, le=1400.0)
    workload_category: str = Field("moderate", description="light | moderate | heavy | very_heavy")
    clothing_type: str = Field(
        "standard_work_clothes",
        description="standard_work_clothes | coveralls_protective | woven_double_layer | impermeable_vapor_barrier",
    )
    is_acclimatised: bool = True
    sun_exposure: str = Field("direct_sun", description="direct_sun | shade")


class WorkerHeatResponse(BaseModel):
    wbgt_c: float
    wbgt_effective_c: float
    threshold_c: float
    hazard_level: str
    exceeds_threshold: bool
    work_rest_cycle: str
    heat_index_c: Optional[float] = None
    utci_c: Optional[float] = None
    recommendation: str
    methodology_note: str
