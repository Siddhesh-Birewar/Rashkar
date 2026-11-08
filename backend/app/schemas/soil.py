from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class SoilVerificationStatus(str, Enum):
    LABORATORY_VERIFIED = "laboratory_verified"
    MAP_DERIVED_ESTIMATE = "map_derived_estimate"
    REGIONAL_ESTIMATE = "regional_estimate"
    NOT_AVAILABLE = "not_available"

class NumericSoilProperty(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    value: Optional[float] = Field(default=None, description="Numeric measurement or null if unavailable")
    unit: str
    depth_interval: str  # "0-5cm", "5-15cm", "0-15cm"
    verification_status: SoilVerificationStatus
    source_id: str
    source_vintage: Optional[str] = None
    spatial_resolution_m: Optional[int] = None
    uncertainty_lower_bound: Optional[float] = None
    uncertainty_upper_bound: Optional[float] = None

class CategoricalSoilProperty(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    value_code: Optional[str] = Field(default=None, description="Categorical code (e.g. 'clay', 'clay_loam')")
    value_display: Optional[str] = None
    depth_interval: str
    verification_status: SoilVerificationStatus
    source_id: str
    source_vintage: Optional[str] = None

class MappedSoilZoneIntersection(BaseModel):
    zone_identifier: str
    zone_name_display: str
    fractional_area_coverage: float = Field(ge=0.0, le=1.0)
    soil_order_taxonomy: Optional[str] = None

class DepthStratifiedSoilObservation(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    depth_interval: str  # "0-5cm", "5-15cm", "15-30cm", "30-60cm"
    ph: Optional[NumericSoilProperty] = None
    organic_carbon_pct: Optional[NumericSoilProperty] = None
    clay_pct: Optional[NumericSoilProperty] = None
    sand_pct: Optional[NumericSoilProperty] = None
    silt_pct: Optional[NumericSoilProperty] = None
    cation_exchange_capacity_cmol_kg: Optional[NumericSoilProperty] = None
    total_nitrogen_g_kg: Optional[NumericSoilProperty] = None

class UnifiedSoilProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    profile_id: str
    farm_id: str
    plot_id: Optional[str] = None
    retrieved_at_utc: datetime
    is_synthetic_test_data: bool = Field(
        default=False,
        description="MUST BE TRUE for unit tests / mock fixtures; false only for real teammate service"
    )
    spatial_coverage_status: str  # "pilot_taluka_covered", "regional_extrapolation", "unsupported"
    mapped_zones: List[MappedSoilZoneIntersection] = Field(default_factory=list)

    # Physical & chemical properties (primary topsoil interval)
    ph: NumericSoilProperty
    organic_carbon_pct: NumericSoilProperty
    clay_pct: NumericSoilProperty
    sand_pct: NumericSoilProperty
    silt_pct: NumericSoilProperty
    usda_texture_class: CategoricalSoilProperty
    cation_exchange_capacity_cmol_kg: NumericSoilProperty
    total_nitrogen_g_kg: NumericSoilProperty

    # Multiple depth-stratified layers (0-5cm, 5-15cm, etc.)
    depth_observations: List[DepthStratifiedSoilObservation] = Field(default_factory=list)

    # Strictly unavailable in current CropNet v1 feeds
    available_nitrogen_kg_ha: Optional[NumericSoilProperty] = Field(default=None)
    available_phosphorus_kg_ha: Optional[NumericSoilProperty] = Field(default=None)
    available_potassium_kg_ha: Optional[NumericSoilProperty] = Field(default=None)
    electrical_conductivity_ds_m: Optional[NumericSoilProperty] = Field(default=None)
    soil_depth_to_bedrock_cm: Optional[NumericSoilProperty] = Field(default=None)
    plant_available_water_capacity_mm: Optional[NumericSoilProperty] = Field(default=None)
