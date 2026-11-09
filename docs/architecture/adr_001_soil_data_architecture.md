# Architecture Decision Record (ADR 001)

## Title: Provider-Independent Geospatial Soil Data Ingestion and Farm Extraction Architecture

* **Status:** Accepted
* **Date:** 2026-11-06
* **Deciders:** CropNet Engineering & Agronomy Architecture Team

---

### Context

CropNet AI is being built from scratch as a mobile-first soil intelligence and crop selection platform for Indian farmers. The initial pilot covers four talukas in Pune district, Maharashtra: **Maval, Mulshi, Baramati, and Indapur**.

The system must satisfy two fundamental requirements:
1. Provide reliable, traceable, farm-level soil intelligence derived from existing geospatial datasets without physical laboratory testing in the initial release.
2. Adhere to strict scientific standards: never fabricate missing NPK values, never confuse total nitrogen with available nitrogen, preserve source-specific uncertainty and provenance, and maintain a provider-independent architecture.

---

### Decision

1. **Provider-Independent Architecture (`SoilDataProvider`):**
   * An abstract interface (`SoilDataProvider`) is established with standardized methods: `get_capabilities()`, `check_coverage()`, and `extract_farm_soil()`.
   * Concrete implementations:
     * `SoilGridsProvider`: Primary operational provider utilizing OGC WCS 2.0.1 for 250m global digital soil mapping.
     * `OpenLandMapProvider`: High-resolution (30m) provider utilizing Cloud-Optimized GeoTIFFs (COGs).
     * `NATMOProvider`: Reference adapter documenting the cartographic WMS display limitation.
     * `BhoomiProvider`: Modular future adapter for ICAR-NBSS&LUP once institutional credentials are obtained.
     * `LocalRasterProvider`: Offline-first fallback reading cached regional GeoTIFFs.

2. **Farm Geometry & Spatial Extraction Standards:**
   * Farms are represented as GeoJSON polygon geometries.
   * Polygon areas are computed exclusively using **geodesic / projected methods** (`pyproj.Geod` on WGS84 ellipsoid), strictly avoiding degree-squared approximations.
   * Parameter values are extracted via **polygon masking and zonal statistics** (`shapely` + `rasterio.mask` + `numpy`).
   * Underlying raster resolutions (e.g. 250m or 30m) are explicitly disclosed; pixel interpolation is never claimed as parcel-specific physical soil testing.

3. **Unified Soil Profile Schema:**
   * Standardized schema (`UnifiedSoilProfile`) where every soil property carries its own value, unit, depth, spatial resolution, vintage, uncertainty, source, dataset version, and verification status (`MAP_DERIVED_ESTIMATE`, `REGIONAL_ESTIMATE`, `NOT_AVAILABLE`, `LABORATORY_VERIFIED`).
   * Missing parameters remain `null` with explicit availability status (`not_available`, `partial_coverage`, `source_unavailable`).

4. **Scientific Restrictions & Crop Selection Integration:**
   * Available N, P, and K are stored as `null` with status `NOT_AVAILABLE`.
   * SoilGrids Total Nitrogen is explicitly tagged with a mandatory scientific note explaining that it is the sum of organic and mineral nitrogen, NOT available nitrogen.
   * The crop recommendation engine consumes the soil profile in **Mode A (Regional/Map-Based Suitability)**, which evaluates agronomic suitability from soil texture, pH, depth, organic carbon, and climate without requiring fabricated NPK values.

---

### Recommended Data-Source Combination

* **Phase 0 & MVP:** Deploy **ISRIC SoilGrids 2.0** as the primary live extraction engine (via WCS 2.0.1) due to verified high availability, low latency, full Maharashtra coverage, depth stratification (0–5cm, 5–15cm, etc.), and built-in uncertainty quantification under CC-BY 4.0.
* **Phase 1 Enhancement:** Pre-cache regional 30m clips from **OpenLandMap** in `data_cache/` for Maval, Mulshi, Baramati, and Indapur to provide localized high-resolution texture and SOC refinement without international S3 network latency.
* **Future Institutional Roadmap:** Pursue formal institutional integration with **ICAR-NBSS&LUP BHOOMI** for localized Indian soil series and cadastral village fertility mapping.
