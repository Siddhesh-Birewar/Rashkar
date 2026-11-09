# CropNet AI — Design Reference

## Brand palette (from `shared/widgets/app_decorations.dart`)

| Token | Hex | Usage |
|---|---|---|
| Primary green | `#1B5E20` | App bar, primary actions, brand logo |
| Leaf green | `#2E7D32` | Success, confirmations, positive values |
| Accent orange | `#E65100` | Warnings, SoilGrids/model estimates, restrictions |
| Soil brown | `#5D4037` | Secondary text, soil-related accents |
| Muted surface | `#F9FBF9` | Page backgrounds |
| Border light | `#E0E0E0` | Card borders/dividers |
| Surface white | `#FFFFFF` | Cards |

Semantic colours:
- **Lab / ground truth:** emerald green (`#1B5E20` / `#2E7D32`, tint `#E8F5E9`).
- **Model / SoilGrids estimate:** amber (`#E65100`, tint `#FFF3E0`).
- **Critical heat / danger:** `#C62828`.
- **High heat / warning:** `#E65100`.
- **Moderate / caution:** `#F9A825`.
- **Low / safe:** `#2E7D32`.

## Spacing tokens (`app_spacing.dart`)

`xxs=2, xs=4, sm=8, md=16, lg=24, xl=32, xxl=48, xxxl=64`.
Page padding: mobile 16, tablet 24, desktop 32 (horizontal); 16/20/24 vertical.

## Radius tokens (`app_decorations.dart`)

`xs=4, sm=8, md=12, lg=16, xl=24, full=999`.
Cards use `md` (12); buttons `sm` (8); chips are pill-shaped.

## Elevation

- Subtle card shadow: `0 2px 8px rgba(0,0,0,0.06)`.
- Standard card: `0 4px 12px rgba(0,0,0,0.08)`.
- Elevated/dialog: `0 8px 20px rgba(0,0,0,0.12)`.

## Typography

The current client uses Flutter Material defaults. Recommended web equivalent:
- Base: **Inter** (or system UI), 14–16 px body.
- Headings: semi-bold, 18–24 px.
- Data values: tabular numerals, 16–20 px bold.
- Marathi/Devanagari: ensure a font with Devanagari coverage (e.g. **Noto Sans Devanagari**).

## Icons

Material Icons in the current app. Suggested mappings for web:
- Farms: map / terrain
- Soil: science / layers
- Crops: grass
- Weather: sunny / cloud
- Advisory: psychology / chat
- History: history
- Schemes: account_balance
- Crop Doctor: eco / local_florist
- Heat Risk: thermostat
- Water: water_drop
- Satellite: satellite_alt

## Layout conventions

- Responsive breakpoints: mobile < 600 px, tablet 600–1199 px, desktop ≥ 1200 px.
- Sidebar navigation on tablet/desktop; bottom navigation on mobile.
- Content max width: 1200 px standard, 800 px readable, 1440 px wide.
- Cards: 12 px radius, 1 px `#E0E0E0` border, subtle shadow.
- Agricultural imagery: satellite/field photos are used as map backgrounds; keep
  a clear green-on-white data style.

## Existing visual assets

Screenshots live in `docs/screenshots/` (dashboard, soil intelligence, weather,
crop catalogue, advisory, history, soil lab, farm health, water, satellite,
schemes). These can be used as visual references for v0, not as production
assets.

## Content/voice

- Plain, direct language for farmers.
- Always distinguish **observed** vs **forecast**, **lab** vs **model**,
  **verified** vs **not verified**.
- Use “Not verified” / “Limited assessment” rather than hiding missing data.

## Accessibility

- High contrast (green on white, amber on white).
- Minimum 44×44 px touch targets.
- Never rely on colour alone: pair status colours with text labels/icons.
