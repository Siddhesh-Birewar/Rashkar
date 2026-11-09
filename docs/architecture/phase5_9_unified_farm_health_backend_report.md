# Phase 5.9A Unified Farm Health Backend Architecture Report

**Author**: Agent 2 (Backend Implementer & Agronomic Systems Engineer)  
**Date**: November 2026  
**Status**: Implemented, Verified, Contract Conforming  
**Target Branch**: `workstream/agent2-farm-health-backend`  
**Shared Contract Reference**: `docs/architecture/farm_health_snapshot_contract.md`

---

## 1. Executive Summary

Phase 5.9A establishes the **Unified Farm Health Backend Service** for CropNet AI. Prior to this implementation, farm operational intelligence was fractured across disparate micro-modules: physical and spatial soil grids, irrigation water quality and BIS/ICAR-CSSRI hazard classifications, Copernicus Sentinel-2 L2A optical reflectance and canopy segregation, real-time weather and 30-year NASA POWER climatology, and Phase 5.1 deterministic agronomic crop decision rules.

This implementation unifies all five foundational domains into a single high-performance, strictly governed, contract-conforming API endpoint:
```http
GET /api/v1/farms/{farm_id}/health-snapshot
```

### Core Architecture Highlights
1. **Isolated Domain Collectors (`services/api/app/services/farm_health/collectors/`)**:
   - `SoilCollector`: Implements strict lab-over-spatial provenance precedence, texture normalization, and 3-year (1095-day) freshness threshold.
   - `WaterCollector`: Integrates active source registries, laboratory test reports, BIS IS 11624:2019 / ICAR-CSSRI hazard evaluations, dynamic SAR/RSC calculation, and 1-year (365-day) freshness threshold.
   - `SatelliteCollector`: Ingests multi-spectral Sentinel-2 observations, segregating pure Class 4 vegetation canopy (NDVI/NDMI) from Class 5 bare soil, surfacing 2D PNG raster visualization URLs, and enforcing a 30-day freshness threshold.
   - `WeatherCollector`: Combines current dry bulb ambient conditions, 48-hour precipitation outlooks, and 30-year climatological normals without hallucinating synthetic data for empty parcels, enforcing a 3-hour freshness threshold.
   - `CropCollector`: Synthesizes Phase 5.1 deterministic suitability states (`VERIFIED_SUITABLE`, `CONDITIONALLY_SUITABLE_PENDING_DATA`, `DISQUALIFIED`, `ABSTAIN`), top limiting factors, and active follow-up questions with a 180-day freshness threshold.

2. **Fault Isolation Architecture (`aggregator.py`)**:
   - Each domain collector runs in an isolated `try...except` boundary.
   - If a domain collector encounters an infrastructure failure, network timeout, or unexpected exception, only that single domain degrades to `NOT_AVAILABLE` with an error diagnostic note. The remaining four domains assemble normally, guaranteeing that farm operational decisions are never blocked by single-domain hiccups.

3. **In-Memory TTL Caching (`cache.py`)**:
   - 300-second (5-minute) TTL cache with thread-safe lock synchronization.
   - Parameterized cache bypass via `force_refresh=true`.
   - Programmatic invalidation hook `invalidate_farm_health_snapshot(farm_id)` and HTTP endpoint `POST /api/v1/farms/{farm_id}/health-snapshot/invalidate` for upstream mutation events (e.g., new soil test upload, water report confirmation).

4. **Strict Agronomic Governance & Integrity**:
   - **ZERO Universal Health Score**: The backend strictly refuses to compute any single composite health percentage or score. Instead, it provides an `OverallEvidenceOverview` containing deterministic state tallies (`domains_available`, `domains_stale`, `domains_not_available`, etc.) and an actionable textual summary.
   - **ZERO Synthetic / Demo Values**: Missing evidence domains return `NOT_AVAILABLE` with explicit `null` fields and actionable onboarding instructions. No placeholder, random, or default numbers are manufactured.
   - **Multi-Tenant Farm Isolation & Security**: Fully enforces `_get_farm_and_verify_owner` and `get_current_user`. Cross-user access is rejected with `HTTP 403 Forbidden`, and non-existent parcels return `HTTP 404 Not Found`.

---

## 2. Shared Contract Conformance Matrix

The implementation in `services/api/app/schemas/farm_health.py` strictly conforms to `docs/architecture/farm_health_snapshot_contract.md`:

| Contract Element | Schema Class | Conformance Status | Implementation Details |
|---|---|---|---|
| Contract Schema Version | `FarmHealthSnapshotResponse.contract_version` | **100% Conforming** | Defaults to `"1.0"`. |
| Top-level Farm Metadata | `FarmHealthSnapshotResponse` | **100% Conforming** | Includes `farm_id`, `farm_name`, `owner_id`, `taluka`, `district`, `state`, `calculated_area_hectares`, `calculated_area_acres`, `snapshot_timestamp`. |
| Overall Evidence Overview | `OverallEvidenceOverview` | **100% Conforming** | Strict counts: `domains_available`, `domains_partially_available`, `domains_stale`, `domains_not_available`, `domains_insufficient_evidence`, `total_domains` (=5), and `actionable_summary`. Zero universal score. |
| Data Availability States | `DataAvailabilityState` Enum | **100% Conforming** | `AVAILABLE`, `PARTIALLY_AVAILABLE`, `NOT_AVAILABLE`, `STALE`, `INSUFFICIENT_EVIDENCE`. |
| Soil Domain Summary | `SoilDomainSummary` | **100% Conforming** | Lab vs spatial provenance (`LABORATORY_CONFIRMED`, `SOILGRIDS_ESTIMATE`), sample depth, 8 core indicators, missing critical parameters, agronomic notes. |
| Water Domain Summary | `WaterDomainSummary` | **100% Conforming** | Active sources list, discharge capacity, pH, EC, TDS, SAR/RSC calculation with status (`AVAILABLE`, `INCOMPLETE_INPUTS`, `UNAVAILABLE`), BIS IS 11624 & ICAR-CSSRI hazard classifications. |
| Satellite Domain Summary | `SatelliteDomainSummary` | **100% Conforming** | Sensor (`Sentinel-2 L2A`), Class 4 canopy NDVI & NDMI, unsegregated composite NDVI, bare soil NDVI, vegetation coverage %, raster map URLs, small-farm warning (<0.5 ha), mandatory optical disclaimer. |
| Weather Domain Summary | `WeatherDomainSummary` | **100% Conforming** | Current observed conditions, 48-hour rainfall expectation, min/max forecasted temp, 30-year climatological normals, potential water stress indicator. |
| Crop Context Domain | `CropContextDomainSummary` | **100% Conforming** | Evaluated season and taluka, evaluated crops count, categorized suitability lists, top limiting factors, pending diagnostic follow-up question count. |

---

## 3. Domain Collector Design & Freshness Rules

### 3.1. Soil Collector (`collectors/soil_collector.py`)
- **Precedence Hierarchy**:
  1. Primary: Confirmed laboratory soil test report (`SoilTestReportModel` with `review_status == "CONFIRMED"`).
  2. Fallback: SoilGrids spatial estimation layers (`SoilProfileLayerModel`).
- **Freshness Window**: 1,095 days (3 Indian agricultural years). Reports older than 1,095 days are classified as `STALE`.
- **Parameter Extraction**: Dynamic mapping for `soil_ph`, `organic_carbon`, `electrical_conductivity`, `available_nitrogen`, `available_phosphorus`, `available_potassium`, `cation_exchange_capacity`, and soil texture (from text or sand/silt/clay fractions).

### 3.2. Water Collector (`collectors/water_collector.py`)
- **Evidence Hierarchy**:
  - Registered water sources (`WaterSourceModel`) define discharge capacity and seasonal availability.
  - Confirmed laboratory water test reports (`WaterTestReportModel`) supply chemical analytes.
- **Dynamic Agronomic Calculations**:
  - Sodium Adsorption Ratio:
    $$\text{SAR} = \frac{[\text{Na}^+]}{\sqrt{\frac{[\text{Ca}^{2+}] + [\text{Mg}^{2+}]}{2}}}$$
  - Residual Sodium Carbonate:
    $$\text{RSC} = ([\text{CO}_3^{2-}] + [\text{HCO}_3^-]) - ([\text{Ca}^{2+}] + [\text{Mg}^{2+}]) \quad (\text{meq/L})$$
- **Institutional Rule Engine Integration**: Automatically runs `WaterRuleEngine` to produce BIS IS 11624:2019 salinity/sodicity hazards and ICAR-CSSRI alkalinity evaluations.
- **Freshness Window**: 365 days (1 agricultural cycle). Reports older than 365 days are marked `STALE`.

### 3.3. Satellite Collector (`collectors/satellite_collector.py`)
- **Spectral Decomposition**:
  - Uses Copernicus Sentinel-2 L2A observations (`SatelliteVegetationObservationModel`).
  - Separates pure vegetation canopy (SCL Class 4) from bare soil (SCL Class 5) to prevent dry-soil background reflectance from artificially depressing canopy vigor readings.
- **Raster Map Integration**: Serves URLs for dynamic 2D visual maps: `/api/v1/satellite/vegetation/farm/{farm_id}/ndvi-map`, `ndmi-map`, `scl-map`.
- **Freshness Windows**:
  - $\le 14$ days: `AVAILABLE`
  - $15 - 30$ days: `PARTIALLY_AVAILABLE` (cloud-delayed or between overpasses)
  - $> 30$ days: `STALE`

### 3.4. Weather Collector (`collectors/weather_collector.py`)
- **Data Stratification**:
  - Current ambient observations (`FarmWeatherSnapshotModel`, threshold: 3 hours).
  - Operational 48-hour rainfall accumulation and daily extremes (`WeatherService.get_forecast`).
  - Multi-decadal climatology (`FarmClimateSummaryModel` / NASA POWER).
- **Synthetic Data Safeguard**: If a parcel is newly registered with zero recorded snapshots in the database, fallback/simulated fixtures are strictly suppressed, and the domain returns `NOT_AVAILABLE` with explicit nulls.

### 3.5. Crop Context Collector (`collectors/crop_collector.py`)
- **Deterministic Outcome Mapping**:
  - Inspects `FarmEvaluationResponse` outcomes from Phase 5.1 decision engine.
  - Partitions candidate crops into `suitable_crops`, `conditionally_suitable_crops`, `disqualified_crops`, and `abstain_crops`.
  - Extracts Marathi localized common names (`marathi_name`) and specific irrigation guidance.
- **Freshness Window**: 180 days (single cropping season).

---

## 4. Caching & Performance Architecture

The farm health aggregation pipeline involves multiple database lookups and domain computations. To maintain sub-50ms latency for mobile clients while preserving data consistency, the service implements a layered caching strategy:

```
[Client Request: GET /farms/{farm_id}/health-snapshot]
                     |
         [force_refresh == true?]
             /                \
          (Yes)               (No)
           /                    \
          |            [In-Memory Cache Hit & Valid (<300s)?]
          |                   /                 \
          |                (Yes)                (No)
          |                 /                     \
          |        [Return Cached JSON]      [Run Aggregator]
          \_______________________________________/
                            |
                   [Compute 5 Domains]
                            |
               [Store in In-Memory Cache]
                            |
                  [Return 200 OK Response]
```

### Cache Invalidation Hooks
- Module: `services/api/app/services/farm_health/cache.py`
- Method: `invalidate_farm_health_snapshot(farm_id: str)`
- REST Endpoint: `POST /api/v1/farms/{farm_id}/health-snapshot/invalidate`
- Invocation Points: Triggered by `POST /farms/{farm_id}/soil-reports`, `POST /farms/{farm_id}/water-reports`, `POST /farms/{farm_id}/satellite/sync`, and `POST /crops/evaluate`.

---

## 5. Security & Multi-Tenant Isolation

Farm data privacy is paramount under CropNet AI architecture:
1. **Ownership Enforcement**: The endpoint invokes `_get_farm_and_verify_owner(farm_id, current_user, db)`.
2. **Access Control**:
   - Unauthorized user requesting an existing farm belonging to another user $\rightarrow$ `HTTP 403 Forbidden` (`"You do not have access to this farm"`).
   - Any user requesting a non-existent farm ID $\rightarrow$ `HTTP 404 Not Found` (`"Farm not found"`).
3. **Multi-Farm Isolation**: Two distinct farms owned by the same user maintain independent cache keys, independent data states, and zero cross-contamination.

---

## 6. Comprehensive Test Suite & Verification Results

A dedicated test suite was built in `services/api/tests/test_farm_health_snapshot.py`, containing 10 comprehensive end-to-end integration tests:

| Test Name | Verification Focus | Result |
|---|---|---|
| `test_full_evidence_snapshot` | Verifies full 5-domain complete evidence (Contract Example A), exact indicator values, BIS water rules, Sentinel-2 canopy NDVI, and `domains_available == 5`. | **PASSED** |
| `test_missing_evidence_brand_new_parcel` | Verifies brand-new parcel with 0 evidence (Contract Example B): exact nulls, zero dummy/demo numbers, `domains_not_available == 5`, actionable onboarding summary. | **PASSED** |
| `test_stale_observation_handling` | Verifies observations past freshness thresholds (Contract Example C): `domains_stale == 5`, exact `data_age_days` (1551d soil, 511d water, 57d satellite), stale warnings. | **PASSED** |
| `test_unauthorized_cross_user_access_rejected_403` | Verifies that User 2 requesting User 1's farm receives `HTTP 403 Forbidden`. | **PASSED** |
| `test_multi_farm_isolation` | Verifies two distinct farms owned by User 1 retain strictly isolated health data and independent cache entries. | **PASSED** |
| `test_nonexistent_farm_rejected_404` | Verifies requesting a random non-existent UUID returns `HTTP 404 Not Found`. | **PASSED** |
| `test_cache_hit_and_force_refresh` | Verifies in-memory cache hit returns identical timestamp within 300s, and `force_refresh=true` executes live aggregation with updated timestamp. | **PASSED** |
| `test_cache_invalidation_helpers` | Verifies `invalidate_farm_health_snapshot()` and `POST /health-snapshot/invalidate` evict cache entries. | **PASSED** |
| `test_domain_fault_isolation` | Verifies that deliberate failure in `SatelliteCollector` (throwing `RuntimeError`) gracefully degrades only satellite to `NOT_AVAILABLE` while the other 4 domains succeed. | **PASSED** |
| `test_governance_prohibition_of_universal_health_score` | Asserts that response JSON strictly prohibits universal scores (`health_score`, `overall_score`, `farm_score`, `index`, `rating`). | **PASSED** |

### Test Execution Command & Output
```bash
pytest services/api/tests/test_farm_health_snapshot.py -v
====================== 10 passed, 1056 warnings in 5.64s =======================
```

### Security Regression Check
```bash
pytest services/api/tests/test_water_satellite_security_regression.py services/api/tests/test_cors_and_security.py -v
======================= 17 passed, 176 warnings in 0.18s =======================
```

---

## 7. Deliverables & File Index

- **Schemas**: `services/api/app/schemas/farm_health.py`
- **Collectors**:
  - `services/api/app/services/farm_health/collectors/base.py`
  - `services/api/app/services/farm_health/collectors/soil_collector.py`
  - `services/api/app/services/farm_health/collectors/water_collector.py`
  - `services/api/app/services/farm_health/collectors/satellite_collector.py`
  - `services/api/app/services/farm_health/collectors/weather_collector.py`
  - `services/api/app/services/farm_health/collectors/crop_collector.py`
- **Aggregator & Cache**:
  - `services/api/app/services/farm_health/aggregator.py`
  - `services/api/app/services/farm_health/cache.py`
  - `services/api/app/services/farm_health/__init__.py`
- **Endpoints & Routing**:
  - `services/api/app/api/v1/endpoints/farm_health.py`
  - `services/api/app/api/v1/router.py` (mounted `/farms/{farm_id}/health-snapshot`)
  - `services/api/app/api/v1/api.py` (re-exports `api_router`)
- **Tests**: `services/api/tests/test_farm_health_snapshot.py`
- **Architecture Documentation**: `docs/architecture/phase5_9_unified_farm_health_backend_report.md`
