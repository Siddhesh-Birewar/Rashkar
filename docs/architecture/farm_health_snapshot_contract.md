# CropNet AI — Shared Farm Health Snapshot API Contract Specification

**Contract Version**: `1.0`  
**Endpoint**: `GET /api/v1/farms/{farm_id}/health-snapshot`  
**Date**: November 8, 2026  
**Status**: APPROVED SHARED CONTRACT  
**Base Commit**: `ae1cef0d1249c3b502093a2b8a9e8227880a014c`  
**Target Branch**: `integration/consolidated-workstreams`  
**Participating Workstreams**:
- **Agent 1**: Phase 5.8.2.1 — AI Quality Verification and Closure
- **Agent 2**: Phase 5.9A — Unified Farm Health Backend Aggregation Service
- **Agent 3**: Phase 5.9B — Farmer-Facing Farm Health Dashboard (Flutter)
- **Agent 4**: Phase 6.0 — Integrated AI Agricultural Advisory (Qwen3:8B)

---

## 1. Architectural Overview & Endpoint Specification

### 1.1 Purpose & Role in CropNet AI
CropNet AI previously maintained isolated intelligence modules for Soil (ISRIC SoilGrids + physical lab test precedence), Water (SAR/RSC and BIS IS 11624:2019 / ICAR-CSSRI evaluations), Satellite Vegetation (Copernicus Sentinel-2 L2A 10m surface reflectance with pure Class 4 canopy segregation), Weather (OpenWeather current/forecast + NASA POWER 30-year climatology), and Crop Suitability (Deterministic Decision Engine).

The **Unified Farm Health Snapshot Service** aggregates these discrete domains into a centralized, single-call REST endpoint. This shared contract forms the canonical interface contract between the backend aggregation service (Agent 2), the farmer-facing Flutter dashboard (Agent 3), and the grounded prompt context for the LLM agricultural advisory (Agent 4).

```
                      +---------------------------------------+
                      | GET /api/v1/farms/{id}/health-snapshot|
                      +-------------------+-------------------+
                                          |
                      +-------------------v-------------------+
                      |   _get_farm_and_verify_owner          |
                      |   (401 Unauthorized / 403 Forbidden)  |
                      +-------------------+-------------------+
                                          |
                      +-------------------v-------------------+
                      |    FarmHealthAggregator & Cache       |
                      |    (In-Memory TTL: 300s, force_ref)   |
                      +-------------------+-------------------+
                                          |
         +----------------+---------------+---------------+----------------+
         |                |               |               |                |
+--------v-------+ +------v------+ +------v-------+ +-----v-------+ +------v------+
| Soil Collector | |Water Collect| | Sat Collector| | Wx Collector| |Crop Collector|
| (Lab + ISRIC)  | | (SAR & BIS) | | (Sentinel-2) | | (Wx & Clim) | | (Decisions) |
+----------------+ +-------------+ +--------------+ +-------------+ +---------------+
```

### 1.2 Endpoint Details
- **Route**: `GET /api/v1/farms/{farm_id}/health-snapshot`
- **HTTP Method**: `GET`
- **Request Headers**:
  - `Authorization: Bearer <jwt_token>` (Mandatory in production; validated via Supabase Auth)
  - `X-Dev-User-Id: <uuid>` (Optional development bypass; accepted ONLY when `ENVIRONMENT=development`)
- **Path Parameters**:
  - `farm_id` (UUID string, required): Unique identifier of the registered farm parcel.
- **Query Parameters**:
  - `force_refresh` (boolean, optional, default: `false`): When `true`, invalidates the in-memory cache and re-collects fresh observations from all underlying domain modules.
  - `target_season` (string, optional, default: current active season, e.g. `"Rabi 2026-27"`): Agricultural season filter for crop evaluation context.
- **Response Format**: `application/json`
- **HTTP Response Codes**:
  - `200 OK`: Successful snapshot generation returning `FarmHealthSnapshotResponse`.
  - `401 Unauthorized`: Missing, invalid, or expired Bearer token in production mode.
  - `403 Forbidden`: Authenticated user does not own the requested farm parcel (`{"detail": "You do not have permission to access this farm"}`).
  - `404 Not Found`: Farm UUID does not exist in storage or database (`{"detail": "Farm <farm_id> not found"}`).
  - `500 Internal Server Error`: Unhandled server exception with structured `request_id`.

### 1.3 Caching & Performance Semantics
- **Cache TTL**: In-memory caching with a 5-minute (300 seconds) TTL per `farm_id`.
- **Cache Invalidation**: Mutation endpoints (e.g., uploading a new soil lab report, adding a water source, triggering satellite sync, updating farm geometry) MUST call `invalidate_snapshot(farm_id)` on the snapshot cache.
- **Target Response Latency**: <= 250ms on cache hit; <= 1500ms on cache miss (with live DB queries).

### 1.4 Fault Isolation & Graceful Degradation
To prevent cascading failures across heterogeneous upstream systems:
- Each domain collector executes within an isolated `try...except` block.
- If an individual collector fails (e.g., Copernicus API timeout, database lock, missing spatial geometry), the aggregator logs the error and returns that domain with `availability_state: "NOT_AVAILABLE"` or `availability_state: "INSUFFICIENT_EVIDENCE"` along with an explanatory error notice.
- The snapshot endpoint MUST NEVER return HTTP 500 solely because an external satellite or weather provider failed.

---

## 2. Authentication & Farm Ownership Enforcement

### 2.1 Security Model
All requests to `/api/v1/farms/{farm_id}/health-snapshot` MUST inject the standard authentication dependency:
```python
current_user: CurrentUser = Depends(get_current_user)
db: Session = Depends(get_db)
```

### 2.2 Environment Rules
1. **Production (`settings.ENVIRONMENT == "production"`)**:
   - The `Authorization: Bearer <token>` header is strictly mandatory.
   - Bearer token is validated against the Supabase Auth user endpoint.
   - `X-Dev-User-Id` headers are completely ignored.
   - Missing or invalid tokens immediately reject with `HTTP 401 Unauthorized`.
2. **Development (`settings.ENVIRONMENT == "development"`)**:
   - If `Authorization` header is omitted, `X-Dev-User-Id` is accepted.
   - If neither is provided, defaults to `settings.DEV_USER_ID` (`00000000-0000-0000-0000-000000000001`).

### 2.3 Farm Ownership Verification
Before initiating any data aggregation, the service calls `_get_farm_and_verify_owner(farm_id, current_user, db)`:
```python
farm = _get_farm_and_verify_owner(farm_id, current_user, db)
```
- If the farm does not exist in memory or PostgreSQL, raises `HTTP 404 Not Found`.
- If `farm["owner_id"] != current_user.user_id`, raises `HTTP 403 Forbidden` with detail `"You do not have permission to access this farm"`.
- This guarantees strict multi-tenant isolation across all farmer records.

---

## 3. Data Availability States & Freshness Thresholds

### 3.1 Canonical State Enum
Every domain summary returned by the snapshot service reports an explicit `availability_state`:

```python
class DataAvailabilityState(str, Enum):
    AVAILABLE = "AVAILABLE"
    PARTIALLY_AVAILABLE = "PARTIALLY_AVAILABLE"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    STALE = "STALE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
```

### 3.2 State Semantics
- **`AVAILABLE`**: Complete, fresh, verified observations exist meeting institutional agronomic standards. All primary indicators are present.
- **`PARTIALLY_AVAILABLE`**: Essential parameters exist (e.g. soil pH or water EC), but secondary or corroborating metrics (e.g. NPK or RSC ions) are missing.
- **`STALE`**: Previously recorded data exists, but the observation age exceeds the domain validity threshold. Requires re-synchronization or new testing.
- **`INSUFFICIENT_EVIDENCE`**: Records exist, but data quality is defective, 100% cloud-masked, uncalibrated, conflicting, or fails scientific validation.
- **`NOT_AVAILABLE`**: Zero records, reports, water sources, or sync runs exist for this farm parcel.

### 3.3 Domain Freshness Thresholds & State Evaluation Rules

| Domain | Freshness Threshold | Stale Threshold | AVAILABLE Condition | PARTIALLY_AVAILABLE Condition | STALE Condition | INSUFFICIENT_EVIDENCE Condition | NOT_AVAILABLE Condition |
|---|---|---|---|---|---|---|---|
| **Soil** | Lab: $\le 1095$ d (3 yr); Spatial: $\le 365$ d | Lab: $> 1095$ d; Spatial: $> 365$ d | Confirmed lab report with primary NPK + pH + SOC; OR fresh spatial SoilGrids profile with chemical & physical parameters. | Lab report confirmed but missing primary nutrients (e.g. pH/SOC present, NPK absent); OR unconfirmed report in review. | Latest lab report $> 3$ years old; OR latest spatial extraction $> 1$ year old. | Qualitative soil notes present, but zero numerical measurements; or extraction failed validation. | No soil profile generated and no soil test reports uploaded. |
| **Water** | Lab: $\le 365$ d (1 yr) | Lab: $> 365$ d | Active water source registered AND confirmed lab test with complete ions (EC, Ca, Mg, Na, HCO3, CO3) enabling SAR & RSC. | Active water source registered with partial test (e.g. EC and TDS only, missing cations for SAR). | Confirmed water report $> 365$ days old (seasonal aquifer fluctuation). | Water source registered with unknown type, zero capacity data, and unverified parameters. | No water sources registered and no water test reports uploaded. |
| **Satellite** | Overpass: $\le 14$ d | Overpass: $> 30$ d | Valid Sentinel-2 L2A observation within 14 days, valid pixels $\ge 5$, pure Class 4 canopy NDVI/NDMI segregated. | Observation within 14 days, but cloud/shadow cover $> 50\%$, or small farm warning ($<0.5$ ha / $<5$ pixels). | Observation date $> 30$ days old. | $100\%$ cloud/shadow obstruction; zero valid surface pixels. | Zero satellite observations or sync runs recorded for this farm. |
| **Weather** | Current: $\le 2$ h; Forecast: $\le 12$ h | Current: $> 2$ h; Forecast: $> 12$ h | Observed current weather within 2h AND 5-day forecast within 12h AND 30-year climate summary present. | Current weather available, but forecast unavailable; or climate summary without current weather. | Current observation $> 2$ hours old; forecast $> 12$ hours old; climate $> 30$ days old. | Sensor coordinates out of bounds or provider returned corrupted payload. | No weather snapshots recorded and external weather provider unreachable. |
| **Crop Context** | Decision: $\le 180$ d (current season) | Decision: $> 180$ d | Active decision evaluated for current season with candidate crops assigned verified decision states. | Decision evaluated, but multiple crops marked `CONDITIONALLY_SUITABLE_PENDING_DATA` due to missing inputs. | Decision evaluated for previous cultivation year or season ($>180$ days). | $> 50\%$ of candidate crops marked `ABSTAIN_INSUFFICIENT_EVIDENCE`. | No crop evaluation has ever been executed for this farm. |

---

## 4. Complete Pydantic Schemas & JSON Data Types

### 4.1 Python Pydantic Model Code
Below is the definitive Pydantic v2 code specification to be implemented in `services/api/app/schemas/farm_health.py`:

```python
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from pydantic import BaseModel, Field

class DataAvailabilityState(str, Enum):
    AVAILABLE = "AVAILABLE"
    PARTIALLY_AVAILABLE = "PARTIALLY_AVAILABLE"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    STALE = "STALE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"

class OverallEvidenceOverview(BaseModel):
    domains_available: int = Field(..., ge=0, le=5, description="Count of domains with complete, fresh data")
    domains_partially_available: int = Field(..., ge=0, le=5, description="Count of domains with partial data")
    domains_stale: int = Field(..., ge=0, le=5, description="Count of domains with expired data")
    domains_not_available: int = Field(..., ge=0, le=5, description="Count of domains with zero data")
    domains_insufficient_evidence: int = Field(..., ge=0, le=5, description="Count of domains with corrupted or uncalibrated data")
    total_domains: int = Field(default=5, description="Total evaluated domains (soil, water, satellite, weather, crop_context)")
    actionable_summary: str = Field(..., description="Actionable English text directing farmer to resolve missing or stale domains")

class SoilKeyIndicators(BaseModel):
    soil_ph: Optional[float] = Field(None, description="Soil reaction (pH in 1:2.5 soil-water suspension)")
    organic_carbon_pct: Optional[float] = Field(None, description="Soil organic carbon percentage (Walkley-Black)")
    electrical_conductivity_ds_m: Optional[float] = Field(None, description="Electrical conductivity in dS/m")
    available_nitrogen_kg_ha: Optional[float] = Field(None, description="Available nitrogen in kg/ha (Alkaline KMnO4)")
    available_phosphorus_kg_ha: Optional[float] = Field(None, description="Available phosphorus in kg/ha (Olsen P)")
    available_potassium_kg_ha: Optional[float] = Field(None, description="Available potassium in kg/ha (Neutral NH4OAc)")
    soil_texture: Optional[str] = Field(None, description="USDA soil textural class (e.g. Clay, Clay Loam)")
    cation_exchange_capacity: Optional[float] = Field(None, description="Cation exchange capacity in cmol(+)/kg")

class SoilDomainSummary(BaseModel):
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
    source_id: str = Field(..., description="Water source identifier")
    source_type: str = Field(..., description="borewell | open_well | canal | river | farm_pond | pipeline")
    name: str = Field(..., description="Farmer-assigned water source name")
    seasonal_availability: str = Field(..., description="perennial | seasonal_monsoon | seasonal_post_monsoon | summer_scarce")
    reliability: str = Field(..., description="reliable | moderate | intermittent")
    irrigation_method: str = Field(..., description="drip | sprinkler | flood | furrow")
    measured_capacity_lph: Optional[float] = Field(None, description="Discharge capacity in liters per hour")
    capacity_provenance: str = Field(..., description="MEASURED | FARMER_REPORTED")

class WaterKeyIndicators(BaseModel):
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
    parameter_key: str = Field(..., description="Evaluated parameter identifier, e.g. electrical_conductivity, sar, rsc")
    parameter_name: str = Field(..., description="Human-readable parameter name")
    hazard_level: str = Field(..., description="SAFE | LOW | MEDIUM | HIGH | VERY_HIGH | HAZARDOUS | UNVERIFIED")
    hazard_title: str = Field(..., description="Institutional hazard classification title")
    standard_applied: str = Field(..., description="BIS IS 11624:2019 | ICAR-CSSRI Karnal Tech Bull 1/98")
    management_guidance: str = Field(..., description="Agronomic management guidance under institutional guidelines")

class WaterDomainSummary(BaseModel):
    availability_state: DataAvailabilityState
    last_updated: Optional[datetime] = Field(None, description="Timestamp of latest confirmed water report")
    data_age_days: Optional[int] = Field(None, description="Age of latest water test in days")
    registered_sources_count: int = Field(default=0, description="Total active water sources registered on farm")
    sources: List[WaterSourceSummaryItem] = Field(default_factory=list, description="List of registered water sources")
    laboratory_name: Optional[str] = Field(None, description="Name of testing laboratory if tested")
    key_indicators: WaterKeyIndicators = Field(default_factory=WaterKeyIndicators)
    institutional_evaluations: List[WaterEvaluationFinding] = Field(default_factory=list, description="BIS/ICAR hazard evaluations")
    missing_critical_parameters: List[str] = Field(default_factory=list, description="Missing water quality parameters")

class SatelliteRasterUrls(BaseModel):
    ndvi_map_url: Optional[str] = Field(None, description="Relative URL to retrieve NDVI 2D PNG raster map")
    ndmi_map_url: Optional[str] = Field(None, description="Relative URL to retrieve NDMI 2D PNG raster map")
    scl_map_url: Optional[str] = Field(None, description="Relative URL to retrieve Scene Classification (SCL) map")

class SatelliteDomainSummary(BaseModel):
    availability_state: DataAvailabilityState
    observation_date: Optional[datetime] = Field(None, description="UTC timestamp of Sentinel-2 satellite overpass")
    observation_age_days: Optional[int] = Field(None, description="Age of satellite overpass in days")
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
    observation_time: Optional[datetime] = Field(None, description="Timestamp of weather observation")
    temperature_c: Optional[float] = Field(None, description="Observed dry bulb temperature in Celsius")
    humidity_percent: Optional[float] = Field(None, description="Relative humidity percentage")
    precipitation_mm: Optional[float] = Field(None, description="Current precipitation rate in mm/h")
    wind_speed_ms: Optional[float] = Field(None, description="Wind speed in meters per second")
    weather_condition: Optional[str] = Field(None, description="Primary weather condition (e.g. Clear, Rain)")
    weather_description: Optional[str] = Field(None, description="Detailed condition description")

class ForecastSummary(BaseModel):
    forecast_days_count: int = Field(default=0, description="Number of days in forecast window")
    next_48h_rain_expected_mm: Optional[float] = Field(None, description="Expected precipitation accumulation in next 48h")
    temp_min_c: Optional[float] = Field(None, description="Forecasted minimum temperature in Celsius")
    temp_max_c: Optional[float] = Field(None, description="Forecasted maximum temperature in Celsius")
    weather_alerts: List[str] = Field(default_factory=list, description="Active weather alerts (e.g. heat wave, unseasonal frost)")

class ClimateNormalsSummary(BaseModel):
    annual_rainfall_mm: Optional[float] = Field(None, description="30-year climatological annual precipitation (NASA POWER)")
    monsoon_rainfall_mm: Optional[float] = Field(None, description="30-year monsoon season precipitation")
    mean_temperature_c: Optional[float] = Field(None, description="30-year mean annual temperature")
    potential_water_stress_indicator: Optional[str] = Field(None, description="Climatological water balance stress indicator")

class WeatherDomainSummary(BaseModel):
    availability_state: DataAvailabilityState
    last_updated: Optional[datetime] = Field(None, description="Timestamp of weather snapshot collection")
    current_weather: CurrentWeatherSummary = Field(default_factory=CurrentWeatherSummary)
    forecast: ForecastSummary = Field(default_factory=ForecastSummary)
    climate_normals: ClimateNormalsSummary = Field(default_factory=ClimateNormalsSummary)

class CropSuitabilityItem(BaseModel):
    crop_id: str = Field(..., description="Crop identifier, e.g. pomegranate, wheat, soybean")
    common_name: str = Field(..., description="English common name")
    marathi_name: Optional[str] = Field(None, description="Marathi common name")
    decision_state: str = Field(..., description="Deterministic decision outcome: VERIFIED_SUITABLE | CONDITIONALLY_SUITABLE_PENDING_DATA | etc.")
    limiting_factors: List[str] = Field(default_factory=list, description="Biological or environmental constraints identified")
    irrigation_guidance: Optional[str] = Field(None, description="Agronomic water management recommendation")

class CropContextDomainSummary(BaseModel):
    availability_state: DataAvailabilityState
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
```

### 4.2 JSON Schema Field Descriptions

| JSON Path | Data Type | Nullable | Description | Validation Constraints |
|---|---|---|---|---|
| `contract_version` | string | No | Schema version identifier | Constant `"1.0"` |
| `farm_id` | string (UUID) | No | Farm UUID | Valid RFC 4122 UUID |
| `farm_name` | string | No | Farm title | Non-empty string |
| `owner_id` | string (UUID) | No | User UUID of farm owner | Valid RFC 4122 UUID |
| `taluka` | string | No | Sub-district administrative unit | Non-empty string |
| `district` | string | No | District administrative unit | Non-empty string |
| `state` | string | No | State administrative unit | Non-empty string |
| `calculated_area_hectares` | number | No | Farm polygon area | $> 0.0$ |
| `calculated_area_acres` | number | No | Farm polygon area in acres | $> 0.0$ |
| `snapshot_timestamp` | string (ISO-8601) | No | Snapshot generation UTC time | Valid ISO 8601 UTC timestamp |
| `overall_evidence_overview.domains_available` | integer | No | Count of domains with full fresh data | $\in [0, 5]$ |
| `overall_evidence_overview.domains_partially_available` | integer | No | Count of domains with partial data | $\in [0, 5]$ |
| `overall_evidence_overview.domains_stale` | integer | No | Count of domains with expired data | $\in [0, 5]$ |
| `overall_evidence_overview.domains_not_available` | integer | No | Count of domains with no data | $\in [0, 5]$ |
| `overall_evidence_overview.domains_insufficient_evidence` | integer | No | Count of domains with bad data | $\in [0, 5]$ |
| `overall_evidence_overview.total_domains` | integer | No | Total evaluated domains | Constant `5` |
| `overall_evidence_overview.actionable_summary` | string | No | Summary of data completeness | Non-empty string |
| `soil.availability_state` | string | No | Soil availability state | One of `DataAvailabilityState` |
| `soil.last_updated` | string (ISO-8601) | Yes | Timestamp of soil update | Null if state is `NOT_AVAILABLE` |
| `soil.data_age_days` | integer | Yes | Age of soil data in days | $\ge 0$ if present |
| `soil.provenance` | string | Yes | Data provenance | `LABORATORY_CONFIRMED`, `SPATIALLY_ESTIMATED_ISRIC`, `MIXED_DUAL_SOURCE` |
| `soil.key_indicators.*` | number / string | Yes | Numerical soil parameters | Null if measurement absent |
| `water.availability_state` | string | No | Water availability state | One of `DataAvailabilityState` |
| `water.registered_sources_count` | integer | No | Number of active water sources | $\ge 0$ |
| `water.sources[]` | array | No | List of water source details | Array of `WaterSourceSummaryItem` |
| `water.key_indicators.sar` | number | Yes | Sodium Adsorption Ratio | Null if cations missing |
| `water.key_indicators.rsc_meq_l` | number | Yes | Residual Sodium Carbonate | Null if carbonate/calcium missing |
| `water.institutional_evaluations[]` | array | No | BIS/ICAR hazard evaluations | Array of `WaterEvaluationFinding` |
| `satellite.availability_state` | string | No | Satellite availability state | One of `DataAvailabilityState` |
| `satellite.canopy_ndvi` | number | Yes | Class 4 pure vegetation mean NDVI | $\in [-1.0, 1.0]$, null if no canopy |
| `satellite.canopy_ndmi` | number | Yes | Class 4 pure vegetation mean NDMI | $\in [-1.0, 1.0]$, null if no canopy |
| `satellite.vegetation_coverage_percent` | number | Yes | Percentage of parcel with canopy | $\in [0.0, 100.0]$ |
| `satellite.raster_maps.*` | string (URL) | Yes | Raster map endpoint paths | Valid relative API path or null |
| `satellite.scientific_disclaimer` | string | No | Mandatory agronomic disclaimer | Non-empty string |
| `weather.availability_state` | string | No | Weather availability state | One of `DataAvailabilityState` |
| `weather.current_weather.*` | number / string | Yes | Current weather metrics | Null if API unreachable |
| `weather.forecast.*` | number / array | Yes | Forecast metrics and alerts | Null/empty if unavailable |
| `weather.climate_normals.*` | number / string | Yes | 30-year climatological normals | Null if climate unavailable |
| `crop_context.availability_state` | string | No | Crop context availability state | One of `DataAvailabilityState` |
| `crop_context.suitable_crops[]` | array | No | List of verified suitable crops | Array of `CropSuitabilityItem` |
| `crop_context.disqualified_crops[]`| array | No | List of disqualified crops | Array of `CropSuitabilityItem` |
| `governance_notice` | string | No | Mandatory governance disclaimer | Non-empty string |

---

## 5. Canonical Payload Examples

### 5.1 Example A: Full Evidence Farm (Live Verified Parcel)
Scenario: Complete, fresh, farmer-confirmed laboratory soil and water reports, recent cloud-free Sentinel-2 overpass, live OpenWeather observation, and active Rabi season crop evaluation.

```json
{
  "contract_version": "1.0",
  "farm_id": "94a1f16e-bf0d-4d3f-9bd3-d63a57189818",
  "farm_name": "Baramati Model Farm",
  "owner_id": "00000000-0000-0000-0000-000000000001",
  "taluka": "Baramati",
  "district": "Pune",
  "state": "Maharashtra",
  "calculated_area_hectares": 2.5,
  "calculated_area_acres": 6.18,
  "snapshot_timestamp": "2026-11-08T11:45:00Z",
  "overall_evidence_overview": {
    "domains_available": 5,
    "domains_partially_available": 0,
    "domains_stale": 0,
    "domains_not_available": 0,
    "domains_insufficient_evidence": 0,
    "total_domains": 5,
    "actionable_summary": "Complete actionable evidence available across all 5 domains. No blocking data gaps."
  },
  "soil": {
    "availability_state": "AVAILABLE",
    "last_updated": "2026-10-15T09:30:00Z",
    "data_age_days": 24,
    "provenance": "MIXED_DUAL_SOURCE",
    "laboratory_name": "KVK Baramati Soil Testing Laboratory",
    "sample_depth": "0-15 cm",
    "key_indicators": {
      "soil_ph": 7.6,
      "organic_carbon_pct": 0.58,
      "electrical_conductivity_ds_m": 0.45,
      "available_nitrogen_kg_ha": 210.0,
      "available_phosphorus_kg_ha": 18.5,
      "available_potassium_kg_ha": 340.0,
      "soil_texture": "Clay Loam",
      "cation_exchange_capacity": 38.2
    },
    "missing_critical_parameters": [],
    "agronomic_notes": [
      "Farmer-confirmed physical laboratory test from KVK Baramati.",
      "Soil organic carbon is moderate (0.58%); nitrogen is low."
    ]
  },
  "water": {
    "availability_state": "AVAILABLE",
    "last_updated": "2026-09-20T14:15:00Z",
    "data_age_days": 49,
    "registered_sources_count": 1,
    "sources": [
      {
        "source_id": "wsrc-001",
        "source_type": "borewell",
        "name": "North Field Borewell",
        "seasonal_availability": "perennial",
        "reliability": "reliable",
        "irrigation_method": "drip",
        "measured_capacity_lph": 12000.0,
        "capacity_provenance": "MEASURED"
      }
    ],
    "laboratory_name": "Agricultural Water Testing Laboratory, Pune",
    "key_indicators": {
      "ph": 7.6,
      "electrical_conductivity_ds_m": 1.85,
      "tds_mg_l": 1184.0,
      "sar": 3.01,
      "sar_status": "AVAILABLE",
      "rsc_meq_l": -1.9,
      "rsc_status": "AVAILABLE",
      "chloride_meq_l": 4.8,
      "boron_mg_l": 0.65
    },
    "institutional_evaluations": [
      {
        "parameter_key": "electrical_conductivity",
        "parameter_name": "Electrical Conductivity (EC)",
        "hazard_level": "MEDIUM",
        "hazard_title": "Medium Salinity (Class 2 - Moderate Restriction)",
        "standard_applied": "BIS IS 11624:2019",
        "management_guidance": "Water can be used on soils with moderate drainage. Leaching fraction required for salt-sensitive crops."
      },
      {
        "parameter_key": "sar",
        "parameter_name": "Sodium Adsorption Ratio (SAR)",
        "hazard_level": "LOW",
        "hazard_title": "Low Sodium Hazard (S1 - Safe)",
        "standard_applied": "BIS IS 11624:2019",
        "management_guidance": "Can be used for irrigation on almost all soils with little danger of harmful sodification."
      },
      {
        "parameter_key": "rsc",
        "parameter_name": "Residual Sodium Carbonate (RSC)",
        "hazard_level": "SAFE",
        "hazard_title": "Safe (Low Alkalinity Hazard)",
        "standard_applied": "ICAR-CSSRI Karnal Tech Bull 1/98",
        "management_guidance": "Water can be used safely without risk of residual sodium carbonate accumulation."
      }
    ],
    "missing_critical_parameters": []
  },
  "satellite": {
    "availability_state": "AVAILABLE",
    "observation_date": "2026-11-04T05:43:53Z",
    "observation_age_days": 4,
    "sensor": "Sentinel-2 L2A",
    "product_id": "S2B_MSIL2A_20261104T053009_N0513_R105_T43QDB_20261104T073410",
    "canopy_ndvi": 0.68,
    "canopy_ndmi": 0.22,
    "composite_mean_ndvi": 0.52,
    "bare_soil_mean_ndvi": 0.28,
    "vegetation_coverage_percent": 68.4,
    "bare_soil_coverage_percent": 31.6,
    "cloud_masked_percent": 0.0,
    "valid_pixel_count": 250,
    "quality_status": "VALID_OBSERVATION",
    "is_small_farm_warning": false,
    "raster_maps": {
      "ndvi_map_url": "/api/v1/farms/94a1f16e-bf0d-4d3f-9bd3-d63a57189818/satellite/latest/raster-map?index_type=ndvi",
      "ndmi_map_url": "/api/v1/farms/94a1f16e-bf0d-4d3f-9bd3-d63a57189818/satellite/latest/raster-map?index_type=ndmi",
      "scl_map_url": "/api/v1/farms/94a1f16e-bf0d-4d3f-9bd3-d63a57189818/satellite/latest/raster-map?index_type=scl"
    },
    "agronomic_interpretation": "Active photosynthetic canopy covering 68.4% of parcel. High vegetative biomass vigor (canopy NDVI 0.68).",
    "scientific_disclaimer": "Sentinel-2 NDVI and NDMI reflect surface optical reflectance (10m GSD). They are indirect canopy vigor indicators, NOT direct disease pathogen or yield diagnoses."
  },
  "weather": {
    "availability_state": "AVAILABLE",
    "last_updated": "2026-11-08T11:30:00Z",
    "current_weather": {
      "observation_time": "2026-11-08T11:20:00Z",
      "temperature_c": 28.4,
      "humidity_percent": 48.0,
      "precipitation_mm": 0.0,
      "wind_speed_ms": 3.1,
      "weather_condition": "Clear",
      "weather_description": "clear sky"
    },
    "forecast": {
      "forecast_days_count": 5,
      "next_48h_rain_expected_mm": 0.0,
      "temp_min_c": 17.5,
      "temp_max_c": 31.0,
      "weather_alerts": []
    },
    "climate_normals": {
      "annual_rainfall_mm": 560.0,
      "monsoon_rainfall_mm": 440.0,
      "mean_temperature_c": 24.5,
      "potential_water_stress_indicator": "Moderate seasonal winter dry spell"
    }
  },
  "crop_context": {
    "availability_state": "AVAILABLE",
    "evaluated_at": "2026-11-08T10:00:00Z",
    "target_season": "Rabi 2026-27",
    "taluka_resolved": "Baramati",
    "evaluated_crops_count": 10,
    "suitable_crops": [
      {
        "crop_id": "wheat",
        "common_name": "Wheat",
        "marathi_name": "गहू",
        "decision_state": "VERIFIED_SUITABLE",
        "limiting_factors": [],
        "irrigation_guidance": "Crown root initiation (CRI) irrigation critical at 21 DAS."
      },
      {
        "crop_id": "chickpea",
        "common_name": "Chickpea",
        "marathi_name": "हरभरा",
        "decision_state": "VERIFIED_SUITABLE",
        "limiting_factors": [],
        "irrigation_guidance": "Branching and pod initiation irrigations recommended."
      }
    ],
    "conditionally_suitable_crops": [
      {
        "crop_id": "onion",
        "common_name": "Rabi Onion",
        "marathi_name": "कांदा",
        "decision_state": "CONDITIONALLY_SUITABLE_PENDING_DATA",
        "limiting_factors": [
          "Moderate salinity sensitivity in Vertisols"
        ],
        "irrigation_guidance": "Frequent light irrigations required to minimize salinity stress."
      }
    ],
    "disqualified_crops": [],
    "abstain_crops": [],
    "top_limiting_factors": [
      "Water EC 1.85 dS/m requires leaching fraction for salt-sensitive crops"
    ],
    "pending_followup_questions_count": 1
  },
  "governance_notice": "CropNet AI provides independent, evidence-gated agricultural domain summaries. In accordance with institutional agricultural guidelines, no universal health score is computed."
}
```

### 5.2 Example B: Missing Evidence Farm (Brand New Parcel)
Scenario: Freshly registered parcel with polygon boundary only. Zero soil tests, zero water sources, zero satellite sync runs, zero weather queries, and zero crop evaluations executed. Strictly returns `null` for missing metrics without fake or manufactured numbers.

```json
{
  "contract_version": "1.0",
  "farm_id": "e4b2d189-9a74-4b5c-897b-3d6e5c9f1a23",
  "farm_name": "New Registered Parcel",
  "owner_id": "00000000-0000-0000-0000-000000000001",
  "taluka": "Indapur",
  "district": "Pune",
  "state": "Maharashtra",
  "calculated_area_hectares": 1.2,
  "calculated_area_acres": 2.97,
  "snapshot_timestamp": "2026-11-08T11:45:00Z",
  "overall_evidence_overview": {
    "domains_available": 0,
    "domains_partially_available": 0,
    "domains_stale": 0,
    "domains_not_available": 5,
    "domains_insufficient_evidence": 0,
    "total_domains": 5,
    "actionable_summary": "Zero evidence recorded for this farm. Immediate actions required: 1) Run initial soil analysis or upload soil card, 2) Register water source, 3) Sync satellite vegetation."
  },
  "soil": {
    "availability_state": "NOT_AVAILABLE",
    "last_updated": null,
    "data_age_days": null,
    "provenance": null,
    "laboratory_name": null,
    "sample_depth": null,
    "key_indicators": {
      "soil_ph": null,
      "organic_carbon_pct": null,
      "electrical_conductivity_ds_m": null,
      "available_nitrogen_kg_ha": null,
      "available_phosphorus_kg_ha": null,
      "available_potassium_kg_ha": null,
      "soil_texture": null,
      "cation_exchange_capacity": null
    },
    "missing_critical_parameters": [
      "soil_ph",
      "organic_carbon",
      "nitrogen",
      "phosphorus",
      "potassium",
      "texture"
    ],
    "agronomic_notes": [
      "No soil profile has been generated or uploaded for this farm.",
      "Action required: Trigger initial SoilGrids spatial analysis or upload a certified laboratory soil test report."
    ]
  },
  "water": {
    "availability_state": "NOT_AVAILABLE",
    "last_updated": null,
    "data_age_days": null,
    "registered_sources_count": 0,
    "sources": [],
    "laboratory_name": null,
    "key_indicators": {
      "ph": null,
      "electrical_conductivity_ds_m": null,
      "tds_mg_l": null,
      "sar": null,
      "sar_status": "UNAVAILABLE",
      "rsc_meq_l": null,
      "rsc_status": "UNAVAILABLE",
      "chloride_meq_l": null,
      "boron_mg_l": null
    },
    "institutional_evaluations": [],
    "missing_critical_parameters": [
      "water_source",
      "electrical_conductivity",
      "sar",
      "rsc"
    ]
  },
  "satellite": {
    "availability_state": "NOT_AVAILABLE",
    "observation_date": null,
    "observation_age_days": null,
    "sensor": "Sentinel-2 L2A",
    "product_id": null,
    "canopy_ndvi": null,
    "canopy_ndmi": null,
    "composite_mean_ndvi": null,
    "bare_soil_mean_ndvi": null,
    "vegetation_coverage_percent": null,
    "bare_soil_coverage_percent": null,
    "cloud_masked_percent": null,
    "valid_pixel_count": 0,
    "quality_status": null,
    "is_small_farm_warning": false,
    "raster_maps": {
      "ndvi_map_url": null,
      "ndmi_map_url": null,
      "scl_map_url": null
    },
    "agronomic_interpretation": "No satellite synchronization has been performed for this farm boundary. Trigger satellite sync to compute Sentinel-2 canopy vigor.",
    "scientific_disclaimer": "Sentinel-2 NDVI and NDMI reflect surface optical reflectance (10m GSD). They are indirect canopy vigor indicators, NOT direct disease pathogen or yield diagnoses."
  },
  "weather": {
    "availability_state": "NOT_AVAILABLE",
    "last_updated": null,
    "current_weather": {
      "observation_time": null,
      "temperature_c": null,
      "humidity_percent": null,
      "precipitation_mm": null,
      "wind_speed_ms": null,
      "weather_condition": null,
      "weather_description": null
    },
    "forecast": {
      "forecast_days_count": 0,
      "next_48h_rain_expected_mm": null,
      "temp_min_c": null,
      "temp_max_c": null,
      "weather_alerts": []
    },
    "climate_normals": {
      "annual_rainfall_mm": null,
      "monsoon_rainfall_mm": null,
      "mean_temperature_c": null,
      "potential_water_stress_indicator": null
    }
  },
  "crop_context": {
    "availability_state": "NOT_AVAILABLE",
    "evaluated_at": null,
    "target_season": null,
    "taluka_resolved": "Indapur",
    "evaluated_crops_count": 0,
    "suitable_crops": [],
    "conditionally_suitable_crops": [],
    "disqualified_crops": [],
    "abstain_crops": [],
    "top_limiting_factors": [
      "No environmental or biological farm context available to evaluate crop suitability."
    ],
    "pending_followup_questions_count": 0
  },
  "governance_notice": "CropNet AI provides independent, evidence-gated agricultural domain summaries. In accordance with institutional agricultural guidelines, no universal health score is computed."
}
```

### 5.3 Example C: Stale Evidence Farm (Expired Historical Records)
Scenario: Farm parcel with historical records exceeding all freshness thresholds. Soil lab report is 4.2 years old (>1095 days), water test is 511 days old (>365 days), Sentinel-2 observation is 57 days old (>30 days), weather cache is 5.7 hours old (>2 hours), and crop evaluation was performed for the previous year (>180 days). Returns `STALE` status and age metadata to prompt re-testing.

```json
{
  "contract_version": "1.0",
  "farm_id": "c8d2e3f4-5678-4abc-9def-0123456789ab",
  "farm_name": "Sangamner Pomegranate Orchard",
  "owner_id": "00000000-0000-0000-0000-000000000001",
  "taluka": "Sangamner",
  "district": "Ahmednagar",
  "state": "Maharashtra",
  "calculated_area_hectares": 3.1,
  "calculated_area_acres": 7.66,
  "snapshot_timestamp": "2026-11-08T11:45:00Z",
  "overall_evidence_overview": {
    "domains_available": 0,
    "domains_partially_available": 0,
    "domains_stale": 5,
    "domains_not_available": 0,
    "domains_insufficient_evidence": 0,
    "total_domains": 5,
    "actionable_summary": "All recorded farm evidence is stale (>30 days for satellite, >2 hours for weather, >1 year for water, >3 years for soil, >180 days for crop evaluation). Re-synchronization and updated testing strongly recommended."
  },
  "soil": {
    "availability_state": "STALE",
    "last_updated": "2022-08-10T10:00:00Z",
    "data_age_days": 1551,
    "provenance": "LABORATORY_CONFIRMED",
    "laboratory_name": "Rahuri Agricultural University Soil Lab",
    "sample_depth": "0-30 cm",
    "key_indicators": {
      "soil_ph": 8.1,
      "organic_carbon_pct": 0.42,
      "electrical_conductivity_ds_m": 0.62,
      "available_nitrogen_kg_ha": 185.0,
      "available_phosphorus_kg_ha": 12.0,
      "available_potassium_kg_ha": 290.0,
      "soil_texture": "Clay",
      "cation_exchange_capacity": 42.0
    },
    "missing_critical_parameters": [],
    "agronomic_notes": [
      "Soil laboratory test report is over 3 years old (1551 days). Soil nutrient and organic carbon levels may have shifted significantly.",
      "Recommendation: Collect fresh soil samples and submit for updated Soil Health Card testing."
    ]
  },
  "water": {
    "availability_state": "STALE",
    "last_updated": "2025-06-15T11:30:00Z",
    "data_age_days": 511,
    "registered_sources_count": 1,
    "sources": [
      {
        "source_id": "wsrc-088",
        "source_type": "open_well",
        "name": "East Perimeter Well",
        "seasonal_availability": "seasonal_post_monsoon",
        "reliability": "moderate",
        "irrigation_method": "drip",
        "measured_capacity_lph": 8000.0,
        "capacity_provenance": "FARMER_REPORTED"
      }
    ],
    "laboratory_name": "District Water Testing Lab, Ahmednagar",
    "key_indicators": {
      "ph": 7.9,
      "electrical_conductivity_ds_m": 2.2,
      "tds_mg_l": 1408.0,
      "sar": 4.1,
      "sar_status": "AVAILABLE",
      "rsc_meq_l": 1.2,
      "rsc_status": "AVAILABLE",
      "chloride_meq_l": 6.5,
      "boron_mg_l": 0.8
    },
    "institutional_evaluations": [
      {
        "parameter_key": "electrical_conductivity",
        "parameter_name": "Electrical Conductivity (EC)",
        "hazard_level": "MEDIUM",
        "hazard_title": "Medium Salinity (Class 2 - Moderate Restriction)",
        "standard_applied": "BIS IS 11624:2019",
        "management_guidance": "Test is 511 days old. Groundwater salinity fluctuates after monsoon recharge; re-testing required."
      }
    ],
    "missing_critical_parameters": []
  },
  "satellite": {
    "availability_state": "STALE",
    "observation_date": "2026-09-12T05:40:02Z",
    "observation_age_days": 57,
    "sensor": "Sentinel-2 L2A",
    "product_id": "S2B_MSIL2A_20260912T053009_N0513_R105_T43QDB_20260912T074000",
    "canopy_ndvi": 0.44,
    "canopy_ndmi": 0.08,
    "composite_mean_ndvi": 0.38,
    "bare_soil_mean_ndvi": 0.25,
    "vegetation_coverage_percent": 35.2,
    "bare_soil_coverage_percent": 64.8,
    "cloud_masked_percent": 0.0,
    "valid_pixel_count": 310,
    "quality_status": "VALID_OBSERVATION",
    "is_small_farm_warning": false,
    "raster_maps": {
      "ndvi_map_url": "/api/v1/farms/c8d2e3f4-5678-4abc-9def-0123456789ab/satellite/latest/raster-map?index_type=ndvi",
      "ndmi_map_url": "/api/v1/farms/c8d2e3f4-5678-4abc-9def-0123456789ab/satellite/latest/raster-map?index_type=ndmi",
      "scl_map_url": "/api/v1/farms/c8d2e3f4-5678-4abc-9def-0123456789ab/satellite/latest/raster-map?index_type=scl"
    },
    "agronomic_interpretation": "Satellite observation is 57 days old (>30 days). Historical canopy vigor may not reflect current vegetative stage. Trigger satellite sync.",
    "scientific_disclaimer": "Sentinel-2 NDVI and NDMI reflect surface optical reflectance (10m GSD). They are indirect canopy vigor indicators, NOT direct disease pathogen or yield diagnoses."
  },
  "weather": {
    "availability_state": "STALE",
    "last_updated": "2026-11-08T06:00:00Z",
    "current_weather": {
      "observation_time": "2026-11-08T05:45:00Z",
      "temperature_c": 21.0,
      "humidity_percent": 65.0,
      "precipitation_mm": 0.0,
      "wind_speed_ms": 1.8,
      "weather_condition": "Haze",
      "weather_description": "haze"
    },
    "forecast": {
      "forecast_days_count": 5,
      "next_48h_rain_expected_mm": 0.0,
      "temp_min_c": 16.0,
      "temp_max_c": 30.0,
      "weather_alerts": []
    },
    "climate_normals": {
      "annual_rainfall_mm": 520.0,
      "monsoon_rainfall_mm": 410.0,
      "mean_temperature_c": 25.1,
      "potential_water_stress_indicator": "High dry season deficit"
    }
  },
  "crop_context": {
    "availability_state": "STALE",
    "evaluated_at": "2025-07-01T08:00:00Z",
    "target_season": "Kharif 2025",
    "taluka_resolved": "Sangamner",
    "evaluated_crops_count": 8,
    "suitable_crops": [
      {
        "crop_id": "pomegranate",
        "common_name": "Pomegranate",
        "marathi_name": "डाळिंब",
        "decision_state": "CONDITIONALLY_SUITABLE_PENDING_DATA",
        "limiting_factors": [
          "Evaluation performed for previous cropping year (>180 days old)"
        ],
        "irrigation_guidance": "Mrungh Bahar flowering schedule requires current water test verification."
      }
    ],
    "conditionally_suitable_crops": [],
    "disqualified_crops": [],
    "abstain_crops": [],
    "top_limiting_factors": [
      "Stale historical evaluation: Run updated crop suitability evaluation for current agricultural season."
    ],
    "pending_followup_questions_count": 2
  },
  "governance_notice": "CropNet AI provides independent, evidence-gated agricultural domain summaries. In accordance with institutional agricultural guidelines, no universal health score is computed."
}
```

---

## 6. Explicit Governance & Agronomic Safeguards

### 6.1 Prohibition of Universal Farm Health Score
1. **Rule**: CropNet AI strictly prohibits calculating, storing, or returning a composite single farm score (e.g. `84/100`, `Grade: A`, `health_index: 0.82`).
2. **Scientific Rationale**:
   - Crop production is strictly bounded by **Liebig's Law of the Minimum**: yield and crop viability are determined by the most scarce or hazardous resource, not by the aggregate average.
   - For example, if a farm has lush vegetative canopy (NDVI 0.75) and excellent weather, but the irrigation water has an EC of 4.5 dS/m and SAR of 18 (severe sodicity/salinity hazard), a weighted composite score would compute a misleading "favorable" grade (~72/100). If a farmer relies on this false aggregate, sensitive crops will experience osmotic wilt and die, and Vertisol soil structure will be permanently damaged.
3. **Institutional Replacement**:
   - The response provides categorical counts in `overall_evidence_overview` (`domains_available`, `domains_partially_available`, `domains_stale`, `domains_not_available`, `domains_insufficient_evidence`).
   - Every domain must be independently evaluated against its own established agronomic standards.

### 6.2 Prohibition of Synthetic or Manufactured Data
1. **Rule**: Missing domain records MUST NOT generate synthetic or dummy numbers (e.g. inserting default pH 7.0, NDVI 0.60, EC 1.2 dS/m, or fake water sources).
2. **Behavior**:
   - If a domain is unrecorded, its `availability_state` MUST be `"NOT_AVAILABLE"`.
   - All indicators in `key_indicators` MUST be `null`.
   - Numeric `0.0` is permitted ONLY for genuine measured zeroes (e.g., 0.0 mm rainfall or 0.0 meq/L carbonate).
   - Clear, user-actionable instructions must guide the farmer to collect real observations.

### 6.3 Preservation of Deterministic Phase 5.1 Rules
1. **Rule**: The aggregation service operates as an evidence observer and reporter. It MUST NOT alter, override, or relax any deterministic decision state, biological constraint threshold, or Bahar water scheduling rule established in Phase 5.1.
2. **Enforcement**:
   - Crop suitability decisions are retrieved strictly from `DeterministicDecisionEngine`.
   - Water quality hazard classifications are evaluated strictly under BIS IS 11624:2019 and ICAR-CSSRI Karnal Tech Bulletin 1/98.

### 6.4 Satellite Imagery Limitations & Disclaimers
1. **Optical Reflectance Boundary**:
   - Copernicus Sentinel-2 L2A Level-2A data measures surface optical reflectance at 10-meter ground sampling distance (GSD).
   - Vegetation indices (NDVI and NDMI) measure canopy greenness, density, and leaf moisture content.
2. **Prohibited Diagnoses**:
   - Optical satellite data CANNOT diagnose specific fungal/bacterial pathogens (e.g., *Xanthomonas axonopodis*, *Phytophthora*).
   - It CANNOT detect subterranean pest infestations (e.g., root-knot nematodes).
   - It CANNOT predict exact absolute crop yield in quintals without multi-point ground-truth calibration.
3. **Mandatory Disclaimer**:
   - The field `scientific_disclaimer` must accompany every satellite payload.

---

## 7. Client Consumption Guidelines

### 7.1 Agent 2: Backend Implementation (`services/api/app/services/farm_health/`)
- Implement Pydantic models in `cropnet/services/api/app/schemas/farm_health.py`.
- Implement isolated domain collectors in `cropnet/services/api/app/services/farm_health/collectors/`.
- Maintain in-memory snapshot cache (300s TTL) with `invalidate_snapshot(farm_id)` helper.
- Mount `GET /api/v1/farms/{farm_id}/health-snapshot` enforcing `_get_farm_and_verify_owner`.
- Ensure comprehensive unit tests covering:
  - Unauthorized access (HTTP 401/403)
  - Missing domains (NOT_AVAILABLE with nulls, no synthetic values)
  - Stale domain handling (STALE status when age exceeds thresholds)
  - Cache validation and `force_refresh=true` invalidation
  - Absence of universal health score in response

### 7.2 Agent 3: Farm Health Dashboard (Flutter Web/Mobile)
- Read `/api/v1/farms/{farm_id}/health-snapshot`.
- Render **Overall Evidence Overview Card**:
  - Show chips for each availability category: Available (Green), Partially Available (Orange), Stale (Amber), Not Available (Grey), Insufficient Evidence (Red).
  - Display `overall_evidence_overview.actionable_summary`.
  - DO NOT render a circular progress dial or percentage health score.
- Render **Domain Cards** (Soil, Water, Satellite, Weather, Crop Context):
  - When `AVAILABLE`: Render all key indicators with agronomic units (e.g. `dS/m`, `kg/ha`, `meq/L`).
  - When `PARTIALLY_AVAILABLE`: Render available metrics and display a warning chip listing `missing_critical_parameters`.
  - When `STALE`: Render amber banner: `"Observation recorded {data_age_days} days ago. Refresh recommended."` with action button linking to update.
  - When `NOT_AVAILABLE`: Render clean empty state card with zero demo numbers and a direct navigation link to the domain workspace (e.g. "Add Water Source", "Upload Soil Report", "Sync Satellite").
- Maintain responsive layout across Mobile (single column stack) and Tablet/Desktop (2 or 3 column responsive grid).

### 7.3 Agent 4: Integrated AI Agricultural Advisory (Qwen3:8B)
- Consume `FarmHealthSnapshotResponse` as structured contextual grounding in `FarmContextBuilder`.
- Use the explicit `availability_state` across each domain to ground LLM reasoning:
  - If a domain is `AVAILABLE`: LLM can cite exact numbers and hazard findings in its response.
  - If a domain is `NOT_AVAILABLE` or `PARTIALLY_AVAILABLE`: LLM must explicitly tell the farmer that the data is unmeasured rather than hallucinating plausible values.
  - If a domain is `STALE`: LLM must preface guidance with a caveat that data is outdated.
- Support bilingual query/response in both English and Marathi, utilizing `marathi_name` for evaluated crops and Marathi agricultural terminology.
- Preserve Phase 5.8.2 guardrails: LLM must NEVER override deterministic crop disqualifications or invent chemical dosages.

---

## 8. Revision History & Attestation

| Version | Date | Author / Agent | Summary of Changes |
|---|---|---|---|
| 1.0 | 2026-11-08 | Milestone M0 Setup Worker (`teamwork_worker_m0_setup`) | Initial publication of agreed Shared Farm Health Snapshot API Contract based on Section 7 survey. Includes full schemas, freshness thresholds, 3 canonical examples (Full, Missing, Stale), and explicit governance rules. |
