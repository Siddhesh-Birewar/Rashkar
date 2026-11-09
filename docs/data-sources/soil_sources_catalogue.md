# CropNet AI — Soil Data Source Catalogue

This catalogue documents the investigation and verification of publicly accessible geospatial soil datasets for CropNet AI, adhering to strict scientific integrity and commercial maintainability standards.

---

## 1. ISRIC SoilGrids 2.0

* **Website:** https://soilgrids.org/
* **Data Server:** https://files.isric.org/soilgrids/latest/data/
* **Access Method:** OGC Web Coverage Service (WCS 2.0.1) via `https://maps.isric.org/mapserv?map=/map/[property].map`
* **Direct REST API Status:** The legacy REST API (`rest.soilgrids.org`) has been deprecated/paused. WCS 2.0.1 and WebDAV bulk access are the approved, fully operational methods.
* **Spatial Resolution:** 250m x 250m grid cells.
* **Depths Supported:** 6 standard depth intervals:
  * 0–5 cm
  * 5–15 cm
  * 15–30 cm
  * 30–60 cm
  * 60–100 cm
  * 100–200 cm
* **Statistical Derivatives:** Mean, Q0.05 (5th percentile), Q0.50 (median), Q0.95 (95th percentile), and uncertainty (standard deviation / standard error of predictions).
* **Licensing:** Creative Commons Attribution 4.0 International (CC BY 4.0). Commercial use is permitted with attribution.
* **Attribution:** *"Soil data derived from SoilGrids 2.0, ISRIC — World Soil Information (https://soilgrids.org)"*
* **Investigated Properties & Conversion Rules:**

| Parameter Key | Map / Coverage | Stored Unit | Scale Factor | Conventional Scientific Unit | Provenance & Scientific Guardrail |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ph` | `phh2o` | $\text{pH} \times 10$ | 10.0 | $\text{pH}$ (0–14) | Extracted from `phh2o_{depth}_mean`. Divide by 10. |
| `soc` | `soc` | $\text{dg/kg}$ | 10.0 | $\text{g/kg}$ fine earth | Soil Organic Carbon content. Multiply by 0.1 for %. |
| `sand_percent` | `sand` | $\text{g/kg}$ | 10.0 | $\%$ (g/100g) | Sand fraction (50–2000 $\mu\text{m}$). Divide by 10. |
| `silt_percent` | `silt` | $\text{g/kg}$ | 10.0 | $\%$ (g/100g) | Silt fraction (2–50 $\mu\text{m}$). Divide by 10. |
| `clay_percent` | `clay` | $\text{g/kg}$ | 10.0 | $\%$ (g/100g) | Clay fraction ($<2 \mu\text{m}$). Divide by 10. |
| `total_nitrogen` | `nitrogen` | $\text{cg/kg}$ | 100.0 | $\text{g/kg}$ | **CRITICAL:** Total Nitrogen is the sum of organic and bound nitrogen. It is **NOT** available mineral nitrogen ($NH_4^+/NO_3^-$) and cannot be compared to fertilizer recommendations. |
| `cation_exchange_capacity` | `cec` | $\text{mmol(c)/kg}$ | 10.0 | $\text{cmol(c)/kg}$ | Fine earth cation exchange capacity at pH 7. Divide by 10. |
| `bulk_density` | `bdod` | $\text{cg/cm}^3$ | 100.0 | $\text{kg/dm}^3$ ($\text{g/cm}^3$) | Bulk density of the fine earth fraction. |
| `wrb_class` | `wrb` | Category | 1.0 | Soil Group | World Reference Base for Soil Resources (WRB) classification. |

---

## 2. OpenLandMap (OpenGeoHub)

* **Website:** https://openlandmap.org/
* **GitHub:** https://github.com/openlandmap/soildb
* **Archive & DOI:** Zenodo DOI: 10.5281/zenodo.15470431
* **Access Method:** Cloud-Optimized GeoTIFFs (COGs) on S3/Wasabi (`http://s3.opengeohub.org/global-soil/global_soil_props_v20250204_mosaics/`) and STAC Browser (`https://stac.openlandmap.org/`).
* **Spatial Resolution:** 30m x 30m grid cells.
* **Depths Supported:** Standard 0–30 cm, 30–60 cm, 60–100 cm (and legacy 0, 10, 30, 60, 100, 200 cm).
* **Modeling Methodology:** Quantile Regression Random Forests combining Landsat, Sentinel, and MODIS Earth Observation with ~500,000 global soil observations.
* **Licensing:** Creative Commons Attribution 4.0 International (CC BY 4.0).
* **Attribution:** *"Soil data derived from OpenLandMap (OpenGeoHub Foundation, Zenodo DOI: 10.5281/zenodo.15470431)"*
* **Operational Findings:**
  * Global 30m mosaic files are approximately 186 GB per layer.
  * Direct remote byte-range reads via GDAL/rasterio vsicurl work, but experience high network latency and intermittent timeouts from Indian internet connections.
  * **Recommendation:** Use OpenLandMap by caching regional 30m clips locally in `data_cache/` for pilot talukas, rather than issuing synchronous 186 GB HTTP range queries on each farmer request.

---

## 3. NATMO Geoportal

* **Website:** https://www.geoportal.natmo.gov.in/
* **Organisation:** National Atlas & Thematic Mapping Organisation (Department of Science & Technology, Govt. of India).
* **Investigated Layers:** National Atlas Thematic Soil Series (Soil Cover, Soil Types, Soil Reaction, Soil Texture, Soil Fertility).
* **Mapping Scale:** 1:1,000,000 to 1:2,000,000 (Macro Regional / National Scale).
* **Data Format:** OGC Web Map Service (WMS) visual raster tiles only.
* **Status & Operational Findings:**
  * Live connectivity check to `https://geoportal.natmo.gov.in` returned **HTTP Error 500: Service unavailable**.
  * No Web Coverage Service (WCS) or downloadable numerical GeoTIFFs are provided by NATMO.
  * No Web Feature Service (WFS) with parcel-level attribute extraction is publicly accessible.
  * **Recommendation:** Mark NATMO provider as non-operational for numerical extraction. Retain adapter for reference and cartographic overlay only.

---

## 4. ICAR-NBSS&LUP BHOOMI Geoportal

* **Website:** https://bhoomigeoportal-nbsslup.in/
* **Organisation:** ICAR – National Bureau of Soil Survey and Land Use Planning, Nagpur.
* **GeoServer Endpoint:** `https://bhoomigeoportal-nbsslup.in/geoserver/wms`
* **Mapping Scale:** 1:250,000 national, 1:50,000 district, and select 1:10,000 cadastral village series.
* **Candidate Properties:** Soil Series, Soil Depth, Soil Texture Class, Slope, Erosion, Drainage, pH, Organic Carbon.
* **Status & Operational Findings:**
  * Live connectivity check confirmed that public requests to `https://bhoomigeoportal-nbsslup.in/geoserver/wms?request=GetCapabilities` return **HTTP Error 403: Forbidden**.
  * Access to raw GIS features requires formal institutional partnership and API credentials from ICAR-NBSS&LUP.
  * **Recommendation:** Keep BHOOMI modular as a future provider adapter (`BhoomiProvider`). Do not block MVP launch on institutional approval or paid access.
