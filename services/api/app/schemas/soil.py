from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class VerificationStatus(str, Enum):
    MAP_DERIVED_ESTIMATE = "map_derived_estimate"
    REGIONAL_ESTIMATE = "regional_estimate"
    NOT_AVAILABLE = "not_available"
    LABORATORY_VERIFIED = "laboratory_verified"


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
    parameter_key: str = Field(..., description="Canonical key, e.g. ph, soc, clay_percent, available_nitrogen")
    display_name: str = Field(..., description="Human-readable title, e.g. Soil pH (0-5cm)")
    value: Optional[float] = Field(None, description="Numeric value or null if unavailable")
    unit: str = Field(..., description="Measurement unit, e.g. pH, %, g/kg, cmol(c)/kg")
    
    # Scientific Provenance
    source: str = Field(..., description="Provider name, e.g. ISRIC SoilGrids, OpenLandMap, NATMO")
    dataset_version: str = Field(..., description="Dataset release or version string, e.g. 2.0.0")
    depth_interval: str = Field(..., description="Depth range, e.g. 0-5cm, 0-30cm, whole_profile")
    spatial_resolution: str = Field(..., description="Raster cell size or mapping scale, e.g. 250m, 30m, 1:250000")
    vintage_year: Optional[int] = Field(None, description="Year of dataset publication/observation")
    uncertainty: Optional[float] = Field(None, description="Uncertainty / standard error if provided by source")
    
    # Status and Interpretation
    verification_status: VerificationStatus = Field(
        default=VerificationStatus.MAP_DERIVED_ESTIMATE,
        description="Whether this is a map estimate, regional estimate, not available, or lab verified"
    )
    availability_status: ParameterAvailability = Field(
        default=ParameterAvailability.AVAILABLE,
        description="Status of parameter retrieval"
    )
    farm_coverage_percent: float = Field(
        default=100.0,
        description="Percentage of farm polygon covered by valid raster cells for this parameter"
    )
    scientific_note: Optional[str] = Field(
        None,
        description="Critical scientific context (e.g. Total Nitrogen is NOT available mineral nitrogen)"
    )


class MappedSoilZone(BaseModel):
    """
    Represents a distinct soil zone / polygon intersecting the farm.
    """
    zone_id: str
    zone_name: str
    area_fraction: float = Field(..., description="Fraction of farm area (0.0 to 1.0) covered by this zone")
    description: Optional[str] = None


class UnifiedSoilProfile(BaseModel):
    """
    Comprehensive, versioned soil profile snapshot for a farm.
    Can be consumed directly by the crop recommendation engine.
    """
    profile_id: str
    farm_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1
    
    # Pilot geography
    taluka: Optional[str] = None
    district: str = "Pune"
    state: str = "Maharashtra"
    
    # Transparency & Disclaimers
    is_map_derived: bool = Field(
        True,
        description="Always true for initial release. Explains that this is an estimate, not a lab test."
    )
    disclaimer: str = Field(
        default="This soil profile is estimated from geospatial soil models and regional maps. "
                "It is not a physical laboratory soil test and does not represent direct chemical soil testing.",
        description="Mandatory farmer-facing disclaimer."
    )
    
    # Primary Soil Parameters
    ph: Optional[SoilParameterObservation] = None
    organic_carbon: Optional[SoilParameterObservation] = None
    sand_percent: Optional[SoilParameterObservation] = None
    silt_percent: Optional[SoilParameterObservation] = None
    clay_percent: Optional[SoilParameterObservation] = None
    total_nitrogen: Optional[SoilParameterObservation] = None
    cation_exchange_capacity: Optional[SoilParameterObservation] = None
    
    # Nutrients with strict availability check (MUST NOT BE FABRICATED)
    available_nitrogen: Optional[SoilParameterObservation] = None
    available_phosphorus: Optional[SoilParameterObservation] = None
    available_potassium: Optional[SoilParameterObservation] = None
    
    # Additional Characteristics
    mapped_soil_zones: List[MappedSoilZone] = Field(default_factory=list)
    additional_parameters: Dict[str, SoilParameterObservation] = Field(default_factory=dict)
    
    # Completeness metrics
    total_requested_parameters: int = 0
    available_parameters_count: int = 0
    data_completeness_ratio: float = 0.0
