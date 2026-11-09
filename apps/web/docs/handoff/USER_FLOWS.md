# CropNet AI — User Flows

All flows assume the FastAPI backend is the source of truth. “Auth” means the
request must carry `Authorization: Bearer <Supabase access token>` (or the
local-only `X-Dev-User-Id` when `ALLOW_DEV_AUTH_BYPASS=true`).

## 1. Onboarding & authentication

1. Farmer opens the app → if no session, redirected to **Login**.
2. **Register** (email + password) → Supabase creates the user (may require
   email confirmation).
3. **Login** → Supabase returns a session; the access token is stored and
   injected into every API call.
4. On token expiry the client refreshes the session; if refresh fails, the user
   is redirected to Login.
5. **Logout** clears the session and returns to Login.

## 2. First farm creation

1. Dashboard shows the empty state (“No farms registered yet”).
2. Farmer taps **Add Farm** → map screen.
3. Farmer taps vertices to draw a closed polygon; live geodesic area is shown.
4. Farmer enters name, taluka (Maval/Mulshi/Baramati/Indapur), irrigation type
   and water source.
5. `POST /api/v1/farms` → farm created, area/centroid computed server-side.
6. Farm appears on the dashboard; selecting it opens the farm workspace.

## 3. Soil intelligence

1. Farmer selects a farm → **Soil**.
2. `POST /api/v1/farms/{id}/soil/analyse` extracts SoilGrids values (pH, SOC,
   texture, CEC, total N). Available NPK are `null` until a lab test exists.
3. Farmer can upload a physical **Soil Lab Report** (PDF/JPG/PNG, ≤15 MB).
4. OCR extracts measurements → report enters `NEEDS_REVIEW`.
5. Farmer reviews each measurement, corrects values if needed, and **confirms**.
6. Confirmed lab values are fused with SoilGrids for display and (where a
   verified rule exists) for crop evaluation; both sources are preserved.
7. Report history and a private document link are available.

## 4. Weather & climate

1. Select farm → **Weather**.
2. Current conditions (`/weather/current`) and 5-day forecast
   (`/weather/forecast`) are shown, labelled as observed vs forecast.
3. NASA POWER 30-year climate summary (`/weather/climate-summary`) is shown
   separately as climatology, not a forecast.

## 5. Crop suitability & advisory

1. Select farm → **Advisory**.
2. The client sends farm context (taluka, soil, season, irrigation) to
   `POST /api/v1/agriculture/evaluate-farm`.
3. The deterministic engine returns per-crop decision states
   (`VERIFIED_SUITABLE`, `CONDITIONALLY_SUITABLE_PENDING_DATA`,
   `REQUIRES_REGIONAL_VALIDATION`, `REGIONAL_SCREENING_ONLY`,
   `UNSUITABLE_VERIFIED_CONSTRAINT`, `ABSTAIN_*`), evidence and missing data.
4. Farmer can request an explanation (`/explain-decision`) — Qwen3 or the
   deterministic fallback, clearly badged.
5. If the engine asks follow-up questions, the farmer answers; the answer is
   submitted (`/follow-up` or in conversation) and the engine re-evaluates.
6. Free-form dialogue continues via `POST /api/v1/agriculture/conversation`.

## 6. Farm Health dashboard

1. Select farm → **Farm Health**.
2. `GET /api/v1/farms/{id}/health-snapshot` aggregates soil, weather, crop,
   water and satellite domains.
3. Each section shows its own provenance and “limited” status; there is no
   invented universal health score.
4. Offline: the client may show a cached snapshot with a “cached” label.

## 7. Satellite vegetation

1. Select farm → **Vegetation**.
2. `POST .../satellite/sync` fetches a Sentinel-2 observation (or returns a
   clearly-labelled synthetic QA observation in dev).
3. Latest observation, NDVI/NDMI stats, SCL masking and raster maps are shown
   with acquisition date and quality status.

## 8. Water intelligence

1. Select farm → **Water**.
2. Add a water source (well/canal/borewell, etc.).
3. Optionally upload a water test report, review and confirm.
4. `GET .../water/evaluation` returns BIS IS 11624:2019 / CSSRI hazard classes
   with the exact inputs used.

## 9. Crop Doctor

1. Open **Crop Doctor** (or Agri Intelligence).
2. Pick a leaf image (JPG/PNG).
3. `POST /api/v1/crop-doctor/predict` returns crop, diagnosis, confidence and
   prevention advice. If the ML runtime is absent, the API returns HTTP 503
   with a clear message.
4. The UI must show the “screening aid, not a lab diagnosis” disclaimer.

## 10. Heat Risk

1. Open **Heat Risk**.
2. Choose a farm and crop (11 verified crops) and optionally a growth stage.
3. `POST /api/v1/heat-risk/farm/{farm_id}` uses the farm’s live forecast to
   return stage-specific heat risk, a multi-day outlook, evidence-linked
   interventions, optional worker WBGT, provenance and explicit limitations.
4. Manual assessments are available via `/heat-risk/crop` and `/heat-risk/worker`.

## 11. Government Schemes

1. Open **Schemes** → search/filter by category, level (Central/State), state.
2. Open a scheme → description, benefits, eligibility, documents, steps,
   department, official link, source link, status and last-verified date.
3. Admins see a **Manage** entry → create/edit/verify/publish/deactivate/seed.

## 12. History

1. Open **History** → chronological list of soil/crop assessments.
2. Selecting an item re-opens the relevant farm/assessment context.
