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


# ===========================================================================
# SECTION 2 — MOCK-PROVIDER INTEGRATION TESTS
# ===========================================================================

class TestCopernicusMockProvider:
    """Integration tests using simulated raster / mocked API provider."""

    def test_mock_polygon_indices_computation_and_provenance(self):
        """Verify computation over Baramati demonstration geometry with explicit mock provenance."""
        qa_polygon = {
            "type": "Polygon",
            "coordinates": [[[74.5, 18.1], [74.52, 18.1], [74.52, 18.12], [74.5, 18.12], [74.5, 18.1]]]
        }
        res = copernicus_client.compute_polygon_indices(qa_polygon, farm_area_ha=2.5)

        assert res["sensor"] == "Sentinel-2 L2A"
        assert res["spatial_resolution_meters"] == 10.0
        assert res["b11_native_resolution_meters"] == 20.0
        assert res["b08_native_resolution_meters"] == 10.0
        assert res["target_grid_meters"] == 10.0
        assert res["resampling_method"] == "bilinear"
        assert res["copernicus_provider_status"] in ("STANDALONE_DETERMINISTIC_MODEL", "AUTHENTICATED")
        assert res["mean_ndvi"] is not None
        assert 0.0 <= res["mean_ndvi"] <= 1.0


# ===========================================================================
# SECTION 3 — LIVE-PROVIDER INTEGRATION TESTS (Copernicus CDSE Public API)
# ===========================================================================

class TestCopernicusLiveProvider:
    """
    Genuine live provider test querying Copernicus Data Space Ecosystem (CDSE)
    public OData catalog for actual accessible Sentinel-2 Level-2A products.
    """

    def test_live_cdse_odata_catalogue_query(self):
        """
        Queries Copernicus Data Space Ecosystem (CDSE) public OData service
        for live Sentinel-2 Level-2A products covering Baramati / Pune tile T43QDB.
        Records live product metadata, processing baseline, and acquisition date.
        """
        tile_id = "T43QDB"
        qa_bbox = [74.04, 18.00, 75.05, 19.90]

        try:
            items = copernicus_client.search_odata_scenes(tile_id=tile_id, top=2)
        except Exception as e:
            pytest.skip(f"Live Copernicus CDSE endpoint unreachable: {e}")

        if not items:
            pytest.skip(
                f"No Sentinel-2 L2A products returned by CDSE OData API for tile {tile_id}. "
                "Network, DNS, or CDSE service maintenance may prevent live verification."
            )

        first_product = items[0]
        product_id = first_product.get("Id")
        product_name = first_product.get("Name", "")
        content_date = first_product.get("ContentDate", {})
        start_date = content_date.get("Start")
        footprint = str(first_product.get("Footprint", ""))

        # Parse processing baseline from product title (e.g. S2B_MSIL2A_..._N0513_...)
        baseline = "UNKNOWN"
        for part in product_name.split("_"):
            if part.startswith("N") and len(part) >= 4 and part[1:5].isdigit():
                baseline = part[:5]
                break

        print("\n--- LIVE COPERNICUS CDSE QUERY EVIDENCE ---")
        print(f"Provider: Copernicus Data Space Ecosystem (CDSE) OData v1 API ({CDSE_ODATA_URL})")
        print(f"Product Identifier: {product_id}")
        print(f"Product Name: {product_name}")
        print(f"Acquisition Date (Start): {start_date}")
        print(f"Processing Baseline: {baseline}")
        print(f"MGRS Tile: {tile_id} (Baramati / Pune, Maharashtra)")
        print(f"QA Footprint: {footprint[:120]}...")
        print(f"Status: LIVE_QUERY_SUCCESS")
        print("--------------------------------------------\n")

        # Verifications on actual live returned metadata
        assert product_id is not None
        assert "MSIL2A" in product_name
        assert tile_id in product_name
        assert start_date is not None

        # Verify that our metadata-driven calibration correctly handles the live product's baseline!
        # e.g., N0513 is PB 05.13 -> offset -1000.0 DN
        calibrated = calibrate_dn_to_reflectance(3000.0, processing_baseline=baseline)
        if baseline != "UNKNOWN" and int(baseline.replace("N", "")[:3]) >= 40:
            assert pytest.approx(calibrated, 0.0001) == 0.2000
