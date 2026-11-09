from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict

class SoilVerificationStatus(str, Enum):
    LABORATORY_VERIFIED = "laboratory_verified"
    MAP_DERIVED_ESTIMATE = "map_derived_estimate"
    REGIONAL_ESTIMATE = "regional_estimate"
    NOT_AVAILABLE = "not_available"

# Parity alias for CropNet
VerificationStatus = SoilVerificationStatus

class ParameterAvailability(str, Enum):
    AVAILABLE = "available"
    PARTIAL_COVERAGE = "partial_coverage"
    NOT_AVAILABLE = "not_available"
    SOURCE_UNAVAILABLE = "source_unavailable"
    STALE = "stale"

class SoilParameterObservation(BaseModel):
    """
    Standard schema for an individual soil parameter observation with full provenance.
    """
    model_config = ConfigDict(from_attributes=True)

    parameter_key: str = Field(..., description="Canonical key, e.g. ph, soc, clay_percent, available_nitrogen")
    display_name: str = Field(..., description="Human-readable title, e.g. Soil pH (0-5cm)")
    value: Optional[float] = Field(None, description="Numeric value or null if unavailable")
    unit: str = Field(..., description="Measurement unit, e.g. pH, %, g/kg, cmol(c)/kg")
    source: str = Field(..., description="Provider name, e.g. ISRIC SoilGrids, OpenLandMap, NATMO")
    dataset_version: str = Field(..., description="Dataset release or version string, e.g. 2.0.0")
    depth_interval: str = Field(..., description="Depth range, e.g. 0-5cm, 0-30cm, whole_profile")
    spatial_resolution: str = Field(..., description="Raster cell size or mapping scale, e.g. 250m, 30m")
    vintage_year: Optional[int] = Field(None, description="Year of dataset publication/observation")
    uncertainty: Optional[float] = Field(None, description="Uncertainty / standard error if provided by source")
    verification_status: SoilVerificationStatus = Field(
        default=SoilVerificationStatus.MAP_DERIVED_ESTIMATE,
        description="Whether this is a map estimate, regional estimate, not available, or lab verified"
    )
    availability_status: ParameterAvailability = Field(
        default=ParameterAvailability.AVAILABLE,
        description="Status of parameter retrieval"
    )
    farm_coverage_percent: float = Field(
        default=100.0,
        description="Percentage of farm polygon covered by valid raster cells"
    )
    scientific_note: Optional[str] = Field(
        None,
        description="Critical scientific context (e.g. Total Nitrogen is NOT available mineral nitrogen)"
    )

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

class MappedSoilZone(BaseModel):
    """
    Represents a distinct soil zone / polygon intersecting the farm.
    """
    model_config = ConfigDict(from_attributes=True)

    zone_id: str
    zone_name: str
    area_fraction: float = Field(..., description="Fraction of farm area (0.0 to 1.0) covered by this zone")
    description: Optional[str] = None

class MappedSoilZoneIntersection(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    zone_identifier: str
    zone_name_display: str
    fractional_area_coverage: float = Field(ge=0.0, le=1.0)
    soil_order_taxonomy: Optional[str] = None

class DepthStratifiedSoilObservation(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    depth_interval: str  # "0-5cm", "5-15cm", "15-30cm", "30-60cm"
    ph: Optional[Union[NumericSoilProperty, SoilParameterObservation]] = None
    organic_carbon_pct: Optional[Union[NumericSoilProperty, SoilParameterObservation]] = None
    clay_pct: Optional[Union[NumericSoilProperty, SoilParameterObservation]] = None
    sand_pct: Optional[Union[NumericSoilProperty, SoilParameterObservation]] = None
    silt_pct: Optional[Union[NumericSoilProperty, SoilParameterObservation]] = None
    cation_exchange_capacity_cmol_kg: Optional[Union[NumericSoilProperty, SoilParameterObservation]] = None
    total_nitrogen_g_kg: Optional[Union[NumericSoilProperty, SoilParameterObservation]] = None

class UnifiedSoilProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    profile_id: str
    farm_id: str
    plot_id: Optional[str] = None
    created_at: Optional[datetime] = None
    retrieved_at_utc: Optional[datetime] = None
    version: int = 1
    taluka: Optional[str] = None
    district: str = "Pune"
    state: str = "Maharashtra"

    is_map_derived: bool = Field(
        default=True,
        description="True for satellite/gridded model estimates. False only if verified by physical lab test."
    )
    is_synthetic_test_data: bool = Field(
        default=False,
        description="MUST BE TRUE for unit tests / mock fixtures; false for real spatial extraction"
    )
    disclaimer: str = Field(
        default=(
            "These results are estimates derived from geospatial soil datasets (ISRIC SoilGrids 2.0). "
            "They are not laboratory soil test results. Actual farm soil conditions may vary."
        ),
        description="Mandatory farmer-facing disclaimer."
    )
    source_dataset: str = Field(default="ISRIC SoilGrids 2.0")
    dataset_version: str = Field(default="2.0.0")
    spatial_resolution: str = Field(default="250m")
    depth_interval: str = Field(default="0-5cm")
    spatial_representativeness_warning: Optional[str] = None
    spatial_coverage_status: Optional[str] = "pilot_taluka_covered"
    soil_texture_class: Optional[str] = None

    # Physical & chemical properties (Supports both CropNet SoilParameterObservation and Legacy NumericSoilProperty)
    ph: Optional[Union[SoilParameterObservation, NumericSoilProperty]] = None
    organic_carbon: Optional[SoilParameterObservation] = None
    organic_carbon_pct: Optional[Union[NumericSoilProperty, SoilParameterObservation]] = None
    clay_percent: Optional[SoilParameterObservation] = None
    clay_pct: Optional[Union[NumericSoilProperty, SoilParameterObservation]] = None
    sand_percent: Optional[SoilParameterObservation] = None
    sand_pct: Optional[Union[NumericSoilProperty, SoilParameterObservation]] = None
    silt_percent: Optional[SoilParameterObservation] = None
    silt_pct: Optional[Union[NumericSoilProperty, SoilParameterObservation]] = None
    total_nitrogen: Optional[SoilParameterObservation] = None
    total_nitrogen_g_kg: Optional[Union[NumericSoilProperty, SoilParameterObservation]] = None
    cation_exchange_capacity: Optional[SoilParameterObservation] = None
    cation_exchange_capacity_cmol_kg: Optional[Union[NumericSoilProperty, SoilParameterObservation]] = None
    usda_texture_class: Optional[CategoricalSoilProperty] = None

    # Nutrients with strict availability check (MUST NOT BE FABRICATED)
    available_nitrogen: Optional[SoilParameterObservation] = None
    available_phosphorus: Optional[SoilParameterObservation] = None
    available_potassium: Optional[SoilParameterObservation] = None
    available_nitrogen_kg_ha: Optional[NumericSoilProperty] = None
    available_phosphorus_kg_ha: Optional[NumericSoilProperty] = None
    available_potassium_kg_ha: Optional[NumericSoilProperty] = None
    electrical_conductivity_ds_m: Optional[NumericSoilProperty] = None
    soil_depth_to_bedrock_cm: Optional[NumericSoilProperty] = None
    plant_available_water_capacity_mm: Optional[NumericSoilProperty] = None

    # Zones and layers
    mapped_zones: List[MappedSoilZoneIntersection] = Field(default_factory=list)
    mapped_soil_zones: List[MappedSoilZone] = Field(default_factory=list)
    additional_parameters: Dict[str, SoilParameterObservation] = Field(default_factory=dict)
    depth_observations: List[DepthStratifiedSoilObservation] = Field(default_factory=list)

    total_requested_parameters: int = 0
    available_parameters_count: int = 0
    data_completeness_ratio: float = 0.0

class SoilLayerInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    parameter_key: str
    display_name: str
    unit: str
    source: str
    dataset_version: str
    spatial_resolution: str
    supported_depth_intervals: List[str]
    is_derived: bool = False
    scientific_note: Optional[str] = None

class SoilProfileSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    profile_id: str
    farm_id: str
    created_at: datetime
    version: int
    depth_interval: str
    source_dataset: str
    is_map_derived: bool
    soil_texture_class: Optional[str] = None
    data_completeness_ratio: float

class SoilIndicatorItem(BaseModel):
    key: str
    display_name: str
    value_display: str
    unit: str
    status: str  # "normal", "high", "low", "unmeasured"
    is_estimated: bool = True
    scientific_note: Optional[str] = None

class CropNetSoilCardResponse(BaseModel):
    """
    Lightweight, farmer-friendly soil intelligence card response for mobile/web UI.
    """
    farm_id: str
    farm_name: str
    location_display: str
    texture_summary: str  # e.g. "Medium Black Vertisol (Clay)"
    reaction_summary: str # e.g. "Slightly Alkaline (pH 7.8)"
    provenance_badge: str # "Location-Based Estimate (SoilGrids 250m)" vs "Laboratory Measured"
    is_lab_measured: bool = False
    last_updated_display: str
    depth_interval: str
    disclaimer: str
    unmeasured_nutrients_notice: str
    indicators: List[SoilIndicatorItem]
    technical_details: Dict[str, Any]
