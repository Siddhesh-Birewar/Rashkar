# CropNet AI — Soil Intelligence & Optimal Crop Selection

## Detailed Product, Data, ML, Backend and Frontend Implementation Specification

**Document purpose:** This is the greenfield implementation handoff for Antigravity. No CropNet application codebase exists yet. Create the project foundation and then implement the two features from scratch. This document defines the intended behaviour, technical architecture, data requirements, APIs, user experience, safeguards and acceptance criteria.

**Core features covered:**
1. Location-Based Soil Intelligence (map-derived soil profiling; no physical testing in the initial release).
2. Optimal Crop Selection (soil-, climate-, location-, season- and market-aware crop recommendations, with yield prediction treated as a separately validated capability).

**Target users:** Indian farmers, initially focusing on Maharashtra and the Pune district pilot area: Maval, Mulshi, Baramati and Indapur.

**Product context:** CropNet is intended to be a low-cost, farmer-friendly, mobile-first agricultural decision-support application for smallholder farmers. Build the application from scratch with a Flutter mobile frontend, Python/FastAPI backend and PostgreSQL + PostGIS database. The first release is Android-first and initially targets Maval, Mulshi, Baramati and Indapur in Pune district, Maharashtra.

---

# 0. CRITICAL IMPLEMENTATION INSTRUCTIONS

Antigravity must follow these instructions throughout implementation.

1. **Build from zero.** No application codebase exists. Create a clean repository, Flutter app, FastAPI service, PostgreSQL/PostGIS database, authentication foundation, migrations, tests and documentation. Do not waste time searching for or claiming to reuse nonexistent modules.
2. **Implement the latest agreed scope.** The first release uses existing government/geospatial soil information and GPS/farm boundaries. Do not make a jar test, chemical strip test, camera-based NPK detector or physical laboratory workflow a requirement for the initial release. These are future extensions only.
3. **Do not fabricate soil values.** If a source does not provide a parameter for a farm, store it as unavailable/null. Never fill missing NPK, pH, organic carbon, texture or depth using arbitrary values, averages or another unrelated field.
4. **Never call a map estimate a laboratory measurement.** The initial feature must be labelled **Location-Based Soil Profile**, **Mapped Soil Estimate** or **Soil Intelligence**. It must not claim to physically test a farm's soil.
5. **Preserve provenance per parameter.** Every extracted soil property must retain its source, layer identifier, map year/version, depth interval, spatial resolution or mapping scale, extraction method, units and availability/quality status wherever metadata is provided.
6. **No blanket accuracy or confidence claims.** Do not display made-up accuracy percentages or confidence values. If a source provides uncertainty, represent it accurately and explain it. Otherwise show source, scale, coverage and limitations instead of inventing confidence.
7. **No unsupported external API assumptions.** A public map viewer is not automatically a public data API. Verify each service, data format, access permission, rate limits, attribution and commercial-use terms before integrating it. Do not scrape visual map tiles or reverse-engineer private endpoints as a substitute for data access.
8. **No hard-coded production outputs.** Do not ship sample soil values, demo farms, fabricated crop recommendations or placeholder market prices as real results. Demo fixtures must be isolated from production and clearly labelled.
9. **Do not require unavailable inputs.** The crop recommendation feature must work in a clearly labelled regional-suitability mode when mapped NPK is unavailable. Do not silently pass invented NPK values into a model.
10. **Make recommendations explainable.** Each suggested crop must include the reasons supporting it, important assumptions, missing inputs and risks. A ranking is decision support, not a guarantee of yield or profit.
11. **Design for Indian field conditions.** Prioritise simple language, large readable controls, low-bandwidth use, Marathi/Hindi/local-language readiness, clear units (including hectares/acres and kg/ha/quintals/acre where appropriate), and low-end Android compatibility.
12. **Build modularly.** Data providers, GIS processing, soil profile generation, agronomic rules, ML models, weather data and market data must be separable. One provider's outage must not break the entire application.
13. **Build incrementally.** Establish a documented greenfield architecture and folder structure first. Produce a short plan for each phase, then implement in incremental, testable steps. Avoid premature abstractions and unrelated modules.
14. **Do not expose API keys or secrets in Flutter.** External provider credentials must remain on the backend or in the approved secrets manager/environment configuration.
15. **Do not claim live integrations until tested.** If a source cannot currently be accessed, implement a provider interface and report it as pending rather than pretending the integration works.

---

# 1. PRODUCT OVERVIEW

## 1.1 Core objective

CropNet should help a farmer answer two linked questions:

1. **What can we reasonably infer about the soil in my farm from existing geographical soil information?**
2. **Considering the available soil information, local climate, season, regional agricultural suitability and economics, which crops should I consider growing?**

The two features must operate as a connected workflow:

`Farmer → Farm Boundary → Soil Map Retrieval → Soil Profile → Crop Suitability → Economic Ranking → Recommendation Explanation`

The farmer should be able to create more than one farm/plot. Different farms must have independent boundaries and profiles.

## 1.2 Important product positioning

The first release is **not an actual soil-testing service**. It is a geospatial soil-intelligence service that retrieves and analyses existing spatial data for a farmer's selected farm.

Use language such as:
- “Mapped soil profile”
- “Estimated soil characteristics based on available soil maps”
- “Regional soil information for your farm location”
- “Data source and mapping year”

Do not use language such as:
- “Your soil has been laboratory tested”
- “Exact NPK of your field”
- “Your farm's nitrogen is 120 kg/ha” unless that exact value is actually supplied by a documented source with appropriate method, unit, depth and coverage.

## 1.3 Initial geographical scope

Initial pilot locations:
- Maval, Pune district, Maharashtra
- Mulshi, Pune district, Maharashtra
- Baramati, Pune district, Maharashtra
- Indapur, Pune district, Maharashtra

Do not assume that all four talukas have complete coverage for every soil parameter. A GIS coverage audit must determine the actual availability and spatial scale of each layer.

## 1.4 Initial release scope

### Included
- Farmer creates/selects a farm.
- Farmer uses GPS or manually searches/selects a location.
- Farmer draws or edits a farm boundary polygon.
- Backend identifies administrative geography where reliable boundary data is available.
- Backend checks a catalogue of approved soil map layers.
- Backend extracts available soil attributes intersecting the farm.
- Backend records missing parameters and data provenance.
- Backend generates a map-derived soil profile.
- Farmer views a readable soil report and source/quality explanation.
- Soil profile is passed to crop selection.
- Crop recommendations consider soil, season, climate and location.
- Economic ranking is added where verified market and cultivation-cost data exist.
- Saved farm/profile data can be viewed offline after it has been cached.

### Deferred / not required in initial release
- Physical jar sedimentation test.
- Chemical NPK/pH strips.
- Camera-based chemical colourimetry.
- Image-based soil classification.
- On-device soil image segmentation.
- Laboratory sample collection and result workflows.
- Fertilizer prescription based on unverified mapped nutrients.

Keep the architecture extensible so physical testing, laboratory reports and Soil Health Card uploads can be added later without redesigning the crop engine.

---

# 2. FEATURE ONE — LOCATION-BASED SOIL INTELLIGENCE

## 2.1 Feature objective

Generate a useful, traceable soil profile for a farmer's selected agricultural plot by combining official Indian soil-resource maps and other approved geospatial datasets.

The profile may include, **only where actual source coverage exists**:
- Soil group/class or mapped soil series.
- Texture class.
- Sand, silt and clay fractions.
- Soil depth.
- Slope/erosion or drainage-related attributes.
- Soil pH.
- Electrical conductivity (EC).
- Organic carbon.
- Available water capacity.
- Available N, P and K where a suitable source provides them.
- Sulphur and micronutrients where mapped.
- Agroecological/agro-climatic context.

Do not treat all listed attributes as guaranteed. Coverage will differ by provider, layer, scale, date and geography.

## 2.2 Farmer workflow

### Step 1 — Start soil intelligence

Farmer selects **Analyse My Soil** or **Soil Intelligence** from the app.

Show a short explanation:
> CropNet will use your farm location and available soil maps to prepare an estimated soil profile. These values are map-derived and are not a substitute for a laboratory soil test.

### Step 2 — Select or create a farm

Offer two ways to locate a farm:
1. **Use current location:** request location permission only after explaining why it is needed. Use the phone GPS to centre the map. GPS coordinates are not automatically the farm boundary.
2. **Search/select manually:** allow the farmer to search for village, taluka, district or a known place and position the map manually.

The farmer must be able to continue without granting GPS permission.

### Step 3 — Draw the farm boundary

The farmer marks the plot using a polygon on a satellite/base map.

Requirements:
- Tap-to-add polygon vertices.
- Undo the last point.
- Remove/reset polygon.
- Save boundary.
- Edit boundary later.
- Show calculated area after converting geometry to a suitable metric projection/geodesic area method.
- Allow manual correction of farm area if needed, while retaining that it was manually entered.
- Validate polygon closure, minimum points, self-intersection and invalid geometry.
- Warn if polygon is extremely small/large or appears outside the selected region; do not silently reject legitimate cases.
- Support multiple plots per farmer.
- Ask for farm/plot name and optional crop/irrigation details if these are needed by crop selection.

A farm polygon represents the farmer-selected area; it is not legal proof of land ownership or a cadastral boundary.

### Step 4 — Confirm farm details

Capture:
- Farm name.
- State, district, taluka, village (as verified or user-confirmed where possible).
- Farm polygon geometry.
- Farm area and area unit.
- Optional irrigation type: rainfed, irrigated, mixed, unknown.
- Optional water source: rainfall, canal, borewell, well, other, unknown.
- Optional current/previous crop and intended season.

Do not make optional fields mandatory without a product reason.

### Step 5 — Generate soil profile

The user taps **Generate Soil Profile**.

The app calls the backend. The backend:
1. Validates the farm geometry and coordinate reference system.
2. Determines the administrative geography using approved boundary data.
3. Finds all active source layers whose geographic extent intersects the farm.
4. Checks whether the layer has usable data and whether its terms permit the intended use.
5. Extracts available attributes from raster/vector sources.
6. Calculates coverage/area distribution for categorical layers and suitable statistics for continuous layers.
7. Applies unit normalization only when the original unit is known.
8. Records source metadata and quality limitations for each result.
9. Stores a versioned soil-profile snapshot.
10. Returns the profile to Flutter.

### Step 6 — View the soil profile

The result screen should separate:
- Mapped soil characteristics.
- Soil fertility/nutrient information (only where sourced).
- Water/land characteristics.
- Missing/unavailable information.
- Data source, mapping year, depth, scale/resolution and limitations.

Every parameter must have an information/help affordance.

### Step 7 — Proceed to crop selection

The farmer can select **Find Suitable Crops**. CropNet passes the stored soil profile and farm context to the crop recommendation service.

## 2.3 Data-source hierarchy

Implement a provider-based architecture. Do not hard-code the entire system to one vendor.

### Primary candidate: ICAR-NBSS&LUP BHOOMI Geoportal

Official portal: https://bhoomigeoportal-nbsslup.in/

Organisation: ICAR – National Bureau of Soil Survey and Land Use Planning.

Candidate data catalogue includes multiple soil-resource mapping scales and property/thematic layers. Potentially relevant layers include:
- Soil resources/soil types.
- Soil texture.
- Soil depth.
- Slope and erosion.
- Soil pH.
- Organic carbon.
- Sulphur and selected micronutrients.
- Available water capacity.
- Rainfall/agroecological context.
- Crop suitability or crop distribution where available.

The portal's catalogue has described national and more detailed mapping scales, including 1:1 million, 1:250,000, 1:50,000 and selected 1:10,000 mapping. These are mapping scales, not a promise of uniform pixel resolution or complete coverage in every pilot taluka.

**Implementation requirement:** verify actual layer coverage, metadata, GIS service endpoints, downloadable formats, access policy, attribution and commercial-use permissions. Do not presume a public API exists for every layer. A portal viewer or WMS image is not enough to extract reliable numerical attributes.

### Regional candidate: Maharashtra PoCRA GIS

Official portal: https://gis.mahapocra.gov.in/

Investigate relevant available services such as Soil Health Card, NBSS advisory and soil moisture information. The dashboard may contain under-development or dated functionality. Confirm that the layer/service is active, accessible, current and licensable before integrating it.

### Government fertility mapping: SLUSI / Soil Health Card-derived maps

Official Ministry information: https://www.pib.gov.in/Pressreleaseshare.aspx?PRID=2110419&lang=2&reg=48

A Government of India release dated 11 March 2025 reported Maharashtra soil fertility maps for 351 villages across 34 districts, generated using geospatial techniques and Soil Health Card data. Reported parameter families include pH, EC, organic carbon, available NPK, sulphur and micronutrients.

This is a promising data source, but the announcement does not itself provide an unrestricted API or prove that every CropNet pilot village is covered. Obtain village-level coverage and access conditions before use.

### Fallback candidate: ISRIC SoilGrids

Official website: https://soilgrids.org/

Potential properties include:
- Sand, silt and clay fractions.
- pH.
- Organic carbon.
- Cation exchange capacity.
- Total nitrogen.
- Soil property estimates at 250 m spatial resolution with uncertainty information for supported layers.

Important limitations:
- SoilGrids is global modelled soil information, not a farm-level soil test.
- A 250 m cell may cover multiple farms and cannot resolve within-field variability.
- Total nitrogen is not the same as plant-available nitrogen.
- Do not infer available phosphorus or potassium from unavailable SoilGrids values.
- The SoilGrids REST API was reported as temporarily paused during the research for this specification. Verify current status before relying on it. Consider approved static data access if available and permitted.

### Other candidates

NATMO or other official state/national data catalogues may be investigated where suitable. Only integrate sources after verifying the actual dataset, data quality, coverage, licensing and technical access.

## 2.4 GIS source catalogue and coverage audit

Before coding a provider integration, create a source/layer catalogue. This should be an admin-maintained database or configuration, not scattered conditionals in business logic.

Each layer record should include:
- Provider name.
- Dataset/layer name and identifier.
- Description/property represented.
- Geometry type: raster, vector or service-only.
- Endpoint or storage location (server-side only).
- Data format: GeoTIFF, COG, GeoPackage, Shapefile, WMS, WFS, WCS, OGC API Features, etc.
- CRS/EPSG code.
- Spatial extent.
- Mapping scale or raster resolution.
- Soil depth interval.
- Measurement/prediction method, if documented.
- Units.
- Data year and publication/update date.
- NoData value and class legend.
- Uncertainty information, where supplied.
- Attribution text.
- Licence/terms and commercial-use permission status.
- Provider access conditions, rate limits and credentials requirement.
- Active/inactive status and last validation date.

Perform a coverage audit for **Maval, Mulshi, Baramati and Indapur**. For each soil property, record whether the layer is available, its scale/resolution, vintage, depth, source and access status. Do not claim pilot coverage until verified.

Create an initial audit matrix such as:

| Pilot area | Soil type | Texture | Depth | pH | EC | Organic carbon | Available N | Available P | Available K | Water capacity |
|---|---|---|---|---|---|---|---|---|---|---|
| Maval | To verify | To verify | To verify | To verify | To verify | To verify | To verify | To verify | To verify | To verify |
| Mulshi | To verify | To verify | To verify | To verify | To verify | To verify | To verify | To verify | To verify | To verify |
| Baramati | To verify | To verify | To verify | To verify | To verify | To verify | To verify | To verify | To verify | To verify |
| Indapur | To verify | To verify | To verify | To verify | To verify | To verify | To verify | To verify | To verify | To verify |

The table must be populated from actual layer inspection, not assumptions.

## 2.5 GIS extraction logic

### Geometry handling

- Accept farm polygons in GeoJSON or an equivalent structured geometry format.
- Validate incoming coordinates and CRS.
- Store canonical geometry in PostGIS using an appropriate spatial reference. EPSG:4326 is suitable for interchange; use an appropriate projected CRS or geodesic calculation for area/statistics.
- Reproject data only when required and retain original CRS metadata.
- Validate self-intersections and invalid polygons with Shapely/PostGIS.
- Avoid calculating area directly in latitude/longitude degrees.

### Administrative geography

Use official or suitably licensed administrative boundary datasets for state/district/taluka/village identification where available.

Reverse geocoding can be used as a convenience or fallback, but its result must be marked as geocoded/suggested until confirmed. A reverse-geocoded place name is not proof of cadastral location or ownership.

### Layer intersection

For vector layers:
- Spatially filter features that intersect the farm polygon.
- Calculate intersection geometry and area coverage.
- Preserve each mapped class and its coverage fraction.
- Return a dominant class only when the coverage rule is met; otherwise return a mixed/heterogeneous result.

For raster layers:
- Mask or clip pixels by the farm polygon.
- Exclude NoData values.
- Calculate meaningful zonal statistics (mean/median/min/max/standard deviation/quantiles as appropriate).
- Calculate valid-pixel coverage as a percentage of the farm area where feasible.
- For categorical rasters, compute class distribution, not an arithmetic mean of class codes.
- Do not imply sub-pixel precision. If the farm is smaller than or comparable to a raster cell, explain that the result is effectively regional/coarse.

For map services:
- WMS is primarily for display. It is not by itself a numerical data source.
- `GetFeatureInfo` may be used only if the service officially supports it and returns meaningful attributes.
- Use WFS/OGC API Features for vector attributes where officially exposed.
- Use WCS or approved GeoTIFF/COG downloads for raster values where available.
- Do not parse pixels from a rendered map screenshot to estimate laboratory-like values.

### Example zonal calculation

For a continuous raster parameter, an area-weighted mean can be used when scientifically appropriate:

`farm_value = sum(intersection_area_i * cell_value_i) / sum(valid_intersection_area_i)`

However, select mean, median, distribution or another statistic according to the variable and source methodology. Preserve the distribution where a farm intersects multiple soil zones; do not hide heterogeneity behind one number.

For categorical vector regions, calculate each class's percentage of farm area. Example:
- Mapped soil zone A: 70% of farm polygon.
- Mapped soil zone B: 30% of farm polygon.

Display the mixed profile rather than claiming the entire field is one soil type.

### Spatial resolution caveat

A spatial intersection does not increase the underlying map resolution. If several farms fall inside one 250 m raster cell, the same underlying cell estimate may be returned for all of them. Flag this clearly and do not claim that the result is an independently measured farm-specific value.

## 2.6 Soil parameter normalization

Use a canonical parameter dictionary. Store raw source values and normalized values separately.

Suggested parameter keys:
- `soil_group`
- `soil_series`
- `texture_class`
- `sand_percent`
- `silt_percent`
- `clay_percent`
- `soil_depth`
- `slope`
- `erosion_class`
- `drainage_class`
- `ph`
- `electrical_conductivity`
- `organic_carbon`
- `available_nitrogen`
- `available_phosphorus`
- `available_potassium`
- `sulphur`
- `zinc`
- `iron`
- `copper`
- `manganese`
- `boron`
- `available_water_capacity`

For each parameter:
- Retain original value and unit.
- Store normalized value/unit only when a valid conversion is defined.
- Store soil depth interval.
- Store source/method and whether it is modelled, mapped, survey-derived or laboratory-measured.
- Store date/year.
- Store valid spatial coverage.
- Store source-provided uncertainty if available.
- Store missing-data reason if no value can be returned.

**Important scientific distinctions:**
- SoilGrids total nitrogen must not be renamed available nitrogen.
- Soil texture class is not the same as soil taxonomic classification (e.g. a texture triangle result does not by itself prove a soil is a Vertisol/Black Cotton Soil).
- Map-derived pH is not a current laboratory pH reading for the exact field.
- A soil group name must not be inferred solely from a colour or broad regional description.

## 2.7 Soil profile status model

Each parameter should have an explicit status, for example:
- `available`: a usable value was extracted.
- `partially_available`: only part of the farm is covered or the source contains partial data.
- `not_available`: no suitable source layer exists for the farm.
- `no_coverage`: source exists but does not cover the farm.
- `no_data`: intersecting source cells/features contain NoData.
- `source_unavailable`: provider cannot currently be reached.
- `access_pending`: data access permission has not been obtained.
- `stale`: data exceeds an internally configured freshness threshold (do not delete it; show its date and warning).
- `awaiting_map_extraction`: development-only state, not a production result.

Profile-level statuses can include:
- `generated`
- `partial`
- `failed`
- `stale`
- `needs_refresh`

Do not convert missing values into 0. Zero is a real value and must not be used to mean unknown.

## 2.8 Soil profile data model

Create PostgreSQL + PostGIS as the default spatial database for this greenfield project. Use SQLAlchemy 2 and Alembic for data access and migrations. If the chosen hosting platform cannot support PostGIS or required GIS operations, document and approve a compatible alternative before implementation. Do not silently remove spatial capability.

Suggested tables:

### `farms`
- `id`
- `user_id`
- `farm_name`
- `boundary_geom` (Polygon/MultiPolygon)
- `area_value`
- `area_unit`
- `state_code`, `district_code`, `taluka_code`, `village_code` where available
- `state_name`, `district_name`, `taluka_name`, `village_name`
- `irrigation_type` nullable
- `water_source` nullable
- `created_at`, `updated_at`

### `soil_data_sources`
- `id`
- `provider_code`
- `provider_name`
- `official_url`
- `licence_name`
- `licence_url`
- `commercial_use_allowed` (true/false/unknown/pending)
- `attribution_text`
- `access_status`
- `last_checked_at`

### `soil_map_layers`
- `id`
- `source_id`
- `layer_code`
- `layer_name`
- `parameter_key`
- `geometry_type`
- `data_format`
- `service_type`
- `service_endpoint` (server-side only)
- `storage_uri` (server-side only)
- `crs`
- `spatial_extent`
- `spatial_resolution_m` nullable
- `mapping_scale` nullable
- `depth_min_cm` nullable
- `depth_max_cm` nullable
- `source_year` nullable
- `published_at` nullable
- `units`
- `nodata_value` nullable
- `legend_json` nullable
- `uncertainty_metadata_json` nullable
- `terms_status`
- `is_active`
- `last_validated_at`

### `farm_soil_profiles`
- `id`
- `farm_id`
- `profile_version`
- `profile_status`
- `profile_type` (initially `location_based_estimate`)
- `generated_at`
- `algorithm_version`
- `coverage_summary_json`
- `profile_summary_json`
- `created_at`

### `soil_parameters`
- `id`
- `profile_id`
- `parameter_key`
- `raw_value_json`
- `normalized_value` nullable
- `unit` nullable
- `status`
- `source_id` nullable
- `layer_id` nullable
- `source_year` nullable
- `depth_min_cm` nullable
- `depth_max_cm` nullable
- `spatial_resolution_m` nullable
- `mapping_scale` nullable
- `coverage_percent` nullable
- `statistic_type` nullable (mean, median, dominant_class, distribution, etc.)
- `uncertainty_json` nullable
- `limitations_json`
- `created_at`

### `farm_soil_zone_intersections` (recommended)
- `id`
- `profile_id`
- `layer_id`
- `zone_code`
- `zone_label`
- `area_sq_m`
- `farm_coverage_percent`
- `attributes_json`

Keep profile snapshots immutable after generation. If data is refreshed or the farm boundary changes, generate a new version; preserve prior versions for traceability.

## 2.9 Example soil profile response

This is an API shape illustration only. Null values must remain null when no data is available.

```json
{
  "farm_id": "farm_001",
  "profile_id": "soil_profile_001",
  "profile_version": 1,
  "profile_type": "location_based_estimate",
  "profile_status": "partial",
  "location": {
    "state": "Maharashtra",
    "district": "Pune",
    "taluka": "Baramati",
    "village": null
  },
  "farm_area": {
    "value": null,
    "unit": "acre",
    "calculation_method": "polygon_area"
  },
  "parameters": {
    "soil_group": {
      "value": null,
      "status": "no_coverage",
      "source": null
    },
    "texture_class": {
      "value": null,
      "status": "not_available",
      "source": null
    },
    "ph": {
      "value": null,
      "unit": "pH",
      "status": "not_available",
      "source": null
    },
    "organic_carbon": {
      "value": null,
      "unit": null,
      "status": "not_available",
      "source": null
    },
    "available_nitrogen": {
      "value": null,
      "unit": null,
      "status": "not_available",
      "source": null
    }
  },
  "verification": {
    "method": "geospatial_map_overlay",
    "laboratory_verified": false
  },
  "limitations": [
    "Values are based on available geographical soil datasets.",
    "The profile is not a laboratory test of the selected farm."
  ],
  "generated_at": "<server-generated ISO 8601 timestamp>"
}
```

Do not copy the illustrative date or identifiers into actual records. Generate real timestamps and IDs.

## 2.10 Soil Intelligence API design

Use the API route conventions, authentication and response envelope established in Phase 0. Suggested endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/v1/farms` | Create farm and save boundary |
| `GET` | `/api/v1/farms` | List farmer's farms |
| `GET` | `/api/v1/farms/{farm_id}` | Get farm details |
| `PATCH` | `/api/v1/farms/{farm_id}` | Update farm details/boundary |
| `DELETE` | `/api/v1/farms/{farm_id}` | Delete farm subject to retention policy |
| `POST` | `/api/v1/farms/{farm_id}/soil-profile` | Generate/refresh map-derived profile |
| `GET` | `/api/v1/farms/{farm_id}/soil-profile/latest` | Get latest profile |
| `GET` | `/api/v1/soil-profiles/{profile_id}` | Get a specific profile version |
| `GET` | `/api/v1/soil/layers/available` | List layers available for a geometry/location |
| `GET` | `/api/v1/soil/sources` | List active public/source information (admin or public subset) |

### Farm creation request (illustrative)

```json
{
  "farm_name": "North Field",
  "boundary": {
    "type": "Polygon",
    "coordinates": [[[75.0, 18.0], [75.001, 18.0], [75.001, 18.001], [75.0, 18.001], [75.0, 18.0]]]]
  },
  "area_unit": "acre",
  "irrigation_type": "rainfed",
  "water_source": "rainfall"
}
```

Validate that the authenticated user owns or is authorised to access the farm. Never trust a client-supplied `user_id` as the ownership authority.

### Soil profile generation request

```json
{
  "refresh": false,
  "preferred_sources": ["BHOOMI", "SLUSI", "SOILGRIDS"],
  "include_partial_coverage": true
}
```

Source identifiers are examples. The service must use only providers that are active, approved and configured.

### Processing behaviour

For potentially slow raster extraction, use a job/task pattern if necessary:
- `POST` starts the soil-profile job.
- Return `job_id` and status.
- `GET /api/v1/jobs/{job_id}` returns processing status.
- Expose job status through a FastAPI endpoint (polling initially). Add push notifications only if a later product requirement justifies them.

Do not block mobile requests for long-running GIS operations.

---

# 3. FEATURE TWO — OPTIMAL CROP SELECTION

## 3.1 Feature objective

Recommend crops that are agronomically suitable for the farmer's specific farm context and season, then rank feasible choices using local economic information where reliable data exists.

The system must answer:
- Which crops are reasonably suitable for this farm and season?
- What mapped soil and climate conditions support each crop?
- What are the major limitations or risks?
- What data is missing or uncertain?
- Which choices may be economically more attractive based on verified market/cost data?

Do not equate high agricultural suitability with maximum profit. Keep agronomic suitability and economic ranking as distinct stages.

## 3.2 Input architecture

### A. Soil parameters

Read the latest available farm soil profile:
- Soil group/type.
- Soil texture and texture fractions.
- Soil depth.
- pH.
- Organic carbon.
- Available water capacity.
- Drainage/slope/erosion where available.
- Available NPK only if genuinely available from a source with documented meaning, unit, depth, date and coverage.

Missing fields must remain missing. The recommender must know whether a parameter is missing, unavailable, stale or present.

### B. Climate and weather

Potential inputs:
- Historical rainfall normals/trends.
- Seasonal rainfall expectation.
- Current/forecast rainfall.
- Minimum/maximum temperature.
- Relative humidity where relevant.
- Extreme weather risk where a reliable source is available.

Potential providers include official IMD datasets/services and an approved weather provider such as OpenWeatherMap. Verify licensing, attribution, commercial-use terms, API limits and temporal/spatial resolution. Do not treat a short-range weather forecast as a seasonal rainfall prediction.

Distinguish:
- Historical climate normal.
- Seasonal outlook.
- Short-term forecast.
- Observed weather.

Store the date/time and source for each input.

### C. Geographical and seasonal context

Use:
- State/district/taluka/village.
- Agro-climatic/agroecological zone if available.
- Kharif/Rabi/Summer or locally appropriate season.
- Sowing window and crop duration.
- Irrigation availability/type.
- Farm area.
- Optional farmer-selected preferences and constraints.

Do not assume GPS alone determines the farmer's crop season or irrigation availability. Ask or infer from supported agricultural calendars with a visible explanation.

### D. Market and economics

Potential inputs:
- Mandi/Agricultural Produce Market Committee price history.
- e-NAM data where officially accessible.
- Local mandi prices and market distance.
- Crop input/cultivation cost estimates.
- Seed/fertilizer/labour/irrigation cost where sourced.
- Crop price volatility and seasonality.

Never fabricate a live mandi price. Store market, commodity variety/grade, unit, date, source and location. A price from a distant mandi or different grade should not be presented as the farmer's guaranteed sale price.

### E. Pest/disease or production risk

This can be a later extension unless high-quality local data exists. Do not invent a `P_risk` probability. Start with transparent risk rules based on sourced climate/crop guidance, and add predictive models only after validation.

## 3.3 Crop selection pipeline

Use a multi-stage recommendation system rather than one opaque classifier.

### Stage 0 — Validate input completeness

- Fetch the selected farm's soil profile.
- Fetch season/location details.
- Fetch climate information.
- Determine which required features are available.
- Mark unavailable/stale values.
- Select the supported recommendation mode.

### Stage 1 — Candidate crop generation

Build a crop knowledge catalogue containing candidate crops and their agronomic requirements. Initially focus on crops relevant to Maharashtra and the pilot region, but make the catalogue data-driven and configurable.

Candidate examples for the pilot to investigate include:
- Soybean.
- Cotton.
- Sugarcane.
- Pomegranate.
- Tur/pigeon pea.
- Groundnut.
- Maize.
- Sorghum/jowar.
- Chickpea/gram.
- Onion and other locally relevant horticultural crops where sufficient information exists.

This is a candidate list for data collection, not a claim that every crop is suitable in every pilot taluka or season.

For each crop, maintain:
- Crop and variety/production-system identifier where necessary.
- Suitable seasons and sowing windows.
- Soil texture/soil-group preference.
- pH range and source of agronomic guidance.
- Soil depth/drainage requirements.
- Water requirement/irrigation conditions.
- Rainfall and temperature suitability.
- Crop duration.
- District/zone relevance.
- Known constraints and risk conditions.
- Source organisation, source document, publication/revision date and reference.

Use official ICAR, State Agricultural University, KVK and other authoritative agronomic references. Every important crop requirement must have a traceable reference. Do not invent thresholds simply to make an algorithm run.

### Stage 2 — Agronomic feasibility filtering

First remove or flag crops that violate critical constraints, for example:
- Wrong season/sowing window.
- Clearly incompatible water availability.
- Soil depth or drainage condition outside documented crop tolerance.
- Severe climate incompatibility.
- Locally unsupported crop/variety where evidence indicates poor suitability.

A hard exclusion should only be applied when there is a defensible source-backed rule. Otherwise use a penalty or uncertainty warning rather than a categorical rejection.

### Stage 3 — Agronomic suitability scoring

Calculate a transparent suitability score from available parameters.

Illustrative formula:

`AgronomicSuitability(crop) = weighted_score(soil_match, climate_match, season_match, water_match, regional_match)`

The exact weights must be configurable, documented and validated with agronomists or authoritative crop guidance. Do not hard-code unsupported weights as scientific facts.

Rules:
- Normalize feature scores consistently to a defined range.
- Do not treat missing data as a zero score.
- Adjust/renormalize weights only under an explicit, documented missing-data policy.
- Display which factors contributed to the result.
- Show a data-completeness indicator, not a made-up model confidence score.
- Keep negative factors and hard constraints visible.

### Stage 4 — Optional ML ranking

Machine learning can improve ranking if there is appropriate training and validation data. It must not replace the transparent agronomic baseline before it is proven better.

Candidate approach:
- Random Forest classifier/ranker as a baseline.
- XGBoost classifier/ranker as a challenger.
- Evaluate with spatial and temporal validation, not only random train/test splits.

A Hugging Face repository investigated during research:

`https://huggingface.co/Sheshank2609/crop-recommendation-system`

It describes a Maharashtra-oriented system with a Random Forest soil/climate model and regional historical suitability scoring. The model card reported a 99.6% five-fold cross-validation result for one component, and a regional scoring component based on historical Maharashtra data. Treat these as repository-reported claims, not independent proof of performance.

**Critical compatibility limitations to audit before reuse:**
- The soil/climate component reportedly contains 22 crop classes and does not include Soybean or Sugarcane, although its regional scoring component reportedly includes them.
- Pomegranate appears in the first component but not the regional scoring component.
- Confirm model files, exact feature order, preprocessing, training data provenance, split strategy, model card, dependencies, licence and commercial-use rights.
- Confirm whether the model accepts missing values. If not, do not invent missing NPK. Either do not use that model in map-only mode or train a separate model with inputs that are genuinely available.
- Re-evaluate performance on held-out Maharashtra districts/talukas and later agricultural seasons.

Do not make this repository a mandatory dependency. It is an experimental baseline candidate.

### Stage 5 — Economic ranking

Once agronomically feasible crops are identified, estimate economics separately.

Illustrative expected net return:

`ExpectedNetReturn = (ExpectedYield × ExpectedFarmGatePrice) - EstimatedCultivationCost`

Where possible, incorporate:
- Expected yield range rather than only one value.
- Price history and volatility.
- Market/mandi distance and transport cost.
- Crop input and labour costs.
- Irrigation/water costs.
- Crop duration and cash-flow considerations.
- Buyer/market availability.

Economic score/ranking must carry source dates and assumptions. If prices or costs are missing, show **economic ranking unavailable** or a clearly qualified estimate. Do not use an old market price as a live price.

### Stage 6 — Final recommendation and explanation

Each crop result should contain:
- Crop name and season.
- Agronomic suitability score or category (only if calibrated/defined).
- Economic ranking/value if data exists.
- Supporting factors.
- Limiting factors.
- Missing data.
- Water/irrigation considerations.
- Expected crop duration/sowing window if sourced.
- Data freshness and sources.
- Recommendation explanation in accessible language.

The first result must not be portrayed as a guaranteed best crop. Give a shortlist, not false certainty.

## 3.4 Recommendation modes for missing NPK

The initial map-only system will not have available NPK for every farm. Therefore implement at least two explicit modes.

### Mode A — Regional / map-based suitability

Use only genuinely available inputs such as:
- Soil type/texture/depth from mapped data.
- Mapped pH/organic carbon/water capacity where available.
- Geography/agroecological zone.
- Season.
- Historical climate and current/seasonal weather data.
- Irrigation information supplied by the farmer.

Do not require NPK if it is not available.

Output language:
> These recommendations use mapped soil characteristics and available climate/location data. Nutrient-specific suitability could not be assessed where available NPK data was missing.

### Mode B — Nutrient-informed suitability

Use only when relevant nutrient measurements/estimates are available with clear provenance and suitable quality. Regional fertility maps may still be estimates rather than farm measurements; label them accordingly.

Do not call Mode B laboratory-verified unless the source is actually a laboratory report for that farm.

## 3.5 Yield prediction — separate and conditional

The original CropNet concept includes an XGBoost yield regressor and yield-gap analysis. Keep this as a planned capability, but do not implement unsupported exact predictions simply because the UI requires a yield number.

Potential features:
- Crop/variety.
- District/zone.
- Season and year.
- Soil type/texture and available mapped properties.
- Rainfall and temperature over the crop growth period.
- Irrigation.
- Sowing date.
- Farm area.
- Management/input variables if genuinely available.

Potential model:
- XGBoost regressor as a candidate.
- Compare against simpler baselines (historical district-season average, Random Forest, linear baseline).

A yield dataset must have clear target unit, geography, season/year, crop identity and provenance. Avoid leakage from future-year variables or aggregate statistics that already encode the target.

Validation:
- Train/test by time (hold out later years).
- Hold out districts/talukas to assess geographical generalization.
- Report MAE/RMSE/R² and error by crop and region.
- Compare against a historical baseline.
- Display ranges/uncertainty where defensible.

Do not display a yield-gap statement such as “you are losing 4 quintals because of phosphorus deficiency” when the farm does not have a verified nutrient measurement and a validated causal/agronomic model. At most show a sourced scenario or a general agronomic limitation, clearly labelled.

## 3.6 Crop knowledge catalogue

Create structured, versioned data rather than embedding crop rules in Python if-statements.

Suggested tables:

### `crops`
- `id`
- `crop_code`
- `crop_name_en`
- `crop_name_mr`
- `crop_name_hi`
- `crop_category`
- `is_active`

### `crop_season_requirements`
- `id`
- `crop_id`
- `season_code`
- `sowing_start_date_or_month`
- `sowing_end_date_or_month`
- `crop_duration_days_min`
- `crop_duration_days_max`
- `source_reference_id`

### `crop_soil_requirements`
- `id`
- `crop_id`
- `texture_preferences_json`
- `soil_depth_min_cm` nullable
- `ph_min` nullable
- `ph_max` nullable
- `drainage_preferences_json`
- `available_water_capacity_requirements_json`
- `nutrient_requirements_json`
- `critical_constraints_json`
- `source_reference_id`

### `crop_climate_requirements`
- `id`
- `crop_id`
- `rainfall_min_mm` nullable
- `rainfall_max_mm` nullable
- `temperature_min_c` nullable
- `temperature_max_c` nullable
- `humidity_requirements_json` nullable
- `climate_constraints_json`
- `source_reference_id`

### `crop_region_suitability`
- `id`
- `crop_id`
- `state_code`
- `district_code` nullable
- `taluka_code` nullable
- `agro_climatic_zone_code` nullable
- `suitability_category`
- `notes`
- `source_reference_id`

### `agronomic_references`
- `id`
- `organisation`
- `document_title`
- `url_or_document_id`
- `publication_date`
- `revision_date`
- `crop_id` nullable
- `parameter_or_rule`
- `page_or_section` nullable
- `notes`

Keep crop requirement sources visible to administrators and available for explanation where useful.

## 3.7 Crop recommendation API design

Use the versioned `/api/v1` route conventions defined for the new FastAPI service. Suggested endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/v1/farms/{farm_id}/crop-recommendations` | Generate crop shortlist |
| `GET` | `/api/v1/farms/{farm_id}/crop-recommendations/latest` | Fetch latest recommendation |
| `GET` | `/api/v1/crop-recommendations/{recommendation_id}` | Fetch a recommendation result |
| `GET` | `/api/v1/crops` | List supported crops |
| `GET` | `/api/v1/crops/{crop_id}` | Get crop information and sources |
| `GET` | `/api/v1/crop-seasons` | List seasons and relevant windows |

### Recommendation request (illustrative)

```json
{
  "soil_profile_id": "soil_profile_001",
  "season": "kharif",
  "irrigation_type": "rainfed",
  "water_source": "rainfall",
  "market_location_id": null,
  "include_economic_ranking": true,
  "include_yield_prediction": false,
  "recommendation_mode": "auto"
}
```

`auto` should choose the most complete valid mode based on actual input coverage. It must return which mode was used and why.

### Recommendation response (illustrative)

```json
{
  "recommendation_id": "rec_001",
  "farm_id": "farm_001",
  "soil_profile_id": "soil_profile_001",
  "mode": "regional_map_based_suitability",
  "season": "kharif",
  "status": "generated_with_limitations",
  "input_completeness": {
    "available": ["texture_class", "district", "season", "rainfall"],
    "missing": ["available_nitrogen", "available_phosphorus", "available_potassium"],
    "stale": []
  },
  "recommendations": [
    {
      "crop_code": "crop_example",
      "crop_name": "Illustrative crop",
      "agronomic_suitability": {
        "score": null,
        "category": "to_be_calculated_from_validated_rules",
        "explanation": ["Illustrative placeholder only"]
      },
      "economic_assessment": {
        "status": "not_available",
        "expected_net_return": null,
        "currency": "INR"
      },
      "yield_prediction": {
        "status": "not_requested",
        "value": null,
        "unit": null
      },
      "limitations": ["NPK data unavailable"]
    }
  ],
  "sources": [],
  "created_at": "server_generated_timestamp"
}
```

Do not return the illustrative crop, scores or values. Actual recommendations must come from the validated crop catalogue and data pipeline.

## 3.8 Recommendation storage

Suggested tables:

### `crop_recommendation_runs`
- `id`
- `farm_id`
- `soil_profile_id`
- `season_code`
- `recommendation_mode`
- `algorithm_version`
- `model_version` nullable
- `input_snapshot_json`
- `status`
- `generated_at`

### `crop_recommendation_results`
- `id`
- `run_id`
- `crop_id`
- `rank`
- `agronomic_score` nullable
- `economic_score` nullable
- `expected_net_return` nullable
- `expected_yield_min` nullable
- `expected_yield_max` nullable
- `result_json`
- `explanation_json`
- `limitations_json`

### `market_price_observations`
- `id`
- `crop_id`
- `market_id`
- `market_name`
- `commodity_variety`
- `grade`
- `price_min`
- `price_max`
- `modal_price`
- `unit`
- `currency`
- `observation_date`
- `source_id`
- `retrieved_at`

### `weather_observations_or_forecasts`
- `id`
- `location_id` or geometry reference
- `source_id`
- `observation_type` (observed, forecast, historical_normal, seasonal_outlook)
- `valid_from`
- `valid_to`
- `parameter_key`
- `value`
- `unit`
- `retrieved_at`

Persist the inputs used for each recommendation run so results can be reproduced and explained later.

---

# 4. FRONTEND / FLUTTER UX REQUIREMENTS

## 4.1 Design principles

- Establish a coherent CropNet design system and initial navigation for these two feature journeys; do not add unrelated modules.
- Use high-contrast outdoor-readable text and controls.
- Keep the main workflow short and accessible to low digital-literacy users.
- Use clear map drawing gestures and visible undo/reset actions.
- Avoid presenting raw GIS terminology without explanation.
- Support Marathi and Hindi localization; keep string resources separate from UI code.
- Provide audio/voice explanation as an extensible capability, not a blocker for the first working release.
- Show loading, partial-data, no-data, offline and failure states.
- Make all scores and status labels understandable; do not use colour alone to convey meaning.

## 4.2 Suggested screens

### Soil Intelligence
1. Soil Intelligence landing/intro.
2. Farm selector / add farm.
3. Map search and GPS location.
4. Farm boundary drawing/editing.
5. Farm details confirmation.
6. Soil profile generation/loading state.
7. Soil profile dashboard.
8. Parameter detail and source/limitations view.
9. Saved soil profile history.

### Optimal Crop Selection
1. Select farm and season.
2. Confirm irrigation/water availability and optional farmer preferences.
3. Recommendation generation/loading state.
4. Crop shortlist/ranking.
5. Crop detail page with supporting and limiting factors.
6. Economic comparison where data exists.
7. Yield estimate view only when a validated model/data source is active.

## 4.3 Soil dashboard behaviour

For each parameter display:
- Parameter name in English and localized language.
- Value and unit, if available.
- Status badge: Available / Partial / Not available / Stale / Source unavailable.
- Source organisation and dataset/layer.
- Source year/date.
- Map scale or resolution.
- Depth interval.
- Area coverage.
- Explanation of what the parameter means.
- Explicit note that it is map-derived and not a field/lab measurement.

Do not render an empty value as `0`, `0.0` or a green “good” indicator.

When a parameter is unavailable, show a clear explanation and still allow the farmer to continue to crop selection if the crop engine can operate with the remaining data.

## 4.4 Crop result behaviour

For each recommended crop display:
- Crop name and image/illustration from a properly licensed source.
- Suggested season and sowing window if sourced.
- Suitability category/score only if supported by the configured method.
- Why the crop was shortlisted.
- What may limit the crop.
- Water/irrigation needs.
- Economic estimate and its date/source if available.
- Yield range only if validated.
- Data completeness and caveats.

Avoid phrases like “guaranteed highest profit”, “perfect crop” or “maximum yield”. Prefer “strong candidate”, “potentially suitable” or “consider based on these conditions”.

---

# 5. OFFLINE AND LOW-CONNECTIVITY SUPPORT

The app should remain useful when internet connectivity is weak.

## When online
- Retrieve and generate soil profiles.
- Store latest profile and source metadata locally.
- Retrieve weather/market information and timestamp it.
- Generate crop recommendations.
- Synchronize farm boundary/profile changes.

## When offline
- Show saved farms and their saved boundaries.
- Show the latest cached soil profile with its generation date and source age.
- Show previously generated crop recommendations with the date and input snapshot.
- Design basic farm profile edits so they can be queued for synchronization when offline. Implement a simple, explicit sync queue in the initial mobile architecture; resolve conflicts by version/timestamp and never silently overwrite a newer server record.
- Queue new soil-profile refresh requests until connectivity returns.
- Clearly label stale cached weather/price data. Do not portray cached values as live.

Do not attempt to bundle all national soil maps into the Flutter APK. Cache only relevant tiles/overlays or generated profiles for the farmer's selected area, subject to provider licence and offline-cache permissions.

---

# 6. SECURITY, PRIVACY AND DATA GOVERNANCE

Farm boundaries and farm-level agricultural information are sensitive business data.

Requirements:
- Authenticate all private farm/profile/recommendation endpoints using the existing authentication system.
- Enforce user-level ownership/authorization on every farm and profile query.
- Do not trust `user_id` supplied by the client.
- Do not expose provider API credentials in the mobile application.
- Use HTTPS in production.
- Validate and limit polygon size/vertex count to prevent abuse.
- Rate-limit expensive GIS jobs.
- Log provider requests and job errors without logging secrets.
- Define retention and deletion behaviour for farms and profile snapshots.
- Explain location permission purpose and request it only when needed.
- Allow manual map selection when GPS permission is denied.
- Do not present farm boundary as legal cadastral/ownership evidence.
- Respect geospatial dataset licence, attribution, caching and redistribution terms.
- Keep administrative source data and farmer private data logically separated.

---

# 7. ERROR HANDLING AND EDGE CASES

## Soil Intelligence cases

1. GPS permission denied: allow manual location search/map selection.
2. GPS inaccurate: show location accuracy when available and allow manual correction.
3. Farm polygon invalid: explain and let user edit it.
4. Farm overlaps multiple soil zones: return distribution/mixed profile.
5. No dataset covers farm: save farm; show “soil map data unavailable for this location”; do not invent values.
6. Only some parameters available: generate a partial profile.
7. Provider unavailable: use another approved provider if possible; otherwise return source-unavailable status and preserve last cached profile.
8. Source licence unknown/pending: do not use it in production.
9. Farm smaller than raster cell: explain coarse regional resolution.
10. Source data old: show its year and stale warning based on parameter-specific freshness policy.
11. Different layers have different depths/years/scales: show provenance separately for each parameter.
12. Geometry outside pilot area: allow if supported by sources, otherwise clearly state coverage limitations.

## Crop Selection cases

1. Missing NPK: use map-based mode if enough other data exists; never impute arbitrary nutrient values.
2. Missing soil profile: prompt farmer to generate or select a profile; only offer region-level fallback if explicitly supported and labelled.
3. Missing weather forecast: use historical climate only if available and label it as historical.
4. Missing market data: show agronomic shortlist without economic ranking.
5. No suitable crop after hard constraints: explain why and ask about irrigation/season/constraints; do not force a recommendation.
6. Out-of-distribution region/crop: return unsupported/low-evidence state or rule-based results with caveat.
7. Conflicting sources: preserve both; apply documented provider precedence or flag conflict. Do not silently average semantically different measurements.
8. Stale market prices: show date and suppress “current price” wording.
9. No validated yield model: disable yield prediction or show “not available”; do not create an arbitrary number.
10. ML confidence is uncalibrated: do not show it as a probability of success.

---

# 8. VALIDATION AND TESTING PLAN

## 8.1 GIS/data validation

- Unit-test polygon validation and area calculations.
- Test CRS transformations.
- Test polygon/raster overlap and NoData handling.
- Test categorical class-area calculations.
- Test continuous zonal statistics.
- Test partial coverage and mixed soil zones.
- Test small farm polygons compared with large raster cells.
- Verify extracted outputs against a manually inspected set of known locations/layers.
- Verify unit conversions and depth intervals.
- Verify source metadata is returned with every parameter.
- Test provider outages and fallback behaviour.
- Ensure no unapproved/uncited layer is included in a profile.

## 8.2 Crop engine validation

- Review crop requirements with agronomically authoritative sources and, where possible, a local agronomist/KVK/SAU expert.
- Unit-test crop season filtering.
- Unit-test soil and climate rules.
- Unit-test missing-value logic so null does not become zero.
- Verify each crop explanation maps to actual input features/rules.
- Test economic calculation and currency/unit conversions.
- Test stale/missing market values.
- Compare rule-based baseline with Random Forest and XGBoost challengers.
- Use held-out districts/talukas for geographical validation.
- Use later seasons/years for temporal validation.
- Evaluate recommendation quality using top-k relevance, suitability review and where possible observed outcomes—not only generic classification accuracy.
- Evaluate yield models with MAE, RMSE, R², crop-wise and region-wise errors against historical baselines.

## 8.3 UI acceptance testing

- Farmer can create a farm without GPS permission.
- Farmer can draw, undo, reset and edit a farm polygon.
- Farmer can save multiple farms.
- Farmer can generate a partial soil profile if some layers are missing.
- Farmer can identify which data is map-derived.
- Farmer can see source date/scale and missing values.
- Farmer can continue to crop recommendations when NPK is unavailable if the supported mode permits it.
- Farmer sees a clear reason when crop/economic/yield information is unavailable.
- Cached profiles are visibly dated and labelled when offline.
- UI works on common low-end Android screen sizes and does not rely on colour alone.

---

# 9. IMPLEMENTATION PHASES AND DELIVERABLES

Antigravity should implement incrementally. Do not attempt to build all features in one unreviewed code dump.

## Phase 0 — Greenfield project foundation and GIS feasibility

There is no existing repository or application. Create the project foundation from scratch before building feature logic.

### Project structure

Create a monorepo:

```text
cropnet/
  apps/mobile/                 # Flutter Android-first application
  services/api/                # FastAPI backend
  infra/
    docker-compose.yml         # Local PostGIS and supporting services
    db/                        # DB configuration and bootstrap assets
  docs/
    architecture/
    data-sources/
    api/
  scripts/
  .env.example
  .gitignore
  README.md
```

Do not commit large, restricted or licensed source datasets. Do not put API secrets in mobile assets or source control.

### Default technology decisions

| Layer | Default | Implementation notes |
|---|---|---|
| Mobile | Flutter / Dart | Android-first; responsive UI and local persistence |
| State management | Riverpod | Consistent providers and testable state |
| Navigation | GoRouter | Central route definitions |
| Map UI | `flutter_map` behind a map abstraction | Use a tile provider whose production terms permit the expected use; do not assume public OSM raster tiles are suitable |
| Backend | Python / FastAPI | REST API under `/api/v1` |
| Validation | Pydantic | Explicit request and response schemas |
| Database | PostgreSQL + PostGIS | Farm polygon storage and spatial queries |
| ORM/migrations | SQLAlchemy 2 + Alembic | Versioned migrations |
| GIS | GeoPandas, Shapely, Rasterio, pyproj | Validate native/system dependencies |
| Authentication | Supabase Auth recommended for MVP | FastAPI verifies JWTs and derives user identity from token claims |
| Tests | pytest; Flutter test and integration_test | Test from the first phase |

Supabase is a recommended managed option, not a pre-existing dependency. Before committing to it, verify PostGIS extension availability, connection mode/pooling, row-level security and deployment cost. Keep provider/auth access behind interfaces so a different managed identity provider can be selected if needed. Never expose a Supabase service-role key or database owner credentials in Flutter.

### Required foundations

- Flutter app shell, theme, routing, localization foundation and environment-based API client.
- FastAPI app factory, settings, health route, versioned API router, CORS allowlist, structured logs and request IDs.
- PostgreSQL/PostGIS local development environment and Alembic baseline.
- Authentication and authorization dependency, or an explicitly development-only auth stub that cannot be enabled in production.
- `.env.example`, `.gitignore`, README and exact setup/run/test/migration instructions.
- CI checks for formatting, linting, tests and builds.
- Basic error-response format shared by API routes.

### GIS feasibility work

Investigate BHOOMI, ICAR-NBSS&LUP, PoCRA, SLUSI/Soil Health Card-derived mapping, Bhuvan and SoilGrids. For each candidate layer, verify actual coverage in the pilot talukas, data format, endpoint/download route, CRS, scale/resolution, depth, year, units, NoData convention, methodology, uncertainty, attribution, licence, commercial use, rate limits and caching/redistribution terms. A public map viewer or WMS display alone does not prove numerical extraction is available.

Create a coverage matrix for Maval, Mulshi, Baramati and Indapur. Mark each parameter as verified available, partial, unavailable, access restricted or not yet checked. Do not infer coverage from state/district-level announcements.

### Phase 0 deliverables and exit criteria

- New repository and monorepo structure.
- Flutter starter app and FastAPI starter service both run locally.
- API health check is reachable from Flutter.
- PostgreSQL/PostGIS starts locally and migrations run.
- Auth/ownership approach is documented and tested at a basic level.
- README allows a new developer to reproduce the environment.
- GIS source/layer catalogue, pilot coverage matrix and licensing risk register exist.
- At least one permitted sample extraction is demonstrated, or a clearly documented blocker/fallback is recorded.
- No feature is represented as complete merely because a placeholder screen exists.

## Phase 1 — Farm mapping and spatial storage

Tasks:
- Implement farm creation/list/detail/update.
- Implement map selection and GPS support in Flutter.
- Implement polygon drawing/editing and area display.
- Validate geometry in FastAPI/PostGIS.
- Save multiple farms per user.
- Add authorization tests.

Deliverables:
- Working farm registration and boundary management.
- Database migrations.
- API and UI tests.

## Phase 2 — GIS provider integration

Tasks:
- Implement provider interfaces.
- Configure approved BHOOMI and/or regional layers.
- Add source/layer metadata registry.
- Implement raster/vector extraction.
- Implement spatial intersections and coverage calculations.
- Implement per-parameter provenance and missing statuses.

Deliverables:
- Repeatable extraction for verified pilot locations.
- GIS unit/integration tests.
- Source attribution and licence records.

## Phase 3 — Soil profile service and dashboard

Tasks:
- Generate versioned soil profiles.
- Store profile snapshots and individual parameter metadata.
- Implement soil-profile APIs.
- Implement Flutter soil dashboard and parameter detail screens.
- Implement partial/no-data/stale/error states.
- Add cached profile display.

Deliverables:
- End-to-end location-based soil intelligence flow.
- No fabricated values.
- Source and resolution shown in the UI.

## Phase 4 — Agronomic crop knowledge base and rule engine

Tasks:
- Build structured crop catalogue for the pilot region.
- Collect source-backed soil, season, water and climate requirements.
- Implement candidate crop generation and feasibility filtering.
- Implement transparent suitability scoring.
- Implement map-based mode for missing NPK.
- Generate reason codes and farmer-readable explanations.

Deliverables:
- Reproducible crop shortlist from a soil profile and seasonal context.
- Traceable agronomic sources.
- Missing-data-aware scoring.

## Phase 5 — Weather and market integration

Tasks:
- Integrate approved weather provider(s).
- Distinguish observations, historical normals, forecasts and seasonal outlooks.
- Integrate available official/approved mandi price data.
- Add price freshness and unit/grade/market handling.
- Add estimated cultivation cost only from sourced/configured data.
- Implement economic ranking separately from agronomic suitability.

Deliverables:
- Climate-aware crop ranking.
- Economic ranking only when inputs are sufficient.

## Phase 6 — ML benchmark and optional yield prediction

Tasks:
- Audit candidate Hugging Face model and dataset licences/provenance.
- Compare transparent rule baseline, Random Forest and XGBoost.
- Ensure features align with map-only availability.
- Use district/taluka and temporal holdouts.
- Train custom yield model only if suitable labelled data exists.
- Deploy model versioning, evaluation reports and rollback.

Deliverables:
- Evidence-based model selection report.
- Reproducible evaluation.
- Production model only if it improves reliable performance and passes validation.

## Phase 7 — Offline, localization and hardening

Tasks:
- Cache farm profiles and recommendation snapshots.
- Implement offline and resync behaviour.
- Add Marathi/Hindi/localized labels and explanations.
- Validate on low-end devices and poor connectivity.
- Complete security, performance and licence review.

Deliverables:
- Pilot-ready implementation with documented limitations.

---

# 10. RECOMMENDED GREENFIELD CODE ORGANIZATION

Create this as the greenfield starting structure. Keep it modular, testable and limited to the two features and their essential shared foundations.

Possible FastAPI backend modules:

```text
backend/
  app/
    api/
      v1/
        farms.py
        soil_profiles.py
        soil_layers.py
        crop_recommendations.py
        crops.py
    core/
      config.py
      security.py
    db/
      session.py
      models/
        farm.py
        soil_source.py
        soil_layer.py
        soil_profile.py
        crop.py
        crop_recommendation.py
    schemas/
      farm.py
      soil_profile.py
      crop_recommendation.py
    services/
      farm_service.py
      soil_intelligence/
        provider_registry.py
        source_catalog.py
        geometry_service.py
        raster_extraction.py
        vector_extraction.py
        profile_builder.py
        provenance.py
      crop_intelligence/
        crop_catalog.py
        season_service.py
        agronomic_rules.py
        suitability_engine.py
        economic_ranker.py
        yield_service.py
      external_data/
        weather_provider.py
        market_provider.py
    tasks/
      soil_profile_jobs.py
      crop_recommendation_jobs.py
    tests/
      test_geometry.py
      test_soil_extraction.py
      test_soil_profile.py
      test_crop_rules.py
      test_crop_recommendations.py
```

Possible Flutter feature organization (adapt to current state management/routing):

```text
lib/
  features/
    farms/
      data/
      domain/
      presentation/
    soil_intelligence/
      data/
      domain/
      presentation/
    crop_recommendations/
      data/
      domain/
      presentation/
  shared/
    maps/
    localization/
    widgets/
```

Keep provider credentials, source URLs requiring authentication and raw dataset storage locations on the backend.

---

# 11. PERFORMANCE AND DEPLOYMENT CONSIDERATIONS

- Large raster operations should run as background jobs where needed.
- Cache source metadata and safe-to-cache data, subject to licence.
- Cache completed soil profiles by farm/profile version; do not repeatedly extract unchanged layers on every page load.
- Recompute when farm geometry, source layer version or profile algorithm changes.
- Avoid downloading entire datasets for every request.
- Use spatial indexes in PostGIS and appropriate raster tiling/COG strategies where permitted.
- Monitor extraction time, provider failures, missing-data rate and cost.
- Add timeouts, retries with backoff and circuit-breaker behaviour for external providers.
- Keep a provider-health status visible to administrators.
- Avoid logging exact farm coordinates in general application logs unless operationally necessary and access-controlled.

---

# 12. ADMIN / OPERATIONS REQUIREMENTS

Provide a simple internal/admin capability (or documented configuration workflow) to:
- Add/deactivate data sources and layers.
- Record licence and attribution information.
- Update source year and metadata.
- View layer coverage and last successful extraction.
- Inspect provider errors.
- View farms with incomplete profiles in aggregate without exposing unnecessary personal data.
- Update crop rules/catalogue and agronomic references.
- Enable/disable a crop, layer or model version.
- Review model evaluation before enabling a production model.

Changes to crop rules and source configurations should be versioned and auditable.

---

# 13. ACCEPTANCE CRITERIA — WHAT “DONE” MEANS

## Soil Intelligence is complete when:

1. A farmer can create a farm using GPS or manual map selection.
2. A farmer can draw and save a valid polygon boundary.
3. The backend identifies the location using configured boundary data or marks it unconfirmed.
4. The backend queries at least one verified and permitted soil-data source for the pilot area.
5. The system extracts actual available soil attributes using vector/raster data, not screenshots.
6. Mixed soil zones and partial coverage are represented correctly.
7. Missing data stays null and has an explicit status.
8. Every returned parameter includes source and available metadata.
9. The UI states that the profile is map-derived and not laboratory-verified.
10. A farm profile can be saved, versioned and retrieved.
11. Provider failure and no-coverage states do not crash the application.
12. Tests cover spatial extraction, provenance, authorization and missing-data handling.

## Optimal Crop Selection is complete when:

1. It consumes a selected farm's soil profile.
2. It knows which input parameters are missing, stale or available.
3. It supports a map-based mode that does not require NPK.
4. It uses a documented crop catalogue for supported crops/seasons/regions.
5. Candidate filtering and suitability scoring are explainable and traceable.
6. It incorporates seasonal and climate data only with source/time context.
7. Economic ranking is separate and only appears when market/cost data is sufficient.
8. Missing market data does not block agronomic recommendations.
9. Yield prediction is disabled unless a validated model and suitable inputs are available.
10. Each recommendation contains supporting reasons, limitations and data completeness.
11. Outputs are persisted with input and algorithm/model versions.
12. Tests cover missing data, rules, market freshness, spatial/temporal model validation and authorization.

---

# 14. RESEARCH LINKS AND SOURCE REGISTER

These are candidate official or model resources identified during product planning. Antigravity must re-check their current status, exact layer availability, access requirements, terms and licences before integrating them.

## Soil and geospatial information

1. **ICAR-NBSS&LUP BHOOMI Geoportal** — https://bhoomigeoportal-nbsslup.in/
2. **ICAR-NBSS&LUP main website** — https://icar-nbsslup.org.in/
3. **Maharashtra PoCRA GIS** — https://gis.mahapocra.gov.in/
4. **Government of India / PIB release on Maharashtra soil fertility maps (11 March 2025)** — https://www.pib.gov.in/Pressreleaseshare.aspx?PRID=2110419&lang=2&reg=48
5. **ISRIC SoilGrids** — https://soilgrids.org/
6. **Government Soil Health Card portal** — https://soilhealth.dac.gov.in/
7. **ISRO Bhuvan** — https://bhuvan.nrsc.gov.in/

## Crop recommendation model candidate

8. **Sheshank2609 Maharashtra crop recommendation repository** — https://huggingface.co/Sheshank2609/crop-recommendation-system

Treat any accuracy/performance figures on a model card as author-reported until independently reproduced. Verify licence, files, feature order, training data, evaluation methodology and commercial rights.

## Weather and market data candidates

9. **India Meteorological Department** — https://mausam.imd.gov.in/
10. **e-NAM** — https://enam.gov.in/

Verify that APIs/downloads are officially available and that their terms allow the intended application. A website's existence does not imply a public API.

---

# 15. FINAL PRODUCT PRINCIPLES

CropNet should be built around these principles:

1. **Evidence before prediction:** use the best available mapped data and preserve its provenance.
2. **No false precision:** spatial maps are not field laboratory measurements.
3. **Missing means unknown:** never convert missing nutrient information to zero or an invented value.
4. **Agronomy before algorithm:** crop rules must be supported by authoritative references; ML is evaluated against a transparent baseline.
5. **Suitability before profitability:** determine agronomic feasibility first, then evaluate economics.
6. **Explain every recommendation:** show why a crop was shortlisted and what could make it unsuitable.
7. **India-first implementation:** prioritise Maharashtra data, local crops, seasons, languages and farmer constraints.
8. **Modular future expansion:** laboratory tests, Soil Health Card imports and physical measurements can later supplement or replace map-derived estimates without rebuilding the crop engine.

**Expected final experience:** A farmer selects a farm on a map, CropNet generates a transparent location-based soil profile from verified available sources, and the farmer receives a reasoned shortlist of crops for the selected season. Where the data is incomplete, CropNet says so clearly rather than pretending to know.
