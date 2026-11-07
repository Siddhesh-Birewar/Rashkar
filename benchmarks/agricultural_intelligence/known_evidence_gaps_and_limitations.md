# CropNet AI — Known Evidence Gaps and Limitations (Phase 5.0)

**Document Version:** 1.0.0  
**Phase:** 5.0 (Intelligence Benchmark & Evaluation Framework)  
**Status:** Living Transparency Register  
**Audit Context:** Consolidated Gaps from Phase 4 Reference Document Audit and Migration 005  

---

## 1. Crop-Specific Agronomic Evidence Gaps

### 1.1 Pomegranate (*Punica granatum*)
- **Lower Tolerable Soil pH Limit:**
  - *Status:* **UNVERIFIED / PRESERVED AS NULL**
  - *Evidence:* ICAR-NRCP and MANAGE (2022, p. 3) explicitly establishes that "Light soil" with pH 6.5–7.0 is most suitable and that pomegranate tolerates pH up to 8.5 under well-managed conditions with adequate organic matter. The publication does **NOT** establish a lower tolerable pH limit (such as 6.0, 5.5, or 5.0).
  - *Limitation:* The AI system must not invent a lower tolerable pH boundary. Any query regarding soil pH below 6.5 must be flagged as `unverified_lower_limit` and treated with caution.
- **Annual Water Requirement in Millimeters:**
  - *Status:* **UNVERIFIED / PRESERVED AS NULL**
  - *Evidence:* ICAR-NRCP and MANAGE (2022) does not report an aggregate annual millimeter water requirement. Instead, the manual specifies daily tree water requirements in **liters per tree per day** across 52 Meteorological Weeks, broken down by tree age (Year 1 to 5+) and Bahar (Mrig, Hasta, Ambia).
  - *Limitation:* Presenting generic figures like "500–1000 mm/year" is an agronomic violation. Water advisory must strictly use daily liters/tree tables indexed by Bahar and tree age.
- **Bahar Regulation Outside Primary Windows:**
  - *Status:* **PARTIALLY SPECIFIED**
  - *Evidence:* Tables 1–3 in ICAR-NRCP (2022, pp. 45–46) cover Mrig Bahar (June flowering), Hasta Bahar (Sept–Oct flowering), and Ambia Bahar (Jan–Feb flowering). Off-season flowering or unmanaged transition seasons have no validated daily water tables in the reference corpus.

---

### 1.2 Chickpea / Bengal Gram (*Cicer arietinum*)
- **Upper Tolerable Soil pH Limit:**
  - *Status:* **UNVERIFIED / PRESERVED AS NULL**
  - *Evidence:* ICRISAT Chickpea Seed Production Manual (2010, p. 8) establishes that deep loams or silty clay loams with pH 6.0–8.0 are "best suited". It notes sensitivity to salinity and waterlogging. The source does **NOT** support an upper tolerance limit of 8.5.
  - *Limitation:* The database schema preserves `ph_tolerable_max` as NULL. The AI engine must not claim tolerance up to 8.5 without qualified, source-backed evidence.
- **Thermal Threshold Scope (Reproductive vs. Universal Mortality):**
  - *Status:* **QUALIFIED REPRODUCTIVE THRESHOLD ONLY**
  - *Evidence:* ICRISAT (2010, p. 3) states that daily maximum temperature $> 35^\circ\text{C}$ and mean daily temperature $< 15^\circ\text{C}$ during the **reproductive stage** (flowering and pod filling) cause flower drop and reduced pod set.
  - *Limitation:* These thresholds must **NOT** be represented as vegetative-stage survival limits, whole-plant killing temperatures, or universal seasonal bounds.
- **Vegetative Stage Thermal Limits:**
  - *Status:* **UNVERIFIED IN LOCAL CORPUS / PRESERVED AS NULL**
  - *Evidence:* Neither ICRISAT (2010) nor MPKV (2023) specifies exact vegetative temperature tolerance limits for Peninsular India varieties in the audited literature.

---

### 1.3 Sugarcane, Cotton, Groundnut, Maize, Bajra, Sorghum, Soybean, Wheat
- **Institutional Attributions vs Parameter Verification:**
  - *Status:* **PARTIAL PROVENANCE MAPPING**
  - *Evidence:* While MPKV (2023) provides comprehensive varietal yield trials and fertilizer recommendations for Vertisols, broad global parameters (e.g., minimum base temperature for germination, exact soil depth thresholds for minor millets) rely on ICAR institute brochures (CICR, DGR, IIMR, IIWBR, IISR) or legacy ICAR agritech compilations.
  - *Limitation:* High-precision physiological thresholds for these crops must be reported with explicit provenance tags (`evidence_status = "provisional_literature"` or `"unverified_parameters"`).

---

## 2. Regional Suitability & Spatial Resolution Limitations

### 2.1 Pilot Taluka Extrapolation
- **Maval and Mulshi Talukas:**
  - *Classification:* `requires_regional_validation` across all 10 priority crops.
  - *Evidence:* MPKV research recommendations released during 2023 focus heavily on the Plain Zone and Scarcity Zone (Vertisols and canal commands of Ahmednagar, Solapur, and eastern Pune). Maval and Mulshi lie in the Western Ghats / High Rainfall Transition Zone characterized by lateritic, acidic, and gravelly soils with steep gradients.
  - *Limitation:* The system cannot certify crop suitability in Maval or Mulshi as verified. It must indicate that field trials in these agroecological conditions are required.
- **Baramati and Indapur Talukas:**
  - *Classification:* `regional_screening` across all 10 priority crops.
  - *Evidence:* MPKV 2023 recommendations apply to the broad Plain Zone Vertisols and scarcity zones. However, individual farms in Baramati and Indapur may feature shallow soil over bedrock, severe canal-seepage salinity (EC $> 2.0\text{ dS/m}$), or hardpans.
  - *Limitation:* Macro-zonal suitability does not guarantee individual farm success. The system must always recommend local soil profile inspection.

---

## 3. Soil & Geospatial Intelligence Limitations

- **ISRIC SoilGrids Coarse Resolution (250m Pixel Size):**
  - *Limitation:* Global gridded soil data (ISRIC SoilGrids) operates at $250\text{ m}$ spatial resolution. It aggregates large land tracts and cannot capture micro-topographic soil variations, local erosion gullies, or field-specific amendment history.
  - *Total vs. Available Nitrogen:* ISRIC SoilGrids estimates total nitrogen (in $\text{cg/kg}$), which reflects organically bound nitrogen. It cannot measure plant-available nitrogen ($\text{NH}_4^+$ and $\text{NO}_3^-$). Fertilizer dosage calculations must never be performed using ISRIC total nitrogen estimates without a mandatory disclaimer requiring laboratory soil testing.
- **Missing Diagnostic Parameters in Satellite/Global Data:**
  - Soil electrical conductivity (salinity), free calcium carbonate ($\text{CaCO}_3$), active lime percentage, and subsoil hardpan depth cannot be reliably extracted from public satellite or coarse raster datasets. These parameters require local laboratory testing.

---

## 4. Meteorological & Climatological Limitations

- **Historical Climatology vs. Weather Forecasts:**
  - Historical 30-year climate normals (from Phase 3 `farm_climate_summaries`) describe macro-climate patterns (average rainfall, average temperature cycles). They are completely blind to inter-annual monsoon delays, unseasonal hail, or cyclonic rain depressions.
  - Operational advice (sowing dates, pesticide spraying, irrigation timing) must rely strictly on real-time 7-to-14 day weather forecasts, never on monthly averages.
- **Forecast Horizon Degradation:**
  - Weather forecasts from Open-Meteo offer high reliability for Days 1–3, moderate reliability for Days 4–7, and significant divergence for Days 8–14. Farm operations involving heavy investment (e.g. planting costly seeds) must not be scheduled based on Day 10+ precipitation forecasts.

---

## 5. Economic & Market Intelligence Limitations

- **Decoupling of Agronomic Feasibility and Financial Profitability:**
  - CropNet's current deployed engine evaluates biological and environmental feasibility (soil, climate, water, regional adaptation).
  - The system has **zero integration with real-time APMC mandi prices, transportation logistics, cold storage availability, or dynamic commodity futures**.
  - A crop that scores $1.0$ (perfect suitability) may experience severe market oversupply and low price realization at harvest.
  - The AI engine is strictly prohibited from making financial return projections, guaranteed net-income claims, or commercial investment recommendations.
Path: file:///Users/siddheshbirewar/Downloads/Cropnet Feature/cropnet/benchmarks/agricultural_intelligence/known_evidence_gaps_and_limitations.md
