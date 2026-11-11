# Phase 0 Audit — Additive RASHKAR Integration into CropNet AI

**Audit Date:** 2026-11-11  
**Integration Branch:** `feat/rashkar-additive-integration` (branched from `integration/figma-frontend-web` at commit `c12d0a2`)  
**Recovery Backup Branch:** `backup/pre-rashkar-integration-20261111` (pinned at `c12d0a2`)  
**Original RASHKAR Source:** `remotes/origin/yeild-and-heat-risk-feature` at commit `7b5641e3dfbea99baf7bc350f0fa9e628a1e8b80`

---

## 1. Purpose & Non-Destructive Preservation Contract

CropNet AI (`cropnet/`) is the **host application and source of truth** for authentication, authorization, farmer/farm entities, geometry boundaries, soil intelligence, soil laboratory OCR, water intelligence, satellite vegetation monitoring, crop knowledge catalog, crop doctor, agricultural decision engine & chatbot, weather/climate normals, government schemes, and Flutter mobile client.

All RASHKAR capabilities (**Worker Heat Risk**, **Crop Heat Risk**, **Yield Intelligence**, **Extra Income Diversification**) are integrated as an **additive module**:
- Backend isolated under `cropnet/services/api/app/rashkar/` and mounted under `/api/v1/rashkar/...`.
- Database schema changes restricted exclusively to additive RASHKAR tables (`infra/db/migrations/versions/010_rashkar_tables.py`), referencing `farms.id` without altering existing CropNet columns or tables.
- Frontend isolated under `cropnet/apps/web/features/rashkar/` and `cropnet/apps/web/app/(app)/rashkar/...`, linked via **one additive entry** in `cropnet/apps/web/components/app-shell.tsx`.
- Existing CropNet routes (`/heat-risk`, `/income`, `/farms/*`, `/soil`, `/weather`, `/water`, `/vegetation`, `/health`, `/advisory`, `/assistant`, `/crop-doctor`, `/schemes`, `/crops`, `/history`, `/profile`, `/settings`) and `apps/mobile` remain untouched.

---

## 2. Host Repository Inventory (`HEAD` = `c12d0a2`)

### 2.1 Backend Architecture (`cropnet/services/api/app/`)
- **Entry Point (`main.py`)**: FastAPI app mounting `api_router` (`api/v1/router.py`), `soil_reports_router`, `water_router`, and `satellite_router` at `/api/v1`.
- **Existing API Routers (`api/v1/router.py`)**: `health`, `farms`, `farm_health`, `soil`, `crops`, `agriculture`, `schemes`, `heat_risk`, `crop_doctor`, `income`.
- **Authentication & Ownership (`core/security.py`, `api/v1/endpoints/farms.py`)**:
  - `get_current_user` validates Supabase Bearer tokens via `/auth/v1/user`.
  - Development `X-Dev-User-Id` header bypass is strictly fail-closed unless `ALLOW_DEV_AUTH_BYPASS=True` in non-production (`validate_cors_security` rejects it in production). Missing auth returns `401 Unauthorized`.
  - Farm ownership is enforced via `_get_farm_and_verify_owner(farm_id, current_user, db)` checking `farm["owner_id"] != current_user.user_id` -> `403 Forbidden`.
- **Database & Migrations (`core/database.py`, `infra/db/migrations/`)**:
  - Sync SQLAlchemy engine (`_sync_db_url = settings.SYNC_DATABASE_URL or "sqlite:///./cropnet_dev.db"`).
  - Shared `Base` defined in `models/soil_and_farm.py`.
  - Alembic head is `009_government_schemes` (`001_initial_schema` -> ... -> `009_government_schemes`). Migrations inspect schema and conditionally configure PostgreSQL RLS only when Supabase `auth` schema exists.
- **Canonical Farm, Soil, Weather & Crop Models**:
  - `FarmModel` (`farms` table): `id` (`String(36)` PK), `owner_id` (`String(36)`), `name`, `village`, `taluka`, `district`, `state`, `irrigation_type`, `water_source`, `geometry_geojson`, `calculated_area_hectares`, `calculated_area_acres`, `centroid_latitude`, `centroid_longitude`.
  - `FarmSoilProfileModel` & `SoilParameterModel` & `SoilTestReportModel`/`SoilMeasurementModel` (SoilGrids + verified lab measurements).
  - `FarmWeatherSnapshotModel` & `FarmClimateSummaryModel` + `WeatherService` (OpenWeather current + 5-day/3-hour forecast + NASA POWER 30-year climate normals).
  - `CropCatalogModel` + related requirements tables (`CropKnowledgeService`).
- **Existing Partial RASHKAR Modules on `c12d0a2`**:
  - **Income (`services/income/` & `endpoints/income.py`)**: `engine.py`, `catalog.py`, `feasibility.py`, `financial.py`, `schemas/income.py` match `7b5641e` business logic (including age, `work_preference`, `payback_horizon`, `family_management_role`, 5 feasibility categories, 6 plain-language Q&A, 3-scenario financial engine, 12-month cash flows). However, `endpoints/income.py` only exposes 5 stateless endpoints and omits DB resource profile persistence (`GET/PUT /farms/{farm_id}/profile`), farm-context prefill discovery (`POST /farms/{farm_id}/discover`), and saved plans (`POST/GET /farms/{farm_id}/plans`).
  - **Heat Risk (`services/heat_risk/` & `endpoints/heat_risk.py`)**: `wbgt_solver.py` (177 lines) and `thermal_indices.py` (325 lines) match `7b5641e` calculations. However, `services/heat_risk/engine.py` (415 lines) and `endpoints/heat_risk.py` (182 lines) are simplified wrappers omitting major `7b5641e` capabilities (listed in Section 3).
  - **Yield Intelligence**: Completely absent from `c12d0a2` (`yield_risk_engine.py`, canonical APY CSV, schemas, endpoints, DB logs).

### 2.2 Frontend Architecture (`cropnet/apps/web/`)
- **Stack**: Next.js `16.4.6` (React `19.3.1`), Tailwind CSS v4 (`@theme` tokens in `app/globals.css`: `--color-forest: #1b5e20`, `--color-leaf: #2e7d32`, `--color-accent: #e65100`, `--color-soil: #5d4037`, `--color-canvas: #f9fbf9`, `--color-ink: #17351e`, `--color-muted: #68786b`, `--color-line: #dfe8e0`), Radix UI primitives (`badge`, `bottom-sheet`, `button`, `card`, `dialog`, `input`, `select`, `tabs`), Leaflet.
- **Navigation & Contexts**:
  - `components/providers.tsx` wraps `<AuthProvider>` and `<FarmProvider>`.
  - `lib/auth-context.tsx` manages Supabase session token (`cropnet_access_token`) + local dev fallback header (`X-Dev-User-Id`).
  - `lib/farm-context.tsx` holds `farms`, `selectedFarm`, `selectedFarmId`, `setSelectedFarmId`, `refreshFarms`.
  - `components/app-shell.tsx` provides desktop sidebar (`primaryNav` + `intelligenceNav`), tablet icon rail, sticky top bar with `FarmSelector`, mobile bottom nav + `MoreSheet`, and floating `<CropNetChatbot />`.
  - Note: Existing `app/(app)/income/page.tsx` is a static placeholder using `IntelligenceWorkspace`, and `app/(app)/heat-risk/page.tsx` binds to `/api/v1/heat-risk/*`. Both remain unmodified.

---

## 3. Original RASHKAR (`7b5641e`) Inventory & Delta vs. `c12d0a2`

| Capability | Original RASHKAR (`7b5641e`) Modules | Status on `c12d0a2` | Missing / Diverged Items to Recover & Adapt |
| --- | --- | --- | --- |
| **Worker Heat Risk** | `worker_heat_engine.py` (494L), `wbgt_solver.py` (177L), `thermal_indices_service.py` (325L), `forecast_scheduler.py`, `heat_ml_pipeline.py` (307L), `schemas/worker_heat.py`, `WorkerHazardAuditLogModel`, `weather_service.py` | Partial (`wbgt_solver.py`, `thermal_indices.py`, simplified `WorkerHeatEngine.assess` in `heat_risk/engine.py`) | 0–6h forecast projection timeline (`hourly_projections`), CAV clothing adjustment tiers (`woven_double_layer`, `coveralls_protective`, `impermeable_vapor_barrier`), `BELOW`/`AT_THRESHOLD`/`ABOVE` threshold messaging, shift-vs-6h-coverage check (`shift_exceeds_forecast_coverage`), `ForecastGridCache` 30-min cadence & elevation lapse downscaling, NIOSH hydration limit guidance, emergency exhaustion vs stroke triage & helpline numbers (`108` / `1800-180-1551`), personalized 0–100 strain score, `HeatMLPipeline` (XGBoost/RF/LSTM benchmark vs Liljegren), and pseudonymised `WorkerHazardAuditLogModel`. |
| **Crop Heat Risk** | `crop_heat_engine.py` (788L), `crop_stage_service.py` (108L), `crop_knowledge.py` models/seeds, `schemas/crop_heat.py`, `CropHeatAssessmentLogModel` | Partial (11 hardcoded crops in `CROP_SPECIES_PHYSIOLOGY`, simplified `CropHeatEngine.assess`, 4 generic intervention strings) | Farm/plot/active crop cycle linking, `CropStageService` DAS calculation + `EXPIRED` season detection (`das > max_das + 15`) with intervention suppression, persistent `farmer_confirmed_stage` override, DB stage/threshold registry + 38 canonical Maharashtra crops, physiological mechanisms per stage, bilingual EN/MR ICAR-sourced crop & irrigation-specific interventions (drip vs furrow), 4-day daily outlook (`daily_outlook`), `personalized_crop_vulnerability_score`, topographic downscaling, and persistent `CropHeatAssessmentLogModel` history. |
| **Yield Intelligence** | `yield_risk_engine.py` (476L), `schemas/yield_risk.py` (89L), `endpoints/yield_risk.py` (52L), `maharashtra_apy_canonical.csv` (17,923 lines / 17,916 DES records), `YieldAssessmentLogModel` | **Absent** | Entire engine, canonical APY dataset, schema, endpoints, and DB audit log missing. Note: Plot-level ML tonnage prediction is **explicitly gated/disabled** (`REQUIRES_FARM_HARVEST_LABELS` / `LOCKED_PENDING_CCE_LABELS`) because verified farm-level CCE harvest labels do not exist. Authentic scope = District Historical APY Benchmark (1997–2021 DES stats with `N < 3` statewide fallback) + 5-dimension biophysical stress screening + edaphic suitability + advisories. |
| **Extra Income** | `income_engine.py`, `income_knowledge_catalog.py`, `opportunity_feasibility_engine.py`, `income_financial_service.py`, `schemas/income.py`, `db/models/income.py` (`FarmerResourceProfileModel`, `IncomeOpportunityModel`, `IncomeScenarioModel`, `SavedIncomePlanModel`), `endpoints/income.py` (327L) | Partial (domain calculation modules exist; DB persistence & personalized farm discovery endpoints absent) | `GET/PUT /farms/{farm_id}/profile` (persisted `FarmerResourceProfileModel` prefilled from real farm area/water/soil/active crop), `POST /farms/{farm_id}/discover` (5 feasibility categories, 6 Q&A, age/work-preference/payback-horizon advisories), `POST/GET /farms/{farm_id}/plans` (`SavedIncomePlanModel`), deterministic scenario persistence (`IncomeScenarioModel`). |
| **Active Crop & Reference Tables** | `db/models/farm.py` (`FarmPlotModel`, `CropCycleModel`), `db/models/crop_knowledge.py` (`CanonicalCropMasterModel`, `CropStageReferenceModel`, `AgronomicThresholdRegistryModel`, `AgronomicAdvisoryCatalogueModel`) | **Absent** (`CropNet` stores farm geometry in `farms`, static catalog in `crop_catalog`) | Additive RASHKAR crop-context tables (`rashkar_crop_cycles`, etc.) and seedable RASHKAR agronomic stage/threshold/advisory reference tables keyed to CropNet `farms.id` (`String(36)`). |

---

## 4. Security, Ownership, & Data-Honesty Remediations Required During Adapter Integration

Inspection of `7b5641e` identified non-negotiable gaps that **must not** be carried into CropNet, and **must** be fixed in the CropNet adapter/endpoint layer (while leaving pure engine formulas, constants, and thresholds untouched):

1. **Missing Authentication & Demo User Fallbacks**:
   - `7b5641e` had no auth dependency and fell back to `"farmer_demo_01"`.
   - **Remediation**: Every RASHKAR endpoint MUST require `current_user: CurrentUser = Depends(get_current_user)`. Every farm-scoped endpoint MUST call CropNet's ownership check (`_get_farm_and_verify_owner`) returning `404` when missing and `403` when owned by another user. No `"farmer_demo_01"` or `DEV_USER_ID` silent fallback.
2. **Fabricated Active Crop Cycle Defaults**:
   - `7b5641e/services/crop_heat_engine.py` line 194 invented a `"soybean"` cycle (`2026-06-15`) when none existed; `7b5641e/endpoints/yield_risk.py` line 37 fell back to `"soybean"` / `2024-06-25`.
   - **Remediation**: If the farm has no active RASHKAR crop cycle (or explicit crop selection is absent), return an explicit structured **"no current crop" / `MISSING_ACTIVE_CROP` / `needs_crop_registration`** state and invite the farmer to register/select a crop cleanly. Never fabricate soybean!
3. **Synthetic Live Weather Fallback**:
   - `7b5641e/services/weather_service.py` lines 148–190 synthesized `"IMD 0.25° Gridded Climatological Normal Calibration"` hourly data if Open-Meteo failed; `openweather.py` also has `_generate_forecast_fixture`.
   - **Remediation**: Live CropNet RASHKAR weather adapter MUST query live Open-Meteo (for 0–6h radiation/wind/temp/RH/dew-point) and/or CropNet `WeatherService` (OpenWeather + NASA POWER). When live forecast providers fail and no `weather_hourly_override` was explicitly supplied (for deterministic unit/parity tests), return explicit **unavailable / provider error** state cleanly without substituting fabricated temperatures as live forecasts.
4. **Hardcoded APY CSV Fallback Stats**:
   - `7b5641e/services/yield_risk_engine.py` lines 96–113 returned `mean=1.42, p10=0.85, p90=2.10` if CSV wasn't found.
   - **Remediation**: Bundle `maharashtra_apy_canonical.csv` in `cropnet/services/api/app/rashkar/data/maharashtra_apy_canonical.csv`, verify path & loading on startup/tests, and return explicit `APY_BASELINE_UNAVAILABLE` status if missing/unmatched rather than inventing yields.
5. **Synthetic Soil Profile Labeling**:
   - CropNet `FarmSoilProfileModel` / `SoilParameterModel` / confirmed `SoilTestReportModel` measurements are adapted into RASHKAR's `UnifiedSoilProfile`, distinguishing `LABORATORY_VERIFIED` vs `MAP_DERIVED_ESTIMATE` vs unavailable/unsampled (`SoilGrids` / unmeasured). Keep pure engine support for explicit `soil_profile_override` in parity tests.

---

## 5. Pre-Integration Baseline Verification (`c12d0a2` -> `feat/rashkar-additive-integration`)

- **Frontend (`cropnet/apps/web`)**:
  - `npx tsc --noEmit`: Passed (exit code `0`).
  - `NODE_ENV=production npm run build`: Passed (exit code `0`, Next.js `16.4.6` Turbopack compiled cleanly, 26 routes generated).
- **Backend Core Offline Suites Executed Prior to RASHKAR Changes**:
  - Core API + Security + Farms + Heat/CropDoctor + Schemes + Crops + Weather (`test_heat_risk_farm.py`, `test_heat_risk_and_crop_doctor.py`, `test_security_remediation.py`, `test_farms_phase1.py`, `test_government_schemes.py`, `test_crops_phase4.py`, `test_weather_phase3.py`): **39 passed** (`0 failed`).
  - Agricultural Intelligence + Agronomic Correctness (`test_agriculture_intelligence_phase5_1.py`, `test_agronomic_correctness_remediation.py`): **81 passed** (`0 failed`).
  - Note: Full unscoped suite (`pytest cropnet/services/api/tests`) contains live-network/LLM suites (`test_live_e2e_validation.py`, `test_copernicus_live_provider.py`, `test_ai_intelligence_benchmark_phase5_8_2.py`, SoilGrids WCS external calls) that block on external HTTP/Ollama connections in offline execution; scoped offline/mocked verification plus RASHKAR parity & security tests will be run cleanly in Phases 3 and 5.
