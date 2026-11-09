# Rashkar — Climate-Smart Agriculture Platform

[![CI Pipeline](https://github.com/Vernit185/Rashkar/actions/workflows/ci.yml/badge.svg)](https://github.com/Vernit185/Rashkar/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Flutter](https://img.shields.io/badge/Frontend-Flutter%20Web-02569B.svg)](https://flutter.dev/)

> **Software-only climate-smart agriculture intelligence platform for Maharashtra, India.**  
> Delivering farm-specific, scientifically grounded decision intelligence for **Worker Heat Risk**, **Crop Heat Risk**, **Yield Risk & Intelligence**, and **Income Diversification**.

---

## 1. What Rashkar Does

Rashkar is an integrated agricultural advisory and micro-climate risk platform designed for smallholder farmers, starting in Maharashtra (with pioneer validation across Pune district: Baramati, Indapur, Haveli, Daund, Shirur, etc.). 

Instead of disconnected static dashboards, Rashkar operates on a unified model of the farm, plot, soil, crop cycle, and local weather to answer two vital questions for farmers:
1. **What is happening on my farm right now?**
2. **What specific, verified action should I take next?**

### Core Product Pillars (Aligned with Official Hackathon Proposal)
- **Pillar 1: Personalized Farm-Level Heat-Risk AI**:
  - **Worker Heat Risk**: High-resolution 0–6 hour wet-bulb globe temperature (WBGT) occupational safety screening using the Liljegren et al. (2008) physics engine calibrated to ACGIH 2023 TLVs and ISO 7243:2017 screening action limits. Supports Rothfusz Heat Index, Steadman Apparent Temperature, UTCI polynomial approximations, signed threshold exceedance logic, workload screening (light, moderate, heavy, very heavy), sun vs. shade micro-climate modeling, shift duration limitation warnings, and clinically reviewed emergency triage.
  - **Topographic Downscaling**: Elevation lapse-rate adjustment (-6.5°C / 1000m) for hyper-local thermal modeling.
  - **Crop Heat Risk**: Phenological heat hazard assessment across 38 canonical Maharashtra crops. Tracks Days After Sowing (DAS), identifies biological stage vulnerabilities, alerts on expired crop cycles, and provides agronomist-reviewed, citation-backed interventions.
  - **Validated ML Pipeline**: Random Forest extreme heat classifier (96.35% accuracy), XGBoost effective temperature regressor ($R^2 = 0.9981$), and PyTorch LSTM sequence forecast ($\text{MAE} = 0.308^\circ\text{C}$).
- **Pillar 2: Plot-Level PMFBY Crop-Loss Verification**:
  - **Optical & Spectral Analysis**: Sentinel-2 10m band deficit tracking for pre/post-event NDVI and NDWI vegetation health declines.
  - **Multimodal Field Vision**: Computer vision pipeline incorporating YOLOv8 damage localization, U-Net area segmentation, and Vision Transformer (ViT) loss severity assessment.
  - **Insurer Claim Dashboard**: Complete triage workflow with mandatory 48-hour SLA countdown timers, claim review dossiers, confidence thresholds, and real-time adjudication actions.

### Supporting Capabilities
- **Yield Intelligence & Yield Risk**: Multi-scenario yield benchmarking and climate risk analysis combining historical APY crop records with agro-climatic normal distributions (1991–2020 IMD normal baseline and 2010–2024 AgERA5 reanalysis).
- **Income Diversification**: Practical farm enterprise addition (dairy, indigenous goat rearing, desi poultry, sericulture, apiary, shade net polyhouse) with realistic CAPEX, recurring OPEX, net margins, and water requirements calibrated to NABARD FY 2026-27 unit cost norms.
- **AI Agricultural Assistant**: Grounded, contextual advice powered by local Ollama models (e.g. `qwen3:8b`) with transparent fallback to deterministic rule engines when AI runtimes are offline. Core agronomic calculations never depend on LLM generation.

---

## 2. Architecture Overview

```
                      +-----------------------------------+
                      |      Flutter Web Client (SPA)     |
                      |   (State Management via Provider) |
                      +-----------------+-----------------+
                                        | REST / JSON
                                        v
                      +-----------------+-----------------+
                      |     FastAPI Backend (Python)      |
                      |  - Pydantic v2 Contract Validation|
                      |  - Async SQLAlchemy ORM           |
                      +---+-----------+-------------+-----+
                          |           |             |
        +-----------------+           |             +-----------------+
        v                             v                               v
+-------+--------+       +------------+-----------+          +--------+--------+
| SQLite/PostGIS |       |  Scientific Engines   |          | External Feeds  |
| - Farms & Plots|       | - Liljegren WBGT Engine|          | - Open-Meteo    |
| - Crop Cycles  |       | - Crop Phenology Reg.  |          | - AgERA5 / IMD  |
| - Risk Audits  |       | - NABARD Income Engine |          | - Optional LLM  |
+----------------+       +------------------------+          +-----------------+
```

---

## 3. Prerequisites

- **Python**: 3.10+ (tested up to 3.13)
- **Flutter SDK**: 3.22+ (stable channel)
- **Node.js** (optional, for Playwright browser verification tests): 18+
- **Docker & Docker Compose** (optional, for containerized deployment)
- **Ollama** (optional, for local LLM inference): Run `ollama run qwen3:8b`

---

## 4. Quick Start & Setup

### A. Clone & Configure Environment
```bash
git clone https://github.com/Vernit185/Rashkar.git
cd Rashkar

# Copy example environment configuration
cp .env.example .env
```

### B. Python Backend Setup
```bash
# Create and activate virtual environment
python -m venv .venv

# On Linux/macOS:
source .venv/bin/activate
# On Windows PowerShell:
# .venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r pyproject.toml
# Or install in editable mode:
pip install -e .
```

### C. Initialize Database
```bash
# Initialize SQLite development database with Maharashtra canonical data
python -c "from backend.app.db.init_db import init_db; init_db()"
```

### D. Run FastAPI Backend
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation and interactive Swagger UI are available at: `http://127.0.0.1:8000/docs`.

### E. Run Flutter Web Client
```bash
cd flutter_client
flutter pub get
flutter run -d chrome --web-port 8080 --dart-define=API_BASE_URL=http://127.0.0.1:8000
```
Open `http://127.0.0.1:8080` in your web browser.

---

## 5. Running Tests

### Backend Test Suite (Pytest)
```bash
# Run all 52 backend unit, engine, and integration tests
python -m pytest backend/tests/ -v
```

### Flutter Analysis & Tests
```bash
cd flutter_client
flutter analyze
flutter test
flutter build web --release --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

### End-to-End Browser Tests (Playwright)
```bash
# Ensure FastAPI is running on :8000 and Web server is running on :8080
python scripts/verify_heat_defects_browser.py
```

---

## 6. Optional Local AI Runtime (Ollama)

Rashkar features an integrated chat assistant for farmers.
- **Ollama Installed**: The assistant synthesizes natural language answers grounded strictly in the active farm's data context.
- **Ollama Offline**: The system operates with zero disruption, providing grounded fallback advisory from canonical agricultural guidelines.
- **Setting up Ollama**:
  ```bash
  ollama pull qwen3:8b
  ollama serve
  ```

---

## 7. Data Sources & Privacy

All datasets integrated into Rashkar are documented in [`docs/DATA_SOURCE_REGISTER.md`](docs/DATA_SOURCE_REGISTER.md):
- **Weather & Forecasts**: Open-Meteo Operational WMO NWP (ECMWF IFS / DWD ICON).
- **Historical Climatology**: IMD 1991–2020 precipitation normal; Copernicus AgERA5 daily reanalysis (2010–2024).
- **Agricultural Statistics**: Directorate of Economics & Statistics (DES) APY Maharashtra records (1997–2021).
- **Enterprise Economics**: NABARD State Focus Paper Unit Cost Norms FY 2026-27.
- **Soil Profiles**: ISRIC SoilGrids / CropNet synthetic parameter adapter with explicit unsampled coordinate disclosures.

> **Privacy Guarantee**: Rashkar repository contains **zero real farmer personally identifiable information (PII)** or proprietary farm boundaries. All development and testing environments use synthetic test fixtures.

---

## 8. Current Limitations & Scientific Disclaimers

1. **Language Scope**: This prototype version is English-only. Marathi localization will be introduced in subsequent validation phases.
2. **Occupational Safety**: Worker heat hazard ratings provide environmental screening guidance only. They do not replace clinical medical evaluation or individual physiological heat strain monitoring.
3. **Yield Modeling**: Yield scenarios represent historical statistical benchmarks and crop weather indices; they are not yield insurance guarantees.
4. **PMFBY Submissions**: Document generation serves as an evidence dossier for farmers; Rashkar does not automatically approve or submit claims to insurers without farmer authorization.

---

## 9. License

This project is licensed under the MIT License — see the [`LICENSE`](LICENSE) file for details.
