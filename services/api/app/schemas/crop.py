from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AgriculturalKnowledgeSourceResponse(BaseModel):
    id: str
    organization: str
    publication_title: str
    publication_year: Optional[int] = None
    document_url_or_ref: Optional[str] = None
    section_or_pages: Optional[str] = None
    evidence_quality: str
    last_verified_date: datetime


class CropSoilRequirementsResponse(BaseModel):
    preferred_textures: List[str]
    acceptable_textures: List[str]
    ph_optimum_min: float
    ph_optimum_max: float
    ph_tolerable_min: float
    ph_tolerable_max: float
    drainage_requirement: str
    salinity_sensitivity: str
    min_soil_depth_cm: float
    optimum_organic_carbon_g_kg: Optional[float] = None
    water_holding_capacity_pref: Optional[str] = None
    source_id: Optional[str] = None


class CropClimateRequirementsResponse(BaseModel):
    temp_optimum_min_c: float
    temp_optimum_max_c: float
    temp_tolerable_min_c: float
    temp_tolerable_max_c: float
    annual_rainfall_min_mm: Optional[float] = None
    annual_rainfall_max_mm: Optional[float] = None
    humidity_preference: Optional[str] = None
    frost_sensitivity: str
    heat_sensitivity: str
    solar_radiation_requirement: Optional[str] = None
    source_id: Optional[str] = None


class CropSeasonRequirementResponse(BaseModel):
    season_name: str
    is_primary_season: bool
    planting_window_maharashtra: str
    harvesting_window_maharashtra: str
    duration_days_min: int
    duration_days_max: int
    planting_calendar_by_region: Optional[Dict[str, str]] = None
    source_id: Optional[str] = None


class CropWaterRequirementsResponse(BaseModel):
    annual_water_requirement_mm_min: float
    annual_water_requirement_mm_max: float
    rainfed_suitable: bool
    irrigation_dependency: str
    critical_growth_stages: List[str]
    waterlogging_sensitivity: str
    drought_sensitivity: str
    source_id: Optional[str] = None


class CropRegionalSuitabilityResponse(BaseModel):
    taluka: str
    district: str
    suitability_status: str
    agronomic_rationale: str
    limiting_factors: Optional[List[str]] = None
    source_id: Optional[str] = None


class CropCatalogSummaryResponse(BaseModel):
    """
    Lightweight summary for crop catalogue listing.
    """
    id: str
    common_name: str
    scientific_name: str
    marathi_name: Optional[str] = None
    hindi_name: Optional[str] = None
    category: str
    crop_type: str
    typical_duration_days_min: Optional[int] = None
    typical_duration_days_max: Optional[int] = None
    recommended_varieties: Optional[List[str]] = None
    primary_source_org: Optional[str] = None


class CropFullProfileResponse(BaseModel):
    """
    Comprehensive, scientifically traceable crop profile.
    Foundation for CropNet's future crop recommendation engine.
    """
    id: str
    common_name: str
    scientific_name: str
    marathi_name: Optional[str] = None
    hindi_name: Optional[str] = None
    category: str
    crop_type: str
    typical_duration_days_min: Optional[int] = None
    typical_duration_days_max: Optional[int] = None
    recommended_varieties: List[str] = Field(default_factory=list)
    
    # Requirement Modules
    soil: Optional[CropSoilRequirementsResponse] = None
    climate: Optional[CropClimateRequirementsResponse] = None
    seasons: List[CropSeasonRequirementResponse] = Field(default_factory=list)
    water: Optional[CropWaterRequirementsResponse] = None
    regional_suitability: List[CropRegionalSuitabilityResponse] = Field(default_factory=list)
    sources: List[AgriculturalKnowledgeSourceResponse] = Field(default_factory=list)


class MaharashtraSeasonCalendarResponse(BaseModel):
    """
    Information on standard agricultural cropping seasons in Maharashtra.
    """
    season_name: str
    marathi_name: str
    period_months: str
    primary_crops: List[str]
    rainfall_dependency: str
    description: str
