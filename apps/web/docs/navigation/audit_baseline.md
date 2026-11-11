# CropNet AI — Global Back Navigation Baseline & Route Inventory

## 1. Objective
Establish the architectural baseline for back navigation across all frontend routes in `apps/web/app/`. This document audits the pre-implementation state, categorizes routes by header architecture, and defines standard fallback destinations.

## 2. Route Inventory & Pre-Implementation Audit (40 Routes)

| Route | Category | Baseline State | Audit Assessment | Target Fallback |
|---|---|---|---|---|
| `/(app)` | Dashboard | No Back button | Deliberately no back button on root | N/A |
| `/(auth)/login` | Auth | No Back button | Deliberately no back button on entry | N/A |
| `/(auth)/register` | Auth | No Back button | Deliberately no back button on entry | N/A |
| `/advisory` | Core Advisory | Static `<Link href="/">` | Hardcoded link; breaks browser history | `/` |
| `/assistant` | Core AI | No Back button | Missing back navigation | `/` |
| `/crop-doctor` | Vision Diagnostics | `PageHeader` without `backHref` | Missing back navigation | `/` |
| `/crops` | Workspace | `IntelligenceWorkspace` | Missing back navigation | `/` |
| `/farms` | Farm Management | `PageHeader` without `backHref` | Missing back navigation | `/` |
| `/farms/new` | Multi-Step Wizard | Static `<Link href="/farms">` | Hardcoded link; no unsaved data guard | `/farms` |
| `/farms/[farmId]` | Farm Dashboard | Static `<Link href="/farms">` | Hardcoded link; breaks in-app history | `/farms` |
| `/farms/[farmId]/edit` | Farm Edit | Static `<Link>` | Hardcoded link; no dirty check | `/farms/[farmId]` |
| `/farms/[farmId]/health` | Farm Health | Static `<Link>` | Hardcoded link | `/farms/[farmId]` |
| `/farms/[farmId]/soil` | Soil Domain | Static `<Link>` | Hardcoded link | `/farms/[farmId]` |
| `/farms/[farmId]/soil/reports` | Soil Reports | Static `<Link>` | Hardcoded link | `/farms/[farmId]/soil` |
| `/farms/[farmId]/soil/reports/[reportId]` | Report Detail | Static `<Link>` | Hardcoded link | `/farms/[farmId]/soil/reports` |
| `/farms/[farmId]/soil/reports/new` | Report Upload | `IntelligenceWorkspace` | Missing back navigation | `/farms/[farmId]/soil/reports` |
| `/farms/[farmId]/vegetation` | Satellite Domain | Static `<Link>` | Hardcoded link | `/farms/[farmId]` |
| `/farms/[farmId]/water` | Water Domain | Static `<Link>` | Hardcoded link | `/farms/[farmId]` |
| `/farms/[farmId]/weather` | Weather Domain | Static `<Link>` | Hardcoded link | `/farms/[farmId]` |
| `/heat-risk` | Climate Resilience | `PageHeader` without `backHref` | Missing back navigation | `/` |
| `/help` | Support | `IntelligenceWorkspace` | Missing back navigation | `/` |
| `/history` | Activity History | `IntelligenceWorkspace` | Missing back navigation | `/` |
| `/income` | Extra Income | `IncomeHeader` | Missing back navigation | `/` |
| `/notifications` | Alerts | `IntelligenceWorkspace` | Missing back navigation | `/` |
| `/profile` | Farmer Profile | `IntelligenceWorkspace` | Missing back navigation | `/` |
| `/rashkar` | RASHKAR Hub | `RashkarShell` | Missing back navigation on overview | `/` |
| `/rashkar/crop-heat` | Thermal Stress | `RashkarShell` static link | Hardcoded link | `/rashkar` |
| `/rashkar/earn-more` | Diversification | `RashkarShell` static link | Hardcoded link | `/rashkar` |
| `/rashkar/worker-heat` | Worker Safety | `RashkarShell` static link | Hardcoded link | `/rashkar` |
| `/rashkar/yield` | APY Yield | `RashkarShell` static link | Hardcoded link | `/rashkar` |
| `/schemes` | Gov Support | Custom header | Missing back navigation | `/` |
| `/schemes/[schemeId]` | Scheme Detail | Static `<Link href="/schemes">` | Hardcoded link | `/schemes` |
| `/schemes/admin` | Gov Admin | `IntelligenceWorkspace` | Missing back navigation | `/schemes` |
| `/settings` | Settings | `IntelligenceWorkspace` | Missing back navigation | `/profile` |
| `/settings/language` | Language Settings | Static `<Link href="/profile">` | Hardcoded link | `/profile` |
| `/health` | Redirect | Instant router redirect | No back button required | N/A |
| `/soil` | Redirect | Instant router redirect | No back button required | N/A |
| `/vegetation` | Redirect | Instant router redirect | No back button required | N/A |
| `/water` | Redirect | Instant router redirect | No back button required | N/A |
| `/weather` | Redirect | Instant router redirect | No back button required | N/A |

## 3. Architecture Principles
1. Never eject a farmer out of the application or into a blank state.
2. In-app navigation must restore prior application state (selected farm, active tabs, search query, scroll position).
3. Minimum touch target of 44px on mobile devices.
4. Unsaved form changes must request confirmation before popping navigation.
