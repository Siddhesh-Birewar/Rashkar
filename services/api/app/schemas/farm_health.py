"""
CropNet AI — Phase 5.9A Farm Health Snapshot Schemas.

Strictly conforms to: docs/architecture/farm_health_snapshot_contract.md
Enforces:
- Explicit DataAvailabilityState across all domains
- Key indicators with explicit NULLs (NO synthetic or manufactured demo values)
- OverallEvidenceOverview with categorical counts (NO universal health score)
- Mandatory agronomic disclaimers and governance notices
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from pydantic import BaseModel, Field, ConfigDict


class DataAvailabilityState(str, Enum):
    AVAILABLE = "AVAILABLE"
    PARTIALLY_AVAILABLE = "PARTIALLY_AVAILABLE"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    STALE = "STALE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class OverallEvidenceOverview(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    domains_available: int = Field(..., ge=0, le=5, description="Count of domains with complete, fresh data")
    domains_partially_available: int = Field(..., ge=0, le=5, description="Count of domains with partial data")
    domains_stale: int = Field(..., ge=0, le=5, description="Count of domains with expired data")
    domains_not_available: int = Field(..., ge=0, le=5, description="Count of domains with zero data")
    domains_insufficient_evidence: int = Field(..., ge=0, le=5, description="Count of domains with corrupted or uncalibrated data")
    total_domains: int = Field(default=5, description="Total evaluated domains (soil, water, satellite, weather, crop_context)")
    actionable_summary: str = Field(..., description="Actionable English text directing farmer to resolve missing or stale domains")


class SoilKeyIndicators(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    soil_ph: Optional[float] = Field(None, description="Soil reaction (pH in 1:2.5 soil-water suspension)")
    organic_carbon_pct: Optional[float] = Field(None, description="Soil organic carbon percentage (Walkley-Black)")
    electrical_conductivity_ds_m: Optional[float] = Field(None, description="Electrical conductivity in dS/m")
    available_nitrogen_kg_ha: Optional[float] = Field(None, description="Available nitrogen in kg/ha (Alkaline KMnO4)")
    available_phosphorus_kg_ha: Optional[float] = Field(None, description="Available phosphorus in kg/ha (Olsen P)")
    available_potassium_kg_ha: Optional[float] = Field(None, description="Available potassium in kg/ha (Neutral NH4OAc)")
    soil_texture: Optional[str] = Field(None, description="USDA soil textural class (e.g. Clay, Clay Loam)")
    cation_exchange_capacity: Optional[float] = Field(None, description="Cation exchange capacity in cmol(+)/kg")


class SoilDomainSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    availability_state: DataAvailabilityState
    last_updated: Optional[datetime] = Field(None, description="Timestamp of latest report or extraction")
    data_age_days: Optional[int] = Field(None, description="Age of latest measurement in days")
    provenance: Optional[str] = Field(None, description="LABORATORY_CONFIRMED | SPATIALLY_ESTIMATED_ISRIC | MIXED_DUAL_SOURCE")
    laboratory_name: Optional[str] = Field(None, description="Name of testing laboratory if lab-confirmed")
    sample_depth: Optional[str] = Field(None, description="Sampling depth interval, e.g. 0-15 cm")
    key_indicators: SoilKeyIndicators = Field(default_factory=SoilKeyIndicators)
    missing_critical_parameters: List[str] = Field(default_factory=list, description="Missing parameters required for full evaluation")
    agronomic_notes: List[str] = Field(default_factory=list, description="Agronomic findings and advisory notices")


class WaterSourceSummaryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source_id: str = Field(..., description="Water source identifier")
    source_type: str = Field(..., description="borewell | open_well | canal | river | farm_pond | pipeline")
    name: str = Field(..., description="Farmer-assigned water source name")
    seasonal_availability: str = Field(..., description="perennial | seasonal_monsoon | seasonal_post_monsoon | summer_scarce")
    reliability: str = Field(..., description="reliable | moderate | intermittent")
    irrigation_method: str = Field(..., description="drip | sprinkler | flood | furrow")
    measured_capacity_lph: Optional[float] = Field(None, description="Discharge capacity in liters per hour")
    capacity_provenance: str = Field(..., description="MEASURED | FARMER_REPORTED")


class WaterKeyIndicators(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ph: Optional[float] = Field(None, description="Water pH")
    electrical_conductivity_ds_m: Optional[float] = Field(None, description="Water salinity in dS/m")
    tds_mg_l: Optional[float] = Field(None, description="Total dissolved solids in mg/L")
    sar: Optional[float] = Field(None, description="Sodium Adsorption Ratio (meq/L basis)")
    sar_status: Optional[str] = Field(None, description="AVAILABLE | INCOMPLETE_INPUTS | UNAVAILABLE")
    rsc_meq_l: Optional[float] = Field(None, description="Residual Sodium Carbonate in meq/L")
    rsc_status: Optional[str] = Field(None, description="AVAILABLE | INCOMPLETE_INPUTS | UNAVAILABLE")
    chloride_meq_l: Optional[float] = Field(None, description="Chloride ion concentration in meq/L")
    boron_mg_l: Optional[float] = Field(None, description="Boron concentration in mg/L")


class WaterEvaluationFinding(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    parameter_key: str = Field(..., description="Evaluated parameter identifier, e.g. electrical_conductivity, sar, rsc")
    parameter_name: str = Field(..., description="Human-readable parameter name")
    hazard_level: str = Field(..., description="SAFE | LOW | MEDIUM | HIGH | VERY_HIGH | HAZARDOUS | UNVERIFIED")
    hazard_title: str = Field(..., description="Institutional hazard classification title")
    standard_applied: str = Field(..., description="BIS IS 11624:2019 | ICAR-CSSRI Karnal Tech Bull 1/98")
    management_guidance: str = Field(..., description="Agronomic management guidance under institutional guidelines")


class WaterDomainSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    availability_state: DataAvailabilityState
    last_updated: Optional[datetime] = Field(None, description="Timestamp of latest confirmed water report")
    data_age_days: Optional[int] = Field(None, description="Age of latest water test in days")
    registered_sources_count: int = Field(default=0, description="Total active water sources registered on farm")
    sources: List[WaterSourceSummaryItem] = Field(default_factory=list, description="List of registered water sources")
    laboratory_name: Optional[str] = Field(None, description="Name of testing laboratory if tested")
    provenance: Optional[str] = Field(None, description="Water quality data provenance: LABORATORY_MEASURED | FARMER_REPORTED | NOT_AVAILABLE")
    key_indicators: WaterKeyIndicators = Field(default_factory=WaterKeyIndicators)
    institutional_evaluations: List[WaterEvaluationFinding] = Field(default_factory=list, description="BIS/ICAR hazard evaluations")
    missing_critical_parameters: List[str] = Field(default_factory=list, description="Missing water quality parameters")


class SatelliteRasterUrls(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ndvi_map_url: Optional[str] = Field(None, description="Relative URL to retrieve NDVI 2D PNG raster map")
    ndmi_map_url: Optional[str] = Field(None, description="Relative URL to retrieve NDMI 2D PNG raster map")
    scl_map_url: Optional[str] = Field(None, description="Relative URL to retrieve Scene Classification (SCL) map")


class SatelliteDomainSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    availability_state: DataAvailabilityState
    observation_date: Optional[datetime] = Field(None, description="UTC timestamp of Sentinel-2 satellite overpass")
    observation_age_days: Optional[int] = Field(None, description="Age of satellite overpass in days")
    provenance: str = Field(default="COPERNICUS_SENTINEL_2_L2A", description="Satellite imagery data provenance")
    sensor: Optional[str] = Field(default="Sentinel-2 L2A", description="Satellite sensor name")
    product_id: Optional[str] = Field(None, description="Copernicus product identifier")
    canopy_ndvi: Optional[float] = Field(None, description="Mean NDVI of pure Class 4 vegetation canopy pixels")
    canopy_ndmi: Optional[float] = Field(None, description="Mean NDMI of pure Class 4 vegetation canopy pixels")
    composite_mean_ndvi: Optional[float] = Field(None, description="Unsegregated parcel-wide mean NDVI")
    bare_soil_mean_ndvi: Optional[float] = Field(None, description="Mean NDVI of bare soil pixels (SCL Class 5)")
    vegetation_coverage_percent: Optional[float] = Field(None, description="Percentage of parcel covered by Class 4 vegetation")
    bare_soil_coverage_percent: Optional[float] = Field(None, description="Percentage of parcel classified as bare soil")
    cloud_masked_percent: Optional[float] = Field(None, description="Percentage of parcel obstructed by cloud/shadow")
    valid_pixel_count: int = Field(default=0, description="Number of unobstructed 10m surface pixels")
    quality_status: Optional[str] = Field(None, description="VALID_OBSERVATION | CLOUD_OBSTRUCTED | SMALL_FARM_WARNING")
    is_small_farm_warning: bool = Field(default=False, description="True if parcel has < 5 pixels (< 0.5 ha)")
    raster_maps: SatelliteRasterUrls = Field(default_factory=SatelliteRasterUrls)
    agronomic_interpretation: Optional[str] = Field(None, description="Canopy vigor and moisture interpretation")
    scientific_disclaimer: str = Field(
        default=(
            "Sentinel-2 NDVI and NDMI reflect surface optical reflectance (10m GSD). "
            "They are indirect canopy vigor indicators, NOT direct disease pathogen or yield diagnoses."
        ),
        description="Mandatory agronomic disclaimer"
    )


class CurrentWeatherSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    observation_time: Optional[datetime] = Field(None, description="Timestamp of weather observation")
    source: str = Field(default="OPENWEATHER_OBSERVATION", description="Weather data source")
    provenance: str = Field(default="OPENWEATHER_OBSERVATION", description="Weather observation provenance")
    temperature_c: Optional[float] = Field(None, description="Observed dry bulb temperature in Celsius")
    humidity_percent: Optional[float] = Field(None, description="Relative humidity percentage")
    precipitation_mm: Optional[float] = Field(None, description="Current precipitation rate in mm/h")
    wind_speed_ms: Optional[float] = Field(None, description="Wind speed in meters per second")
    weather_condition: Optional[str] = Field(None, description="Primary weather condition (e.g. Clear, Rain)")
    weather_description: Optional[str] = Field(None, description="Detailed condition description")


class ForecastSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provenance: str = Field(default="OPENWEATHER_FORECAST", description="Forecast data provenance")
    forecast_days_count: int = Field(default=0, description="Number of days in forecast window")
    next_48h_rain_expected_mm: Optional[float] = Field(None, description="Expected precipitation accumulation in next 48h")
    temp_min_c: Optional[float] = Field(None, description="Forecasted minimum temperature in Celsius")
    temp_max_c: Optional[float] = Field(None, description="Forecasted maximum temperature in Celsius")
    weather_alerts: List[str] = Field(default_factory=list, description="Active weather alerts (e.g. heat wave, unseasonal frost)")


class ClimateNormalsSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provenance: str = Field(default="NASA_POWER_CLIMATOLOGY", description="Historical climatology provenance")
    annual_rainfall_mm: Optional[float] = Field(None, description="30-year climatological annual precipitation (NASA POWER)")
    monsoon_rainfall_mm: Optional[float] = Field(None, description="30-year monsoon season precipitation")
    mean_temperature_c: Optional[float] = Field(None, description="30-year mean annual temperature")
    potential_water_stress_indicator: Optional[str] = Field(None, description="Climatological water balance stress indicator")


class WeatherDomainSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    availability_state: DataAvailabilityState
    last_updated: Optional[datetime] = Field(None, description="Timestamp of weather snapshot collection")
    current_weather: CurrentWeatherSummary = Field(default_factory=CurrentWeatherSummary)
    forecast: ForecastSummary = Field(default_factory=ForecastSummary)
    climate_normals: ClimateNormalsSummary = Field(default_factory=ClimateNormalsSummary)


class CropSuitabilityItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    crop_id: str = Field(..., description="Crop identifier, e.g. pomegranate, wheat, soybean")
    common_name: str = Field(..., description="English common name")
    marathi_name: Optional[str] = Field(None, description="Marathi common name")
    decision_state: str = Field(..., description="Deterministic decision outcome: VERIFIED_SUITABLE | CONDITIONALLY_SUITABLE_PENDING_DATA | etc.")
    limiting_factors: List[str] = Field(default_factory=list, description="Biological or environmental constraints identified")
    irrigation_guidance: Optional[str] = Field(None, description="Agronomic water management recommendation")


class CropContextDomainSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    availability_state: DataAvailabilityState
    provenance: str = Field(default="CROP_DECISION_ENGINE", description="Decision engine provenance")
    evaluated_at: Optional[datetime] = Field(None, description="Timestamp of decision engine evaluation")
    target_season: Optional[str] = Field(None, description="Cropping season evaluated (e.g. Rabi 2026-27)")
    taluka_resolved: Optional[str] = Field(None, description="Taluka used for agro-ecological zone resolution")
    evaluated_crops_count: int = Field(default=0, description="Total candidate crops evaluated")
    suitable_crops: List[CropSuitabilityItem] = Field(default_factory=list, description="Crops verified suitable with no blocking constraints")
    conditionally_suitable_crops: List[CropSuitabilityItem] = Field(default_factory=list, description="Crops suitable pending additional data")
    disqualified_crops: List[CropSuitabilityItem] = Field(default_factory=list, description="Crops disqualified due to hard biological violations")
    abstain_crops: List[CropSuitabilityItem] = Field(default_factory=list, description="Crops abstained due to missing evidence")
    top_limiting_factors: List[str] = Field(default_factory=list, description="Primary limiting factors affecting the parcel")
    pending_followup_questions_count: int = Field(default=0, description="Number of active diagnostic questions remaining")


class FarmHealthSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    contract_version: str = Field(default="1.0", description="Contract schema version")
    farm_id: uuid.UUID = Field(..., description="Unique farm parcel UUID")
    farm_name: str = Field(..., description="Registered farm name")
    owner_id: uuid.UUID = Field(..., description="Owner user UUID")
    taluka: str = Field(..., description="Taluka / Tehsil")
    district: str = Field(..., description="District")
    state: str = Field(..., description="State")
    calculated_area_hectares: float = Field(..., description="Parcel area in hectares calculated from GeoJSON polygon")
    calculated_area_acres: float = Field(..., description="Parcel area in acres")
    snapshot_timestamp: datetime = Field(..., description="UTC timestamp when snapshot was assembled")
    overall_evidence_overview: OverallEvidenceOverview = Field(..., description="Categorical evidence completeness overview")
    soil: SoilDomainSummary = Field(..., description="Soil intelligence summary")
    water: WaterDomainSummary = Field(..., description="Irrigation water intelligence summary")
    satellite: SatelliteDomainSummary = Field(..., description="Copernicus Sentinel-2 vegetation summary")
    weather: WeatherDomainSummary = Field(..., description="Weather, forecast and climate summary")
    crop_context: CropContextDomainSummary = Field(..., description="Deterministic crop suitability evaluation summary")
    governance_notice: str = Field(
        default=(
            "CropNet AI provides independent, evidence-gated agricultural domain summaries. "
            "In accordance with institutional agricultural guidelines, no universal health score is computed."
        ),
        description="Mandatory governance disclaimer"
    )
