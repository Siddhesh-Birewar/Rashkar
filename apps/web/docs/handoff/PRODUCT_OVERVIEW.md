# CropNet AI — Product Overview

## What CropNet AI is

CropNet AI is an agricultural decision-support platform for Indian smallholder
farmers. It combines geospatial soil data, weather, satellite vegetation
indices, deterministic agronomic rules and a local language model to help a
farmer answer: *what can I grow on this plot, and what should I do next?*

The pilot covers four talukas in Pune district, Maharashtra: **Maval, Mulshi,
Baramati, Indapur**. The system is designed to be scientifically conservative:
it prefers abstaining or flagging missing data over fabricating a result.

## Current architecture (as implemented)

| Layer | Technology | Location |
|---|---|---|
| Existing frontend | Flutter Web (Dart) | `apps/mobile` |
| Backend API | FastAPI (Python 3.13) | `services/api/app` |
| Database | Supabase PostgreSQL + PostGIS (SQLite fallback for local dev) | `infra/db` |
| Authentication | Supabase Auth (Bearer JWT verified server-side) | `services/api/app/core/security.py` |
| Explanations | Local Ollama `qwen3:8b` — explanation/dialogue only | `services/api/app/services/llm` |
| Soil data | ISRIC SoilGrids 2.0 (primary), OpenLandMap, NATMO, BHOOMI, local raster | `services/api/app/services/soil_providers` |
| Weather | OpenWeather (current/forecast), NASA POWER (climate normals) | `services/api/app/services/weather_providers` |
| Satellite | Sentinel-2 L2A via Copernicus CDSE / Earth Search STAC | `services/api/app/services/satellite` |
| Crop Doctor | PlantVillage MobileNetV2 (optional torch/transformers runtime) | `services/api/app/services/crop_doctor` |
| Heat Risk | Deterministic crop-stage + WBGT engines | `services/api/app/services/heat_risk` |
| Income | Deterministic opportunity catalogue + financial engine | `services/api/app/services/income` |

## User roles

1. **Farmer (authenticated)** — owns farms, views soil/weather/crop advice,
   uploads soil lab reports, uses Crop Doctor and Heat Risk, answers follow-up
   questions, browses Government Schemes.
2. **Administrator** — everything a farmer can do, plus create/edit/verify/
   publish/deactivate Government Schemes. Admin identity is an email/user-id
   allowlist (`ADMIN_EMAILS`, `ADMIN_USER_IDS`) enforced by `require_admin`.
3. **Operator/developer** — runs the FastAPI service, Ollama, and the data
   refresh jobs. No end-user UI.

## Non-negotiable product principles

1. **The deterministic engine is the authority.** The LLM never decides crop
   suitability; it only explains the engine's decision. The engine lives in
   `services/api/app/services/agriculture_intelligence`.
2. **No fabricated NPK.** Available N/P/K are `null` unless a physical
   laboratory report provides them. Total Nitrogen is never treated as
   available Nitrogen.
3. **Provenance is preserved.** Every soil/water/satellite/heat value carries a
   source, date, depth and verification status. Modelled estimates are never
   presented as laboratory results.
4. **Abstain over invent.** Missing context produces `ABSTAIN_*` decisions,
   `LIMITED` assessments and explicit `limitations[]`, not guesses.
5. **LLM stays server-side.** Ollama is never exposed to the browser or mobile
   app; all LLM calls go through FastAPI.

## What a v0/Next.js frontend should consume

The existing FastAPI service is the **single source of truth**. The new
frontend should:

- Authenticate users with Supabase and send `Authorization: Bearer <access_token>`.
- Call the REST endpoints documented in `openapi.json`.
- Render empty/loading/error/limited states faithfully.
- Never compute agronomic decisions client-side.
- Never display fabricated values; render `null`/`Not verified` as such.

See `API_REFERENCE.md`, `DATA_MODELS.md`, `AUTHENTICATION.md` and
`FRONTEND_ARCHITECTURE.md` in this folder.
