# Rashkar Historical Dataset Foundation & Acquisition Status

**Document Version:** `2.1.0`  
**Generated Date:** `2026-11-08`  
**System Status:** Operational & Fully Verified  
**Canonical Scope:** Maharashtra Statewide Platform with 4-Taluk Pune Pilot Slice (Baramati, Indapur, Maval, Mulshi)

---

## 1. Executive Summary

This report documents the completion of the historical dataset foundation for **Yield Intelligence** and **Heat-Risk Intelligence** in the **Rashkar** climate-smart agriculture platform.

All datasets have been acquired via official sanctioned pathways, verified for physical consistency and spatial/temporal continuity, hashed using SHA-256, and formally registered in the Rashkar database registry (`DatasetRegistryModel`).

### Summary of Completed Milestones
1. **IMD Pune 0.25° Daily Rainfall (1991–2024):** Complete 34-year continuous daily time series acquired, verified (365/366 records per file, EPSG:4326, mm/day units, fill value `-999.0`), and registered.
2. **Derived Rainfall Reference Baselines:**
   - **Climate Normal (1991–2020):** Official WMO-compliant 30-year gridded climate normal produced and registered (`P-01-IMD-NORMAL-1991-2020`).
   - **Recent Agricultural Reference (2010–2024):** 15-year recent agricultural baseline produced and registered (`P-02-IMD-RECENT-REF-2010-2024`). *Explicitly designated as NOT an official WMO 30-year climate normal*.
3. **AgERA5 v2 Multi-Variable Daily Suite (Copernicus CDS):** Extracted across the 4-taluk Pune pilot domain (`[17.8°–19.2°N, 73.2°–75.2°E]`) for all 7 requested agrometeorological indicators:
   - 2m Temperature (Mean, Maximum, Minimum)
   - Precipitation Flux
   - Solar Radiation Flux
   - 10m Wind Speed
   - 2m Relative Humidity (06:00 and 12:00)
   - Reference Evapotranspiration ($ET_0$)
   - Vapour Pressure Deficit at Maximum Temperature ($VPD_{max}$)
4. **ERA5-Land Hourly Heat Season & Liljegren WBGT Processing:** Standardized May 2024 heat wave hourly slice (`data_0.nc`):
   - Kelvin to Celsius conversions for $T_{2m}$ and $T_{dew}$
   - Wind speed conversion: $u_{10} = \sqrt{u^2 + v^2}$ and reduction to 2m crop canopy height via logarithmic wind profile ($z_0 = 0.03\text{ m}$, reduction factor $\approx 0.723$)
   - Solar radiation flux conversion: accumulated $J/\text{m}^2 \to W/\text{m}^2$
   - Relative humidity via August-Roche-Magnus formulation
   - Retrospective Liljegren et al. (2008) outdoor ($WBGT_{sun}$) and shaded ($WBGT_{shade}$) numerical energy-balance computation
   - Registered as `P-03-ERA5-LAND-STANDARDIZED-2024-05` with strict disclaimer that ERA5-Land is retrospective data for backtesting only and never a live forecast.
5. **Maharashtra APY Master Dataset v2:**
   - Reconciled against DES (MoA&FW), UPAg, and Dataful (Dataset 5632)
   - Preserved raw input values (`area_ha_raw`, `production_tonnes_raw`, `yield_raw`, `yield_raw_unit`)
   - Explicitly converted `kg/ha` to `t/ha` (/ 1000) where applicable
   - Reconciled against calculated yield ($P / A$) with discrepancy tracking
   - Standardized against 38-crop canonical crop registry
   - Registered as `Y-01-MAHA-APY-CANONICAL-V2` (17,916 records, 17,604 valid).
6. **Geographical Administrative Boundaries:**
   - **36 Districts Layer:** Reconciled Palghar district bifurcation from Thane (Aug 2014) and resolved Mumbai City vs Mumbai Suburban separation (`S-05-MAHA-DISTRICTS-36`).
   - **Taluka Boundary Layer:** 307 Maharashtra talukas extracted, mapped to revenue names, and explicitly tagged for the Pune pilot talukas (Baramati, Indapur, Maval [Wadgaon], and Mulshi [Paud]) (`S-06-MAHA-TALUKAS`).

---

## 2. Dataset Inventory & Provenance Register

| Dataset ID | Dataset Name | Publisher / Source | Format | Spatial Coverage & Resolution | Temporal Range | Status | SHA-256 (Prefix) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **S-03-IMD-RAIN-1991..2024** | IMD 0.25° Daily Rainfall (34 Years) | Climate Research & Services, IMD Pune | NetCDF4 | All India (0.25° grid, EPSG:4326) | 1991-01-01 to 2024-12-31 | Verified | `fd5f8309..1ef02aeb` |
| **P-01-IMD-NORMAL-1991-2020** | IMD Rainfall 30-Year Climate Normal | IMD Pune / Rashkar Derived | NetCDF4 | Maharashtra BBox (0.25° grid) | 1991–2020 (30-Year WMO Normal) | Verified | `6d3c5240c745` |
| **P-02-IMD-RECENT-REF-2010-2024**| IMD Rainfall Recent Agricultural Ref | IMD Pune / Rashkar Derived | NetCDF4 | Maharashtra BBox (0.25° grid) | 2010–2024 (15-Year Recent Ref) | Verified | `a152acc40fd4` |
| **S-01-AGERA5-TEMP-2023** | AgERA5 v2 2m Temp (Mean, Max, Min) | ECMWF Copernicus CDS (`sis-agrometeorological-indicators`) | NetCDF / ZIP | Pune BBox [17.8–19.2N, 73.2–75.2E] (0.1°) | 2023-05-01 to 2023-05-15 | Verified | `a2a22beee8f9` |
| **S-01-AGERA5-PRECIP-2023** | AgERA5 v2 Precipitation Flux | ECMWF Copernicus CDS | NetCDF / ZIP | Pune BBox (0.1° grid) | 2023-05-01 to 2023-05-15 | Verified | `0828eab6bf1f` |
| **S-01-AGERA5-SOLAR-2023** | AgERA5 v2 Solar Radiation Flux | ECMWF Copernicus CDS | NetCDF / ZIP | Pune BBox (0.1° grid) | 2023-05-01 to 2023-05-15 | Verified | `d99bd7451819` |
| **S-01-AGERA5-WIND-2023** | AgERA5 v2 10m Mean Wind Speed | ECMWF Copernicus CDS | NetCDF / ZIP | Pune BBox (0.1° grid) | 2023-05-01 to 2023-05-15 | Verified | `6cc2422fa998` |
| **S-01-AGERA5-RH-2023** | AgERA5 v2 2m Relative Humidity | ECMWF Copernicus CDS | NetCDF / ZIP | Pune BBox (0.1° grid) | 2023-05-01 to 2023-05-15 | Verified | `6c8acd497309` |
| **S-01-AGERA5-ET0-2023** | AgERA5 v2 Reference Evapotranspiration | ECMWF Copernicus CDS | NetCDF / ZIP | Pune BBox (0.1° grid) | 2023-05-01 to 2023-05-15 | Verified | `9d97c1a5bf63` |
| **S-01-AGERA5-VPD-2023** | AgERA5 v2 Vapour Pressure Deficit | ECMWF Copernicus CDS | NetCDF / ZIP | Pune BBox (0.1° grid) | 2023-05-01 to 2023-05-15 | Verified | `2d7250bc49af` |
| **S-02-ERA5-LAND-2024-05** | ERA5-Land Hourly Raw (Heat Season) | ECMWF Copernicus CDS (`reanalysis-era5-land`) | NetCDF4 | Pune BBox (0.1° grid) | 2024-05-01 to 2024-05-15 (120 steps) | Verified | `49e754b2715a` |
| **P-03-ERA5-LAND-STANDARDIZED** | Standardized Heat & Liljegren WBGT | ECMWF / Rashkar Processed | NetCDF4 | Pune BBox (0.1° grid) | 2024-05-01 to 2024-05-15 (120 steps) | Verified | `1e63ecd411b0` |
| **Y-01-MAHA-APY-CANONICAL-V2** | Maharashtra APY Canonical v2 | DES MoA&FW / UPAg / Dataful 5632 | CSV | Maharashtra (36 Districts) | 1997 to 2019 (17,916 records) | Verified | `701427864674` |
| **S-05-MAHA-DISTRICTS-36** | Maharashtra 36-District Boundaries | Survey of India / Census / Datameet | GeoJSON | Maharashtra Statewide (36 Districts) | Current (Post-Palghar 2014) | Verified | `8f55d8b54a47` |
| **S-06-MAHA-TALUKAS** | Maharashtra Taluka Boundaries Layer | Census / Geohacker / Rashkar | GeoJSON | 307 Talukas (Tagging 4 Pune Pilot) | Current | Verified | `6cc069ab6d4a` |
| **Y-07-MIRCA-OS-2020** | MIRCA-OS Crop Calendar (Rainfed) | University of Bonn / Zenodo | NetCDF4 | Global / Maharashtra (0.0833°) | Monthly Cropping Calendar | Verified | `4610c5a3d702` |

---

## 3. Methodological & Scientific Standards Applied

### 3.1 IMD Pune Climate Normals vs Agricultural Baselines
- **1991–2020 (30-year):** Computed as the arithmetic mean and standard deviation across all 30 years over the Maharashtra domain. Compliant with WMO guidelines for standard climatological normals.
- **2010–2024 (15-year):** Computed as a recent baseline reflecting modern climate trends and drought episodes (e.g. 2015–16 drought and recent unseasonal excess rainfall). In strict accordance with user constraints, this product is catalogued as a **Recent Agricultural Reference Period Baseline** and is **never** presented as an official WMO 30-year normal.

### 3.2 ERA5-Land Reanalysis Standardisation & Liljegren WBGT
1. **Air Temperature & Dew Point:** Converted from Kelvin ($K$) to Celsius ($^\circ\text{C}$):
   $$T_c = T_K - 273.15$$
2. **Relative Humidity ($RH$):** Formulated using the August-Roche-Magnus psychrometric relationship:
   $$e_s(T) = 6.1094 \cdot \exp\left(\frac{17.625 \cdot T_c}{243.04 + T_c}\right)$$
   $$e(T_{dp}) = 6.1094 \cdot \exp\left(\frac{17.625 \cdot T_{dp,c}}{243.04 + T_{dp,c}}\right)$$
   $$RH = \text{clip}\left(100.0 \cdot \frac{e(T_{dp})}{e_s(T_c)}, 0.0, 100.0\right)$$
3. **Logarithmic Wind Profile Conversion (10m to 2m):**
   $$u_2 = u_{10} \cdot \frac{\ln(z / z_0)}{\ln(z_{ref} / z_0)} = u_{10} \cdot \frac{\ln(2 / 0.03)}{\ln(10 / 0.03)} \approx 0.723 \cdot u_{10}$$
   where $z_0 = 0.03\text{ m}$ is the standard aerodynamic surface roughness for agricultural field crops.
4. **Surface Solar Radiation Downwards Flux ($SSRD$):**
   Converted from step-accumulated energy ($J/\text{m}^2$) to mean downward flux ($W/\text{m}^2$):
   $$\text{Solar Irradiance Flux } (W/\text{m}^2) = \frac{\text{ssrd } (J/\text{m}^2)}{\Delta t = 10,800\text{ s}}$$
5. **Retrospective WBGT:** Evaluated using the numerical heat-balance solver from Liljegren et al. (2008), providing both outdoor in-sun WBGT ($0.7 T_{nw} + 0.2 T_g + 0.1 T_a$) and shaded WBGT ($0.7 T_{nw} + 0.3 T_g$).
   - *Operational Warning:* ERA5-Land is retrospective reanalysis data used strictly for historical baseline calibration, threshold validation, and model backtesting. It must never be presented as a live weather forecast.

### 3.3 Unit Harmonisation & Reconciliation for Maharashtra APY
- **Yield Units:** National APY recorded yield in metric tonnes per hectare ($t/\text{ha}$). Dataful / DES statistics present yield in kilograms per hectare ($\text{kg}/\text{ha}$). In `maharashtra_apy_canonical_v2.csv`:
  - `yield_raw` and `yield_raw_unit` preserve the exact source values.
  - `yield_t_ha` is rigorously standardised to $t/\text{ha}$ ($\text{kg}/\text{ha} / 1000$).
  - `calculated_yield_t_ha` computes $\text{production\_tonnes} / \text{area\_ha}$.
  - Rows with area $\le 0$ or extreme discrepancy ($>25\%$) are flagged in `quality_flag`.
- **District Reconciliation:** Reconciled 36 districts including the 2014 Palghar bifurcation from Thane and the separation of Mumbai City from Mumbai Suburban.

---

## 4. Operational File Locations & Storage Architecture

Due to storage constraints on local drives, raw immutable binary NetCDFs are stored under a managed NTFS directory junction:
- **Junction Source:** `D:\CSE AIML\Rashkar\data\01_raw_immutable\WEATHER`
- **Target Storage:** `C:\Users\verni\Rashkar_Data\WEATHER` (218 GB available)
- **Processed Artifacts:** `D:\CSE AIML\Rashkar\data\02_processed\`
- **Database Registry:** SQLite database `rashkar_dev.db` table `dataset_registry` (PostgreSQL/PostGIS schema identical)
- **FastAPI Endpoints:** Live on `http://127.0.0.1:8000/api/v1/registry/datasets`
