# Rashkar Prototype Implementation & Validation Status

**Date:** 08 November 2026  
**Platform Target:** Browser-based Web Prototype (Flutter Web in Chrome / Edge)  
**Primary Language:** English Only (multilingual / speech deferred to v2)

---

## 1. Local Runtime Endpoints

| Component | URL | Status | Runtime Notes |
| :--- | :--- | :--- | :--- |
| **FastAPI Backend** | `http://127.0.0.1:8000` | **ONLINE** | Uvicorn running with auto-reload, PostGIS target & SQLite development fallback |
| **API Documentation** | `http://127.0.0.1:8000/docs` | **ONLINE** | OpenAPI v3 interactive schema Explorer |
| **Flutter Web Client** | `http://127.0.0.1:8080` | **ONLINE** | Compiled release bundle served via HTTP, CanvasKit engine |
| **Ollama AI Runtime** | `http://127.0.0.1:11434` | **OPTIONAL** | Local `qwen3:8b`; graceful fallback to grounded templates when inactive |

---

## 2. Verification Test Suite Summary

### A. Playwright Browser Journey Tests (`tests/test_browser_journeys.py`)
- `test_backend_reachable_and_healthy`: **PASSED**
- `test_flutter_web_serves_html_and_assets`: **PASSED**
- `test_responsive_viewports_and_screenshots`: **PASSED** (Desktop 1440×900, Laptop 1024×768, Tablet 768×1024, Mobile 390×844)
- `test_browser_api_data_fetch`: **PASSED** (CORS-enabled cross-origin API integration verified inside browser)

### B. Flutter Widget & Navigation Tests (`flutter_client/test/widget_test.dart`)
- `Rashkar main app boots and renders navigation shell`: **PASSED**
- `Home screen displays 4 primary action buttons and Ask Rashkar banner`: **PASSED**
- `Farm registration screen displays 5-step guided flow`: **PASSED**
- `Extra income screen renders budget and simulation actions`: **PASSED**
- `Ask Rashkar chat screen renders prompt chips and input field`: **PASSED**
- `Crop loss screen renders tabs and form controls`: **PASSED**

### C. Backend Unit & End-to-End Tests (`backend/tests/`)
- 28 of 28 tests **PASSED** in 0.46s (Crop heat, worker heat, CropNet adapter, risk edge cases, income diversification, PMFBY evidence & human reviewer audit queue, grounded assistant, and end-to-end farmer journey).

---

## 3. UI Viewport Screenshots
Saved to `docs/screenshots/`:
- `viewport_desktop_1440x900.png` (118 KB)
- `viewport_laptop_1024x768.png` (69 KB)
- `viewport_tablet_768x1024.png` (112 KB)
- `viewport_mobile_390x844.png` (67 KB)

---

## 4. Key Design & Safety Disclosures
1. **No Prescriptive Work/Rest Schedules:** Worker Heat Risk uses outdoor Liljegren WBGT proxies with sun vs. shade differentials; explicit advisory states guidance requires clinical review.
2. **Deterministic Calculations:** Yield risk, heat thresholds, income projections, and PMFBY dossiers are calculated via validated Python algorithms, not LLMs.
3. **No Fake Approvals:** PMFBY evidence packets are explicitly designated as draft preparation dossiers for human review; no claim of automatic insurer payout is presented.
4. **Git Policy:** Local commits only. No code is pushed to GitHub.
