# RASHKAR — Farm-Level Heat Risk AI Architectural & Scientific Specification

**Hackathon Proposal Reference:** PCCOE International Grand Challenge 2026, Theme: AI for Climate Change  
**Product Pillar 1:** Personalized Farm-Level Heat Risk AI (Predict early, prevent heat exhaustion)  
**Implementation Target:** FastAPI Backend + Flutter Web Client (Chrome / Edge)  

---

## 1. Executive Summary & PPT Alignment

The official Rashkar presentation defines Core Pillar 1 as:
> *"Predict heat risk at 1 km resolution every 30 minutes, with a 0–6 hour forecast. Personalize alerts using worker profile, crop stage, and local weather conditions. Zero hardware: No wearables, no IoT weather stations."*

To realize this vision with scientific integrity and operational reproducibility, the Rashkar platform implements:
1. **Multi-Index Thermal Safety Suite:** Concurrently computes physics-based Liljegren WBGT, NOAA National Weather Service Heat Index (Rothfusz equation with low/high humidity corrections), and Universal Thermal Climate Index (UTCI operational polynomial approximation).
2. **Topographic Elevation Lapse-Rate Downscaling:** Resolves the discrepancy between provider NWP grid resolution (~11 km / 0.1°) and individual smallholder plots (1 km target) using standard environmental lapse-rate downscaling ($\Delta T = -0.0065^\circ\text{C}/\text{m} \times \Delta h$), with honest metadata disclosure.
3. **30-Minute Cadence Grid Caching (`ForecastGridCache`):** Aggregates adjacent farms within $0.1^\circ$ geographic grid bins to share atmospheric retrievals, while executing farm-specific topographic downscaling and worker personalizations on a 30-minute validity cycle.
4. **Explainable 0–100 Personalized Heat Risk Scores:** Synthesizes environmental thermal stress, metabolic workload, acclimatization, age vulnerability, and shift duration into calibrated 0–100 scores for agricultural workers and crops.
5. **Machine Learning Pipeline (XGBoost + Random Forest + PyTorch LSTM):** Fast ML forecasting and personalization anchored against the Liljegren numerical physics solver.

---

## 2. Multi-Index Thermal Safety Suite

Thermal stress in Indian agricultural environments is multifaceted: dry heat in Vidarbha/Marathwada differs drastically from humid heat during the monsoon in Pune and coastal Maharashtra. Rashkar evaluates three complementary thermal indices:

### A. Liljegren et al. (2008) Wet-Bulb Globe Temperature (WBGT)
- **Physics Solver:** Solves the coupled heat-and-mass balance equations for the natural wet bulb temperature ($T_{\text{nw}}$) and the 2-inch black globe temperature ($T_{\text{g}}$) under direct solar radiation and wind convection.
- **Formula:**
  $$\text{WBGT}_{\text{outdoor}} = 0.7 \cdot T_{\text{nw}} + 0.2 \cdot T_{\text{g}} + 0.1 \cdot T_{\text{a}}$$
  $$\text{WBGT}_{\text{shade}} = 0.7 \cdot T_{\text{nw}} + 0.3 \cdot T_{\text{g,shade}}$$
- **Occupational Standards:** ACGIH TLVs (2023) and ISO 7243:2017 screening action limits (25°C to 31°C depending on metabolic rate).

### B. NOAA National Weather Service Heat Index (Rothfusz Regression)
- **Application:** Evaluates perceived temperature based on ambient dry-bulb temperature ($T_{\text{a}}$) and relative humidity ($RH$).
- **Algorithm:**
  $$\text{HI} = -42.379 + 2.04901523 \cdot T + 10.14333127 \cdot RH - 0.22475541 \cdot T \cdot RH - 0.00683783 \cdot T^2 - 0.05481717 \cdot RH^2 + 0.00122874 \cdot T^2 \cdot RH + 0.00085282 \cdot T \cdot RH^2 - 0.00000199 \cdot T^2 \cdot RH^2$$
  - Includes low-humidity reduction adjustment when $RH < 13\%$ and $80^\circ\text{F} \le T \le 112^\circ\text{F}$.
  - Includes high-humidity addition adjustment when $RH > 85\%$ and $80^\circ\text{F} \le T \le 87^\circ\text{F}$.

### C. Universal Thermal Climate Index (UTCI)
- **Application:** Bioclimatic metric reflecting the multi-node Fiala human thermoregulation model, accounting for solar radiation, air temperature, humidity, and wind speed at 10m height ($v_{10\text{m}}$).
- **Stress Categories:**
  - $\text{UTCI} > 46^\circ\text{C}$: Extreme Heat Stress
  - $38^\circ\text{C} \le \text{UTCI} \le 46^\circ\text{C}$: Very Strong Heat Stress
  - $32^\circ\text{C} \le \text{UTCI} \le 38^\circ\text{C}$: Strong Heat Stress
  - $26^\circ\text{C} \le \text{UTCI} \le 32^\circ\text{C}$: Moderate Heat Stress
  - $9^\circ\text{C} \le \text{UTCI} \le 26^\circ\text{C}$: Thermal Comfort / No Thermal Stress

---

## 3. Spatial Resolution & Topographic Downscaling

While commercial NWP models (Open-Meteo, ECMWF IFS, DWD ICON, GFS) operate at base grid resolutions of 9–11 km ($0.1^\circ$), farm plots vary in micro-topography and elevation (e.g. Pune district elevations range from 480m in Indapur to 650m in Haveli/Maval).

Rashkar downscales temperature to the 1 km farm plot target using the standard environmental lapse rate:
$$\Delta T = - 0.0065^\circ\text{C}/\text{m} \times (\text{farm\_elevation\_m} - \text{grid\_elevation\_m})$$
$$T_{\text{plot, downscaled}} = T_{\text{grid}} + \Delta T$$

### Honest Disclosure Protocol
The API and Flutter Web interface explicitly disclose:
- `base_grid_provider`: "Open-Meteo Operational WMO NWP (ECMWF IFS / DWD ICON)"
- `base_grid_resolution_km`: 11.0 km
- `target_plot_resolution_km`: 1.0 km
- `elevation_offset_m`: e.g. +20.0 m
- `lapse_adjustment_c`: e.g. -0.13°C

---

## 4. 30-Minute Cadence Grid Caching & Alert Lifecycle

Slide 5 of the presentation requires:
> *"Efficient: 1 forecast grid serves multiple nearby farms."*

Rashkar's `ForecastGridCache` (`backend/app/services/forecast_scheduler.py`):
1. **Spatial Binning:** Rounds geographic coordinates to $0.1^\circ$ (approx 11.1 km). Multiple smallholder plots registered in the same taluka share a single cached weather payload, dramatically minimizing cloud API latency and rate limits.
2. **Temporal Cadence:** Cached entries have a strict TTL of 1,800 seconds (30 minutes). Every request reports `seconds_until_refresh` and `next_assessment_refresh_ist`.
3. **Alert State Lifecycle:**
   $$\text{generated} \longrightarrow \text{delivered} \longrightarrow \text{acknowledged} \longrightarrow \text{updated} \longrightarrow \text{expired}$$
   Alerts persist in memory and can be queried or acknowledged via API.

---

## 5. Explainable 0–100 Personalized Heat Risk Scores

### Worker Heat Strain Score ($0\text{--}100$)
$$\text{Score} = \min(100, S_{\text{thermal}} + S_{\text{workload}} + S_{\text{vulnerability}} + S_{\text{duration\_hydration}})$$

1. **Base Thermal Exceedance ($0\text{--}60$ pts):** Compares effective WBGT with ISO 7243 screening threshold.
   - At threshold: 45 pts.
   - 3°C above threshold: 60 pts.
   - Safely below threshold (>-6°C): 0 to 15 pts.
2. **Metabolic Workload Factor ($0\text{--}15$ pts):**
   - Light (spading seeds): 2 pts.
   - Moderate (weeding, thinning): 6 pts.
   - Heavy (manual harvesting, plowing): 10 pts.
   - Very Heavy (pesticide backpack spraying in full heat): 15 pts.
3. **Acclimatization & Age Vulnerability ($0\text{--}15$ pts):**
   - Unacclimatized: +10 pts.
   - Age $\ge 50$: +5 pts; Age $40\text{--}49$: +2 pts.
4. **Shift Duration & Hydration ($0\text{--}10$ pts):**
   - Continuous shift $\ge 6\text{h}$: +5 pts; $\ge 4\text{h}$: +2.5 pts.
   - Limited/no hydration: +5 pts.

**Classification:**
- $0\text{--}34$: `LOW_RISK` (Green)
- $35\text{--}59$: `MODERATE_HEAT_STRAIN` (Yellow)
- $60\text{--}79$: `HIGH_HEAT_STRAIN` (Orange)
- $80\text{--}100$: `EXTREME_LIFE_THREATENING` (Red)

---

## 6. Machine Learning Staged Pipeline Performance

| Model Component | Framework | Primary Inputs | Target Output | Benchmark Metric |
|:---|:---|:---|:---|:---|
| **XGBoost WBGT Regressor** | XGBoost 3.4.1 | $T_{\text{a}}, RH, v_{10\text{m}}$, Solar, Zenith, Elevation | Next-hour outdoor WBGT | $\text{MAE} = 0.217^\circ\text{C}$, $\text{RMSE} = 0.278^\circ\text{C}$, $R^2 = 0.9981$ |
| **Random Forest Personalization** | Scikit-Learn 1.8 | WBGT, Age, Acclimatization, Workload, Duration | Strain Severity (Low, Mod, High, Extreme) | $\text{Accuracy} = 96.35\%$ |
| **PyTorch LSTM Trajectory** | PyTorch 2.11 | Sequential 6-hour lag meteorological vector | 0–6 hour future WBGT trajectory | $\text{MAE} = 0.308^\circ\text{C}$ |
| **Physics Ground Truth** | Pure Python/NumPy | Radiative & sensible heat balance | Reference baseline | Liljegren et al. (2008) numerical solver |
