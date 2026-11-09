# CropNet AI — Authentication

## Mechanism (as implemented)

Authentication is delegated to **Supabase Auth (GoTrue)**. The FastAPI backend
does not issue tokens; it **verifies** the Supabase access token on each
protected request.

### Request flow

1. The client authenticates with Supabase (email/password) and receives a
   `Session` containing an `access_token` (JWT).
2. The client sends `Authorization: Bearer <access_token>` on protected calls.
3. The backend calls
   `GET {SUPABASE_URL}/auth/v1/user` with the token and the project `apikey`.
4. On `200`, the user is resolved (`CurrentUser`); on failure the API returns
   **401**.
5. Missing credentials → **401** with
   `WWW-Authenticate: Bearer`.

Implementation: `services/api/app/core/security.py`.

### Auth dependencies

- `get_current_user` — resolves `CurrentUser { user_id, email, is_authenticated, is_admin }`.
- `require_admin` — returns **403** unless `is_admin` is true.

### Endpoint protection summary

| Group | Protection |
|---|---|
| `/api/v1/health` | Public |
| `/api/v1/crops*` | Public |
| `/api/v1/agriculture/seasons` | Public |
| `/api/v1/schemes` (GET list/detail/filters) | Public |
| `/api/v1/schemes` (POST/PUT/PATCH/DELETE/seed, `/admin/status`) | Authenticated; writes require **admin** |
| `/api/v1/farms*` (all farm, soil, weather, water, satellite, health, soil-reports) | Authenticated |
| `/api/v1/agriculture/evaluate-farm`, `explain-decision`, `conversation`, `follow-up`, `decision/{id}` | Authenticated |
| `/api/v1/soil/*` | Authenticated |
| `/api/v1/crop-doctor/*` | Public |
| `/api/v1/heat-risk/crop`, `/worker`, `/crops` | Public |
| `/api/v1/heat-risk/farm/{farm_id}` | Authenticated (farm ownership enforced) |
| `/api/v1/income/*` | Public (catalogue/compute only) |

### Authorization rules

- **Tenant isolation:** farm-owned resources verify `owner_id == current_user.user_id`;
  cross-tenant access returns **403** (or **404** if the farm is not found).
- **Admin:** `ADMIN_EMAILS` (comma-separated/JSON) or `ADMIN_USER_IDS`; the
  dev-bypass user is treated as admin in local development.

## Session lifecycle

- **Persistence:** the existing Flutter client persists the Supabase session
  and refreshes it automatically.
- **Refresh:** the client SDK refreshes the access token; after a refresh, retry
  the failed request once with the new token.
- **Expiry:** an expired/invalid token yields **401**; the client should
  attempt refresh, then redirect to Login if refresh fails.
- **Logout:** call Supabase `signOut()` and clear local session state.

## Local development bypass (never for production)

- `ALLOW_DEV_AUTH_BYPASS=true` + header `X-Dev-User-Id: <uuid>`.
- The backend rejects this configuration in production
  (`config.py` model validator raises if `ENVIRONMENT=production`).
- The Flutter client enables the header only in builds compiled with
  `--dart-define=DEV_AUTH=true`.

## Guidance for the new Next.js frontend

1. Use `@supabase/supabase-js` (or `@supabase/ssr` for server components).
2. Store the session securely (httpOnly cookies via `@supabase/ssr` is
   recommended for a Vercel deployment).
3. Inject `Authorization: Bearer <access_token>` on every protected API call.
4. Never put Supabase service keys or the Ollama URL in `NEXT_PUBLIC_*`.
5. Only these values are browser-safe: `NEXT_PUBLIC_SUPABASE_URL`,
   `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_API_BASE_URL`.
