# CropNet AI — Antigravity Development Roadmap

**Project:** CropNet AI  
**Features in scope:** 1) Location-Based Soil Intelligence, 2) Optimal Crop Selection  
**Initial geography:** Maval, Mulshi, Baramati and Indapur, Pune district, Maharashtra, India  
**Starting point:** Greenfield — no application codebase exists yet  
**Frontend to create:** Flutter mobile application (Android-first)  
**Backend to create:** Python + FastAPI  
**Database to create:** PostgreSQL + PostGIS  
**Purpose:** A sequential, execution-focused roadmap for creating the project foundation and implementing both features from scratch.

---

## 0. How Antigravity must use this roadmap

This document is the implementation sequence. The companion document **`CropNet_Two_Feature_Greenfield_Implementation_Specification.md`** is the detailed product, data, API, GIS, model, UI and acceptance specification. Antigravity must read both before creating the project.

**Greenfield instruction:** There is no existing CropNet repository, Flutter app, FastAPI backend, database, authentication flow or UI to preserve. Create the project structure and foundational services from zero. Do not waste time searching for existing feature code or claim to have reused components that do not exist.

### Required working method

1. Work phase by phase. Do not attempt to implement both complete features in one large change.
2. Begin by creating a clean project foundation. Confirm the toolchain and versions, establish the monorepo structure, scaffold Flutter and FastAPI, provision the database, and document architecture decisions before feature implementation.
3. Before each phase, list the files/modules that will be created or changed and explain why.
4. Implement only the current phase. Since the project is greenfield, create only the modules required by the approved architecture; avoid premature abstractions and unrelated features.
5. After each phase, run the relevant tests, linters, type checks and application builds. Report exact commands and results.
6. Do not mark a phase complete if its acceptance criteria are not met. Record blockers, missing credentials, unavailable data or unverified assumptions explicitly.
7. Keep the application runnable after each phase. Use feature flags or clearly isolated incomplete integrations where needed.
8. Keep secrets on the backend. Never put data-provider API keys or privileged credentials in Flutter.
9. Use versioned database migrations from the first schema change. Keep local, staging and production environments separate; never commit secrets or real farmer data.
10. Do not generate fake production soil values, market prices, farm records, model outputs or recommendations. Test fixtures must be isolated and visibly labelled as test data.

### Scope decisions that must not change silently

- The first release uses GPS/manual farm selection, farm polygons and existing approved geospatial soil datasets.
- Physical soil testing, jar tests, chemical strips, camera-based NPK estimation and laboratory workflows are **not** part of the initial implementation.
- The feature must be named **Location-Based Soil Profile** or **Soil Intelligence**, not a laboratory soil test.
- Every soil parameter must retain its own source and provenance.
- Missing soil values remain `null`/unavailable. Never substitute zero, a regional average, a neighbouring farm's value or a guessed number.
- NPK must not be invented to satisfy an existing crop model. The crop recommender must support a map-based mode that works without available NPK.
- Agronomic suitability and economic attractiveness are separate stages.
- Yield prediction is optional and must remain disabled until suitable data and validation exist.
- The first model should be a transparent, source-backed agronomic rules baseline. ML is a challenger, not an automatic replacement.
- No source integration is considered complete until its access method, layer coverage, licence, attribution, freshness and commercial-use permissions are checked.

---

# 1. Overall build sequence

The two features share a single critical dependency: a trustworthy, versioned soil profile for each farm. Build that contract first, then connect crop selection to it.

```text
GREENFIELD PROJECT FOUNDATION
(Flutter + FastAPI + PostgreSQL/PostGIS)
        |
        v
GIS DATA SOURCE / COVERAGE / LICENCE AUDIT
        |
        v
FARM REGISTRATION + MAP + POLYGON STORAGE
        |
        v
GIS PROVIDER ADAPTERS + SPATIAL EXTRACTION
        |
        v
VERSIONED SOIL PROFILE + SOIL DASHBOARD
        |
        +-----------------------------------+
        |                                   |
        v                                   v
CROP KNOWLEDGE CATALOGUE              WEATHER / SEASON INPUTS
        |                                   |
        +----------------+------------------+
                         |
                         v
             AGRONOMIC RULES ENGINE
                         |
                         v
                CROP SHORTLIST
                         |
                         v
             OPTIONAL MARKET RANKING
                         |
                         v
              EXPLAINABLE RESULTS
                         |
                         v
              TEST / OFFLINE / PILOT
```

## Suggested release gates

| Release gate | What must be working | Do not proceed until |
|---|---|---|
| Gate 0 | Greenfield foundation runs and geospatial data feasibility is understood | Flutter, FastAPI and PostGIS run locally; data access blockers are documented |
| Gate 1 | Farmer can create and save a farm polygon | Geometry, authorization and area tests pass |
| Gate 2 | At least one approved soil source can be queried for a pilot location | Real source data can be extracted with provenance |
| Gate 3 | Soil profile is generated and displayed honestly | Missing data and source metadata work correctly |
| Gate 4 | Crop recommendations work from the soil profile without NPK | Rules and crop requirements have traceable sources |
| Gate 5 | Weather and market data improve results where available | Freshness, units, location and provider terms are handled |
| Gate 6 | ML model has been independently evaluated, or is deliberately not shipped | Spatial/temporal validation supports deployment |
| Gate 7 | Pilot-ready app supports low connectivity and local-language UI | End-to-end acceptance tests pass |

---

# 2. Phase 0 — Greenfield project foundation and GIS feasibility

**Priority:** Critical
**Implementation mode:** Create the minimum working project foundation, then verify GIS data feasibility.

There is no existing codebase. Antigravity must create the project from scratch rather than perform a repository audit.

## Tasks

### 0.1 Create the repository and project structure

Create a clean monorepo with clear boundaries between mobile, API, infrastructure and documentation. Recommended starting structure:

```text
cropnet/
  apps/
    mobile/                 # Flutter Android-first app
  services/
    api/                    # FastAPI backend
  infra/
    docker-compose.yml      # Local PostgreSQL/PostGIS and supporting services
    db/                     # SQL/bootstrap and migration configuration
  docs/
    architecture/
    data-sources/
    api/
  scripts/
  .env.example
  .gitignore
  README.md
```

Keep large or licensed geospatial datasets out of Git. Store only source metadata, access instructions, checksums and permitted small test fixtures in the repository.

### 0.2 Establish the technology baseline

Use these as the default implementation choices unless a documented compatibility blocker is found:

| Layer | Greenfield default | Notes |
|---|---|---|
| Mobile | Flutter, Dart | Android-first; responsive layouts |
| State management | Riverpod | Use one consistent pattern |
| Navigation | GoRouter | Central route definitions |
| Maps | `flutter_map` behind a map abstraction | Configure an approved tile provider; do not assume public OSM raster tiles are suitable for production |
| Backend | Python + FastAPI | Versioned REST API under `/api/v1` |
| Validation | Pydantic | Request/response schemas |
| Database | PostgreSQL + PostGIS | Spatial geometry and queries |
| ORM/migrations | SQLAlchemy 2 + Alembic | Versioned schema changes |
| GIS | GeoPandas, Shapely, Rasterio, pyproj | Install system geospatial dependencies deliberately |
| Authentication | Supabase Auth for MVP, unless the project chooses another managed identity provider before implementation | JWT verified by FastAPI; never trust client-supplied user IDs |
| File storage | Supabase Storage or equivalent private object storage | Only if/when farmer uploads are introduced |
| Testing | pytest; Flutter test/integration_test | Add tests from the first phase |

If Supabase is selected, use a restricted database connection and Row Level Security as an additional protection. The FastAPI backend remains responsible for business logic and authorization. Never place a Supabase service-role key in Flutter. If PostGIS or a required GIS extension is unavailable on the chosen plan, document the blocker and select a compatible PostgreSQL deployment before proceeding.

### 0.3 Scaffold and run the empty application

Create:
- Flutter application with environment-based API configuration, app theme, localization foundation, routing and a basic home/navigation shell.
- FastAPI application with health endpoint, configuration, structured logging, CORS allowlist, request IDs and `/api/v1` router structure.
- PostgreSQL/PostGIS local development configuration and Alembic migration setup.
- Environment variable templates and secret-handling instructions.
- CI workflow for formatting, linting, unit tests and build checks.
- README with exact setup, run, test and migration commands.

Do not build unrelated CropNet modules. The initial navigation should expose only the farm/soil and crop-selection journeys plus the minimum settings/profile/auth screens needed for the two features.

### 0.4 Establish authentication and ownership model

Create the initial sign-up/sign-in integration and authenticated API dependency. The backend must derive the user identity from a validated token. Every farm and recommendation resource must be scoped to its owner. Add tests proving one user cannot read or modify another user's farms.

If the product team is not ready to configure a real identity provider, use a local-only development auth mode that is impossible to enable in production. Do not ship a fake production login.

### 0.5 Verify geospatial feasibility and data permissions

Investigate candidate datasets and services, beginning with:
- ICAR-NBSS&LUP BHOOMI Geoportal: https://bhoomigeoportal-nbsslup.in/
- ICAR-NBSS&LUP: https://icar-nbsslup.org.in/
- Maharashtra PoCRA GIS: https://gis.mahapocra.gov.in/
- Soil Health Card portal: https://soilhealth.dac.gov.in/
- ISRO Bhuvan: https://bhuvan.nrsc.gov.in/
- ISRIC SoilGrids: https://soilgrids.org/
- Government/SLUSI soil-fertility mapping information.

For each usable data layer, verify:
- Actual layer name and parameter.
- Coverage in Maval, Mulshi, Baramati and Indapur.
- Raster/vector/service-only format.
- Official endpoint or download route.
- CRS/EPSG and spatial extent.
- Raster resolution or map scale.
- Soil depth interval.
- Data year/publication/update date.
- Units, class legend and NoData convention.
- Source methodology and uncertainty, if available.
- Attribution requirements, licence and commercial-use permission.
- Authentication, rate limits, terms and cache/redistribution rules.

A public map viewer or WMS display is not enough to prove numerical extraction is possible. Prefer approved WFS/OGC API Features, WCS, GeoTIFF/COG, GeoPackage or documented feature-info services where available. Do not scrape screenshots or reverse-engineer private endpoints.

### 0.6 Produce a pilot coverage matrix

Populate the matrix from actual source inspection. Do not fill it with assumptions.

| Pilot area | Soil group | Texture | Depth | pH | EC | Organic carbon | Available N | Available P | Available K | Water capacity |
|---|---|---|---|---|---|---|---|---|---|---|
| Maval | Verify | Verify | Verify | Verify | Verify | Verify | Verify | Verify | Verify | Verify |
| Mulshi | Verify | Verify | Verify | Verify | Verify | Verify | Verify | Verify | Verify | Verify |
| Baramati | Verify | Verify | Verify | Verify | Verify | Verify | Verify | Verify | Verify | Verify |
| Indapur | Verify | Verify | Verify | Verify | Verify | Verify | Verify | Verify | Verify | Verify |

For each cell, record the actual source, layer, date, scale/resolution, depth and access status in a separate source catalogue.

### 0.7 Produce an architecture and implementation decision record

Document the confirmed folder structure, dependency versions, database/auth choices, map-provider abstraction, environment configuration, source-access findings and known blockers. Do not silently substitute a different stack.

## Deliverables

- New Git repository and greenfield monorepo structure.
- Runnable Flutter starter application.
- Runnable FastAPI starter application.
- Local PostgreSQL/PostGIS configuration and first migration baseline.
- Authentication/authorization foundation or a clearly documented blocked configuration.
- `.env.example`, `.gitignore`, README and CI checks.
- GIS source/layer catalogue and pilot-area coverage matrix.
- Source-access/licensing risk register.
- Architecture decision record and phase implementation plan.
- At least one repeatable test proving an approved source can be accessed and attributes extracted, or a clearly documented blocker and fallback plan.

## Exit criteria

- A new developer can clone the repository, configure environment variables and run Flutter, FastAPI and the database using the README.
- Health check succeeds and Flutter can reach the local API.
- Database migrations run cleanly.
- Authentication/ownership plan is established.
- GIS data feasibility and access rights are transparent.
- No fabricated integration or soil data is presented as real.

### Antigravity prompt — Phase 0

> Read `CropNet_Two_Feature_Greenfield_Implementation_Specification.md` and `CropNet_Antigravity_Greenfield_Development_Roadmap.md` completely. This is a GREENFIELD project: no codebase exists. Create the repository structure and the minimum runnable foundations from scratch using the documented Flutter + FastAPI + PostgreSQL/PostGIS architecture. Set up environment configuration, migrations, basic auth/authorization approach, logging, health endpoint, Flutter app shell, API connectivity, tests and README. In parallel, investigate real GIS access, coverage and permissions for BHOOMI, PoCRA, SLUSI/Soil Health Card-derived maps, Bhuvan and SoilGrids for Maval, Mulshi, Baramati and Indapur. Do not assume an API exists because a website or map viewer exists. Do not build either feature's full business logic in this phase. Produce all Phase 0 deliverables and stop for review before Phase 1. Clearly distinguish verified facts, assumptions and blockers.

---

# 3. Phase 1 — Data contracts, database design and farm mapping

**Priority:** Critical  
**Feature ownership:** Shared foundation for both features.

## Tasks

### 1.1 Define shared data contracts

Before building UI and GIS integrations, agree on canonical schemas for:
- Farm.
- Farm polygon and geometry metadata.
- Soil data source.
- Soil map layer.
- Soil profile snapshot.
- Individual soil parameter observation.
- Crop catalogue entry and requirement reference.
- Recommendation run and recommendation result.
- Weather/market observation.

Every soil parameter must be independently traceable. Store the raw source value and unit as well as a normalized value/unit only when a valid conversion exists.

### 1.2 Database work

Create the initial database schema using PostgreSQL + PostGIS as the default. If the selected hosting/database environment cannot support PostGIS, document and approve an alternative before building spatial functionality. Plan migrations for structures equivalent to:

| Entity/table | Main purpose |
|---|---|
| `farms` | Farm metadata, owner, boundary and area |
| `soil_data_sources` | Provider, terms, attribution and access metadata |
| `soil_map_layers` | Layer identifier, property, coverage, CRS, scale/resolution, depth, vintage |
| `farm_soil_profiles` | Versioned soil profile snapshots for a farm |
| `soil_parameters` | One observation/status/provenance record per parameter/profile |
| `farm_soil_zone_intersections` | Multiple mapped zones and area fractions inside a farm |
| `crop_catalogue` / related tables | Crop, season, soil/climate requirements and references |
| `crop_recommendation_runs` | Inputs and version for a recommendation run |
| `crop_recommendation_results` | Ranked results, reasons, limits and economics |

Use the detailed schema in the companion specification as the starting point. Establish consistent naming, UUID IDs, timestamps, foreign keys, indexes, constraints and migration conventions for the new project.

### 1.3 Build farm APIs

Implement or extend endpoints for:
- Create farm.
- List the authenticated user's farms.
- Get a farm.
- Update farm details/boundary.
- Archive/delete according to existing product policy.

Requirements:
- Validate GeoJSON/polygon geometry.
- Validate coordinate order and CRS.
- Detect invalid/self-intersecting polygons.
- Calculate area using an appropriate projected/geodesic method; never calculate area directly in latitude/longitude degrees.
- Store geometry in canonical CRS and preserve CRS metadata.
- Enforce user ownership/authorization at every endpoint.
- Support multiple farms for one user.

### 1.4 Build Flutter farm mapping experience

Implement:
- Add farm screen.
- Search/manual location selection.
- Optional GPS centring with permission explanation and denial fallback.
- Polygon drawing, close/save, undo, reset and edit.
- Area display with unit choice.
- Farm name and administrative details confirmation.
- Farm list and farm detail screen.
- Clear indication that a selected polygon is user-drawn and not a legal cadastral record.

Create the initial CropNet navigation and visual language. Use the product brief's farmer-friendly, high-contrast, outdoor-readable design direction; do not invent unrelated application modules.

## Deliverables

- Reviewed shared data contracts.
- Database migrations.
- Farm CRUD APIs and authorization.
- Flutter farm mapping flow.
- Unit and integration tests for geometry and farm ownership.

## Exit criteria

A logged-in farmer can create, save, reopen and edit more than one farm polygon. Invalid geometry is handled safely. Another user cannot read or modify that farm.

### Antigravity prompt — Phase 1

> Implement Phase 1 only: shared data contracts, first production-schema migrations and farm mapping. Build on the greenfield Flutter/FastAPI/PostgreSQL/PostGIS foundation created in Phase 0. Implement secure farm CRUD APIs and the Flutter flow for GPS/manual map selection and polygon drawing/editing. Validate geometry, calculate area correctly, support multiple farms and enforce user ownership. Do not integrate soil map providers yet. Do not implement crop recommendations yet. Add tests and run the app. At the end, report every changed file, migration, API route, test command and test result. Do not proceed to Phase 2 until the farm mapping acceptance criteria pass.

---

# 4. Phase 2 — GIS provider adapters and spatial extraction

**Priority:** Critical  
**Feature ownership:** Location-Based Soil Intelligence.

## Tasks

### 2.1 Build provider abstraction

Create a common provider interface so the soil engine is independent of a specific data source. A provider should support, as appropriate:
- List/describe available layers.
- Check layer coverage for a geometry or location.
- Retrieve source metadata.
- Extract raster/vector attributes for a farm geometry.
- Return source errors and missing-data reasons in a consistent format.

Implement adapters only for data sources with a verified, permitted data access route. Keep unavailable sources marked as planned/pending, not as working integrations.

### 2.2 Build and maintain the layer catalogue

Each layer record should contain:
- Provider and dataset name/identifier.
- Parameter represented.
- Raster/vector/service type and data format.
- Endpoint or storage reference (backend-side only).
- CRS, extent, scale/resolution, depth interval.
- Year/date, units, class legend and NoData value.
- Methodology/uncertainty where documented.
- Attribution, licence and commercial-use status.
- Rate limits, access credentials requirement and active status.
- Last successful validation/check date.

### 2.3 Implement vector extraction

For vector datasets:
- Query features intersecting the farm polygon.
- Reproject safely when necessary.
- Calculate intersection area and percentage of farm coverage.
- Preserve multiple mapped zones.
- Return a dominant category only when the chosen, documented coverage rule is met; otherwise return a mixed/heterogeneous result.

### 2.4 Implement raster extraction

For raster datasets:
- Mask/clip by the farm polygon.
- Respect CRS and pixel alignment.
- Exclude NoData values.
- Calculate valid spatial coverage.
- Calculate meaningful statistics for continuous variables (mean/median/distribution as appropriate).
- Calculate class-area fractions for categorical rasters; never average category codes.
- Preserve raster resolution and the original map unit.
- Warn when a farm is smaller than or comparable to a raster cell.

A spatial intersection does not increase map resolution. Multiple farms in one coarse raster cell may receive the same estimate; label it accordingly.

### 2.5 Parameter semantics and normalization

Use canonical parameter keys such as:
- `soil_group`, `soil_series`, `texture_class`
- `sand_percent`, `silt_percent`, `clay_percent`
- `soil_depth`, `slope`, `erosion_class`, `drainage_class`
- `ph`, `electrical_conductivity`, `organic_carbon`
- `available_nitrogen`, `available_phosphorus`, `available_potassium`
- `sulphur`, `zinc`, `iron`, `copper`, `manganese`, `boron`
- `available_water_capacity`

Maintain strict scientific distinctions:
- Total nitrogen is not available nitrogen.
- Texture class is not soil taxonomic classification.
- Map-derived pH is not a current exact-field lab reading.
- A map-derived value must not be labelled laboratory-measured.
- Unknown unit/method means do not normalize or compare as if known.

### 2.6 Failure and fallback behaviour

- Provider timeout: return provider unavailable; do not crash the entire workflow.
- No coverage: return parameter unavailable with reason.
- Partial coverage: return actual coverage fraction and partial status.
- Stale data: retain source date and apply configured freshness label; do not quietly call it current.
- Licence/access failure: disable the provider and log an operational error; do not bypass restrictions.
- One provider's outage must not erase a profile from other valid sources.

## Deliverables

- Provider interface and approved adapters.
- Source/layer catalogue.
- Vector/raster spatial extraction services.
- Unit and parameter normalization service.
- GIS tests using approved sample data.
- Actual extraction evidence for at least one pilot location and each supported parameter.

## Exit criteria

At least one real, permitted soil dataset is extracted repeatably for a pilot farm polygon. The backend can return partial coverage, mixed zones and unavailable parameters correctly. Provenance is attached to every result.

### Antigravity prompt — Phase 2

> Implement Phase 2 only: GIS provider abstraction, verified provider adapter(s), layer registry and spatial extraction. Use only endpoints/downloads whose access method and terms were verified in Phase 0. Implement vector intersection and raster zonal statistics as appropriate. Preserve multiple zones, valid coverage, units, layer scale/resolution, depth, vintage and provenance. Never extract numeric soil values from screenshots. Never fabricate missing NPK or other attributes. Add provider timeout/no-data/partial-coverage/stale-data handling and tests. Demonstrate extraction against a real approved pilot-area dataset. If a source is inaccessible or permissions are unclear, leave its adapter disabled and document the blocker rather than simulating success.

---

# 5. Phase 3 — Soil profile service and Flutter dashboard

**Priority:** Critical  
**Feature ownership:** Location-Based Soil Intelligence.

## Tasks

### 3.1 Generate versioned soil profiles

For a selected farm:
1. Load and validate the saved farm polygon.
2. Select applicable active layers from the layer catalogue.
3. Request extraction from approved providers.
4. Normalize only values with known units/semantics.
5. Record values, metadata, coverage and missing reasons parameter by parameter.
6. Calculate overall data completeness from a transparent count/coverage method; do not call it model confidence.
7. Save a versioned snapshot with generation time and source versions.
8. Return the snapshot to Flutter.

### 3.2 Parameter status model

Use explicit statuses such as:
- `available`
- `partial_coverage`
- `not_available`
- `source_unavailable`
- `stale`
- `invalid_source_value`
- `awaiting_source_access`

Do not encode unavailable values as zero.

### 3.3 Soil APIs

Implement or extend endpoints for:
- Generate/refresh soil profile for a farm.
- Get latest soil profile.
- List profile history.
- Get details/source metadata for an individual parameter.
- Get mapped soil zones intersecting a farm.

Use authenticated ownership checks. Add idempotency/background-task handling if GIS extraction is too slow for a synchronous request. Provide a job status endpoint if processing is asynchronous.

### 3.4 Flutter soil experience

Build screens/states for:
- Soil Intelligence landing/intro.
- Farm selection.
- Map selection and boundary drawing (reuse Phase 1).
- Generate/loading state.
- Soil profile dashboard.
- Parameter details/provenance.
- Mixed mapped soil zones.
- No coverage/partial coverage/provider unavailable.
- Stale profile and refresh.
- Cached profile while offline.

For each parameter show, where available:
- Name, value and unit.
- Status.
- Data source and layer.
- Data year/date.
- Map scale or raster resolution.
- Soil depth interval.
- Farm coverage percentage.
- Explanation of what the property means.
- Explicit statement that the value is map-derived, not a physical/laboratory measurement.

Do not use green “healthy” indicators unless there is a validated parameter-specific interpretation with an authoritative threshold and proper context.

## Deliverables

- Soil profile generation service.
- Versioned database records.
- Soil APIs.
- Flutter dashboard and parameter detail views.
- Clear loading, partial, unavailable, stale, offline and error states.
- End-to-end tests from farm polygon to profile display.

## Exit criteria

A farmer can select a saved farm, generate and view its mapped soil profile, inspect the source behind each value, understand missing data, and see a clear map-derived/not-lab-tested disclaimer.

### Antigravity prompt — Phase 3

> Implement Phase 3 only: the versioned Soil Profile service, APIs and Flutter dashboard. Consume only the real extraction results from Phase 2. Make each parameter independently traceable to its source, data date, depth, scale/resolution, coverage and unit. Support all missing/partial/stale/provider-error states. Never display null as zero and never invent a confidence score. Show that outputs are map-derived and not laboratory verified. Persist profile snapshots and allow the farmer to view profile history. Add end-to-end tests and verify the complete farm-to-soil-report journey.

---

# 6. Phase 4 — Crop knowledge catalogue and transparent agronomic engine

**Priority:** Critical for Feature Two  
**Feature ownership:** Optimal Crop Selection.

## Tasks

### 4.1 Build crop catalogue before ML

Create structured, versioned crop reference data for the Maharashtra pilot. Initial candidate crops to investigate include:
- Soybean.
- Cotton.
- Sugarcane.
- Pomegranate.
- Tur/pigeon pea.
- Groundnut.
- Maize.
- Sorghum/jowar.
- Chickpea/gram.
- Onion and other locally relevant crops only where good references exist.

This is a candidate research list, not a claim that all these crops fit every taluka or season.

For each crop, record:
- Crop identity and variety/production-system if relevant.
- Suitable seasons and sowing windows.
- Soil group/texture preference.
- pH range where a reliable reference gives it.
- Soil depth and drainage requirements.
- Water/irrigation requirement.
- Rainfall and temperature needs.
- Crop duration.
- District/agro-climatic relevance.
- Important constraints and risks.
- Reference organisation, document, URL, publication/revision date and relevant page/section.

Use authoritative sources such as ICAR, Maharashtra agricultural universities, KVK and official agricultural guidance. Each threshold/rule must have a traceable source. If there is no trustworthy reference, leave the requirement unknown rather than inventing a threshold.

### 4.2 Define recommendation modes

**Mode A — Regional/map-based suitability:** works without available NPK. Uses available soil group, texture, depth, pH, organic carbon, water capacity, location, season, climate and farmer-supplied irrigation details.

**Mode B — Nutrient-informed suitability:** may use mapped nutrient information only when the parameter's meaning, unit, depth, source, date and coverage are adequate. It is still map-derived unless it is an actual laboratory report for the farm.

The engine must choose a mode and report which inputs were used and which were unavailable.

### 4.3 Implement multi-stage recommendation pipeline

**Stage 0 — Input readiness**
- Fetch the latest eligible soil profile.
- Confirm farm/location and season.
- Retrieve weather/climate information if available.
- Identify missing, stale and low-resolution inputs.
- Select Mode A or Mode B explicitly.

**Stage 1 — Candidate generation**
- Retrieve crops relevant to the selected district/zone and season from the crop catalogue.
- Do not recommend crops that have no configured agronomic reference for the relevant context unless explicitly marked exploratory.

**Stage 2 — Feasibility filtering**
- Check sowing season/window.
- Check critical water/irrigation constraints.
- Check soil depth/drainage constraints.
- Check severe documented climate incompatibilities.
- Hard-exclude only where a defensible source-backed rule exists; otherwise flag a limitation or apply a documented penalty.

**Stage 3 — Agronomic suitability scoring**
- Score available soil match, climate match, season match, water match and regional match.
- Normalize each factor consistently.
- Use configurable weights that are documented and validated; do not present arbitrary weights as scientific truth.
- Do not convert missing inputs to zero.
- Define a documented missing-data policy, including whether weights are renormalized and when the result must be withheld.
- Return reason codes and factor-level explanations.

**Stage 4 — Shortlist**
Return a concise set of suitable/possible crops and alternatives, not a single guaranteed “best crop”. Each result includes supporting factors, limitations, missing inputs and assumptions.

### 4.4 Build recommendation API and persistence

Implement an API to:
- Request recommendations for a farm and season.
- Return selected recommendation mode and input completeness.
- Return ranked/shortlisted crops with agronomic factors and explanation codes.
- Retrieve a previous recommendation run.

Persist a reproducibility snapshot containing:
- Farm/profile version.
- Season and farmer inputs.
- Climate input references/timestamps.
- Crop catalogue and ruleset version.
- Optional model version.
- Source references.
- Final results and explanations.

## Deliverables

- Source-backed crop catalogue for the pilot region.
- Rule and threshold reference register.
- Deterministic agronomic rules engine.
- Map-based mode without NPK.
- Explainable shortlist and API.
- Database persistence and tests.

## Exit criteria

The crop engine receives a stored map-derived soil profile, handles missing NPK without imputing it, and produces a reproducible crop shortlist whose rules and explanations can be traced to references.

### Antigravity prompt — Phase 4

> Implement Phase 4 only: the structured crop knowledge catalogue and deterministic agronomic recommendation engine. Do not start with a black-box ML classifier. Build the catalogue from authoritative, traceable agronomic references for the Maharashtra pilot crops/seasons. Implement candidate generation, evidence-backed feasibility filtering, transparent suitability scoring and reason codes. Support the regional/map-based mode when NPK is missing and a nutrient-informed mode only when valid nutrient data exists. Missing values must not become zero or be imputed. Store ruleset/catalogue versions and recommendation inputs. Add unit tests for crop rules, missing data, seasons and irrigation constraints.

---

# 7. Phase 5 — Weather, season and economic ranking

**Priority:** High  
**Feature ownership:** Optimal Crop Selection.

## Tasks

### 5.1 Season and farmer context

Capture or determine:
- Target season (Kharif/Rabi/Summer or locally appropriate season).
- Intended sowing window/date if known.
- Irrigation status and source.
- Farm area.
- Optional crop preferences, budget or risk tolerance if the product design supports them.

Do not assume GPS determines irrigation availability or intended crop season.

### 5.2 Weather/climate provider integration

Investigate and integrate approved sources. Candidate categories:
- IMD historical/observed/forecast information where accessible.
- Approved commercial weather API if terms and resolution are suitable.

Keep these distinct:
- Historical climate normal/trend.
- Observed weather.
- Short-range forecast.
- Seasonal outlook.

For each input store provider, location/spatial reference, observation/forecast period, retrieval time, unit and source timestamp. Do not treat a short-range forecast as a seasonal outlook.

### 5.3 Market data integration

Investigate official/approved market sources such as e-NAM and appropriate mandi/APMC feeds.

Every price must retain:
- Commodity/crop identity and variety/grade.
- Market/mandi location.
- Price type (modal/min/max/other).
- Unit.
- Observation date.
- Provider/source.
- Retrieval time and freshness status.

Do not call an old price “live”. Do not use prices from a different grade or distant market without clearly showing that limitation.

### 5.4 Economic ranking

Keep economic ranking separate from agronomic feasibility. Where sufficient verified data exists, estimate:

`ExpectedNetReturn = (ExpectedYield × ExpectedFarmGatePrice) - EstimatedCultivationCost`

Include assumptions such as market distance/transport, crop input and labour costs, irrigation costs, crop duration, yield range and price variability when supported. If the economics inputs are insufficient, show that economic ranking is unavailable and retain the agronomic shortlist.

### 5.5 Frontend

Show separate views or tabs for:
- Agronomic suitability.
- Market/economic comparison (only when data is sufficient).

Show market name, date, commodity grade/unit and assumptions near every financial result.

## Deliverables

- Season/farmer input flow.
- Weather integration with timestamps and input categories.
- Verified market price integration or documented pending status.
- Separate economics service/ranking.
- UI explanation of source, freshness and assumptions.

## Exit criteria

Weather inputs are correctly timestamped and interpreted. Economic ranking only appears when adequate market/cost/yield inputs exist. Missing market data never blocks agronomic crop recommendations and never results in fabricated prices.

### Antigravity prompt — Phase 5

> Implement Phase 5 only: season/farmer context, approved weather integration and optional market/economic ranking. Verify actual API/data access and terms first. Store timestamps, units, locations, grade and source for every observation. Keep historical normals, observed weather, short-range forecast and seasonal outlook separate. Keep agronomic suitability separate from net-return estimates. If reliable mandi prices or cultivation costs cannot be obtained, return an explicit unavailable state rather than fabricated economics. Add freshness and source details to the Flutter UI and tests for stale/missing data.

---

# 8. Phase 6 — Hugging Face model audit, ML benchmark and optional yield prediction

**Priority:** Conditional; do not block rules-based MVP.

## Tasks

### 6.1 Audit candidate crop model

Candidate repository to investigate:

`https://huggingface.co/Sheshank2609/crop-recommendation-system`

Before reuse, verify:
- Model files and framework compatibility.
- Exact input feature order, units and preprocessing.
- Crop labels and overlap with the CropNet crop catalogue.
- Training dataset source, geography, seasons and sample dates.
- Train/test split and evaluation method.
- Missing-value handling.
- Model and dataset licences, including commercial rights.
- Dependencies and security.

Do not assume model-card accuracy transfers to CropNet or to unseen districts. The model must not be used if its inputs require unavailable NPK or if it cannot handle the map-only feature set without fabrication.

### 6.2 Benchmark candidates

Compare:
1. Transparent agronomic rules baseline.
2. Random Forest candidate.
3. XGBoost candidate.

Use only features truly available in production. Run spatial/temporal validation:
- Hold out districts/talukas to assess geographical generalization.
- Hold out later seasons/years to assess temporal generalization.
- Prevent leakage from target-encoded/aggregate future information.
- Report class/rank quality, confusion where appropriate, per-crop/per-region performance and calibration if probabilities are shown.

Deploy ML only if it demonstrably improves on the rules baseline and has suitable commercial licensing.

### 6.3 Yield prediction is a separate capability

Do not add yield output simply to fill a dashboard card.

Only build a yield model if a dataset exists with reliable crop identity, geography, season/year, target unit and yield labels. Include irrigation/management variables only when genuine data exists.

Benchmark at least:
- Historical district-season/crop average baseline.
- Simple regression baseline.
- Random Forest regressor.
- XGBoost regressor.

Validate with later-year holdouts and district/taluka holdouts. Report MAE, RMSE, R² and errors by crop/region. Do not make a causal statement that a specific nutrient deficiency causes a farm's yield gap without verified inputs and a validated causal/agronomic method.

## Deliverables

- Model/data/licence audit report.
- Reproducible train/evaluate pipeline if training is justified.
- Comparison against rules baseline.
- Deployment decision with evidence.
- Model versioning and rollback plan if deployed.
- Yield prediction only if all prerequisites pass.

## Exit criteria

An ML model is shipped only when spatial and temporal validation show a justified improvement, the inputs match available production data, and the licence allows the intended use. Otherwise the transparent rules engine remains the production implementation.

### Antigravity prompt — Phase 6

> Implement Phase 6 as an evaluation task first, not an automatic model integration. Audit the Maharashtra Hugging Face crop recommendation candidate and any datasets/models for feature compatibility, provenance, leakage, reproducibility and commercial licence. Compare the candidate with the Phase 4 rules baseline using only inputs available in CropNet's map-only mode. Use district/taluka and temporal holdouts. Do not fill missing NPK. Make a written deploy/no-deploy recommendation. Only integrate a model if the evidence and licence support production use. Treat yield prediction as a separate optional project with its own dataset and evaluation gates.

---

# 9. Phase 7 — Offline support, localization, accessibility and pilot hardening

**Priority:** Required before field pilot.

## Tasks

### 7.1 Offline behaviour

When online:
- Generate/refresh soil profile.
- Save soil profile and its metadata locally.
- Save recommendation and its input snapshot.
- Retrieve current weather/market inputs and timestamps.

When offline:
- Show saved farms and boundaries.
- Show the last saved soil profile with its generation date and source freshness.
- Show previously generated recommendations with the date and input snapshot.
- Queue supported edits/refresh requests for later synchronization.
- Never show cached data as live.

Respect all provider restrictions for offline caching and data redistribution. Do not package all national soil maps in the app.

### 7.2 Localization and usability

- Externalize UI strings for Marathi, Hindi and English.
- Use farmer-friendly wording and explain unfamiliar technical terms.
- Use large outdoor-readable text and tappable controls.
- Do not depend on colour alone for status.
- Support clear units and local area/production units where needed.
- Add voice/audio explanations as an extensible enhancement if not already available.

### 7.3 Security and privacy

- Enforce farm ownership and API authorization.
- Keep GIS/weather/market credentials on backend.
- Avoid exposing exact farm coordinates unnecessarily in logs/analytics.
- Protect stored polygons and farmer information.
- Review provider licences and attribution in the UI.
- Apply rate limits and request validation.

### 7.4 Performance and resilience

- Run heavy raster/vector jobs asynchronously where needed.
- Cache only permitted results and use cache expiry/versioning.
- Set provider timeouts and retries with backoff.
- Add observability for provider failures, layer freshness, extraction duration and no-coverage rates.
- Test low-end Android hardware and poor/unstable network conditions.

## Deliverables

- Cached profile/recommendation experience.
- Offline and resync behaviour.
- Localized strings and accessible controls.
- Security review and provider attribution.
- Performance test report.
- Pilot checklist and known-limitations document.

## Exit criteria

The app remains useful with weak connectivity, clearly distinguishes cached from current information, protects farm data and passes the complete pilot test suite.

### Antigravity prompt — Phase 7

> Implement Phase 7 only: offline caching, synchronization, Marathi/Hindi/English localization, accessibility, security and pilot hardening. Respect every provider's offline/cache licence. Store the source dates and profile/recommendation versions with cached data. Clearly label stale values and previous recommendations. Test low-end Android and intermittent connectivity. Complete authorization, secret-handling, performance and attribution reviews. Do not add new product features during this hardening phase unless required to fix a release blocker.

---

# 10. Shared API and data contracts to protect

The exact endpoint names should follow the API conventions established in the greenfield FastAPI scaffold, but the feature boundary should remain clear.

## Soil intelligence API concepts

| Operation | Purpose |
|---|---|
| Create/list/get/update farm | Farm metadata and polygon lifecycle |
| Generate/refresh soil profile | Trigger GIS extraction and snapshot creation |
| Get latest soil profile | Retrieve latest profile for a farm |
| List soil profile history | Compare profile versions and source vintages |
| Get parameter details | Explain an individual parameter and its provenance |
| Get mapped zones | Return multiple soil zones and area coverage |
| Get processing status | Track asynchronous GIS job state if needed |

## Crop recommendation API concepts

| Operation | Purpose |
|---|---|
| Get supported crops/seasons | Populate the farmer's selection flow |
| Generate recommendations | Create a recommendation run for farm + season |
| Get recommendation run | Retrieve ranked shortlist and explanations |
| Get crop details | Show requirements, constraints and references |
| Get economic comparison | Return market/economic view only when supported |

## Common soil parameter object

Every returned soil property should conceptually carry:

```json
{
  "parameter": "ph",
  "value": null,
  "raw_value": null,
  "unit": null,
  "status": "not_available",
  "source_id": null,
  "layer_id": null,
  "source_name": null,
  "source_date": null,
  "mapping_scale": null,
  "spatial_resolution_m": null,
  "depth_top_cm": null,
  "depth_bottom_cm": null,
  "valid_farm_coverage_percent": 0,
  "method": null,
  "uncertainty": null,
  "missing_reason": "No approved layer with coverage was found"
}
```

This is an illustrative contract. Adapt field names to existing backend standards, but preserve the meaning and provenance fields.

## Recommendation result object

Each crop result should conceptually include:
- Crop identifier/name and season.
- Rank/position.
- Agronomic suitability score/category and scoring-method version, if supported.
- Economic estimate/rank only where inputs are sufficient.
- Supporting reason codes and farmer-readable explanations.
- Limiting factors and hard constraints.
- Missing/stale input list.
- Soil profile version used.
- Weather/market source references and timestamps.
- Crop catalogue/ruleset/model version.
- Clear disclaimer that the result is decision support, not a guarantee.

---

# 11. Testing strategy and quality gates

Antigravity must add tests throughout implementation, not only at the end.

## Soil intelligence tests

- Valid polygon accepted; malformed/self-intersecting polygon rejected with clear error.
- Farm area calculated using a correct spatial method.
- Farm/user authorization is enforced.
- CRS transformation is correct.
- Vector overlay returns correct area fractions for mixed soil zones.
- Raster statistics exclude NoData and report valid coverage.
- Categorical raster values are counted by class, not averaged.
- Coarse raster resolution warning is triggered where relevant.
- Unit conversion occurs only when source units are known.
- Total nitrogen is not stored as available nitrogen.
- Missing values remain null and include a reason.
- Provenance remains attached after save/read.
- Provider timeout/no-coverage does not crash the workflow.
- WMS display is not mistakenly used as a numeric measurement source.

## Crop selection tests

- Recommendation generation works when NPK is missing.
- Missing inputs are not treated as zero.
- Season filters behave correctly.
- Irrigation/water constraints are applied only when supported by rules.
- Hard exclusions require configured source-backed constraints.
- Missing-data scoring policy is applied consistently.
- Each result includes explainable reason and limitation codes.
- Market prices are checked for source, grade, unit and freshness.
- Economic ranking is hidden/unavailable when required inputs are missing.
- Weather historical/observed/forecast/seasonal types are not mixed.
- Yield prediction remains disabled without a validated model.
- Recommendation is reproducible from stored input/ruleset versions.

## End-to-end pilot tests

Run test journeys for:
- A farm in each pilot taluka (when actual source coverage permits).
- A farm partially covered by a source layer.
- A farm with mixed mapped soil zones.
- A farm with no useful soil layer coverage.
- A farmer who denies GPS permission and uses manual map selection.
- Poor or no internet after a profile has been generated.
- A provider outage during soil-profile refresh.
- A profile where NPK is unavailable but crop suggestions can still be generated.
- A market-data outage where agronomic recommendations still appear without economic ranking.

Do not use fabricated values to pass a test. Use isolated, clearly labelled fixtures for unit tests and actual permitted sample data for integration tests.

---

# 12. Antigravity execution protocol

Use the following operating loop for every phase:

1. **Read:** Re-read the relevant sections of the implementation specification and this roadmap.
2. **Inspect:** Inspect the files and modules created in earlier phases; treat those as the project's baseline.
3. **Plan:** List implementation steps and exact files/migrations.
4. **Implement:** Make the smallest coherent changes for the current phase.
5. **Test:** Run unit tests, integration tests, lint/type checks and builds relevant to the change.
6. **Review:** Inspect for duplicated code, fake values, hard-coded secrets, poor error states and changes outside scope.
7. **Report:** Summarize files changed, APIs added, migrations, tests run, results, screenshots if UI changed, known issues and next blockers.
8. **Stop:** Do not start the next phase until the current exit criteria are met and the user has reviewed the result.

## Required phase completion report template

Antigravity should produce this after each phase:

```text
PHASE:
STATUS: Complete / Partially complete / Blocked

WHAT WAS IMPLEMENTED:
- ...

FILES CREATED OR MODIFIED:
- ...

DATABASE MIGRATIONS:
- ...

API ROUTES / CONTRACTS:
- ...

UI SCREENS / USER FLOW:
- ...

TESTS RUN:
- Command:
- Result:

MANUAL VERIFICATION:
- ...

DATA SOURCES / LICENCES VERIFIED:
- ...

KNOWN LIMITATIONS / BLOCKERS:
- ...

ACCEPTANCE CRITERIA:
- [x] ...
- [ ] ...

RECOMMENDED NEXT PHASE:
- ...
```

---

# 13. Final definition of done

## Feature One — Location-Based Soil Intelligence

- [ ] Farmer can create multiple farms using GPS or manual location selection.
- [ ] Farmer can draw, save and edit a farm polygon.
- [ ] Farm geometry and area are stored correctly and securely.
- [ ] Administrative geography is sourced/confirmed, not blindly guessed.
- [ ] At least one approved soil data source has real, repeatable extraction for supported pilot locations.
- [ ] The system reports actual per-parameter availability and partial coverage.
- [ ] Vector/raster extraction preserves spatial scale and mixed zones.
- [ ] Every available value contains source, year/date, unit, depth and resolution/scale metadata where provided.
- [ ] Missing values remain unavailable/null.
- [ ] The UI says that values are map-derived and not laboratory verified.
- [ ] Farmer can view soil profile history and source details.
- [ ] Provider failures, stale data and offline states are handled.

## Feature Two — Optimal Crop Selection

- [ ] Crop catalogue is sourced from authoritative agronomic references.
- [ ] Farmer can select farm and season and provide relevant irrigation context.
- [ ] Engine consumes the selected farm's versioned soil profile.
- [ ] Mode A works without NPK.
- [ ] Missing/stale values are handled transparently and never imputed silently.
- [ ] Candidate generation and agronomic feasibility checks are explainable.
- [ ] Suitability scoring is documented and configurable.
- [ ] Results show supporting factors, limitations and missing data.
- [ ] Weather data, if integrated, retains source/time/type.
- [ ] Economic ranking is separate and only shown when adequate price/cost/yield inputs exist.
- [ ] ML is deployed only after licence and spatial/temporal validation.
- [ ] Yield prediction is separate and disabled until validated.
- [ ] Recommendation run stores the input snapshot and rule/catalogue/model version.

## Product-level completion

- [ ] The full journey works: farmer → farm polygon → mapped soil profile → crop shortlist.
- [ ] The app preserves the authentication and user-ownership model.
- [ ] The app works on supported Android devices and degrades gracefully on weak connectivity.
- [ ] UI labels and explanations are ready for Marathi/Hindi localization.
- [ ] No fake production values, recommendations or prices are shown.
- [ ] Data permissions, provider attribution and commercial-use terms have been reviewed.
- [ ] Technical limitations and supported geographical coverage are documented for the pilot.

---

## Recommended first action

Give Antigravity the companion implementation specification and this greenfield roadmap. Use **Phase 0 prompt only** first. Review the newly created project foundation, setup instructions, database/auth decisions and the real layer coverage/access permissions for Maval, Mulshi, Baramati and Indapur. Once Phase 0 is accepted and both apps run locally, proceed one phase at a time using the prompt provided under each phase.
