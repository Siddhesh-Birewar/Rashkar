# CropNet AI — Recommended Next.js Architecture (for v0)

## Stack

- **Next.js (App Router)** + **TypeScript** + **Tailwind CSS**
- **@supabase/ssr** (cookie-based session) + `@supabase/supabase-js`
- Optional: `@tanstack/react-query` for authenticated client-side caching
- Deploy: **Vercel**

## Route structure (App Router)

```
app/
  layout.tsx
  globals.css
  page.tsx                       # marketing/redirect
  (auth)/
    login/page.tsx
    register/page.tsx
  (app)/
    layout.tsx                   # shell: sidebar (desktop) / bottom nav (mobile)
    farms/page.tsx
    farms/new/page.tsx
    farms/[farmId]/page.tsx
    farms/[farmId]/soil/page.tsx
    farms/[farmId]/soil/reports/page.tsx
    farms/[farmId]/soil/reports/[reportId]/page.tsx
    farms/[farmId]/weather/page.tsx
    farms/[farmId]/health/page.tsx
    farms/[farmId]/water/page.tsx
    farms/[farmId]/vegetation/page.tsx
    advisory/page.tsx
    crops/page.tsx
    crops/[cropId]/page.tsx
    schemes/page.tsx
    schemes/[schemeId]/page.tsx
    schemes/admin/page.tsx
    history/page.tsx
    crop-doctor/page.tsx
    heat-risk/page.tsx
    income/page.tsx
```

## Layer structure

```
lib/
  supabase/client.ts        # browser client
  supabase/server.ts        # server client (cookies)
  supabase/middleware.ts    # session refresh + auth gate
  api/client.ts             # fetch wrapper: base URL, Bearer token, error mapping
  api/endpoints.ts          # typed endpoint functions
  api/types.ts              # shared request/response types (from openapi.json)
  api/errors.ts             # typed errors + status mapping
  design/tokens.ts          # colors/spacing/radius tokens

components/
  ui/                       # Button, Card, Badge, Input, Skeleton, EmptyState, ErrorState
  layout/                   # AppShell, Sidebar, BottomNav, PageHeader
  domain/                   # FarmCard, SoilProfileCard, WeatherCard, CropOutcomeCard,
                            # SchemeCard, HeatRiskCard, CropDoctorCard, ...

middleware.ts               # protect (app) routes; redirect to /login
```

## Auth & data fetching

1. **Session:** use `@supabase/ssr` to store the session in httpOnly cookies.
2. **Middleware:** refresh the session; redirect unauthenticated users from
   `(app)` routes to `/login`.
3. **Token injection:** `api/client.ts` reads the current session and sends
   `Authorization: Bearer <access_token>`.
4. **Server Components:** fetch public data (crops, schemes, heat-risk metadata)
   directly from the API; do not expose secrets.
5. **Client Components:** authenticated actions (farm CRUD, uploads, advisory)
   use the API client; optionally TanStack Query for caching.
6. **401 handling:** refresh once, retry once, then redirect to `/login`.

## Environment variables

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
# Server-only (never prefixed with NEXT_PUBLIC_):
SUPABASE_SERVICE_ROLE_KEY=        # only if a server action needs it
```

`apps/web/.env.example` contains safe placeholders.

## Tailwind theme

Extend `tailwind.config.ts` with the brand tokens:

```ts
colors: {
  brand: { DEFAULT: "#1B5E20", leaf: "#2E7D32" },
  accent: "#E65100",
  soil: "#5D4037",
  surface: "#F9FBF9",
  border: "#E0E0E0",
},
borderRadius: { card: "12px", button: "8px" },
```

## Guardrails for v0

- **Do not** compute crop suitability, NPK or heat thresholds in the frontend.
  Always call the API.
- **Do not** invent values; render `null` as “Not verified”, show
  `limitations[]`, and distinguish observed vs forecast.
- **Do not** place secrets in `NEXT_PUBLIC_*`.
- **Do not** call Ollama directly; all LLM calls go through FastAPI.
- Uploads use `multipart/form-data` to the soil-report endpoints; enforce the
  15 MB / PDF-JPG-PNG limits client-side too.
- Render `X-Request-ID` in error toasts for support.

## Suggested build order for v0

1. Design system + shell (sidebar/bottom nav, cards, states).
2. Auth (login/register, session, middleware).
3. Farms (list/create/detail).
4. Soil (profile, lab upload/review/history).
5. Weather + Crop catalogue.
6. Advisory (evaluate → outcome cards → explanation → follow-ups).
7. Farm Health + Satellite.
8. Water.
9. Government Schemes (+ admin).
10. Crop Doctor + Heat Risk.
11. Income (backend ready; build UI).
12. History.
