"""
Rigorous Copernicus Sentinel-2 Provider Verification Test Suite.

Explicitly Separated Sections:
1. SECTION 1 — UNIT TESTS (Radiometric calibration matrix, baseline handling, DN=0 masking)
2. SECTION 2 — MOCK-PROVIDER INTEGRATION TESTS (Simulated catalog & polygon index calculation)
3. SECTION 3 — LIVE-PROVIDER INTEGRATION TESTS (Real network query against Copernicus CDSE OData API)

Auditing Principle:
Mocked retrieval is strictly labeled as MOCK and never reported as live verification.
Live queries record actual provider metadata, product ID, baseline, and coordinates.
"""
import os
import pytest
from datetime import datetime
import httpx

from cropnet.services.api.app.services.satellite.copernicus_client import (
    copernicus_client,
    calibrate_dn_to_reflectance,
    convert_raw_dn_to_reflectance,
    validate_cog_reflectance_conversion,
    SCL_MASKED_CLASSES,
    SCL_VALID_CLASSES,
    CDSE_ODATA_URL,
)


# ===========================================================================
# SECTION 1 — UNIT TESTS (Offline Deterministic Radiometric Calibration)
# ===========================================================================

class TestCopernicusUnitCalibration:
    """Offline unit tests verifying radiometric calibration mathematics."""

    def test_legacy_baseline_zero_offset(self):
        """Legacy baselines (PB < 04.00, e.g. N0214, N0300) must apply BOA_ADD_OFFSET = 0 DN."""
        # Reflectance = DN / 10000.0
        val = calibrate_dn_to_reflectance(2500.0, processing_baseline="N0214")
        assert pytest.approx(val, 0.0001) == 0.2500
        val3 = calibrate_dn_to_reflectance(1800.0, processing_baseline="N0301")
        assert pytest.approx(val3, 0.0001) == 0.1800

    def test_modern_baselines_negative_offset(self):
        """Baselines PB >= 04.00 (N0400, N0500, N0510, N0511, N0513) must apply BOA_ADD_OFFSET = -1000 DN."""
        # Reflectance = (DN - 1000.0) / 10000.0
        val_0400 = calibrate_dn_to_reflectance(3000.0, processing_baseline="N0400")
        assert pytest.approx(val_0400, 0.0001) == 0.2000

        val_0500 = calibrate_dn_to_reflectance(3500.0, processing_baseline="N0500")
        assert pytest.approx(val_0500, 0.0001) == 0.2500

        val_0510 = calibrate_dn_to_reflectance(5000.0, processing_baseline="N0510")
        assert pytest.approx(val_0510, 0.0001) == 0.4000

        val_0511 = calibrate_dn_to_reflectance(2200.0, processing_baseline="N0511")
        assert pytest.approx(val_0511, 0.0001) == 0.1200

        val_0513 = calibrate_dn_to_reflectance(4500.0, processing_baseline="N0513")
        assert pytest.approx(val_0513, 0.0001) == 0.3500

    def test_dn_zero_treated_as_no_data(self):
        """In Sentinel-2 Level-2A raster specifications, DN = 0 is strictly reserved for NO_DATA."""
        assert calibrate_dn_to_reflectance(0.0, processing_baseline="N0500") is None
        assert calibrate_dn_to_reflectance(0, processing_baseline="N0214") is None

    def test_negative_reflectance_preservation(self):
        """Over dark surfaces or atmospheric over-correction, Level-2A BOA reflectance can be negative."""
        # DN = 800 in PB N0500 -> (800 - 1000)/10000 = -0.020
        neg = calibrate_dn_to_reflectance(800.0, processing_baseline="N0500", allow_negative_reflectance=True)
        assert pytest.approx(neg, 0.0001) == -0.0200

        # When clamped to positive surface reflectance:
        clamped = calibrate_dn_to_reflectance(800.0, processing_baseline="N0500", allow_negative_reflectance=False)
        assert clamped == 0.0

    def test_pre_calibrated_reflectance_passthrough(self):
        """If provider already returns calibrated surface reflectance float [0.0, 1.0], no offset/scale is reapplied."""
        res = calibrate_dn_to_reflectance(0.3845, is_calibrated_reflectance=True)
        assert res == 0.3845

    def test_product_metadata_dict_precedence(self):
        """Product metadata dict directly supplies BOA_ADD_OFFSET and QUANTIFICATION_VALUE."""
        meta = {
            "BOA_ADD_OFFSET": -1000.0,
            "QUANTIFICATION_VALUE": 10000.0,
            "processing_baseline": "05.10",
        }
        val = calibrate_dn_to_reflectance(4200.0, metadata=meta)
        assert pytest.approx(val, 0.0001) == 0.3200

    def test_validate_cog_offset_already_applied(self):
        """Element 84 Earth Search COGs with earthsearch:boa_offset_applied=True must use scale=0.0001, offset=0.0."""
        props = {"earthsearch:boa_offset_applied": True, "s2:processing_baseline": "05.13"}
        scale, offset, status = validate_cog_reflectance_conversion(item_props=props)
        assert scale == 0.0001
        assert offset == 0.0
        assert status == "HARMONIZED_COG_BOA_OFFSET_ALREADY_APPLIED"

    def test_validate_cog_offset_not_applied(self):
        """COGs with earthsearch:boa_offset_applied=False on modern baseline PB>=04.00 must apply -0.10 offset."""
        props = {"earthsearch:boa_offset_applied": False, "s2:processing_baseline": "05.13"}
        scale, offset, status = validate_cog_reflectance_conversion(item_props=props)
        assert scale == 0.0001
        assert offset == -0.10
        assert status == "RAW_SAFE_DN_OFFSET_REQUIRED"

    def test_validate_cog_geotiff_embedded_tags(self):
        """Embedded GeoTIFF tags for non-default scale/offset take precedence."""
        scale, offset, status = validate_cog_reflectance_conversion(
            raster_scales=(0.0002,), raster_offsets=(-0.05,)
        )
        assert scale == 0.0002
        assert offset == -0.05
        assert status == "GEOTIFF_EMBEDDED_METADATA"

    def test_validate_cog_contradictory_metadata(self):
        """Contradictory metadata (e.g. negative scale or invalid tags) fails closed with CONTRADICTORY_METADATA_UNVERIFIED."""
        scale, offset, status = validate_cog_reflectance_conversion(
            raster_scales=(-0.0001,), raster_offsets=(0.0,)
        )
        assert status == "CONTRADICTORY_METADATA_UNVERIFIED"
        assert scale == 0.0
        assert offset == 0.0

    def test_validate_cog_missing_metadata(self):
        """Missing metadata fails closed with MISSING_CONVERSION_METADATA_UNVERIFIED."""
        scale, offset, status = validate_cog_reflectance_conversion(item_props=None, asset_dict=None)
        assert status == "MISSING_CONVERSION_METADATA_UNVERIFIED"
        assert scale == 0.0
        assert offset == 0.0

    def test_validate_cog_precalibrated_float(self):
        """Pre-calibrated float reflectance yields unity scale and zero offset."""
        scale, offset, status = validate_cog_reflectance_conversion(is_calibrated_reflectance=True)
        assert scale == 1.0
        assert offset == 0.0
        assert status == "PRE_CALIBRATED_FLOAT"


# ===========================================================================
# SECTION 2 — MOCK-PROVIDER INTEGRATION TESTS
# ===========================================================================

class TestCopernicusMockProvider:
    """Integration tests using simulated raster / mocked API provider."""

    def test_mock_polygon_indices_computation_and_provenance(self):
        """Verify computation over Baramati demonstration geometry with explicit mock provenance."""
        import unittest.mock
        qa_polygon = {
            "type": "Polygon",
            "coordinates": [[[74.5, 18.1], [74.52, 18.1], [74.52, 18.12], [74.5, 18.12], [74.5, 18.1]]]
        }
        mock_raster_result = {
            "sensor": "Sentinel-2 L2A",
            "spatial_resolution_meters": 10.0,
            "b11_native_resolution_meters": 20.0,
            "b08_native_resolution_meters": 10.0,
            "target_grid_meters": 10.0,
            "resampling_method": "bilinear",
            "copernicus_provider_status": "AUTHENTICATED",
            "mean_ndvi": 0.58,
            "mean_ndmi": 0.25,
            "valid_pixel_count": 50,
            "quality_status": "VALID_OBSERVATION",
        }
        with unittest.mock.patch.object(copernicus_client, "fetch_live_raster_indices", return_value=mock_raster_result):
            res = copernicus_client.compute_polygon_indices(qa_polygon, farm_area_ha=2.5)
            assert res["sensor"] == "Sentinel-2 L2A"
            assert res["spatial_resolution_meters"] == 10.0
            assert res["b11_native_resolution_meters"] == 20.0
            assert res["b08_native_resolution_meters"] == 10.0
            assert res["target_grid_meters"] == 10.0
            assert res["resampling_method"] == "bilinear"
            assert res["copernicus_provider_status"] == "AUTHENTICATED"
            assert res["mean_ndvi"] is not None
            assert 0.0 <= res["mean_ndvi"] <= 1.0

        # Unmocked / retrieval failure must fail closed to PROVIDER_UNAVAILABLE
        with unittest.mock.patch.object(copernicus_client, "fetch_live_raster_indices", return_value=None):
            res_fail = copernicus_client.compute_polygon_indices(qa_polygon, farm_area_ha=2.5)
            assert res_fail["quality_status"] == "NO_USABLE_OBSERVATION"
            assert res_fail["copernicus_provider_status"] == "PROVIDER_UNAVAILABLE"
            assert res_fail["mean_ndvi"] is None


# ===========================================================================
# SECTION 3 — LIVE-PROVIDER INTEGRATION TESTS (Copernicus CDSE & Sentinel-2 Pipeline)
# ===========================================================================

class TestCopernicusLiveProvider:
    """
    Genuine live provider test suite verifying the complete Sentinel-2 L2A pipeline:
    A. Catalogue discovery (CDSE OData public catalogue).
    B. Product download authentication boundary (precisely reports CDSE credentials requirement).
    C. Raster decoding (Direct GDAL/rasterio opening of Sentinel-2 L2A band).
    D. Farm polygon clipping (Real Baramati Pilot Grape Vineyard polygon, SCL masking).
    E. Real NDVI calculation (Pixel-level band math on valid calibrated pixels).
    F. Real NDMI calculation (Bilinear resampling of 20m SWIR B11 to 10m grid).
    G. Database persistence and retrieval (Verification of database models & metadata).
    """

    BARAMATI_FARM_POLYGON = {
        "type": "Polygon",
        "coordinates": [
            [
                [74.528, 18.178],
                [74.532, 18.178],
                [74.532, 18.182],
                [74.528, 18.182],
                [74.528, 18.178],
            ]
        ],
    }
    BARAMATI_FARM_ID = "94a1f16e-bf0d-4d3f-9bd3-d63a57189818"
    BARAMATI_FARM_AREA_HA = 18.736

    def test_live_a_catalogue_discovery(self):
        """
        [STEP A] Queries Copernicus Data Space Ecosystem (CDSE) public OData service
        for live Sentinel-2 Level-2A products covering Baramati / Pune tile T43QDB.
        Records live product metadata, processing baseline, and acquisition date.
        """
        tile_id = "T43QDB"
        try:
            items = copernicus_client.search_odata_scenes(tile_id=tile_id, top=2)
        except Exception as e:
            pytest.skip(f"Live Copernicus CDSE endpoint unreachable: {e}")

        if not items:
            pytest.skip(
                f"No Sentinel-2 L2A products returned by CDSE OData API for tile {tile_id}."
            )

        first_product = items[0]
        product_id = first_product.get("Id")
        product_name = first_product.get("Name", "")
        content_date = first_product.get("ContentDate", {})
        start_date = content_date.get("Start")
        footprint = str(first_product.get("Footprint", ""))

        baseline = "UNKNOWN"
        for part in product_name.split("_"):
            if part.startswith("N") and len(part) >= 4 and part[1:5].isdigit():
                baseline = part[:5]
                break

        print("\n--- [STEP A] LIVE COPERNICUS CDSE QUERY EVIDENCE ---")
        print(f"Provider: Copernicus Data Space Ecosystem (CDSE) OData v1 API ({CDSE_ODATA_URL})")
        print(f"Product Identifier: {product_id}")
        print(f"Product Name: {product_name}")
        print(f"Acquisition Date (Start): {start_date}")
        print(f"Processing Baseline: {baseline}")
        print(f"MGRS Tile: {tile_id} (Baramati / Pune, Maharashtra)")
        print(f"QA Footprint: {footprint[:120]}...")
        print(f"Status: LIVE_QUERY_SUCCESS")
        print("----------------------------------------------------\n")

        assert product_id is not None
        assert "MSIL2A" in product_name
        assert tile_id in product_name
        assert start_date is not None

        calibrated = calibrate_dn_to_reflectance(3000.0, processing_baseline=baseline)
        if baseline != "UNKNOWN" and int(baseline.replace("N", "")[:3]) >= 40:
            assert pytest.approx(calibrated, 0.0001) == 0.2000

    def test_live_b_product_download_authentication_boundary(self):
        """
        [STEP B] Tests the CDSE OData direct download endpoint.
        Precisely reports that token authentication is required for full product download.
        Never substitutes a mock or fakes passed status when uncredentialed.
        """
        diag = copernicus_client.test_cdse_download_access()
        print("\n--- [STEP B] CDSE DOWNLOAD AUTHENTICATION BOUNDARY ---")
        print(f"Download URL: {diag['url']}")
        print(f"HTTP Status: {diag['status_code']}")
        print(f"OAuth2 Authenticated: {diag['authenticated']}")
        print(f"Response Preview: {diag.get('response_preview')}")
        print("------------------------------------------------------\n")

        # In our environment without paid/personal CDSE user credentials,
        # CDSE download endpoint returns HTTP 401 with token error code DAT-ZIP-604.
        if not diag["authenticated"]:
            assert diag["status_code"] == 401
            assert "Token not found" in diag.get("response_preview", "")
        else:
            assert diag["status_code"] in (200, 302)

    def test_live_c_raster_decoding_and_metadata(self):
        """
        [STEP C] Verifies direct raster decoding using rasterio on real Sentinel-2 L2A COG.
        Inspects raster profile, CRS, 10m affine transform, and non-empty pixel arrays.
        """
        import rasterio
        url = "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/43/Q/DA/2026/11/S2B_43QDA_20261104_0_L2A/B04.tif"

        try:
            with rasterio.open(url) as src:
                profile = src.profile
                crs = src.crs
                transform = src.transform
                width = src.width
                height = src.height
                # Read a 5x5 sample window
                sample_pixels = src.read(1, window=((5000, 5005), (5000, 5005)))
        except Exception as e:
            pytest.skip(f"Live raster endpoint unreachable: {e}")

        print("\n--- [STEP C] RASTER DECODING EVIDENCE ---")
        print(f"Raster URL: {url}")
        print(f"Driver: {profile['driver']}")
        print(f"CRS: {crs}")
        print(f"Dimensions: {width} x {height}")
        print(f"Pixel Resolution: {transform.a}m x {-transform.e}m")
        print(f"Sample 5x5 Decoded Pixels (DN):\n{sample_pixels}")
        print("-----------------------------------------\n")

        assert profile["driver"] == "GTiff"
        assert str(crs) == "EPSG:32643"
        assert transform.a == 10.0
        assert transform.e == -10.0
        assert width == 10980
        assert height == 10980
        assert sample_pixels.shape == (5, 5)
        assert sample_pixels.dtype.kind in ("u", "i")
        assert (sample_pixels > 0).all()

    def test_live_d_farm_polygon_clipping_and_scl_mask(self):
        """
        [STEP D] Clips real Sentinel-2 L2A rasters (B04 and SCL) using the registered
        Baramati Pilot Grape Vineyard polygon. Verifies total pixel count, SCL masking,
        and valid coverage percentage.
        """
        live_res = copernicus_client.fetch_live_raster_indices(
            polygon_geojson=self.BARAMATI_FARM_POLYGON,
            farm_area_ha=self.BARAMATI_FARM_AREA_HA,
        )
        if not live_res:
            pytest.skip("Live raster fetch failed due to network / provider connectivity.")

        print("\n--- [STEP D] FARM POLYGON CLIPPING & MASKING EVIDENCE ---")
        print(f"Farm: Baramati Pilot Grape Vineyard ({self.BARAMATI_FARM_AREA_HA} ha)")
        print(f"Total Farm Pixels: {live_res['total_pixel_count']}")
        print(f"Valid Pixels (SCL classes 4, 5, 6): {live_res['valid_pixel_count']}")
        print(f"Invalid Pixels (Cloud / Shadow): {live_res['total_pixel_count'] - live_res['valid_pixel_count']}")
        print(f"Farm Coverage %: {live_res['farm_coverage_percent']}%")
        print(f"Product-Level Cloud Cover: {live_res['product_cloud_coverage_percent']}%")
        print(f"Farm-Level Cloud Masked: {live_res['cloud_masked_percent']}%")
        print("--------------------------------------------------------\n")

        assert live_res["total_pixel_count"] == 1918
        assert live_res["valid_pixel_count"] == 1848
        assert live_res["farm_coverage_percent"] == 96.4
        assert live_res["cloud_masked_percent"] == 0.0
        assert live_res["boundary_masked_percent"] == 3.6
        assert live_res["vegetation_pixel_count"] == 1104
        assert live_res["bare_soil_pixel_count"] == 744
        assert live_res["water_pixel_count"] == 0
        assert live_res["quality_status"] == "VALID_OBSERVATION_WITH_MASKED_PIXELS"
        assert live_res["radiometric_conversion_provenance"] == "HARMONIZED_COG_BOA_OFFSET_ALREADY_APPLIED"
        assert live_res["polygon_area_hectares"] == 18.736
        assert live_res["raster_discretized_area_hectares"] == 19.180

    def test_live_e_real_ndvi_calculation(self):
        """
        [STEP E] Validates pixel-level NDVI calculation: (B08 - B04) / (B08 + B04).
        Verifies NDVI statistics fall strictly within valid agronomic bounds for vineyard canopy
        and bare soil paths.
        """
        live_res = copernicus_client.fetch_live_raster_indices(
            polygon_geojson=self.BARAMATI_FARM_POLYGON,
            farm_area_ha=self.BARAMATI_FARM_AREA_HA,
        )
        if not live_res:
            pytest.skip("Live raster fetch failed.")

        print("\n--- [STEP E] REAL NDVI CALCULATION EVIDENCE ---")
        print(f"Formula: NDVI = (B08 - B04) / (B08 + B04) at 10m native resolution")
        print(f"Vegetation Canopy Mean NDVI (Class 4): {live_res['vegetation_mean_ndvi']}")
        print(f"Bare Soil Mean NDVI (Class 5): {live_res['bare_soil_mean_ndvi']}")
        print(f"Surface Aggregate Mean NDVI: {live_res['surface_mean_ndvi']}")
        print(f"Mean NDVI: {live_res['mean_ndvi']}")
        print(f"Median NDVI: {live_res['median_ndvi']}")
        print(f"Min NDVI: {live_res['min_ndvi']}")
        print(f"Max NDVI: {live_res['max_ndvi']}")
        print(f"Std Dev: {live_res['std_ndvi']}")
        print("-----------------------------------------------\n")

        assert live_res["mean_ndvi"] is not None
        assert pytest.approx(live_res["mean_ndvi"], 0.01) == 0.640
        assert pytest.approx(live_res["vegetation_mean_ndvi"], 0.01) == 0.640
        assert pytest.approx(live_res["bare_soil_mean_ndvi"], 0.01) == 0.458
        assert pytest.approx(live_res["surface_mean_ndvi"], 0.01) == 0.567
        assert -1.0 <= live_res["min_ndvi"] <= live_res["max_ndvi"] <= 1.0
        assert live_res["std_ndvi"] > 0.0

    def test_live_f_real_ndmi_calculation_and_resampling(self):
        """
        [STEP F] Validates pixel-level NDMI calculation: (B08 - B11) / (B08 + B11).
        Verifies bilinear resampling of 20m B11 to 10m grid, and spatial truth preservation.
        """
        live_res = copernicus_client.fetch_live_raster_indices(
            polygon_geojson=self.BARAMATI_FARM_POLYGON,
            farm_area_ha=self.BARAMATI_FARM_AREA_HA,
        )
        if not live_res:
            pytest.skip("Live raster fetch failed.")

        print("\n--- [STEP F] REAL NDMI CALCULATION EVIDENCE ---")
        print(f"Formula: NDMI = (B08 - B11) / (B08 + B11)")
        print(f"B11 Native Resolution: {live_res['b11_native_resolution_meters']}m")
        print(f"B08 Native Resolution: {live_res['b08_native_resolution_meters']}m")
        print(f"Target Output Grid: {live_res['target_grid_meters']}m")
        print(f"Resampling Method: {live_res['resampling_method']}")
        print(f"Vegetation Canopy Mean NDMI (Class 4): {live_res['vegetation_mean_ndmi']}")
        print(f"Surface Aggregate Mean NDMI: {live_res['surface_mean_ndmi']}")
        print(f"Mean NDMI: {live_res['mean_ndmi']}")
        print(f"Resampling Notes: {live_res['resampling_notes']}")
        print("-----------------------------------------------\n")

        assert live_res["mean_ndmi"] is not None
        assert pytest.approx(live_res["mean_ndmi"], 0.01) == 0.217
        assert pytest.approx(live_res["vegetation_mean_ndmi"], 0.01) == 0.217
        assert pytest.approx(live_res["surface_mean_ndmi"], 0.01) == 0.157
        assert live_res["b11_native_resolution_meters"] == 20.0
        assert live_res["b08_native_resolution_meters"] == 10.0
        assert live_res["resampling_method"] == "bilinear"
        assert "Resampling does not create native 10m information" in live_res["resampling_notes"]

    def test_live_g_database_persistence_and_retrieval(self):
        """
        [STEP G] Persists the real Sentinel-2 observation into SQLite database
        for farm 94a1f16e-bf0d-4d3f-9bd3-d63a57189818, then queries it back
        and verifies all persisted columns and metadata provenance.
        """
        import uuid
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from cropnet.services.api.app.models.soil_and_farm import Base, FarmModel
        from cropnet.services.api.app.models.satellite import SatelliteVegetationObservationModel

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        farm = FarmModel(
            id=self.BARAMATI_FARM_ID,
            owner_id="test-user-id",
            name="Baramati Pilot Grape Vineyard",
            taluka="Baramati",
            district="Pune",
            state="Maharashtra",
            calculated_area_hectares=self.BARAMATI_FARM_AREA_HA,
            calculated_area_acres=round(self.BARAMATI_FARM_AREA_HA * 2.47105, 3),
            centroid_latitude=18.18,
            centroid_longitude=74.53,
            geometry_geojson=self.BARAMATI_FARM_POLYGON,
        )
        db.add(farm)
        db.commit()

        # Compute live observation
        indices = copernicus_client.compute_polygon_indices(
            polygon_geojson=self.BARAMATI_FARM_POLYGON,
            farm_area_ha=self.BARAMATI_FARM_AREA_HA,
            use_live_raster=True,
        )

        obs_id = str(uuid.uuid4())
        obs_model = SatelliteVegetationObservationModel(
            id=obs_id,
            farm_id=self.BARAMATI_FARM_ID,
            observation_date=indices["observation_date"],
            product_id=indices["product_id"],
            tile_id=indices["tile_id"],
            sensor=indices["sensor"],
            processing_baseline=indices["processing_baseline"],
            mean_ndvi=indices["mean_ndvi"],
            median_ndvi=indices["median_ndvi"],
            min_ndvi=indices["min_ndvi"],
            max_ndvi=indices["max_ndvi"],
            std_ndvi=indices["std_ndvi"],
            mean_ndmi=indices["mean_ndmi"],
            valid_pixel_count=indices["valid_pixel_count"],
            total_pixel_count=indices["total_pixel_count"],
            farm_coverage_percent=indices["farm_coverage_percent"],
            cloud_masked_percent=indices["cloud_masked_percent"],
            spatial_resolution_meters=indices["spatial_resolution_meters"],
            quality_status=indices["quality_status"],
            quality_notes=indices["quality_notes"],
            is_small_farm_warning=indices["is_small_farm_warning"],
        )
        db.add(obs_model)
        db.commit()

        # Query back from database
        persisted = db.query(SatelliteVegetationObservationModel).filter(
            SatelliteVegetationObservationModel.id == obs_id
        ).first()

        print("\n--- [STEP G] DATABASE PERSISTENCE & RETRIEVAL EVIDENCE ---")
        print(f"Persisted Observation ID: {persisted.id}")
        print(f"Farm ID: {persisted.farm_id}")
        print(f"Product ID: {persisted.product_id}")
        print(f"Baseline: {persisted.processing_baseline}")
        print(f"Mean NDVI: {persisted.mean_ndvi}")
        print(f"Mean NDMI: {persisted.mean_ndmi}")
        print(f"Valid Pixels: {persisted.valid_pixel_count}/{persisted.total_pixel_count}")
        print(f"Quality Status: {persisted.quality_status}")
        print("----------------------------------------------------------\n")

        assert persisted is not None
        assert persisted.farm_id == self.BARAMATI_FARM_ID
        assert persisted.mean_ndvi == indices["mean_ndvi"]
        assert persisted.mean_ndmi == indices["mean_ndmi"]
        assert persisted.valid_pixel_count == indices["valid_pixel_count"]
        assert persisted.quality_status == indices["quality_status"]
        db.close()

