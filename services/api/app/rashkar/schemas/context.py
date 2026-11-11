"""Context and crop-cycle schemas shared between CropNet adapters and RASHKAR engines."""

from datetime import date, datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RashkarFarmContext(BaseModel):
    """Normalized representation of a canonical CropNet farm passed into RASHKAR engines."""

    model_config = ConfigDict(from_attributes=True)

    farm_id: str
    owner_id: str
    farm_name: str
    district: Optional[str] = None
    taluka: Optional[str] = None
    village: Optional[str] = None
    state: Optional[str] = "Maharashtra"
    latitude: float
    longitude: float
    elevation_m: Optional[float] = None
    total_area_acres: Optional[float] = None
    irrigation_type: Optional[str] = None
    water_source: Optional[str] = None


class RashkarSoilContext(BaseModel):
    """Normalized edaphic context; preserves None for any unmeasured property."""

    model_config = ConfigDict(from_attributes=True)

    soil_texture: Optional[str] = None
    soil_ph: Optional[float] = None
    organic_carbon_pct: Optional[float] = None
    cation_exchange_capacity: Optional[float] = None
    available_water_capacity_mm_m: Optional[float] = None
    effective_rooting_depth_cm: Optional[float] = None
    clay_pct: Optional[float] = None
    sand_pct: Optional[float] = None
    silt_pct: Optional[float] = None
    bulk_density_g_cm3: Optional[float] = None
    climate_normal_rainfall_mm: Optional[float] = None
    data_provenance: Optional[str] = None
    is_lab_measured: bool = False
    is_synthetic: bool = False


class RashkarCropCycleCreate(BaseModel):
    """Payload to register or activate a farm's crop cycle."""

    crop_code: str = Field(..., min_length=1, max_length=50)
    variety_name: Optional[str] = Field(default=None, max_length=100)
    sowing_date: Optional[date] = None
    season: Optional[str] = Field(default=None, max_length=30)
    planted_area_acres: Optional[float] = Field(default=None, ge=0.0)
    irrigation_type: Optional[str] = Field(default=None, max_length=50)
    current_stage_code: Optional[str] = Field(default=None, max_length=50)
    stage_source: str = Field(default="estimated_from_das", max_length=30)
    stage_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    is_active: bool = True


class RashkarCropCycleUpdate(BaseModel):
    """Payload to update an existing crop cycle (including farmer stage confirmation)."""

    variety_name: Optional[str] = Field(default=None, max_length=100)
    sowing_date: Optional[date] = None
    season: Optional[str] = Field(default=None, max_length=30)
    planted_area_acres: Optional[float] = Field(default=None, ge=0.0)
    irrigation_type: Optional[str] = Field(default=None, max_length=50)
    current_stage_code: Optional[str] = Field(default=None, max_length=50)
    stage_source: Optional[str] = Field(default=None, max_length=30)
    stage_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    is_active: Optional[bool] = None


class RashkarCropCycleResponse(BaseModel):
    """Serialized crop cycle record from `rashkar_crop_cycles`."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    farm_id: str
    owner_id: str
    crop_code: str
    variety_name: Optional[str] = None
    sowing_date: Optional[date] = None
    season: Optional[str] = None
    planted_area_acres: Optional[float] = None
    irrigation_type: Optional[str] = None
    current_stage_code: Optional[str] = None
    stage_source: str
    stage_confidence: Optional[float] = None
    is_active: bool
    created_at_utc: datetime
    updated_at_utc: datetime


class RashkarCanonicalCropItem(BaseModel):
    """Canonical crop reference entry."""

    model_config = ConfigDict(from_attributes=True)

    crop_code: str
    common_name_en: str
    common_name_mr: str
    botanical_name: str
    crop_category: str
    standard_season: str
    is_pioneer_pilot_crop: bool
    support_level: str
    apy_alias_list: List[Any] = Field(default_factory=list)


__all__ = [
    "RashkarFarmContext",
    "RashkarSoilContext",
    "RashkarCropCycleCreate",
    "RashkarCropCycleUpdate",
    "RashkarCropCycleResponse",
    "RashkarCanonicalCropItem",
]
