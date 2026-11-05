# CropNet AI — Soil Intelligence & Optimal Crop Selection

CropNet AI is a scientifically responsible, commercially maintainable agricultural decision-support platform designed for Indian smallholder farmers. 

The initial release focuses on **Location-Based Soil Intelligence** and **Optimal Crop Selection** across four pilot talukas in Pune district, Maharashtra: **Maval, Mulshi, Baramati, and Indapur**.

---

## 1. Core Scientific Principles & Safeguards

1. **Map-Derived Estimates, Not Lab Tests:** Soil intelligence is derived from verified geospatial digital soil mapping (ISRIC SoilGrids 2.0). It is **not** a physical laboratory soil test. Every screen and API response discloses this explicitly.
2. **Total Nitrogen $\neq$ Available Nitrogen:** SoilGrids predicts Total Nitrogen (organic and matrix-bound). Only 1–3% of total N is plant-available mineral nitrogen ($NH_4^+/NO_3^-$). CropNet strictly preserves available N as `null` / `not_available` with clear scientific explanations.
3. **No Fabricated NPK:** Available Phosphorus ($P_2O_5$) and Potassium ($K_2O$) are not provided by approved public rasters and are **never** invented, interpolated, or guessed.
4. **Mode A Crop Suitability:** Optimal crop selection operates in **Mode A (Regional & Soil-Characteristic Suitability)**, evaluating crops against verified soil texture, pH, depth, organic carbon, and climate without requiring fabricated NPK values.
5. **Multi-User Isolation:** Farm polygons and soil profile snapshots are strictly scoped to authenticated user accounts.

---

## 2. Project Architecture & Monorepo Structure

```text
cropnet/
  apps/
    mobile/                 # Flutter mobile application (Android-first)
      lib/main.dart         # High-contrast, outdoor-readable UI
      test/                 # Flutter tests
      pubspec.yaml
  services/
    api/                    # FastAPI backend service
      app/
        api/v1/             # REST endpoints (health, farms, soil)
        core/               # Config, logging, security/auth
        models/             # SQLAlchemy ORM models
        schemas/            # Pydantic Unified Soil Profile & Farm schemas
        services/           # Spatial extractor & provider adapters
          soil_providers/   # SoilGrids, OpenLandMap, NATMO, BHOOMI, LocalRaster
      tests/                # Automated pytest suite
      requirements.txt
  infra/
    docker-compose.yml      # Local PostgreSQL 16 + PostGIS service
    db/
      alembic.ini           # Alembic database migration config
      init_postgis.sql      # PostGIS extension initialization
      migrations/           # Versioned schema migrations
  docs/
    architecture/           # Architecture Decision Records (ADR 001)
    data-sources/           # Soil source catalogue, coverage matrix, risk register
  .env.example              # Environment configuration template
  .gitignore
  README.md
```

---

## 3. Quick Start & Setup Guide

### Prerequisites
* **Python 3.10+** (tested on Python 3.13)
* **Flutter 3.20+**
* **Docker & Docker Compose** (optional for local PostgreSQL/PostGIS; SQLite supported for local dev)

### Step 1: Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### Step 2: Database Setup & Migrations
To start local PostgreSQL with PostGIS:
```bash
cd cropnet/infra
docker-compose up -d
```
Run Alembic schema migrations:
```bash
cd cropnet
alembic -c infra/db/alembic.ini upgrade head
```

### Step 3: Run the FastAPI Backend
Install dependencies and run the server:
```bash
cd cropnet/services/api
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
* Interactive API Documentation (Swagger): `http://localhost:8000/api/v1/docs`
* Health Endpoint: `http://localhost:8000/api/v1/health`
* Soil Providers Capabilities: `http://localhost:8000/api/v1/soil/providers`
* Pilot Regions Coverage: `http://localhost:8000/api/v1/soil/pilot-coverage`

### Step 4: Run the Flutter Mobile App
```bash
cd cropnet/apps/mobile
flutter pub get
flutter run
```

---

## 4. Running Automated Tests

Run the complete backend test suite:
```bash
python3 -m pytest cropnet/services/api/tests/test_api_and_soil.py -v
```

This verifies:
* Backend health and provider capability reporting.
* Farm registration, polygon GeoJSON validation, and geodesic area calculation (hectares/acres).
* Multi-user tenancy isolation (User A cannot access User B's farms).
* Live ISRIC SoilGrids WCS 2.0.1 extraction, unit conversions, and depth stratification.
* Strict preservation of missing available NPK as `null` with explicit scientific notices.
