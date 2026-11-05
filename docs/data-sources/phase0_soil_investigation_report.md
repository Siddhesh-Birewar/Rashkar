# CropNet AI — Phase 0 Soil Investigation & Feasibility Report

## Executive Summary

As directed by the Greenfield Implementation Specification and Development Roadmap, Phase 0 required a complete, evidence-based investigation of publicly accessible geospatial soil datasets for CropNet AI before proceeding with full GIS integration.

We investigated four primary candidate sources:
1. **ISRIC SoilGrids** (`soilgrids.org`)
2. **OpenLandMap** (`openlandmap.org`)
3. **NATMO Geoportal** (`geoportal.natmo.gov.in`)
4. **ICAR-NBSS&LUP BHOOMI Geoportal** (`bhoomigeoportal-nbsslup.in`)

---

## 1. Investigation Findings by Data Source

### A. ISRIC SoilGrids 2.0
* **Status:** **FULLY OPERATIONAL & VERIFIED**
* **Access Method:** Direct OGC Web Coverage Service (WCS 2.0.1) endpoints at `https://maps.isric.org/mapserv?map=/map/[property].map`.
* **REST API Notice:** The legacy REST API (`rest.soilgrids.org`) has been deprecated. Our implementation does not depend on it and uses WCS 2.0.1.
* **Tested Properties:**
  * Soil pH in H2O (`phh2o`): raw integer / 10 -> pH (0–14).
  * Soil Organic Carbon (`soc`): raw dg/kg / 10 -> g/kg fine earth.
  * Texture fractions (`sand`, `silt`, `clay`): raw g/kg / 10 -> % (g/100g).
  * Total Nitrogen (`nitrogen`): raw cg/kg / 100 -> g/kg.
  * Cation Exchange Capacity (`cec`): raw mmol(c)/kg / 10 -> cmol(c)/kg.
* **Depth Intervals Verified:** 0–5cm, 5–15cm, 15–30cm, 30–60cm, 60–100cm, 100–200cm.
* **Uncertainty Quantification:** SoilGrids provides distinct layers for median ($Q0.5$), 5th percentile ($Q0.05$), 95th percentile ($Q0.95$), and prediction uncertainty ($SE$).
* **Licensing:** Creative Commons Attribution 4.0 International (CC BY 4.0). Commercial use permitted with attribution.
* **Network Performance:** Average request latency for cropped pilot bounding boxes was **1.5 to 3.5 seconds**.

### B. OpenLandMap (OpenGeoHub)
* **Status:** **OPERATIONAL; HIGH LATENCY ON REMOTE GLOBAL MOSAICS**
* **Access Method:** Cloud-Optimized GeoTIFFs (COGs) on S3/Wasabi (`http://s3.opengeohub.org/global-soil/global_soil_props_v20250204_mosaics/`).
* **Spatial Resolution:** 30m global resolution.
* **Tested Properties:** Soil organic carbon density, pH in H2O, clay, sand, silt fractions.
* **Depths:** 0–30cm, 30–60cm, 60–100cm.
* **Licensing:** CC BY 4.0.
* **Performance Assessment:** Remote byte-range reads on 186 GB global COG mosaics experience network latency (30–60s) from India.
* **Recommendation:** Pre-download regional GeoTIFF clips for the Maharashtra pilot into local storage (`data_cache/`) to enable sub-second 30m lookups.

### C. NATMO Geoportal
* **Status:** **UNAVAILABLE / NON-OPERATIONAL FOR NUMERICAL EXTRACTION**
* **Live Connectivity:** `https://geoportal.natmo.gov.in` returned **HTTP Error 500: Service unavailable**.
* **Data Format Limitation:** NATMO publishes visual Web Map Service (WMS) raster tiles designed for human map viewing. No Web Coverage Service (WCS) or raw numerical GeoTIFFs exist for parcel extraction.
* **Mapping Scale:** Macro-regional cartographic scale (1:1,000,000 to 1:2,000,000).

### D. ICAR-NBSS&LUP BHOOMI Geoportal
* **Status:** **PROTECTED (HTTP 403 FORBIDDEN)**
* **Live Connectivity:** `https://bhoomigeoportal-nbsslup.in/geoserver/wms` returned **HTTP 403 Forbidden**.
* **Access Requirement:** Requires formal institutional credentials and approval from ICAR-NBSS&LUP.
* **Architectural Action:** Implemented modular adapter (`BhoomiProvider`) reporting `Awaiting institutional credentials`. The core platform remains independent of institutional approval.

---

## 2. Sample Extraction Values for the Four Pilot Regions

We extracted real values for all four pilot regions using polygon zonal statistics:

| Parameter | Maval (High Rainfall Foothills) | Mulshi (Western Ghats Valley) | Baramati (Canal/Deep Black Soil) | Indapur (Rain Shadow Vertisol) |
| :--- | :--- | :--- | :--- | :--- |
| **Soil pH (0-5cm)** | **6.50** | **6.44** | **7.29** | **7.07** |
| **Organic Carbon (0-5cm)** | **19.38 g/kg** (1.94%) | **23.48 g/kg** (2.35%) | **15.36 g/kg** (1.54%) | **24.17 g/kg** (2.42%) |
| **Sand Fraction** | 31.09% | 29.66% | 29.36% | 33.51% |
| **Silt Fraction** | 31.03% | 29.43% | 28.35% | 21.84% |
| **Clay Fraction** | 37.89% | 40.91% | 42.30% | 44.64% |
| **USDA Texture Class** | Clay Loam | Clay | Heavy Clay | Heavy Clay |
| **Total Nitrogen** | 2.12 g/kg (Total N) | 2.21 g/kg (Total N) | 1.25 g/kg (Total N) | 1.47 g/kg (Total N) |
| **Cation Exchange Capacity** | 37.30 cmol(c)/kg | 33.31 cmol(c)/kg | 38.24 cmol(c)/kg | 26.61 cmol(c)/kg |
| **Available NPK** | **NOT AVAILABLE** | **NOT AVAILABLE** | **NOT AVAILABLE** | **NOT AVAILABLE** |

---

## 3. Data Quality & Limitations

1. **Resolution vs. Parcel Size:** A 250m raster pixel covers 6.25 hectares (approx. 15.4 acres). Smallholder plots of 1–3 acres fall inside a single pixel or span across 2–4 pixels. Spatial extraction computes area-weighted zonal statistics across intersecting pixels, but underlying resolution remains 250m.
2. **Total Nitrogen vs. Available Nitrogen:** Total Nitrogen in SoilGrids reflects organic and matrix-bound nitrogen. It **MUST NEVER** be treated as plant-available nitrogen ($NH_4^+/NO_3^-$).
3. **Missing Nutrients:** Available Phosphorus and Potassium are not present in approved public rasters. They must remain `null` in the Unified Soil Profile.

---

## 4. Best Data-Source Combination Recommendation

1. **Primary Operational Source:** **ISRIC SoilGrids 2.0 (via WCS 2.0.1)**. Proven high availability, low latency, full Maharashtra coverage, depth stratification, and built-in uncertainty quantification.
2. **Secondary Local Cache:** **OpenLandMap 30m Clips**. Cache pilot talukas locally in `data_cache/` to provide high-resolution texture refinement without international S3 latency.
3. **Future Extension:** **ICAR-NBSS&LUP BHOOMI**. Connect once official institutional credentials are provided.
