# CropNet AI — Error States & UX Behaviour

## HTTP error mapping (current client behaviour)

The Flutter `ApiClient` maps responses to typed exceptions; the new frontend
should mirror this.

| Status | Meaning | UI treatment |
|---|---|---|
| `400` | Bad request / invalid input | Inline field errors + toast |
| `401` | Missing/invalid/expired Bearer token | Attempt Supabase refresh; if it fails → redirect to Login |
| `403` | Not owner / not admin | “You don’t have permission” screen; no retry |
| `404` | Resource not found | Empty/not-found state with back action |
| `422` | Validation error (`detail[]`) | Field-level errors from `loc`/`msg` |
| `500` | Server error | Generic error + retry + request id |
| `503` | Dependency unavailable (Crop Doctor model, weather, OCR) | Explain what is unavailable + retry later |
| Timeout | Client timeout (30 s default; uploads 60 s) | “Timed out” + retry |
| Network | Connection failure | Offline banner + retry |

FastAPI error body: `{ "detail": string | Array<{loc,msg,type}> }`.

## Empty states (must be shown, not faked)

- **No farms:** “No farms registered yet” + Add Farm CTA.
- **No soil profile:** “Run soil analysis first”.
- **No soil reports:** “No laboratory reports uploaded yet”.
- **No weather forecast cached:** fetch live; if unavailable, show
  “Forecast unavailable”.
- **No satellite observation:** “No observation for this farm yet” + Sync.
- **No schemes matching filters:** “No schemes match your filters”.
- **No crops:** degraded-mode notice (crops API can return
  `X-CropNet-Degraded-Mode: true`).
- **No income opportunities matching:** explain filters.

## Loading states

- Use skeletons for cards/lists; spinners for single actions.
- Long operations (OCR upload, satellite sync, advisory explanation) show
  progress + a “this can take up to N seconds” hint.
- Never show a blank screen; always show a loading or empty state.

## “Limited assessment” (do not invent results)

- **Advisory:** `input_validation_status` can be `ABSTAIN_ZERO_CONTEXT` or
  `ABSTAIN_UNREGISTERED_CROP`; `missing_information[]` and
  `uncertainty_notes[]` must be rendered. Never fill with a guess.
- **Heat Risk:** `limitations[]` must be displayed (e.g., worker WBGT uses
  default wind/solar). Unsupported crop → `422` with a clear message.
- **Farm Health:** sections may be “limited”/unavailable; render the domain’s
  own provenance rather than a fabricated health score.
- **Soil:** `value: null` means “not available / lab required”; render
  “Not verified”, never `0`.
- **Crop Doctor:** `503` when the ML runtime/model is absent; show the exact
  detail and a “screening aid” disclaimer.

## Offline behaviour

- The Flutter `FarmHealthRepository` caches the last snapshot and returns it
  with `isFromCache: true` + `cachedAt` when the network fails.
- The new frontend should:
  1. Persist the last successful snapshot per farm (localStorage/IndexedDB).
  2. On network failure, show the cached snapshot with a visible “cached at …”
     label.
  3. Never present cached data as live.
  4. Queue no mutations offline (writes require connectivity); show a clear
     “reconnect to save” message.

## Retry guidance

- Transient (timeout, 5xx, network): retry button; optional exponential backoff
  (1s, 2s, 4s) for idempotent GETs.
- `401`: refresh once, then login.
- `403`/`404`/`422`: do not auto-retry.
- `503` (dependency): retry later; show which dependency is unavailable.

## Request tracing

Every response includes `X-Request-ID` and `X-Process-Time`. Surface the
request id in error toasts for support.

## Security-related UX

- Never display tokens, keys or `.env` values.
- Never log full request headers in production.
- Document previews must use the authenticated `.../document` stream or the
  short-lived signed URL — never a public storage URL.
