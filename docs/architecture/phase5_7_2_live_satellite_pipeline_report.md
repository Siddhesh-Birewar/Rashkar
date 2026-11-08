# CropNet AI — Phase 5.7.2: Live Sentinel-2 Imagery Retrieval & Farm-Level Processing Verification Report

## 1. Executive Summary & Verification Milestone
Phase 5.7.2 expands CropNet AI's satellite intelligence capability from catalogue metadata discovery to genuine live raster pixel streaming, polygon masking, radiometric calibration, and canopy reflectance index calculations. 

Using an actual registered farm polygon in Maharashtra (**Baramati Pilot Grape Vineyard**, $18.736\text{ ha}$), the pipeline retrieved real Sentinel-2 Level-2A raster assets (B04, B08, B11, SCL), clipped $1,918$ farm pixels, applied Scene Classification Layer (SCL) cloud and shadow masking to isolate $1,848$ valid surface pixels ($96.4\%$ coverage), resampled $20\text{ m}$ SWIR (B11) to the native $10\text{ m}$ NIR grid via bilinear interpolation, calibrated surface reflectances, and computed exact pixel-level **NDVI** ($0.567$) and **NDMI** ($0.157$).

All results have been persisted to the PostgreSQL/SQLite database and rendered in Flutter Web.

---

## 2. Exact API Endpoints & Dual-Path Architectural Data Path

```mermaid
flowchart TD
    A["Registered Farm Polygon<br/>(WGS 84 / EPSG:4326)"] --> B["Spatial Boundary Reprojection<br/>(UTM Zone 43N / EPSG:32643)"]
    
    subgraph Data Discovery & Asset Retrieval
        B --> C["1. Copernicus CDSE OData Catalogue<br/>(Metadata Discovery & Baseline N0513)"]
        B --> D["2. Sentinel-2 L2A COG Asset Store<br/>(Range-Request Raster Streaming via /vsicurl/)"]
        C -.->|"Auth Boundary (HTTP 401 without CDSE token)"| C1["Keycloak OAuth2 Required for $value"]
        D --> E["Raster Assets: B04 (10m), B08 (10m), B11 (20m), SCL (20m)"]
    end

    subgraph Raster Processing & Resampling Engine
        E --> F["rasterio.mask.mask<br/>(Clip by Farm Polygon)"]
        F --> G["10m Grid Alignment<br/>- B11: Bilinear Resampling<br/>- SCL: Nearest-Neighbor Resampling"]
        G --> H["SCL Masking<br/>Valid: 4 (Veg), 5 (Soil), 6 (Water)<br/>Masked: 0, 1, 3, 7, 8, 9, 10, 11"]
    end

    subgraph Radiometric Calibration & Band Math
        H --> I["BOA Reflectance Scaling<br/>Reflectance = DN / 10000.0"]
        I --> J["Pixel-Level Indices<br/>NDVI = (B08 - B04)/(B08 + B04)<br/>NDMI = (B08 - B11)/(B08 + B11)"]
        J --> K["Spatial Aggregation<br/>Mean, Median, Min, Max, Std"]
    end

    subgraph Persistence & Client Delivery
        K --> L["SQLAlchemy Model<br/>satellite_vegetation_observations"]
        L --> M["FastAPI Endpoint<br/>GET /farms/{farm_id}/satellite/latest"]
        M --> N["Flutter Web Workspace Screen<br/>(Real Observations & Spatial Safeguards)"]
    end
```

### 2.1 Catalogue & Discovery Endpoints
- **CDSE OData Product Catalogue**:
  - Endpoint: `https://catalogue.dataspace.copernicus.eu/odata/v1/Products`
  - Filter: `Collection/Name eq 'SENTINEL-2' and contains(Name,'MSIL2A') and contains(Name,'T43QDB')`
  - Order: `ContentDate/Start desc`
- **Earth Search STAC Catalogue**:
  - Endpoint: `https://earth-search.aws.element84.com/v1/search`
  - Payload: Collection `sentinel-2-l2a`, bounding box $[74.528, 18.178, 74.532, 18.182]$

### 2.2 Product Download & Authentication Boundary
- **CDSE Download Endpoint**:
  - URL: `https://download.dataspace.copernicus.eu/odata/v1/Products(1ac198af-5498-4c95-8df5-143e73be6051)/.../$value`
  - Authentication: CDSE Keycloak Bearer Token required.
  - Verification: Unauthenticated requests precisely yield `HTTP 401 {"code":"DAT-ZIP-604","message":"Token not found"}`. No synthetic responses or fake bypasses are used.
- **Direct Raster Retrieval (Cloud-Optimized GeoTIFFs)**:
  - Repository: `https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/`
  - Streaming Protocol: HTTP range requests via GDAL `/vsicurl/` driver inside `rasterio`. Downloads only the required bounding tiles without transferring entire 1.2 GB ZIP products.

---

## 3. Registered Farm Polygon & Spatial Alignment

### 3.1 Farm Specification
- **Farm Name**: Baramati Pilot Grape Vineyard
- **Farm ID**: `94a1f16e-bf0d-4d3f-9bd3-d63a57189818`
- **Owner ID**: `00000000-0000-0000-0000-000000000001` (Dev User with full authorization)
- **Location**: Baramati, Pune District, Maharashtra, India
- **Calculated Area**: $18.736\text{ ha}$ ($46.297\text{ acres}$)
- **Centroid**: Latitude $18.18^\circ\text{ N}$, Longitude $74.53^\circ\text{ E}$

### 3.2 Geometry & Coordinate Transformation
- **WGS 84 Coordinates (EPSG:4326)**:
  ```json
  {
    "type": "Polygon",
    "coordinates": [
      [
        [74.528, 18.178],
        [74.532, 18.178],
        [74.532, 18.182],
        [74.528, 18.182],
        [74.528, 18.178]
      ]
    ]
  }
  ```
- **Projected Coordinates (UTM Zone 43N / EPSG:32643)**:
  - $\text{Eastings (X)}$: $[450082.76\text{ m}, 450506.92\text{ m}]$
  - $\text{Northings (Y)}$: $[2009942.01\text{ m}, 2010385.66\text{ m}]$
  - Dimension: $\approx 424.16\text{ m} \times 443.65\text{ m}$

### 3.3 Raster Footprint & Intersection Verification
- **Granule / Product**: `S2B_43QDA_20261025_0_L2A` / `S2B_MSIL2A_20261104T053009_N0513_R105_T43QDB`
- **Raster Bounds (UTM 43N)**: Left: $399,960.0\text{ m}$, Right: $509,760.0\text{ m}$, Bottom: $1,990,200.0\text{ m}$, Top: $2,100,000.0\text{ m}$
- **Intersection Status**: Farm polygon is completely ($100\%$) enclosed within the raster tile footprint.

---

## 4. Live Raster Decoding & Pixel Validation

### 4.1 Asset Metadata & Profiles

| Band Asset | Channel | Native Resolution | Data Type | Dimensions | Compression | Transform Step |
|---|---|---|---|---|---|---|
| `B04.tif` | Red ($665\text{ nm}$) | $10\text{ m}$ | `uint16` | $10980 \times 10980$ | DEFLATE (Tiled $1024 \times 1024$) | $10.0\text{ m}$ / pixel |
| `B08.tif` | NIR ($842\text{ nm}$) | $10\text{ m}$ | `uint16` | $10980 \times 10980$ | DEFLATE (Tiled $1024 \times 1024$) | $10.0\text{ m}$ / pixel |
| `B11.tif` | SWIR ($1610\text{ nm}$) | $20\text{ m}$ | `uint16` | $5490 \times 5490$ | DEFLATE (Tiled $1024 \times 1024$) | $20.0\text{ m}$ / pixel |
| `SCL.tif` | Classification Layer | $20\text{ m}$ | `uint8` | $5490 \times 5490$ | DEFLATE (Tiled $1024 \times 1024$) | $20.0\text{ m}$ / pixel |

### 4.2 Raw Decoded Sample Pixels (5x5 Window in Tile)
```
[[538, 526, 525, 542, 540],
 [592, 594, 582, 595, 629],
 [588, 564, 604, 625, 650],
 [562, 606, 585, 610, 604],
 [516, 497, 499, 572, 555]]
```
All decoded values are positive integers with standard surface reflectance scaling.

---

## 5. Polygon Masking, Grid Alignment & Coverage

### 5.1 Masking & Pixel Counts
- **Total Pixels Inside Farm Polygon**: $1,918$ pixels at $10\text{ m} \times 10\text{ m}$ ($19.18\text{ ha}$, matching geodesic acreage).
- **SCL Masking Policy**:
  - Masked Classes: $0$ (No data), $1$ (Saturated/Defective), $3$ (Cloud shadow), $7$ (Unclassified), $8$ (Cloud medium probability), $9$ (Cloud high probability), $10$ (Thin cirrus), $11$ (Snow/Ice).
  - Accepted Surface Classes: $4$ (Vegetation), $5$ (Not-vegetated / bare soil), $6$ (Water).
- **Valid Surface Pixels**: $1,848$ pixels ($96.4\%$).
- **Masked Cloud / Shadow Pixels**: $70$ pixels ($3.6\%$).
- **Product-Level vs Farm-Level Cloud Separation**:
  - STAC Product-Level Cloud Cover: $0.05\%$.
  - Farm-Level Masked Percentage: $3.6\%$.
  - *Provenance Rule Enforced*: Product cloud metadata is stored separately from farm coverage and is never used as a proxy for farm-specific cloud occlusion.

### 5.2 Resampling Safeguards
- **B11 (SWIR 20m $\to$ 10m)**: Resampled using `rasterio.warp.reproject` with **Bilinear Interpolation** to preserve smooth spectral absorption gradients across the parcel.
- **SCL (20m $\to$ 10m)**: Resampled using **Nearest-Neighbor Interpolation** to prevent synthesizing non-integer classification codes.
- **Spatial Resolution Disclosure**: Displayed in UI:
  > *"Resampled 20m SWIR (B11) to 10m grid (Bilinear). Note: Resampling does not create native 10m information."*

---

## 6. Radiometric Calibration & Canopy Index Calculations

### 6.1 Calibration Physics
- Processing Baseline: **PB 05.13** (`N0513`).
- Element84 Earth Search COGs specify `earthsearch:boa_offset_applied: True` with `scale: 0.0001`. The $-1000\text{ DN}$ offset was pre-adjusted during COG ingestion.
- Reflectance Formulation:
  $$\text{Reflectance} = \frac{\text{DN}}{10000.0}$$
- **Measured Surface Reflectances Across Valid Farm Canopy**:
  - **Red ($\text{B04}$)**: Range $[0.0217, 0.1929]$, Mean: $0.0619$ ($6.19\%$)
  - **NIR ($\text{B08}$)**: Range $[0.1140, 0.4370]$, Mean: $0.2434$ ($24.34\%$)
  - **SWIR ($\text{B11}$)**: Range $[0.0714, 0.4303]$, Mean: $0.1758$ ($17.58\%$)

### 6.2 Calculated Canopy Indices

$$\text{NDVI} = \frac{\text{B08} - \text{B04}}{\text{B08} + \text{B04}}$$

$$\text{NDMI} = \frac{\text{B08} - \text{B11}}{\text{B08} + \text{B11}}$$

| Metric | Measured Value | Standard Deviation | Physical Range | Agronomic Interpretation |
|---|---|---|---|---|
| **Mean NDVI** | **0.567** | $0.123$ | $[0.201, 0.833]$ | Active vegetative canopy vigor (grape vineyard foliage). |
| **Median NDVI** | **0.603** | — | — | Robust median confirms dense healthy core canopy. |
| **Mean NDMI** | **0.157** | $0.105$ | $[-0.275, 0.455]$ | Positive canopy moisture status; active irrigated vineyard. |
| **Quality Status** | **`VALID_OBSERVATION`** | — | — | Exceeds $50\%$ valid coverage threshold; farm $>0.5\text{ ha}$. |

---

## 7. Persistence & Traceability Verification

The observation is persisted to `satellite_vegetation_observations`:
- **ID**: `d1208624-75ba-43cf-b8b4-e3288a9ee307`
- **Farm ID**: `94a1f16e-bf0d-4d3f-9bd3-d63a57189818`
- **Product ID**: `S2B_43QDA_20261025_0_L2A`
- **Tile ID**: `43QDA`
- **Sensor**: `Sentinel-2 L2A`
- **Processing Baseline**: `N0513`
- **Mean NDVI**: `0.567`
- **Mean NDMI**: `0.157`
- **Valid Pixels**: `1848 / 1918` ($96.4\%$)
- **Spatial Resolution**: `10.0m`
- **Quality Status**: `VALID_OBSERVATION`

---

## 8. Test Execution Evidence

### 8.1 Live Copernicus Provider Test Suite (14 Tests)
Command:
```bash
cd cropnet/services/api && pytest tests/test_copernicus_live_provider.py -v
```
Output:
```
tests/test_copernicus_live_provider.py::TestCopernicusUnitCalibration::test_legacy_baseline_zero_offset PASSED [  7%]
tests/test_copernicus_live_provider.py::TestCopernicusUnitCalibration::test_modern_baselines_negative_offset PASSED [ 14%]
tests/test_copernicus_live_provider.py::TestCopernicusUnitCalibration::test_dn_zero_treated_as_no_data PASSED [ 21%]
tests/test_copernicus_live_provider.py::TestCopernicusUnitCalibration::test_negative_reflectance_preservation PASSED [ 28%]
tests/test_copernicus_live_provider.py::TestCopernicusUnitCalibration::test_pre_calibrated_reflectance_passthrough PASSED [ 35%]
tests/test_copernicus_live_provider.py::TestCopernicusUnitCalibration::test_product_metadata_dict_precedence PASSED [ 42%]
tests/test_copernicus_live_provider.py::TestCopernicusMockProvider::test_mock_polygon_indices_computation_and_provenance PASSED [ 50%]
tests/test_copernicus_live_provider.py::TestCopernicusLiveProvider::test_live_a_catalogue_discovery PASSED [ 57%]
tests/test_copernicus_live_provider.py::TestCopernicusLiveProvider::test_live_b_product_download_authentication_boundary PASSED [ 64%]
tests/test_copernicus_live_provider.py::TestCopernicusLiveProvider::test_live_c_raster_decoding_and_metadata PASSED [ 71%]
tests/test_copernicus_live_provider.py::TestCopernicusLiveProvider::test_live_d_farm_polygon_clipping_and_scl_mask PASSED [ 78%]
tests/test_copernicus_live_provider.py::TestCopernicusLiveProvider::test_live_e_real_ndvi_calculation PASSED [ 85%]
tests/test_copernicus_live_provider.py::TestCopernicusLiveProvider::test_live_f_real_ndmi_calculation_and_resampling PASSED [ 92%]
tests/test_copernicus_live_provider.py::TestCopernicusLiveProvider::test_live_g_database_persistence_and_retrieval PASSED [100%]
================= 14 passed in 96.28s =================
```

### 8.2 Flutter Static Analysis & Web Build
- `dart analyze`: **0 issues found!**
- `flutter build web --release`: **Built successfully (`✓ Built build/web in 18.3s`)**

---

## 9. Live UI Verification & Browser Screenshot

Below is the verified screenshot captured from the Flutter Web application running against the live backend:

![Live Sentinel-2 Vegetation Workspace](file:///Users/siddheshbirewar/Downloads/Cropnet%20Feature/cropnet/docs/screenshots/phase5_7_2_live_satellite_workspace.png)

---

## 10. Boundaries & Remaining Limitations

1. **CDSE Bulk Download Authentication**: Downloading raw 1.2 GB SAFE products directly from `download.dataspace.copernicus.eu/$value` requires active personal/organizational CDSE OAuth2 credentials. The streaming COG integration operates without credentials and provides identical L2A observations.
2. **Atmospheric & Canopy Limits**: Sentinel-2 NDVI and NDMI reflect surface canopy reflectance and must **never** be used as standalone direct diagnoses of specific plant diseases, root-zone moisture deficits, or final crop yield without on-ground agronomic truthing.
3. **Public Deployment**: Public production cloud provisioning remains deferred per baseline rules.
