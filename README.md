# CropNet AI — Multi-Domain Agricultural Decision Support System

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![Backend Tests](https://img.shields.io/badge/pytest-34%2F34%20passed-brightgreen.svg)]()
[![Mobile Tests](https://img.shields.io/badge/flutter%20test-150%2F150%20passed-brightgreen.svg)]()
[![Static Analysis](https://img.shields.io/badge/dart%20analyze-0%20issues-brightgreen.svg)]()
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)]()
[![Flutter](https://img.shields.io/badge/flutter-3.20%2B%20(Web%2FAndroid%2FiOS)-02569B.svg)]()
[![Pilot Geography](https://img.shields.io/badge/pilot-Pune%20District%20(Baramati%2C%20Indapur%2C%20Maval%2C%20Mulshi)-orange.svg)]()
[![License](https://img.shields.io/badge/license-Proprietary%20%2F%20Pilot-lightgrey.svg)]()

> **Scientifically responsible, commercially maintainable agricultural decision intelligence designed for Indian smallholder farmers.**

CropNet AI unifies **spatial soil intelligence**, **irrigation water chemistry**, **high-resolution Sentinel-2 satellite radiometry**, and **hyper-local agro-meteorology** into a 100% deterministic agricultural feasibility engine paired with a local, guardrailed LLM conversational assistant (**Qwen3:8B**) supporting English and Marathi (*मराठी*).

---

## Table of Contents

1. [Executive Overview & Scientific Governance](#1-executive-overview--scientific-governance)
2. [The 5 Agricultural Evidence Domains](#2-the-5-agricultural-evidence-domains)
3. [System Architecture & Monorepo Structure](#3-system-architecture--monorepo-structure)
4. [End-to-End Farmer User Journey](#4-end-to-end-farmer-user-journey)
5. [Mobile Ergonomics & Offline Resilience](#5-mobile-ergonomics--offline-resilience)
6. [Visual Interface Tour & Screenshots](#6-visual-interface-tour--screenshots)
7. [FastAPI REST API Reference](#7-fastapi-rest-api-reference)
8. [Local Prototype Setup & Quick Start](#8-local-prototype-setup--quick-start)
9. [Automated Testing & Verification Suite](#9-automated-testing--verification-suite)
10. [Pilot Case Study: Baramati Grape Vineyard](#10-pilot-case-study-baramati-grape-vineyard)
11. [System Status, Known Boundaries & Roadmap](#11-system-status-known-boundaries--roadmap)
12. [Documentation Index & Architecture Reports](#12-documentation-index--architecture-reports)

---

## 1. Executive Overview & Scientific Governance

Smallholder farmers across the semi-arid Deccan Plateau (such as Pune district's Baramati and Indapur talukas) face compounded agronomic risks: soil salinity, sodicity, erratic monsoon patterns, and severe groundwater depletion. Existing digital tools frequently present misleading claims—such as deriving nitrogen or phosphorus from visual phone cameras, or guessing laboratory soil metrics from low-resolution coarse satellite imagery.

CropNet AI is founded on **strict scientific integrity** and **institutional agronomic governance**:

```
                       ┌────────────────────────────────────────────────────────┐
                       │          CropNet AI Scientific Principles              │
                       └────────────────────────────────────────────────────────┘
                                                   │
         ┌─────────────────────────┬───────────────┴───────────────┬─────────────────────────┐
         ▼                         ▼                               ▼                         ▼
┌───────────────────┐    ┌───────────────────┐           ┌───────────────────┐     ┌───────────────────┐
│ Mapped Estimates  │    │  Total Nitrogen   │           │ Zero Fabricated   │     │  No Universal     │
│   ≠ Lab Tests     │    │   ≠ Available N   │           │      NPK          │     │   Health Score    │
│ Spatial rasters   │    │ Total N (Soil-    │           │ Available P and K │     │ Single aggregate  │
│ clearly labelled; │    │ Grids) is bound;  │           │ never guessed.    │     │ scores obscure    │
│ physical tests    │    │ Available N stays │           │ Unmeasured stays  │     │ limiting factors; │
│ verified by OCR.  │    │ null without lab. │           │ null.             │     │ domain cards used.│
└───────────────────┘    └───────────────────┘           └───────────────────┘     └───────────────────┘
```

### Core Governance Tenets
1. **Digital Soil Map Estimates $\neq$ Physical Laboratory Soil Tests**: Soil intelligence derived from ISRIC SoilGrids 2.0 WCS 250m gridded data is explicitly disclosed as *Location-Based Soil Profile Estimates*. Physical lab reports uploaded by farmers retain a separate, accredited classification (`LABORATORY_MEASURED`).
2. **Total Nitrogen $\neq$ Available Mineral Nitrogen**: SoilGrids predicts total nitrogen (organic and matrix-bound). Only 1–3% of total N is plant-available mineral nitrogen ($NH_4^+/NO_3^-$). CropNet strictly preserves plant-available N as `null` / `not_available` with plain-language scientific explanations rather than passing uninterpreted total N into crop models.
3. **Strict Non-Fabrication of Available NPK**: Available Phosphorus ($P_2O_5$) and Potassium ($K_2O$) are not provided by approved public rasters and are **never** invented, interpolated, or guessed.
4. **Deterministic Agronomic Authority**: The deterministic decision engine (`decision_engine.py`) is the **sole authority** on crop suitability, soil constraints, and irrigation thresholds. The conversational LLM (Qwen3:8B) explains deterministic findings, but **cannot override** decisions, hallucinate scores, or invent crops.
5. **Prohibition of Universal Farm Health Scores**: Agricultural science recognizes that a high soil score cannot compensate for toxic irrigation water or heat-induced floral abortion. CropNet strictly bans universal aggregate scores (e.g. `82/100`), presenting independent domain evidence boards instead.
6. **Multi-Tenant User Isolation**: Farm geometries, soil records, water sources, and AI dialogue histories are scoped to authenticated farmer UUIDs (`owner_id`). Unauthorized cross-tenant queries return **HTTP 403 Forbidden**.

---

## 2. The 5 Agricultural Evidence Domains

```mermaid
graph TD
    subgraph MultiDomainEvidence["CropNet Multi-Domain Evidence Architecture"]
        D1["<b>1. Soil Intelligence</b><br/>ISRIC SoilGrids 250m WCS<br/>+ NABL Physical Lab OCR<br/>(pH, SOC, Clay, CEC, Texture)"]
        D2["<b>2. Water Intelligence</b><br/>Borewell, Well & Canal Sources<br/>BIS IS 11624:2019 Chemistry<br/>(EC, SAR, RSC, Boron)"]
        D3["<b>3. Satellite Radiometry</b><br/>Sentinel-2 L2A (Tile 43QDA)<br/>Element 84 Earth Search COGs<br/>(Canopy NDVI 0.640, NDMI 0.217)"]
        D4["<b>4. Weather & Climate</b><br/>OpenWeather Real-Time & 5-Day<br/>NASA POWER 30-Year Normals<br/>(Temp, Rain, GDD, Humidity)"]
        D5["<b>5. Decision Engine Context</b><br/>100% Deterministic Feasibility<br/>Hard Agronomic Constraints<br/>(Dynamic Follow-up Questions)"]
    end

    D1 --> Snapshot["Unified Farm Health Snapshot Service<br/>(Aggregates Multi-Domain Evidence & Checks Provenance)"]
    D2 --> Snapshot
    D3 --> Snapshot
    D4 --> Snapshot
    D5 --> Snapshot

    Snapshot --> UI["Responsive Flutter Client<br/>(Web, Tablet, Mobile)"]
    Snapshot --> LLM["Local Ollama Qwen3:8B<br/>(Guardrailed Agricultural Advisory)"]
```

### Domain 1: Soil Intelligence
- **Spatially Estimated (ISRIC SoilGrids 2.0)**: Automatic WCS 2.0.1 extraction for farm centroid and polygon bounding box. Retrieves pH in $H_2O$, Soil Organic Carbon (SOC %), Clay %, Silt %, Sand %, Cation Exchange Capacity (CEC cmol(+)/kg), and Bulk Density ($cg/cm^3$) across the 0–30 cm root zone.
- **Laboratory Measured (Physical Soil Test Reports)**: Farmers upload physical soil test cards (PDF/JPEG). CropNet extracts parameters via an Indian agricultural OCR pipeline supporting English and Marathi Devanagari labels (उदा. *सामू (pH)*, *सेंद्रिय कर्ब (OC)*, *उपलब्ध नत्र (N)*). Farmer reviews and confirms measurements before the profile is persisted.
- **Unmeasured Safeguard**: Missing nutrients remain `null` and trigger recommendations to conduct a physical lab test.

### Domain 2: Water Quality & Irrigation Intelligence
- **Source Inventory**: Per-farm registration of irrigation infrastructure: Deep Borewells, Open Dug Wells, River/Canal Lifts, and Farm Ponds (*Shet Tale*), including discharge rates (LPH) and seasonality.
- **Institutional Standards**: Fully implements **BIS IS 11624:2019** (*Guidelines for the quality of irrigation water*) and **CSSRI Karnal** guidelines.
- **Biochemical Formulations**:
  $$\text{SAR (Sodium Adsorption Ratio)} = \frac{\text{Na}^+}{\sqrt{\frac{\text{Ca}^{2+} + \text{Mg}^{2+}}{2}}}$$
  $$\text{RSC (Residual Sodium Carbonate)} = (\text{CO}_3^{2-} + \text{HCO}_3^{-}) - (\text{Ca}^{2+} + \text{Mg}^{2+})$$
- Evaluates Salinity Hazard (EC in dS/m), Sodicity Hazard (SAR), Alkali Hazard (RSC meq/L), and specific ion toxicity (Boron < 0.7 mg/L safe, Chloride, Nitrate).

### Domain 3: Satellite Vegetation Intelligence
- **Copernicus Sentinel-2 L2A**: Discover products via Copernicus Data Space Ecosystem (CDSE) catalogue and stream cloud-optimized GeoTIFFs (COGs) from Element 84 Earth Search AWS S3.
- **Farm Polygon Clipping & Radiometric Calibration**: Uses Rasterio / GDAL to clip B04 (Red), B08 (NIR), B11 (SWIR-1), and SCL (Scene Classification Layer) to the cadastral farm boundary.
- **Pure Canopy Isolation (Class-4 SCL Masking)**:
  $$\text{NDVI} = \frac{\rho_{B08} - \rho_{B04}}{\rho_{B08} + \rho_{B04}} \quad\quad \text{NDMI} = \frac{\rho_{B08} - \rho_{B11}}{\rho_{B08} + \rho_{B11}}$$
  Filters out cloud shadows, water, and bare soil pixels, computing pure vegetative canopy vigour and moisture index.

### Domain 4: Weather & Agro-Climatology
- **Real-Time & Forecast**: OpenWeatherMap API provides current conditions (temperature, relative humidity, wind speed, solar radiation) and 3-hourly 5-day forecasts.
- **30-Year Climatological Normals**: NASA POWER agro-climatology baseline provides historical seasonal precipitation, growing degree days (GDD), and thermal stress hazard windows for the pilot taluka.

### Domain 5: Deterministic Crop Decision Engine & Context
- **Authoritative Rules**: Evaluates 11 regional crops across Kharif, Rabi, and Summer seasons: **Grape, Sugarcane, Pomegranate, Soybean, Chickpea, Sorghum, Onion, Tomato, Cotton, Wheat, and Maize**.
- **Hard Constraints**: Evaluates strict agronomic gates:
  - Soil depth (< 30 cm aborts deep-rooted perennials like Pomegranate/Grape).
  - Subsoil drainage (Heavy clay + poor drainage disqualifies Pomegranate bacterial blight risk).
  - Water Salinity ($EC_w > 2.0\text{ dS/m}$ limits grape export quality).
  - Flowering heat stress (Chickpea reproductive phase $> 35^\circ\text{C}$ aborts pod setting).
- **Dynamic Follow-Ups**: When limiting data is absent, the engine prioritizes targeted diagnostic questions (e.g. *"Does your plot have subsoil drainage installed?"*). Farmer responses trigger instant, authoritative re-evaluation.

---

## 3. System Architecture & Monorepo Structure

```mermaid
graph LR
    subgraph Client["Frontend Client (apps/mobile)"]
        Flutter["Flutter Web / Mobile App<br/>(Riverpod + GoRouter)"]
        Cache["Local Snapshot Cache<br/>(Offline Resilience)"]
    end

    subgraph API["Backend Gateway (services/api)"]
        FastAPI["FastAPI 0.115+<br/>(Python 3.10-3.13)"]
        SnapService["FarmHealthService<br/>(Aggregator & Invalidator)"]
        DecEngine["DecisionEngine<br/>(Deterministic Rules)"]
        Guardrails["GuardrailValidator<br/>(LLM Verification)"]
    end

    subgraph Data["Storage & PostGIS (infra)"]
        Postgres[("PostgreSQL 16/17 + PostGIS<br/>(or Local SQLite in Dev)")]
    end

    subgraph Providers["External & Local AI Services"]
        ISRIC["ISRIC SoilGrids 250m WCS"]
        Sentinel["Element 84 S3 / CDSE COGs"]
        OWM["OpenWeatherMap API"]
        NASA["NASA POWER Agroclimatology"]
        Ollama["Local Ollama<br/>(Qwen3:8B on :11434)"]
    end

    Flutter <-->|REST / JSON<br/>X-Dev-User-Id / Supabase JWT| FastAPI
    Flutter --- Cache
    FastAPI <--> SnapService
    SnapService <--> DecEngine
    FastAPI <--> Postgres
    FastAPI <--> ISRIC
    FastAPI <--> Sentinel
    FastAPI <--> OWM
    FastAPI <--> NASA
    DecEngine --> Guardrails
    Guardrails <--> Ollama
```

### Monorepo Directory Tree

```text
cropnet/
├── apps/
│   └── mobile/                     # Cross-platform Flutter client (Web, Android, iOS)
│       ├── lib/
│       │   ├── core/               # Routing, API clients, theme, responsive breakpoints
│       │   ├── features/
│       │   │   ├── advisory/       # Conversational AI dialogue workspace & Marathi support
│       │   │   ├── auth/           # Supabase GoTrue authentication & token provider
│       │   │   ├── farm_health/    # Unified Farm Health Dashboard & offline repository cache
│       │   │   ├── farms/          # Farm polygon geofence registration & cadastral mapping
│       │   │   ├── satellite/      # Sentinel-2 vegetation indices, raster maps, SCL history
│       │   │   ├── soil/           # ISRIC spatial profiles & lab OCR review workflow
│       │   │   └── water/          # Water sources, lab report entry & BIS IS 11624 analytics
│       │   └── main.dart
│       ├── test/                   # Flutter widget, repository, and offline resilience tests
│       └── pubspec.yaml
├── services/
│   └── api/                        # FastAPI agricultural intelligence backend service
│       ├── app/
│       │   ├── api/v1/endpoints/   # Modular REST controllers (farms, soil, water, satellite, health)
│       │   ├── core/               # App configuration, security, CORS guards, structured logging
│       │   ├── models/             # SQLAlchemy ORM models (farms, soil, water, satellite, weather)
│       │   ├── schemas/            # Pydantic v2 domain schemas & strict serialization contracts
│       │   └── services/           # Domain business logic & spatial collectors
│       │       ├── agriculture_intelligence/ # Deterministic crop decision engine & follow-ups
│       │       ├── explanation/    # Ollama Qwen3:8B client, prompt builder, guardrail validator
│       │       ├── farm_health/    # Multi-domain evidence aggregator & collector fault isolation
│       │       ├── satellite/      # STAC discovery, COG streaming, SCL pure canopy masking
│       │       ├── soil_ocr/       # Indian soil lab report extraction & Marathi translation
│       │       └── water_intelligence/ # BIS IS 11624 chemistry engine & irrigation scoring
│       ├── tests/                  # Pytest test suites (34 passed)
│       └── requirements.txt
├── infra/                          # Infrastructure & containerization definitions
│   ├── docker-compose.yml          # PostgreSQL 16 + PostGIS service
│   └── db/                         # PostGIS extension initialization scripts & Alembic migrations
├── docs/                           # Comprehensive technical specifications & audit reports
│   ├── architecture/               # ADRs, Phase reports, Snapshot contracts, Pilot audit reports
│   ├── data-sources/               # Soil/Water/Satellite data catalogues & licensing registers
│   ├── screenshots/                # Verified application screenshots across viewports
│   └── local_development_startup_guide.md
├── scripts/                        # Automation & runtime management scripts
│   ├── start_local_prototype.sh    # One-click environment launcher (FastAPI + Ollama + Flutter)
│   └── stop_local_prototype.sh     # Clean process termination script
├── .env.example                    # Environment variable configuration template
└── README.md                       # Comprehensive project documentation (this file)
```

---

## 4. End-to-End Farmer User Journey

The 14-step farmer journey transitions seamlessly from parcel mapping to AI conversation:

```mermaid
flowchart TD
    S1["1. Auth & Session"] --> S2["2. Farm Registration"]
    S2 --> S3["3. Boundary Polygon"]
    S3 --> S4["4. Baseline Profile"]
    S4 --> S5["5. Soil Lab Upload"]
    S5 --> S6["6. Soil Confirmation"]
    S6 --> S7["7. Water Sources"]
    S7 --> S8["8. Water Lab Upload"]
    S8 --> S9["9. Satellite Retrieval"]
    S9 --> S10["10. Farm Health Dashboard"]
    S10 --> S11["11. Crop Evaluation"]
    S11 --> S12["12. Diagnostic Follow-ups"]
    S12 --> S13["13. AI Advisory (Qwen3)"]
    S13 --> S14["14. History & Persistence"]
```

1. **Authentication**: Farmer logs in via phone/email; API client auto-injects bearer token.
2. **Farm Registration**: Enters farm name, taluka boundary, and primary crop.
3. **Cadastral Boundary Mapping**: Draws closed polygon on map; PostGIS computes geodesic area in hectares and acres.
4. **Baseline Agronomic Profile**: Default spatial extraction from ISRIC SoilGrids runs automatically.
5. **Soil Lab Report Review**: Optional photo upload of soil health card; OCR parses parameters.
6. **Soil Confirmation**: Farmer confirms OCR values; cache invalidates and updates profile to `LABORATORY_MEASURED`.
7. **Water Source Inventory**: Registers borewells, open dug wells, or canal lift connections.
8. **Water Lab Test Upload**: Enters water test results; BIS IS 11624 calculates SAR and RSC.
9. **Satellite Radiometry Retrieval**: Streams Sentinel-2 COGs; isolates pure canopy Class-4 pixels.
10. **Farm Health Dashboard**: Comprehensive multi-domain evidence board with provenance chips.
11. **Crop Suitability Evaluation**: Deterministic engine evaluates feasibility (e.g. Grape: `SUITABLE` 0.88).
12. **Diagnostic Follow-ups**: Targeted agronomic questions resolve uncertainty (e.g. drainage status).
13. **Conversational AI Advisory**: Local Ollama Qwen3:8B provides bilingual explanation in plain language.
14. **History & Persistence**: All snapshot audits, evaluations, and conversation threads are saved.

---

## 5. Mobile Ergonomics & Offline Resilience

Indian agricultural field conditions frequently suffer from poor 2G/3G connectivity. CropNet AI is engineered with an **offline-first repository architecture**:

```
┌────────────────────────────────────────────────────────────────────────┐
│ ⚠ Offline Mode — Showing Cached Snapshot from 14:32.                  │
│   Live cloud synchronization will resume automatically when connected. │
└────────────────────────────────────────────────────────────────────────┘
```

1. **Transparent Snapshot Caching**: In [`FarmHealthRepository`](apps/mobile/lib/features/farm_health/data/farm_health_repository.dart), successful API fetches are persisted in memory and local storage. When a network disconnection or timeout occurs, the client automatically displays the cached snapshot with `isFromCache = true`.
2. **Prominent Visual Indicators**: An amber alert banner is displayed at the top of the screen, and the farm status badge switches from `Live Synced` (emerald) to `Cached Offline` (amber).
3. **Offline Diagnostic Action Queuing**: When offline, farmers can still answer diagnostic follow-up questions. Responses are queued in `_pendingActions` with ISO timestamps and automatically synchronized with the backend upon reconnection.
4. **Responsive Adaptive Viewports**:
   - **Mobile (< 600px)**: 390px single-column layout, bottom navigation bar, full-bleed touch targets ($\ge 48\text{px}$).
   - **Tablet (600px–1024px)**: 820px 2-column split with collapsible navigation rail.
   - **Desktop (> 1024px)**: 1280px–1440px master-detail layout inside `CenteredPageContainer`.

---

## 6. Visual Interface Tour & Screenshots

| Interface View | Screen Description & Agricultural Highlights | Screenshot Reference |
| :--- | :--- | :--- |
| **Unified Farm Health Dashboard (Desktop)** | Full multi-domain view featuring Soil, Water, Satellite, Weather, and Crop cards with explicit provenance badges (`COPERNICUS_SENTINEL_2_L2A`, `BIS IS 11624 Lab`, `ISRIC SoilGrids`). | ![Dashboard Desktop](docs/screenshots/phase6_1_farm_health_dashboard_desktop.png) |
| **Offline Resilience Banner & Status** | Amber offline resilience alert banner showing cached snapshot timestamp and offline mode indicators. | ![Offline Banner](docs/screenshots/phase6_1_offline_resilience_banner.png) |
| **Mobile Responsive Layout (390x844)** | Optimized single-column mobile experience with outdoor-readable high-contrast typography and bottom navigation. | ![Dashboard Mobile](docs/screenshots/phase6_1_farm_health_dashboard_mobile.png) |
| **Integrated AI Advisory Workspace** | Conversational Qwen3:8B dialogue interface displaying deterministic evidence chips without raw JSON leaks. | ![AI Advisory](docs/screenshots/phase6_1_ai_advisory_workspace.png) |
| **Satellite Pure Canopy Raster Map** | Spatial false-colour vegetation map displaying pure Class-4 canopy NDVI (0.640) and NDMI (0.217). | ![Satellite Spatial Map](docs/screenshots/phase5_7_3_satellite_spatial_raster_map.png) |
| **Soil Intelligence & Lab Review** | Mapped SoilGrids profile side-by-side with physical laboratory test confirmation review card. | ![Soil Intelligence](docs/screenshots/phase5_6_4_soil_intelligence_overview.png) |

---

## 7. FastAPI REST API Reference

The backend exposes 42 REST endpoints documented via OpenAPI/Swagger at `/api/v1/docs`:

| Method | Endpoint Path | Tags | Description & Agricultural Safeguards |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Health | Service liveness, database status, and provider health. |
| `GET` | `/api/v1/farms` | Farms | List registered farms for the authenticated user. |
| `POST` | `/api/v1/farms` | Farms | Register new farm with GeoJSON polygon; calculates geodesic area. |
| `GET` | `/api/v1/farms/{farm_id}` | Farms | Retrieve farm parcel details and boundaries. |
| `GET` | `/api/v1/farms/{farm_id}/health-snapshot` | Farm Health | **Unified Health Snapshot**: aggregates Soil, Water, Satellite, Weather, and Feasibility. Supports `force_refresh=true`. |
| `POST` | `/api/v1/farms/{farm_id}/health-snapshot/invalidate` | Farm Health | Explicitly invalidates memory cache for the farm. |
| `GET` | `/api/v1/soil/farms/{farm_id}/profile` | Soil | Retrieve current active soil profile (ISRIC or confirmed lab). |
| `POST` | `/api/v1/soil/farms/{farm_id}/profile` | Soil | Trigger fresh ISRIC SoilGrids 250m WCS extraction for farm boundary. |
| `POST` | `/api/v1/farms/{farm_id}/soil-reports/upload` | Soil Reports | Upload physical lab test PDF/JPEG for OCR extraction. |
| `POST` | `/api/v1/farms/{farm_id}/soil-reports/{id}/confirm` | Soil Reports | Confirm farmer-verified measurements; invalidates health snapshot. |
| `GET` | `/api/v1/farms/{farm_id}/water/sources` | Water | List irrigation sources (borewell, canal, dug well, farm pond). |
| `POST` | `/api/v1/farms/{farm_id}/water/sources` | Water | Register irrigation infrastructure with discharge rate and seasonality. |
| `POST` | `/api/v1/farms/{farm_id}/water/reports/upload` | Water | Submit water lab test; calculates SAR, RSC, and BIS IS 11624 classes. |
| `GET` | `/api/v1/farms/{farm_id}/satellite/latest` | Satellite | Retrieve latest Copernicus Sentinel-2 L2A observation and canopy statistics. |
| `GET` | `/api/v1/farms/{farm_id}/satellite/latest/raster-map` | Satellite | Retrieve clipped PNG raster map with SCL cloud/shadow mask. |
| `GET` | `/api/v1/farms/{farm_id}/satellite/timeseries` | Satellite | Historical timeseries of canopy NDVI, NDMI, and vegetation cover %. |
| `GET` | `/api/v1/farms/{farm_id}/weather/current` | Weather | Real-time OpenWeatherMap observations for farm centroid. |
| `GET` | `/api/v1/farms/{farm_id}/weather/forecast` | Weather | 5-day 3-hourly forecast precipitation and temperature outlook. |
| `POST` | `/api/v1/agriculture/evaluate-farm` | Agriculture | Deterministic crop feasibility evaluation across 11 regional crops. |
| `POST` | `/api/v1/agriculture/follow-up` | Agriculture | Submit follow-up question answers; triggers dynamic re-evaluation. |
| `POST` | `/api/v1/agriculture/explain-decision` | Advisory | Guardrailed Ollama Qwen3:8B explanation of deterministic decision. |
| `POST` | `/api/v1/agriculture/conversation` | Advisory | Interactive multi-turn agricultural conversational assistant. |

---

## 8. Local Prototype Setup & Quick Start

### Prerequisites
- **Python 3.10+** (tested up to 3.13)
- **Flutter 3.20+** (tested with Flutter 3.29 / 3.41)
- **Ollama** installed with `qwen3:8b` model pulled
- **SQLite 3** (default zero-dependency dev DB) or **PostgreSQL 16 + PostGIS** (optional via Docker)

### Option A: One-Click Startup (Recommended)
From the repository root:
```bash
./scripts/start_local_prototype.sh
```
This launcher automatically:
1. Verifies local Ollama running on `127.0.0.1:11434` and pulls `qwen3:8b` if missing.
2. Launches FastAPI on `http://127.0.0.1:8000` with hot reloading.
3. Launches Flutter Web on `http://localhost:8080`.

To terminate all processes cleanly:
```bash
./scripts/stop_local_prototype.sh
```

### Option B: Manual Step-by-Step Setup

#### 1. Backend Service (FastAPI)
```bash
cd cropnet/services/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start FastAPI server
PYTHONPATH="../..:." python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- Interactive API Docs: `http://127.0.0.1:8000/api/v1/docs`
- Health Endpoint: `http://127.0.0.1:8000/api/v1/health`

#### 2. Local AI Engine (Ollama)
```bash
# Pull model and verify
ollama pull qwen3:8b
ollama serve
```

#### 3. Mobile Frontend (Flutter Web)
```bash
cd cropnet/apps/mobile
flutter pub get
flutter run -d chrome --web-port=8080
```

---

## 9. Automated Testing & Verification Suite

CropNet enforces continuous verification with strict regression gates:

### Backend Pytest Suite (34/34 Passed)
```bash
cd cropnet
python3 -m pytest services/api/tests/test_pilot_readiness_phase6_1.py \
                  services/api/tests/test_farm_health_snapshot.py \
                  services/api/tests/test_agriculture_intelligence_phase5_1.py -v
```
- `test_pilot_farm_multi_domain_provenance`: Validates complete multi-domain evidence on Baramati pilot.
- `test_brand_new_farm_clean_not_available_states`: Proves brand new parcel renders clean not-available states without crashing.
- `test_stale_observation_detection`: Confirms observations older than threshold are flagged `STALE`.
- `test_cross_user_authorization_rejected`: Confirms HTTP 403 Forbidden for cross-tenant access.
- `test_snapshot_caching_and_force_refresh`: Validates in-memory cache hit and force refresh bypass.
- `test_domain_collector_fault_isolation`: Simulates external provider outages; confirms zero cascading failures.
- `test_governance_prohibition_of_universal_health_score`: Enforces prohibition of aggregate scores.

### Mobile Flutter Test Suite (150/150 Passed)
```bash
cd cropnet/apps/mobile
flutter test
```
- `farm_health_offline_resilience_test.dart`: Validates offline cache fallback and follow-up action queuing.
- `api_client_test.dart`: Validates error mapping (HTTP 401, 403, 404, 422) and auth token injection.
- `farm_health_dashboard_widget_test.dart`: Validates all 8 dashboard sections and responsive breakpoints.

### Static Analysis & Web Build
```bash
cd cropnet/apps/mobile
dart analyze lib/            # 0 issues found
flutter build web --release  # Compiles release bundle in ~18s
```

---

## 10. Pilot Case Study: Baramati Grape Vineyard

The platform was independently audited against the registered Baramati pilot parcel:

- **Parcel ID**: `94a1f16e-bf0d-4d3f-9bd3-d63a57189818`
- **Owner ID**: `00000000-0000-0000-0000-000000000001`
- **Cadastral Boundary**: 18.736 hectares (46.297 acres), 16-vertex polygon in Baramati Taluka, Pune.
- **Centroid**: $18.151944^\circ\text{ N}, 74.577222^\circ\text{ E}$.

```
┌────────────────────────────────────────────────────────────────────────┐
│               Baramati Pilot Audited Evidence Matrix                  │
├──────────────────────┬────────────────────────┬────────────────────────┤
│ Domain               │ Measurement / Value    │ Provenance Classification│
├──────────────────────┼────────────────────────┼────────────────────────┤
│ Soil pH              │ 7.30 (Neutral/Alkaline)│ SPATIALLY_ESTIMATED_ISRIC│
│ Soil Organic Carbon  │ 1.62% (Moderate)       │ SPATIALLY_ESTIMATED_ISRIC│
│ Soil Texture         │ Clay (48.2% Clay)      │ SPATIALLY_ESTIMATED_ISRIC│
│ Available Nitrogen   │ null (Unmeasured)      │ SPATIALLY_ESTIMATED_ISRIC│
│ Water Source 1       │ Borewell (4,500 LPH)   │ FARMER_REPORTED        │
│ Water Source 2       │ Canal Lift (12,000 LPH)│ FARMER_REPORTED        │
│ Water Salinity (EC)  │ 1.15 dS/m (Class II)   │ LABORATORY_MEASURED    │
│ Sodium Adsorption    │ SAR 4.20 (Class S1)    │ LABORATORY_MEASURED    │
│ Residual Carbonate   │ RSC -0.80 meq/L (Safe) │ LABORATORY_MEASURED    │
│ Water Boron          │ 0.40 mg/L (Safe < 0.7) │ LABORATORY_MEASURED    │
│ Sentinel-2 Granule   │ Tile 43QDA (2026-10-25)│ COPERNICUS_SENTINEL_2  │
│ Pure Canopy NDVI     │ 0.640 (Vigorous)       │ SCL Class-4 Masked COG │
│ Pure Canopy NDMI     │ 0.217 (Adequate Water) │ SCL Class-4 Masked COG │
│ Crop Feasibility     │ Grape: SUITABLE (0.88) │ CROP_DECISION_ENGINE   │
└──────────────────────┴────────────────────────┴────────────────────────┘
```

---

## 11. System Status, Known Boundaries & Roadmap

| Feature / Subsystem | Status | Engineering Notes & Boundaries |
| :--- | :---: | :--- |
| **Location-Based Soil Profile** | **Production Ready** | Live ISRIC WCS 250m extraction; strict missing available NPK safeguards. |
| **Physical Soil Lab OCR** | **Verified** | Parsed against Maharashtra lab test formats; requires farmer review. |
| **Water Quality Intelligence** | **Production Ready** | Full BIS IS 11624:2019 & CSSRI math; evaluated against crop thresholds. |
| **Sentinel-2 Radiometry** | **Production Ready** | Element 84 COG streaming; SCL Class 4 pure canopy masking. |
| **Agro-Weather Intelligence** | **Production Ready** | Real-time OpenWeather observations + NASA POWER 30-year normals. |
| **Deterministic Decision Engine** | **Production Ready** | 100% authoritative rule engine; 11 regional crops evaluated. |
| **AI Dialogue & Advisory** | **Production Ready** | Local Ollama Qwen3:8B; bilingual English & Marathi; zero JSON leaks. |
| **Mobile Offline Resilience** | **Production Ready** | In-memory/storage snapshot cache; offline alert banner; action queue. |
| **Android / iOS App Bundles** | *In Progress* | Flutter Web release verified; Android APK gradle bundling in progress. |
| **Voice / Speech Interface** | *Roadmap* | Audio input and Marathi Text-to-Speech (TTS) planned for Phase 7. |
| **Microclimate IoT Telemetry** | *Roadmap* | Integration with LoRaWAN soil moisture/tensiometer field probes. |

---

## 12. Documentation Index & Architecture Reports

For detailed engineering specifications, refer to the documentation repository:

- 📘 [Phase 6.1 Farmer Pilot Readiness Master Report](docs/architecture/phase6_1_farmer_pilot_readiness_master_report.md)
- 🔬 [Phase 6.1 Data Provenance & Pilot Validation Report](docs/architecture/phase6_1_data_provenance_validation_report.md)
- 🚜 [Phase 6.1 Farmer Workflow End-to-End Report](docs/architecture/phase6_1_farmer_workflow_report.md)
- 📱 [Phase 6.1 Mobile Experience & Offline Readiness Report](docs/architecture/phase6_1_mobile_offline_readiness_report.md)
- 🛡️ [Phase 6.1 Integration Reliability & Security Audit Report](docs/architecture/phase6_1_integration_reliability_report.md)
- 📐 [Farm Health Snapshot Architecture Contract](docs/architecture/farm_health_snapshot_contract.md)
- 🧠 [Agricultural Intelligence Decision Architecture](docs/architecture/agricultural_intelligence_architecture.md)
- 🏛️ [ADR 001: Geospatial Soil Data Architecture](docs/architecture/adr_001_soil_data_architecture.md)
- 📊 [Pilot Geographic Coverage Matrix](docs/data-sources/pilot_coverage_matrix.md)
- 📜 [Geospatial Soil Data Sources Catalogue](docs/data-sources/soil_sources_catalogue.md)
- 🚀 [Local Development & Startup Guide](docs/local_development_startup_guide.md)

---

**Developed for smallholder farmers across Maharashtra.**  
*CropNet AI — Grounded in Soil, Validated by Science, Powered by Truth.*
