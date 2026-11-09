# RASHKAR — Data Source Register & Provenance
**Comprehensive Catalog of Integrated Institutional Datasets**  
**Document ID:** RASHKAR-DOC-DATA-01  
**Project:** Rashkar Climate-Smart Agriculture Platform (Maharashtra Pilot)  
**Date:** November 2026

---

## 1. Overview

This register documents all primary, secondary, and institutional datasets utilized across Rashkar's intelligence modules. It details their spatial resolution, temporal coverage, update cadence, physical storage location, and verification status.

---

## 2. Integrated Dataset Catalog

| Dataset Identifier | Institutional Source | Spatial Domain & Resolution | Temporal Domain | Primary Variables | File Storage / Access Endpoint | Quality & Verification Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **IMD-RAIN-025** | India Meteorological Department (IMD) Pune | All India / Maharashtra clip (0.25° × 0.25° grid) | 1991–2024 (34 years daily) | Daily precipitation (`rainfall`, mm/day) | `data/raw/imd/` (NetCDF4 format) | Verified: Daily continuity checked; 1991–2020 official climate normal computed. |
| **AGERA5-V2** | Copernicus Climate Change Service (C3S) / ECMWF | Global / Maharashtra clip (0.1° × 0.1° grid) | 2010–2024 daily | 2m Tmax, Tmin, Tmean, Solar radiation, 10m Wind speed, Relative humidity, Reference ET ($ET_0$), VPD | `data/raw/agera5/` (NetCDF4 format) | Verified: NetCDF variable extraction verified; AgERA5 v2 format. |
| **ERA5-LAND-HOURLY** | Copernicus Climate Change Service (C3S) | Global / Pune pilot clip (0.1° × 0.1° grid) | 2010–2024 hot seasons (March–May) | 2m dry-bulb temperature, 2m dew-point temperature, surface solar irradiance, 10m u/v wind components | `data/raw/era5_land/` (NetCDF4 format) | Verified: 120h Pune heatwave benchmark verified; exact timestamps validated. |
| **OPEN-METEO-NWP** | Open-Meteo Operational WMO NWP (ECMWF IFS / DWD ICON / GFS) | Global on-demand grid point (lat/lon) | Real-time + 48-hour hourly forecast | 2m temperature, relative humidity, wind speed, direct/diffuse solar radiation, dewpoint, precipitation | `WeatherService` dynamic API endpoint (`api.open-meteo.com`) | Operational: Live bounding checks for Maharashtra ($15.5^\circ\text{N} - 22.2^\circ\text{N}$, $72.5^\circ\text{E} - 81.0^\circ\text{E}$). |
| **DES-APY-MAHA** | Directorate of Economics & Statistics (DES), Ministry of Agriculture | 36 Districts of Maharashtra | 1997–2021 (24 harvest years) | District, Crop, Season, Area (ha), Production (tonnes), Yield (kg/ha) — 17,916 records | `data/apy_maharashtra_cleaned.csv` | Cleaned & Verified: Filtered outliers, standard crop naming, indexed for sub-millisecond querying. |
| **AGMARKNET-OGD** | Agmarknet, Directorate of Marketing & Inspection (DMI) / OGD India | 300+ APMC Mandis across Maharashtra | Historical & daily market arrivals | Modal price, minimum price, maximum price, arrivals (quintals) | `data/mandi_prices_maharashtra.csv` / API | Verified: Modal price distributions mapped to 38 canonical crops. |
| **NABARD-UNIT-COSTS** | National Bank for Agriculture and Rural Development (NABARD) | Maharashtra State (all 6 revenue divisions) | FY 2026-27 State Focus Paper | Unit capital investment (Capex), recurring operating cost (Opex), standard bank loan margins | `backend/app/services/income_engine.py` / database tables | Verified: Calibrated to FY26-27 state norms for animal husbandry, horticulture, sericulture. |
| **CROPNET-SOIL** | CropNet Synthetic Soil Adapter / ISRIC SoilGrids 250m | Maharashtra agricultural soils | Continuous vertical profile (0–100 cm) | Sand, Silt, Clay %, pH, Bulk Density, CEC, Organic Carbon (SOC), Available Water Capacity (AWC) | `backend/app/services/cropnet_adapter.py` | Verified: Safe non-inference synthetic fallback; zero unverified deep learning hallucinations. |
| **SENTINEL2-MSI-L2A** | European Space Agency (ESA) Copernicus / Sentinel-2 | Plot-level polygon (10m spatial resolution) | 5-day revisit cycle | B2 (Blue, 490nm), B4 (Red, 665nm), B8 (NIR, 842nm), B11 (SWIR, 1610nm) | `backend/app/services/pmfby_vision_service.py` | Verified: Computes NDVI, NDWI, EVI pre/post peril event anomaly for plot crop loss verification. |
| **SMS-IVR-GATEWAY** | Simulated Telecom Gateway (Kisan Call Centre / Twilio Protocol) | Pan-India mobile cellular networks (SMS/IVR) | Real-time dispatch triggered on risk exceedance | Plaintext Marathi/Hindi/English SMS alert & interactive voice prompt synthesis | `backend/app/services/forecast_scheduler.py` | Operational Architecture: Defined schema contracts for low-connectivity basic feature phones without app dependence. |

---

## 3. Storage Hierarchy and Immutability Safeguards

All raw historical files (`.nc`, `.zip`, `.csv`) are stored in immutable directories:
- `data/raw/imd/`: Raw IMD NetCDF files with SHA-256 integrity logs.
- `data/raw/agera5/`: Official ECMWF AgERA5 v2 daily indicators.
- `data/raw/era5_land/`: Hourly reanalysis slices for hot season validation.
- `data/processed/`: Derived reference files, including:
  - `imd_rainfall_normals_1991_2020.nc` (Official WMO climate normal)
  - `imd_rainfall_reference_2010_2024.nc` (Recent 15-year agricultural baseline)

No raw data file is ever overwritten by runtime processes.
