# CropNet AI — Feature Inventory

Status legend: **Complete** = implemented and wired; **Partial** = implemented
but limited/disconnected; **Backend-only** = API exists, no current UI;
**Deferred** = not integrated.

## Authentication & onboarding

| Feature | Status | Backend | Current UI |
|---|---|---|---|
| Email/password login | Complete | Supabase Auth (client) + Bearer verification | `features/auth/login_screen.dart` |
| Registration | Complete (limited by Supabase email rate limits) | Supabase Auth | `features/auth/register_screen.dart` |
| Session persistence / refresh | Complete | Supabase SDK | `auth_service.dart` / `auth_state.dart` |
| Auth gate / deep-link redirect | Complete | — | `app_router.dart` redirect |
| Logout | Complete | Supabase | — |
| Dev auth bypass (local only) | Complete | `X-Dev-User-Id` when `ALLOW_DEV_AUTH_BYPASS=true` | compile-time `DEV_AUTH` flag |

## Farms

| Feature | Status | Backend | Current UI |
|---|---|---|---|
| List farms (tenant-isolated) | Complete | `GET /api/v1/farms` | Farms dashboard |
| Create farm with GeoJSON polygon | Complete | `POST /api/v1/farms` | Add/Edit Farm + map |
| Edit farm / boundary | Complete | `PUT /api/v1/farms/{farm_id}` | Add/Edit Farm |
| Delete farm (cascades weather) | Complete | `DELETE /api/v1/farms/{farm_id}` | Farm detail |
| Geodesic area / centroid | Complete | server-side (`shapely`, `pyproj`) | displayed |
| Farm selection / deep links | Complete | `GET /api/v1/farms/{farm_id}` | router |

## Soil intelligence

| Feature | Status | Backend | Current UI |
|---|---|---|---|
| SoilGrids profile extraction | Complete | `POST /api/v1/farms/{farm_id}/soil/analyse`, `GET .../soil` | Soil Intelligence |
| Depth stratification | Complete | `?depth=` | Soil Intelligence |
| USDA texture derivation | Complete | server-side | Soil Intelligence |
| Available NPK non-fabrication | Complete | `available_*` = `null` | UI shows "Lab required" |
| Soil history | Complete | `GET .../soil/history` | Soil Intelligence |
| Soil lab report upload | Complete | `POST .../soil-reports/upload` | Soil Lab Upload |
| OCR extraction + review | Complete | `GET .../soil-reports/{id}`, `.../measurements` | Review screen |
| Farmer corrections | Complete | `PATCH/PUT .../measurements/{id}` | Review screen |
| Farmer confirmation | Complete | `POST .../soil-reports/{id}/confirm` | Review screen |
| Dual-source fusion (lab + SoilGrids) | Complete | server-side (`_fuse_confirmed_laboratory_measurements`) | Comparison widget |
| Report history / signed URL | Complete | `GET .../soil-reports`, `.../document-url` | History screen |
| Reprocess extraction | Complete | `POST .../soil-reports/{id}/reprocess` | — |

## Weather & climate

| Feature | Status | Backend | Current UI |
|---|---|---|---|
| Current weather | Complete | `GET .../weather/current` | Weather screen |
| 5-day / 3-hour forecast | Complete | `GET .../weather/forecast` | Weather screen |
| NASA POWER climate summary | Complete | `GET .../weather/climate-summary` | Weather screen |
| Weather history | Complete | `GET .../weather/history` | — |

## Crops & advisory (deterministic)

| Feature | Status | Backend | Current UI |
|---|---|---|---|
| 10-crop knowledge base | Complete | `GET /api/v1/crops`, `.../{id}`, `.../{id}/sources` | Crop Catalogue |
| Seed knowledge base | Complete | `POST /api/v1/crops/seed` (admin/ops) | — |
| Deterministic farm evaluation | Complete | `POST /api/v1/agriculture/evaluate-farm` | Advisory |
| Decision retrieval | Complete | `GET /api/v1/agriculture/decision/{id}` | — |
| Follow-up answers / re-evaluation | Complete | `POST /api/v1/agriculture/follow-up` | Advisory |
| Qwen3 explanation | Complete | `POST /api/v1/agriculture/explain-decision` | Advisory |
| Bilingual dialogue | Complete | `POST /api/v1/agriculture/conversation` | Advisory |
| Deterministic fallback when Ollama offline | Complete | server-side | — |
| Maharashtra seasons | Complete | `GET /api/v1/agriculture/seasons` | — |

## Farm Health & satellite

| Feature | Status | Backend | Current UI |
|---|---|---|---|
| Unified farm health snapshot | Complete | `GET /api/v1/farms/{farm_id}/health-snapshot` | Farm Health dashboard |
| Snapshot invalidation | Complete | `POST .../health-snapshot/invalidate` | — |
| Sentinel-2 sync | Complete | `POST .../satellite/sync` | Satellite vegetation |
| Latest observation / raster / metadata | Complete | `GET .../satellite/latest`, `.../raster-map`, `.../spatial-metadata` | Satellite vegetation |
| Vegetation timeseries | Complete | `GET .../satellite/timeseries` | Satellite vegetation |

## Water intelligence

| Feature | Status | Backend | Current UI |
|---|---|---|---|
| Water sources CRUD | Complete | `GET/POST/PUT/DELETE .../water/sources` | Water workspace |
| Water quality evaluation (BIS/CSSRI) | Complete | `GET .../water/evaluation` | Water workspace |
| Water lab report upload/confirm | Complete | `POST .../water/reports/upload`, `.../confirm` | Water workspace |

## Crop Doctor

| Feature | Status | Backend | Current UI |
|---|---|---|---|
| Image-based disease diagnosis | Complete (requires optional ML runtime) | `POST /api/v1/crop-doctor/predict` | Crop Doctor tab |
| Model status | Complete | `GET /api/v1/crop-doctor/status` | — |

## Heat Risk

| Feature | Status | Backend | Current UI |
|---|---|---|---|
| Crop heat assessment | Complete | `POST /api/v1/heat-risk/crop` | Heat Risk tab |
| Supported crops / stages | Complete | `GET /api/v1/heat-risk/crops` | Crop/stage selectors |
| Worker WBGT hazard | Complete | `POST /api/v1/heat-risk/worker` | Heat Risk tab |
| Farm-context assessment (forecast, outlook, interventions) | Complete | `POST /api/v1/heat-risk/farm/{farm_id}` | Farm section in Heat Risk |

## Government Schemes

| Feature | Status | Backend | Current UI |
|---|---|---|---|
| Scheme catalogue / search / filters | Complete | `GET /api/v1/schemes`, `.../filters` | Schemes dashboard |
| Scheme detail | Complete | `GET /api/v1/schemes/{scheme_id}` | Scheme detail |
| Admin create/edit/verify/publish/deactivate | Complete (admin only) | `POST/PUT/PATCH/DELETE /api/v1/schemes...` | Admin screens |
| Seed verified schemes | Complete (admin) | `POST /api/v1/schemes/seed` | Admin "Seed" button |

## Income Diversification

| Feature | Status | Backend | Current UI |
|---|---|---|---|
| Opportunity catalogue (14 items, 5 tiers) | Backend-only | `GET /api/v1/income/opportunities` | — |
| Match opportunities to farmer | Backend-only | `POST /api/v1/income/match-opportunities` | — |
| Financial scenario simulation | Backend-only | `POST /api/v1/income/calculate-scenario` | — |
| Compare opportunities | Backend-only | `POST /api/v1/income/compare-opportunities` | — |
| Farmer resource profile / saved plans | Deferred | Rashkar-only DB tables | — |

## History & saved items

| Feature | Status | Backend | Current UI |
|---|---|---|---|
| Assessment/advisory history | Complete (client session) | in-memory decision store | History screen |
| Soil report history | Complete | `GET .../soil-reports` | Soil Lab history |

## Not integrated / deferred

| Feature | Status | Notes |
|---|---|---|
| Yield Intelligence | Deferred | Source depends on pandas + APY dataset + Rashkar DB models |
| PMFBY Loss Verification | Backend module only | `services/pmfby/service.py` ported; no endpoint/UI |
| Farmer resource profile persistence | Deferred | Requires Rashkar income/farm-cycle tables |
| Dashboard "issue-first" service | Deferred | Requires Rashkar farm-cycle/stage tables |
| Ollama grounded assistant (`/api/v1/assistant`) | Not integrated | Existing LLM advisory covers explanations |

## Known disconnected / limited behaviours

- **Crop heat thresholds** are verified only for 11 crops (soybean, cotton,
  jowar, onion, sugarcane, wheat, gram, tur, bajra, maize, groundnut). Other
  crops return HTTP 422 rather than a guessed result.
- **Farm-context worker WBGT** uses forecast max temperature + humidity with
  default wind/solar; the response includes an explicit limitation note.
- **Crop Doctor** returns HTTP 503 if torch/transformers or the model are not
  installed.
- **Decisions and farm state** have in-memory components; in multi-worker
  deployments the decision store is per-process.
- **Registration** is limited by Supabase free-tier email rate limits.
