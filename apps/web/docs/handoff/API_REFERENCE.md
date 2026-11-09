# CropNet AI — API Reference

Base URL: `http://127.0.0.1:8000` in local development; configure
`NEXT_PUBLIC_API_BASE_URL` for deployed environments.

**Authoritative machine-readable contract:** [`openapi.json`](./openapi.json)
(84 operations, 72 paths, 128 schemas). This document summarises the groups and
the important request/response shapes; use `openapi.json` for exact fields.

Auth: `Authorization: Bearer <Supabase access token>` unless marked **Public**.
Errors: FastAPI `{"detail": "..."}` (string or validation array).

---

## Health

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/api/v1/health` | Public | Service status |

## Farms

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/api/v1/farms` | Bearer | List caller's farms |
| POST | `/api/v1/farms` | Bearer | Create farm (`name`, `taluka`, `geometry` GeoJSON Polygon, `irrigation_type`, `water_source`) |
| GET | `/api/v1/farms/{farm_id}` | Bearer | Farm detail (403 cross-tenant) |
| PUT | `/api/v1/farms/{farm_id}` | Bearer | Update farm/boundary |
| DELETE | `/api/v1/farms/{farm_id}` | Bearer | Delete farm |
| POST | `/api/v1/farms/{farm_id}/advisory/evaluate` | Bearer | Evaluate farm advisory |
| GET | `/api/v1/farms/decision/{decision_id}` | Bearer | Decision alias |

## Soil intelligence

| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/api/v1/farms/{farm_id}/soil/analyse` | Bearer | Trigger SoilGrids extraction (`?depth=0-5cm`) |
| GET | `/api/v1/farms/{farm_id}/soil` | Bearer | Latest unified soil profile |
| GET | `/api/v1/farms/{farm_id}/soil/history` | Bearer | Profile history |
| POST | `/api/v1/soil/extract-polygon` | Bearer | Ad-hoc polygon extraction |
| POST | `/api/v1/soil/farms/{farm_id}/profile` | Bearer | Generate profile for farm |
| GET | `/api/v1/soil/providers` | Bearer | Provider capabilities |
| GET | `/api/v1/soil/layers` | Bearer | Available layers |
| GET | `/api/v1/soil/pilot-coverage` | Bearer | Pilot coverage matrix |
| GET | `/api/v1/soil/report-status/{job_id}` | Bearer | Async extraction status |

## Soil laboratory reports

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/api/v1/farms/{farm_id}/soil-reports` | Bearer | List reports |
| POST | `/api/v1/farms/{farm_id}/soil-reports/upload` | Bearer | Multipart upload (PDF/JPG/PNG ≤15 MB) |
| GET | `/api/v1/farms/{farm_id}/soil-reports/{report_id}` | Bearer | Report + measurements |
| GET | `.../soil-reports/{report_id}/measurements` | Bearer | Measurements |
| PATCH/PUT | `.../measurements/{measurement_id}` | Bearer | Correct a measurement |
| POST | `.../soil-reports/{report_id}/confirm` | Bearer | Confirm transcription |
| POST | `.../soil-reports/{report_id}/reprocess` | Bearer | Re-run extraction |
| DELETE | `.../soil-reports/{report_id}` | Bearer | Delete report |
| GET | `.../soil-reports/{report_id}/document` | Bearer | Stream private document |
| GET | `.../soil-reports/{report_id}/document-url` | Bearer | Time-limited signed URL |

## Weather & climate

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/api/v1/farms/{farm_id}/weather/current` | Bearer | Observed current conditions |
| GET | `/api/v1/farms/{farm_id}/weather/forecast` | Bearer | 5-day / 3-hour forecast |
| GET | `/api/v1/farms/{farm_id}/weather/climate-summary` | Bearer | NASA POWER climatology |
| GET | `/api/v1/farms/{farm_id}/weather/history` | Bearer | Weather snapshots |

## Crops

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/api/v1/crops` | Public | Catalogue (`?category=`, `?season=`) |
| GET | `/api/v1/crops/{crop_id}` | Public | Full crop profile |
| GET | `/api/v1/crops/{crop_id}/requirements` | Public | Soil/climate/season/water requirements |
| GET | `/api/v1/crops/{crop_id}/sources` | Public | Citations |
| POST | `/api/v1/crops/seed` | Public | Seed knowledge base (ops) |

## Agricultural intelligence & advisory

| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/api/v1/agriculture/evaluate-farm` | Bearer | Deterministic evaluation (`FarmContextInput`) |
| GET | `/api/v1/agriculture/decision/{decision_id}` | Bearer | Stored decision |
| POST | `/api/v1/agriculture/explain-decision` | Bearer | Qwen3 explanation or deterministic fallback |
| POST | `/api/v1/agriculture/follow-up` | Bearer | Submit follow-up answers, re-evaluate |
| POST | `/api/v1/agriculture/conversation` | Bearer | Dialogue / diagnostic answers |
| GET | `/api/v1/agriculture/seasons` | Public | Maharashtra season calendar |

## Farm Health & Satellite

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/api/v1/farms/{farm_id}/health-snapshot` | Bearer | Multi-domain snapshot (`?force_refresh=`, `?target_season=`) |
| POST | `/api/v1/farms/{farm_id}/health-snapshot/invalidate` | Bearer | Invalidate cache |
| POST | `/api/v1/farms/{farm_id}/satellite/sync` | Bearer | Fetch latest Sentinel-2 observation |
| GET | `/api/v1/farms/{farm_id}/satellite/latest` | Bearer | Latest observation |
| GET | `.../satellite/latest/raster-map` | Bearer | NDVI/NDMI/SCL raster (PNG) |
| GET | `.../satellite/latest/spatial-metadata` | Bearer | Raster bounds/metadata |
| GET | `.../satellite/observations` | Bearer | Observation history |
| GET | `.../satellite/timeseries` | Bearer | Vegetation timeseries |

## Water intelligence

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET/POST | `/api/v1/farms/{farm_id}/water/sources` | Bearer | List/create water sources |
| GET/PUT/DELETE | `.../water/sources/{source_id}` | Bearer | Read/update/delete |
| GET | `.../water/evaluation` | Bearer | BIS/CSSRI water quality evaluation |
| GET/POST | `.../water/reports` / `.../reports/upload` | Bearer | List/upload water reports |
| GET | `.../water/reports/{report_id}` | Bearer | Report detail |
| POST | `.../water/reports/{report_id}/confirm` | Bearer | Confirm report |

## Crop Doctor

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/api/v1/crop-doctor/status` | Public | `{ loaded, model_id, error }` |
| POST | `/api/v1/crop-doctor/predict` | Public | Multipart `file` (image) → `{ crop, diagnosis, confidence_percent, is_healthy, actionable_advice, disclaimer }`; **503** if model unavailable |

## Heat Risk

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/api/v1/heat-risk/crops` | Public | 11 verified crops with stage codes |
| POST | `/api/v1/heat-risk/crop` | Public | `{ crop_code, forecast_tmax_c, forecast_tmin_c, growth_stage?, days_after_sowing?, forecast_sun_hours? }` |
| POST | `/api/v1/heat-risk/worker` | Public | `{ air_temp_c, relative_humidity_pct, wind_speed_ms?, solar_irradiance_wm2?, workload_category?, clothing_type?, is_acclimatised?, sun_exposure? }` |
| POST | `/api/v1/heat-risk/farm/{farm_id}` | Bearer | Farm forecast assessment → risk, outlook, interventions, worker heat, limitations, provenance |

## Government Schemes

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/api/v1/schemes` | Public | `?search=&category=&government_level=&state=&status=&verification_status=&skip=&limit=` |
| GET | `/api/v1/schemes/filters` | Public | Categories, levels, states |
| GET | `/api/v1/schemes/{scheme_id}` | Public | Scheme detail |
| GET | `/api/v1/schemes/admin/status` | Bearer | `{ is_admin }` |
| POST | `/api/v1/schemes` | **Admin** | Create |
| PUT | `/api/v1/schemes/{scheme_id}` | **Admin** | Update |
| PATCH | `/api/v1/schemes/{scheme_id}/status` | **Admin** | `?status=&verification_status=` |
| DELETE | `/api/v1/schemes/{scheme_id}` | **Admin** | Delete |
| POST | `/api/v1/schemes/seed` | **Admin** | Seed verified schemes |

## Income Diversification

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/api/v1/income/opportunities` | Public | `?category=&crop_code=&max_budget=` |
| GET | `/api/v1/income/opportunities/{opportunity_id}` | Public | Single opportunity |
| POST | `/api/v1/income/match-opportunities` | Public | `FarmerResourceProfile` → ranked opportunities |
| POST | `/api/v1/income/calculate-scenario` | Public | `{ opportunity_id, custom_budget_inr, water_availability }` |
| POST | `/api/v1/income/compare-opportunities` | Public | `{ opportunity_ids[], custom_budget_inr }` |

---

## Common response envelopes

- **Success:** the resource object or list directly (no wrapper).
- **Validation error (422):** `{"detail": [{"loc": [...], "msg": "...", "type": "..."}]}`.
- **Business error (400/401/403/404/503):** `{"detail": "..."}`.
- **No content (204):** empty body (deletes).

Full schemas: `openapi.json` → `components.schemas`.
