# CropNet AI — Web Frontend Foundation

Next.js (App Router) + TypeScript + Tailwind CSS foundation for the redesigned,
mobile-first CropNet AI frontend. Built to be developed further in **Vercel v0**.

> This package contains **no product screens yet** — only the foundation and the
> handoff documentation. The existing FastAPI backend is the source of truth.

## Docs

All handoff documentation is in [`docs/handoff/`](./docs/handoff/):

- `PRODUCT_OVERVIEW.md`
- `FEATURE_INVENTORY.md`
- `USER_FLOWS.md`
- `API_REFERENCE.md`
- `openapi.json` (generated from the live FastAPI app)
- `DATA_MODELS.md`
- `AUTHENTICATION.md`
- `DESIGN_REFERENCE.md`
- `ERROR_STATES.md`
- `FEATURE_API_MAPPING.md`
- `FRONTEND_ARCHITECTURE.md`

## Setup

```bash
cd apps/web
cp .env.example .env.local
npm install
npm run dev
```

Open http://localhost:3000.

## Environment

| Variable | Purpose |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | FastAPI base URL (default `http://127.0.0.1:8000`) |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key (browser-safe) |
| `SUPABASE_SERVICE_ROLE_KEY` | Server-only; never expose |

## Scripts

- `npm run dev` — development server
- `npm run build` — production build
- `npm run start` — serve the production build
- `npm run typecheck` — TypeScript check
