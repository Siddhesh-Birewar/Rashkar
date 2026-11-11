# RASHKAR Engine Recovery & Parity Report (Phase 3)

**Branch**: `feat/rashkar-additive-integration`  
**Reference Source Commit**: `remotes/origin/yeild-and-heat-risk-feature` (`7b5641e3dfbea99baf7bc350f0fa9e628a1e8b80`)  
**Host Base Commit**: `c12d0a2`  
**Date**: 2026-11-11

---

## 1. Recovery Scope & Module Mapping

All calculation, phenological staging, biophysical risk screening, and diversification engines from `7b5641e` were recovered into the isolated `cropnet.services.api.app.rashkar` package without altering any existing CropNet agronomic rule, endpoint contract, or model schema:

| Capability | `7b5641e` Source Module | CropNet Recovered Module |
|---|---|---|
| Physics WBGT & VPD | `services/wbgt_solver.py` | `services/api/app/rashkar/engines/wbgt_solver.py` |
| Thermal Indices (HI, UTCI, Lapse, Vulnerability) | `services/thermal_indices_service.py` | `services/api/app/rashkar/engines/thermal_indices.py` |
| ML Forecast Pipeline (XGBoost + LSTM + RF) | `ml/heat_ml_pipeline.py` | `services/api/app/rashkar/engines/heat_ml_pipeline.py` |
| Forecast Scheduler Cache | `services/forecast_scheduler.py` | `services/api/app/rashkar/engines/forecast_scheduler.py` |
| Worker Heat Engine | `services/worker_heat_engine.py` | `services/api/app/rashkar/engines/worker_heat_engine.py` |
| Crop Stage Service | `services/crop_stage_service.py` | `services/api/app/rashkar/engines/crop_stage_service.py` |
| Crop Heat Engine | `services/crop_heat_engine.py` | `services/api/app/rashkar/engines/crop_heat_engine.py` |
| Yield Risk Engine + DES APY Dataset | `services/yield_risk_engine.py` + `maharashtra_apy_canonical.csv` | `services/api/app/rashkar/engines/yield_risk_engine.py` + `services/api/app/rashkar/data/maharashtra_apy_canonical.csv` (17,923 lines) |
| Extra Income Catalogue, Feasibility & Financials | `services/{income_knowledge_catalog,opportunity_feasibility_engine,income_financial_service,income_engine}.py` | `services/api/app/rashkar/engines/income.py` (re-exporting CropNet's identical `services/income/*` modules verified with empty schema diff) |
| Reference Knowledge Seeder | `db/init_db.py` | `services/api/app/rashkar/seed.py` (38 crops, stages, thresholds, advisories, opportunities; demo seed omitted) |

---

## 2. Side-by-Side Parity Results (`test_engine_parity.py`)

Side-by-side comparison tests ran directly against the read-only `7b5641e` reference package in an isolated in-memory SQLite fixture on identical inputs:

1. **WBGT, Dew Point, NOAA Heat Index, UTCI, Topographic Lapse & Vulnerability Scores (`test_wbgt_and_thermal_indices_exact_parity`)**:
   - Tested across four meteorological regimes `(38.5°C/42% RH, 33.0°C/78% RH, 29.5°C/55% RH shade, 43.2°C/18% RH)` plus lapse downscaling `(37.4°C, 560m vs 540m)`, worker strain score, and crop heat vulnerability score.
   - **Result**: Exact equality (`==`) across every WBGT estimate, dew point, Heat Index, UTCI approximation, lapse adjustment, strain score, and crop vulnerability score.

2. **Worker Heat 0–6h Engine (`test_worker_heat_engine_parity_and_missing_weather_honesty`)**:
   - Tested two full profiles across identical 7-hour weather feeds: (`heavy` workload / `standard_work_clothes` / acclimatised / `direct_sun` / `4.0h`) and (`moderate` / `impermeable_vapor_barrier` / unacclimatised / `partial_shade` / `8.5h`).
   - **Result**: Exact match across `clothing_cav_c`, `screening_threshold_c`, `max_wbgt_effective_c`, `max_hazard_level_in_window`, `threshold_difference_c`, `threshold_comparison_state`, `shift_exceeds_forecast_coverage`, `personalized_heat_strain_score["score_0_100"]`, and all 7 hourly projections (`wbgt_estimated_c`, `wbgt_effective_c`, `heat_index_c`, `utci_c`, `hazard_level`, `exceeds_screening_threshold`, `work_rest_cycle`). Verified `RashkarWorkerHazardAuditLogModel` persistence (`2` audit rows).

3. **Crop Stage & Crop Heat Engine (`test_crop_stage_and_crop_heat_engine_parity_and_no_active_crop`)**:
   - Tested DAS stage inference (DAS 20, 40, 60, farmer confirmation `R1_FLOWERING`, and expired season DAS 140) and full soybean `R3_POD_FILLING` heat evaluation (`tmax=38.5°C`, `tmin=24.0°C`, `RH=35%`).
   - **Result**: Exact match on `growth_stage_code` (`R3_POD_FILLING`), `critical_tmax_threshold_c` (`35.0`), `daytime_heat_stress_level`, `overall_crop_heat_risk`, `hours_above_critical`, `warm_night_respiration_hazard`, `warm_night_penalty_score`, `cumulative_heat_units_gdd`, `personalized_crop_vulnerability_score["score_0_100"]`, `recommended_interventions` IDs, and 4-day `daily_outlook` tuples, plus `peak_vpd_kpa` and `RashkarCropHeatLogModel` persistence. Verified `CROP_SPECIES_PHYSIOLOGY` covers >=12 crops including `rice`.

4. **Yield Risk DES APY Baseline & 5-Dimension Screening (`test_yield_risk_apy_parity_and_zero_fabrication`)**:
   - Tested `calculate_apy_district_baseline` for `(Pune, soybean)`, `(Pune, cotton)`, `(Pune, gram)`, and `(Sindhudurg, cotton)` statewide fallback, plus `"chickpea"` alias normalization and full 5-dimension `assess_yield_risk` for `soybean` (Pune/Baramati, DAS 42, 14 dry days, Clay Loam pH 7.4).
   - **Result**: Exact match on `status`, `geographical_unit`, `sample_seasons_count`, `historical_mean_t_ha`, `historical_median_t_ha`, `historical_p10_t_ha`, `historical_p90_t_ha`, `min_recorded_t_ha`, `max_recorded_t_ha`, `historical_std_dev`, all 5 `risks` `(risk_dimension, risk_level)` pairs, and `ml_prediction_gate["farm_level_supervised_model"] == "LOCKED_PENDING_CCE_LABELS"`. Added `historical_p25_t_ha` monotonic quartile check (`P10 <= P25 <= Median <= P90`).

5. **Extra Income Catalogue, Feasibility & Financial Simulator (`test_extra_income_engine_parity`)**:
   - Verified catalog parity (`len(EXTENDED_OPPORTUNITY_CATALOG)` matches `7b5641e`), exact ranking/suitability/category parity on ₹0-budget farmer (`OPP_FIELD_BUND_DRUMSTICK_01` etc.), non-disqualification for `age_range="above_65"`, exact CAPEX/OPEX/net profit/break-even/12-month cash flow parity on `OPP_OSMANABADI_GOAT_10_PLUS_1` at ₹90,000 budget, and multi-enterprise comparison.

---

## 3. Security & Zero-Fabrication Remediations (Host Integration Layer)

While engine mathematics preserves 1:1 fidelity when supplied inputs match `7b5641e`, host adapters and endpoints eliminate every mock/demo fallback from `7b5641e`:

1. **Authentication & Ownership**: All `/api/v1/rashkar/**` endpoints enforce Supabase/CropNet `get_current_user` (`401` unauthenticated when bypass is off) and delegate farm ownership checks to `_get_farm_and_verify_owner` (`403` cross-user, `404` missing farm, `422` invalid UUID). `"farmer_demo_01"` and demo farm seeding were removed completely.
2. **No Default Soybean Cycle**: When a registered CropNet farm has no active row in `rashkar_crop_cycles`, Crop Heat and Yield Risk explicitly return `status="NO_ACTIVE_CROP"`, `has_active_crop=False`, `needs_crop_registration=True` (unless an explicit transient `?crop_code=...` pre-sowing screening preview is requested on Yield Risk, marked `"screening_mode": "PRE_SOWING_PREVIEW"`).
3. **No Synthetic Weather Fabrication**: `adapters/weather.py` queries live Open-Meteo (`https://api.open-meteo.com/v1/forecast`, 6.0s timeout, 10-min TTL coordinate cache) combined with stored `FarmClimateSummaryModel.annual_rainfall_mm`. On outage/timeout, Worker Heat, Crop Heat, and Yield Risk return `WEATHER_UNAVAILABLE` with `null` measurements rather than diurnal sine approximations.
4. **No Synthetic Soil Fabrication**: `adapters/soil.py` resolves confirmed `SoilTestReportModel`/`SoilMeasurementModel` first, followed by `FarmSoilProfileModel`/`SoilParameterModel` (excluding synthetic/unavailable entries), and preserves `None` for any unmeasured parameter.
5. **No Fake APY Yield Mean**: Missing/unreadable `maharashtra_apy_canonical.csv` returns `status="unavailable"` with `None` metrics instead of a hardcoded scalar fallback (`1.42` / `1.25 t/ha`).

---

## 4. Database Schema & Migration `010_rashkar_tables`

- Revision: `010_rashkar_tables` (`down_revision = "009_government_schemes"`).
- Adds 12 additive `rashkar_*` tables with `farms.id` `ON DELETE CASCADE` foreign keys and guarded Supabase RLS policies (`_auth_schema_exists` check).
- Verified via `alembic -c infra/db/alembic.ini heads` -> `010_rashkar_tables (head)` and round-trip `009 -> 010 -> 009 -> 010` SQLite migration tests.

---

## 5. Phase 3 Verification Outputs

- **RASHKAR Suite (`pytest "cropnet/services/api/tests/rashkar" -v --tb=short`)**:
  `21 passed, 197 warnings in 1.71s` (0 failed, 0 skipped) across `test_engine_parity.py` (5), `test_migration_010.py` (5), `test_rashkar_api_security.py` (4), `test_rashkar_e2e_workflows.py` (4), `test_seed_idempotency.py` (3).
- **Host Core Regression (`pytest` across `test_farms_phase1.py`, `test_heat_risk_farm.py`, `test_heat_risk_and_crop_doctor.py`, `test_security_remediation.py`, `test_government_schemes.py`, `test_weather_phase3.py`, `test_agriculture_intelligence_phase5_1.py`)**:
  `49 passed, 294 warnings in 7.71s` (0 failed, 0 skipped).
- **Alembic Head (`cd cropnet && alembic -c infra/db/alembic.ini heads`)**:
  `010_rashkar_tables (head)`.
