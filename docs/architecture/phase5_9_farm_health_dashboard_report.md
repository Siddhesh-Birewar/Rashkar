# Phase 5.9B Unified Farm Health Dashboard Architectural Report

**Document Status**: Final / Verified  
**Workstream**: Agent 3 (Phase 5.9B Frontend Architecture & Flutter Implementation)  
**Branch**: `workstream/agent3-dashboard`  
**Target Path**: `apps/mobile/lib/features/farm_health/` & `docs/architecture/phase5_9_farm_health_dashboard_report.md`  
**Shared Contract**: `docs/architecture/farm_health_snapshot_contract.md` (v1.0)  

---

## 1. Executive Summary & Architectural Mission

Phase 5.9B establishes the farmer-facing **Unified Farm Health Dashboard** for CropNet AI. The application aggregates multi-modal agronomic intelligence across five foundational domains:
1. **Soil Laboratory Intelligence** (pH, organic carbon, electrical conductivity, primary N-P-K nutrients, test freshness, ICAR-aligned ratings).
2. **Water Quality & Source Intelligence** (borewell/canal/well inventory, SAR, RSC, salinity classification, BIS IS 10500 / IS 11624 hazard detection).
3. **Satellite Earth Observation** (Sentinel-2 L2A BOA surface reflectance, canopy NDVI, NDMI moisture index, bare soil vs vegetation fraction, valid pixel statistics).
4. **Meteorological & Climatology Intelligence** (hyperlocal current conditions, 5-day rain/temperature outlook, 30-year IMD climatology baselines).
5. **Farm Longitudinal Observations & Agronomic Changes** (chronological event stream of tests, status transitions, and environmental snapshots).

The implementation strictly consumes the live Phase 5.9A backend snapshot contract (`GET /api/v1/farms/{farm_id}/health-snapshot`), integrates into the Flutter navigation hierarchy via GoRouter at `/farms/:farmId/health`, and adopts responsive design principles across mobile phones, tablets, and wide desktop screens.

---

## 2. Shared Contract Consumption & Data Integrity

The frontend adheres strictly to the canonical v1.0 snapshot contract agreed upon in `docs/architecture/farm_health_snapshot_contract.md`.

### 2.1 Endpoint Specification & Networking
- **Endpoint**: `GET /api/v1/farms/{farm_id}/health-snapshot`
- **Query Parameters**:
  - `force_refresh` (boolean, optional): Invalidate server cache and fetch live domain summaries.
  - `target_season` (string, optional): Target agricultural season (e.g., `KHARIF`, `RABI`, `SUMMER`).
- **Client Implementation**:
  - `ApiConstants.farmHealthSnapshot(farmId, {forceRefresh, targetSeason})` in `apps/mobile/lib/core/network/api_constants.dart`.
  - `FarmHealthRepository.getFarmHealthSnapshot(farmId, ...)` in `apps/mobile/lib/features/farm_health/data/farm_health_repository.dart`.
  - Maps HTTP 403 to `ForbiddenException` and HTTP 404 to `NotFoundException`.
  - Fully mockable via standard `ApiClient` injection.

### 2.2 Truth in UI & Strict Governance Mandate
In strict accordance with the project integrity principles and **Liebig's Law of the Minimum**:
1. **No Universal Health Score**:
   - The UI does **not** compute, synthesize, or display any single composite score (e.g., "78/100" or "Overall Grade B+").
   - Agricultural productivity is constrained by the most limiting factor (e.g., severe water salinity or nutrient deficiency), not by an average. A single composite number gives a dangerously misleading sense of safety to farmers.
2. **Zero Fake or Hardcoded Demo Data**:
   - When a domain lacks data, the dashboard does not display default zeros (0.0) or dummy mock samples.
   - Missing domains render explicit `NOT_AVAILABLE` states with actionable call-to-action buttons (e.g., "Upload Soil Report", "Register Water Source").
3. **Explicit Stale Data Banners**:
   - Stale domain records (>3 years for soil, >1 year for water, >30 days for satellite, >2 hours for weather) display prominent amber warning banners informing the farmer of data obsolescence.

---

## 3. Data Model Architecture (`farm_health_models.dart`)

All contract entities are modeled with immutable Dart classes, robust deserializers, and defensive JSON parsers under `apps/mobile/lib/features/farm_health/models/farm_health_models.dart`:

```
FarmHealthSnapshotResponse (Root)
├── contract_version, farm_id, farm_name, taluka, district, state
├── calculated_area_hectares, calculated_area_acres, snapshot_timestamp
├── OverallEvidenceOverview (counts by DataAvailabilityState, actionable_summary)
├── SoilIntelligenceSummary (pH, organic carbon, EC, NPK, data_age_days, provenance)
├── WaterIntelligenceSummary (source_count, sources[], BIS hazard alerts)
├── SatelliteVegetationSummary (canopy NDVI, NDMI, coverage %, disclaimer)
├── WeatherSummary (current, forecast, 30-year climatology normals)
└── buildTimelineItems() (chronological observation and event stream)
```

### Categorical State Mapping (`DataAvailabilityState`)
- `AVAILABLE`: Live, valid, and recent evidence is present.
- `PARTIALLY_AVAILABLE`: Baseline data exists but requires secondary parameters or confirmation.
- `NOT_AVAILABLE`: No records exist for this farm parcel.
- `STALE`: Records exist but exceed agronomic validity thresholds.
- `INSUFFICIENT_EVIDENCE`: Registered data fails scientific precision standards (e.g., cloudy satellite scenes or parcel < 0.2 ha).

---

## 4. Section Widget Architecture & Visual Layouts

The dashboard is structured into 8 modular, independent section widgets located in `apps/mobile/lib/features/farm_health/presentation/widgets/`:

| Section | Widget Class | Key Responsibilities & Elements |
|---|---|---|
| **1. Farm Overview** | `FarmOverviewCard` | Gradient banner, farm name, taluka/district/state location, area in ha & acres, snapshot assembly timestamp, contract version badge, interactive refresh button with loading spinner. |
| **2. Overall Evidence Status Board** | `OverallEvidenceCard` | Grid of availability chips (`AVAILABLE`, `PARTIALLY_AVAILABLE`, `NOT_AVAILABLE`, `STALE`, `INSUFFICIENT_EVIDENCE`), domain status pills across all 5 domains, actionable synthesis narrative explaining what is missing. |
| **3. Soil Intelligence** | `SoilIntelligenceCard` | Diagnostic badges for pH, Organic Carbon, Electrical Conductivity, and Primary N-P-K nutrient availability. Laboratory provenance badge, test freshness chip, stale warnings, and missing test empty state with link to `/soil-testing`. |
| **4. Water Intelligence** | `WaterIntelligenceCard` | Total water sources count, source types breakdown, salinity classification (Class 1 to 4 with EC values), SAR & RSC metrics, BIS IS 10500 / IS 11624 hazard callouts, and empty state with deep link to `/farms/:farmId/water`. |
| **5. Satellite Vegetation** | `SatelliteVegetationCard` | Sentinel-2 L2A canopy NDVI gauge (0.0 to 1.0 color-coded), NDMI moisture index, bare soil vs vegetation coverage breakdown bar, valid pixel count, small-farm precision notice (<0.5 ha), mandatory scientific disclaimer, and link to `/farms/:farmId/vegetation`. |
| **6. Weather & Climate** | `WeatherSummaryCard` | Hyperlocal current temperature, condition icon, humidity %, precipitation, wind speed. 5-day precipitation and temperature forecast outlook. 30-year IMD climatology normals (annual and monsoon rainfall). Deep link to weather workspace. |
| **7. Observations Timeline** | `FarmTimelineCard` | Vertical timeline with connected indicator dots and domain-colored icons. Displays tests logged, status transitions, and environmental synchronizations in reverse chronological order with source attribution. |
| **8. AI Assistant Entry Points** | `AiEntryPointsCard` | Pre-engineered contextual prompt chips (e.g., "Analyze soil test results & NPK deficiencies", "Check water salinity suitability for current crop", "Explain recent NDVI vegetation change"). Automatically selects farm context and navigates to `/advisory`. |

---

## 5. Responsive Layout Architecture

The screen implementation (`FarmHealthDashboardScreen`) adheres to the application's responsive foundation via `ResponsiveScaffold`, `CenteredPageContainer`, and `AppBreakpoints`:

### 5.1 Mobile Layout (`width < 600px`)
- **Structure**: Single-column vertical stack.
- **Hierarchy**:
  1. Farm Overview Card
  2. Overall Evidence Status Board
  3. AI Assistant Entry Points
  4. Soil Intelligence Summary
  5. Water Intelligence Summary
  6. Satellite Vegetation Summary
  7. Weather & Climate Summary
  8. Farm Observations Timeline
  9. Workspace Quick Navigation Shortcuts

### 5.2 Tablet Layout (`600px <= width <= 1024px`)
- **Structure**: 2-Column Responsive Grid (`Row` with two `Expanded` columns).
- **Column 1 (Left, 50%)**: Farm Overview, Overall Evidence Status Board, Soil Intelligence, Water Intelligence.
- **Column 2 (Right, 50%)**: AI Assistant Entry Points, Satellite Earth Observation, Weather & Climate, Observations Timeline, Workspace Shortcuts.

### 5.3 Desktop Layout (`width > 1024px`)
- **Structure**: 3-Column Responsive Grid (`Row` with `Expanded(flex: 4)`, `Expanded(flex: 4)`, `Expanded(flex: 3)`).
- **Column 1 (Primary Agronomy, 36.3%)**: Farm Overview, Soil Intelligence, Water Intelligence.
- **Column 2 (Remote Sensing & Atmosphere, 36.3%)**: Overall Evidence Board, Satellite Earth Observation, Weather & Climate.
- **Column 3 (Advisory & Timeline, 27.4%)**: AI Assistant Entry Points, Observations Timeline, Workspace Navigation Shortcuts.
- **Max Width**: Centered within `AppBreakpoints.maxContentWidthWide` (1440px) to prevent unnatural stretching on ultra-wide monitors.

---

## 6. Navigation Mounting & Deep Links

### 6.1 Route Registration
The route is mounted in `apps/mobile/lib/core/router/app_router.dart`:
```dart
GoRoute(
  path: 'health',
  name: RouteNames.farmHealthDashboard,
  parentNavigatorKey: rootNavigatorKey,
  builder: (context, state) {
    final farmId = state.pathParameters['farmId'] ?? '';
    return FarmRouteResolver(
      farmId: farmId,
      featureName: 'Farm Health Dashboard',
      builder: (context, farm) => FarmHealthDashboardScreen(
        farmId: farm.id,
        farm: farm,
      ),
    );
  },
),
```

### 6.2 Entry Points
- **From Farm Detail Screen (`FarmDetailScreen`)**: Prominent green primary button with heart-pulse icon: `"View Unified Farm Health Dashboard"`.
- **From Farm Cards**: Direct navigation to `/farms/:farmId/health`.
- **Workspace Outbound Links**:
  - Soil Testing: `/farms/:farmId/soil` and `/soil-testing`
  - Water Quality: `/farms/:farmId/water`
  - Satellite Vegetation: `/farms/:farmId/vegetation`
  - Weather Forecast: `/farms/:farmId/weather`
  - Crop Recommendations: `/crop-recommendation`
  - AI Advisory: `/advisory` (with `FarmRepository.instance.selectedFarmId` pre-selected)

---

## 7. Verification & Quality Assurance Results

### 7.1 Static Analysis (`dart analyze`)
Command executed:
```bash
cd apps/mobile && dart analyze
```
**Result**:
```
Analyzing mobile...
No issues found!
```
- **0 errors**, **0 warnings**, **0 lints** across all 12 implementation and test files.

### 7.2 Automated Test Suite (`flutter test test/features/farm_health/`)
Command executed:
```bash
cd apps/mobile && flutter test test/features/farm_health/
```
**Result**:
```
00:01 +13: All tests passed!
```

#### Detailed Test Inventory:
1. `DataAvailabilityState enum parses canonical state strings correctly` — **PASS**
2. `DataAvailabilityState enum serializes back to canonical API strings` — **PASS**
3. `Example A: Full Evidence Farm parses completely with all 5 domains` — **PASS**
4. `Example B: Empty Evidence Farm (New Parcel) safely handles nulls without default numbers` — **PASS**
5. `Example C: Stale Evidence Farm marks STALE status and reports ages` — **PASS**
6. `FarmHealthRepository fetches health snapshot successfully on HTTP 200` — **PASS**
7. `FarmHealthRepository propagates force_refresh and target_season query parameters` — **PASS**
8. `FarmHealthRepository throws ForbiddenException on HTTP 403 unauthorized access` — **PASS**
9. `FarmHealthRepository throws NotFoundException on HTTP 404 missing farm` — **PASS**
10. `Renders all 8 required sections with live full evidence data` — **PASS**
11. `Missing evidence parcel renders clean NOT_AVAILABLE empty states without fake numbers` — **PASS**
12. `Stale evidence parcel displays warning banners` — **PASS**
13. `Responsive layouts adapt across Mobile, Tablet, and Desktop` (tested with dynamic viewport resizing) — **PASS**

---

## 8. Summary of Completed File Artifacts

| File Path | Description |
|---|---|
| `apps/mobile/lib/core/network/api_constants.dart` | Added `farmHealthSnapshot(farmId, ...)` route helper |
| `apps/mobile/lib/core/router/route_paths.dart` | Added `farmHealthDashboardPath(farmId)` |
| `apps/mobile/lib/core/router/route_names.dart` | Added `RouteNames.farmHealthDashboard` |
| `apps/mobile/lib/core/router/app_router.dart` | Mounted subroute `/farms/:farmId/health` under `FarmRouteResolver` |
| `apps/mobile/lib/main.dart` | Added primary entry button on `FarmDetailScreen` |
| `apps/mobile/lib/features/farm_health/models/farm_health_models.dart` | Complete domain data models and state enums |
| `apps/mobile/lib/features/farm_health/data/farm_health_repository.dart` | Repository with HTTP client error handling and refresh params |
| `apps/mobile/lib/features/farm_health/presentation/screens/farm_health_dashboard_screen.dart` | Main dashboard with Mobile/Tablet/Desktop responsive grids |
| `apps/mobile/lib/features/farm_health/presentation/widgets/farm_overview_card.dart` | Section 1: Overview, farm metadata, area, refresh |
| `apps/mobile/lib/features/farm_health/presentation/widgets/overall_evidence_card.dart` | Section 2: 5-state categorical board & actionable summary |
| `apps/mobile/lib/features/farm_health/presentation/widgets/soil_intelligence_card.dart` | Section 3: pH, OC, EC, NPK, lab provenance, age |
| `apps/mobile/lib/features/farm_health/presentation/widgets/water_intelligence_card.dart` | Section 4: Sources, SAR, RSC, EC, BIS hazards |
| `apps/mobile/lib/features/farm_health/presentation/widgets/satellite_vegetation_card.dart` | Section 5: NDVI gauge, NDMI, soil fraction, disclaimer |
| `apps/mobile/lib/features/farm_health/presentation/widgets/weather_summary_card.dart` | Section 6: Current conditions, 5-day forecast, 30-yr climatology |
| `apps/mobile/lib/features/farm_health/presentation/widgets/farm_timeline_card.dart` | Section 7: Longitudinal event and observation stream |
| `apps/mobile/lib/features/farm_health/presentation/widgets/ai_entry_points_card.dart` | Section 8: Contextual prompt chips deep-linking to advisory |
| `apps/mobile/test/features/farm_health/farm_health_models_and_repository_test.dart` | Unit test suite for models and repository |
| `apps/mobile/test/features/farm_health/farm_health_dashboard_widget_test.dart` | Widget test suite for sections, governance, empty states, and responsive layouts |
| `docs/architecture/phase5_9_farm_health_dashboard_report.md` | This architectural report |
