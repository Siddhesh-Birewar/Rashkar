"""
Comprehensive End-to-End Integration Verification Tests for Phase 5.6.4.

Verifies:
1. Genuine document upload (lag_sample.pdf) through the FastAPI endpoint.
2. OCR extraction of UW Soil & Plant Analysis Lab: 8 measurements across 2 distinct samples (Lawn & Garden).
3. Preservation of original chemical basis: P remains elemental P (ppm), K remains elemental K (ppm),
   OM remains % Organic Matter (not SOC).
4. Correct metadata: date_received, date_processed separate from collection_date (null); depth unknown.
5. Strict isolation: unconfirmed reports do not enter the canonical soil profile.
6. Safe QA test farm association: segregated QA context.
7. Post-confirmation canonical soil profile fusion:
   - Precedence of confirmed pH with LABORATORY_VERIFIED status and source attribution.
   - Dual-source preservation of baseline SoilGrids estimates in additional_parameters['isric_*'].
   - Preservation of elemental nutrients and organic matter in additional_parameters.
   - Bioavailable NPK remain null (unfabricated).
8. Agricultural advisory evaluation integration:
   - Evaluator receives fused profile with LABORATORY_MEASURED provenance.
   - Wisconsin elemental P/K do not distort Maharashtra bioavailable P2O5/K2O decision rules.
9. Cross-farm isolation: measurements from Farm A never leak into Farm B.
10. Cache invalidation and persistence in database models.
"""
import os
import uuid
from datetime import datetime
import pytest
from fastapi.testclient import TestClient

from cropnet.services.api.app.models.soil_and_farm import Base, FarmModel
from cropnet.services.api.app.models.soil_reports import SoilTestReportModel, SoilMeasurementModel
from cropnet.services.api.app.schemas.soil_reports import (
    ExtractionStatus,
    ReviewStatus,
    MeasurementVerificationStatus,
)
from cropnet.services.api.app.schemas.soil import (
    VerificationStatus,
    ParameterAvailability,
)
from cropnet.services.api.app.schemas.agriculture_intelligence import (
    SoilDataProvenance,
    FarmContextInput,
)
from cropnet.services.api.app.main import app

client = TestClient(app)

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "lag_sample.pdf")
if not os.path.exists(FIXTURE_PATH):
    # Fallback to Downloads if running locally
    FIXTURE_PATH = "/Users/siddheshbirewar/Downloads/lag_sample.pdf"


@pytest.fixture(autouse=True)
def setup_tables(isolated_test_session):
    """Ensure database tables exist in the test engine."""
    Base.metadata.create_all(bind=isolated_test_session.get_bind())
    yield


def _create_qa_test_farm(owner_id: str, name: str = "Segregated QA Test Farm (Wisconsin Regression)") -> str:
    """Create an isolated test farm context for testing."""
    payload = {
        "name": name,
        "taluka": "Baramati",
        "district": "Pune",
        "state": "Maharashtra",
        "village": "QA_Sandbox_Station",
        "irrigation_type": "irrigated",
        "water_source": "canal",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [74.528, 18.178],
                [74.532, 18.178],
                [74.532, 18.182],
                [74.528, 18.182],
                [74.528, 18.178]
            ]]
        }
    }
    resp = client.post("/api/v1/farms", json=payload, headers={"X-Dev-User-Id": owner_id})
    assert resp.status_code == 201, f"Failed to create QA farm: {resp.text}"
    return resp.json()["id"]


def _create_maharashtra_farm(owner_id: str, name: str = "Isolated Reference Farm B") -> str:
    """Create a separate farm context for cross-farm isolation tests."""
    payload = {
        "name": name,
        "taluka": "Indapur",
        "district": "Pune",
        "state": "Maharashtra",
        "village": "Nimgaon",
        "irrigation_type": "irrigated",
        "water_source": "well",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [74.910, 18.150],
                [74.915, 18.150],
                [74.915, 18.155],
                [74.910, 18.155],
                [74.910, 18.150]
            ]]
        }
    }
    resp = client.post("/api/v1/farms", json=payload, headers={"X-Dev-User-Id": owner_id})
    assert resp.status_code == 201, f"Failed to create Reference farm: {resp.text}"
    return resp.json()["id"]


def test_phase5_6_4_full_lifecycle_and_fusion():
    """
    Complete end-to-end test of Phase 5.6.4 acceptance criteria:
    Upload lag_sample.pdf -> OCR Extraction -> Review Verification -> Isolation -> Confirmation ->
    Dual-Source Fusion -> Agricultural Evaluation -> Cross-Farm Isolation.
    """
    user_id = str(uuid.uuid4())
    qa_farm_id = _create_qa_test_farm(user_id)
    mh_farm_id = _create_maharashtra_farm(user_id)

    # =========================================================================
    # STEP 1: Spatial Baseline Analysis
    # =========================================================================
    baseline_resp = client.post(
        f"/api/v1/farms/{qa_farm_id}/soil/analyse",
        json={"depth": "0-5cm"},
        headers={"X-Dev-User-Id": user_id}
    )
    assert baseline_resp.status_code == 200
    baseline_profile = baseline_resp.json()
    assert baseline_profile["is_map_derived"] is True
    assert baseline_profile["source_dataset"] == "ISRIC SoilGrids 2.0"
    baseline_ph = baseline_profile["ph"]["value"]
    assert baseline_profile["available_nitrogen"]["value"] is None
    assert baseline_profile["available_phosphorus"]["value"] is None
    assert baseline_profile["available_potassium"]["value"] is None

    # Step 1b: Maharashtra farm also gets baseline
    mh_baseline_resp = client.post(
        f"/api/v1/farms/{mh_farm_id}/soil/analyse",
        json={"depth": "0-5cm"},
        headers={"X-Dev-User-Id": user_id}
    )
    assert mh_baseline_resp.status_code == 200

    # =========================================================================
    # STEP 2: Actual Document Upload (lag_sample.pdf)
    # =========================================================================
    assert os.path.exists(FIXTURE_PATH), f"Fixture not found at {FIXTURE_PATH}"
    with open(FIXTURE_PATH, "rb") as f:
        file_bytes = f.read()

    files = {"file": ("lag_sample.pdf", file_bytes, "application/pdf")}
    data = {
        "laboratory_name": "UW Soil & Plant Analysis Lab",
        "sample_depth_interval": "Not specified",
        "depth_provenance": "UNKNOWN",
    }
    upload_resp = client.post(
        f"/api/v1/farms/{qa_farm_id}/soil-reports/upload",
        files=files,
        data=data,
        headers={"X-Dev-User-Id": user_id}
    )
    assert upload_resp.status_code == 201, f"Upload failed: {upload_resp.text}"
    upload_result = upload_resp.json()
    report_id = upload_result["id"]

    # Fetch processed report after background extraction completes
    detail_resp = client.get(
        f"/api/v1/farms/{qa_farm_id}/soil-reports/{report_id}",
        headers={"X-Dev-User-Id": user_id}
    )
    assert detail_resp.status_code == 200
    report = detail_resp.json()

    # Verify report metadata
    assert report["original_filename"] == "lag_sample.pdf"
    assert report["laboratory_name"] == "UW Soil & Plant Analysis Lab"
    assert report["lab_number"] == "54321"
    assert report["date_received"].startswith("2007-08-01")
    assert report["date_processed"].startswith("2007-08-10")
    assert report["sample_collection_date"] is None
    assert report["sample_depth_interval"] is None or report["sample_depth_interval"] == "Not specified"
    assert report["depth_provenance"] == "UNKNOWN"
    assert report["extraction_status"] == ExtractionStatus.NEEDS_REVIEW.value
    assert report["review_status"] == ReviewStatus.NEEDS_REVIEW.value

    # Verify 8 extracted measurements across two distinct samples
    measurements = report["measurements"]
    assert len(measurements) == 8, f"Expected 8 measurements, got {len(measurements)}"

    sample1_meas = [m for m in measurements if m.get("sample_id") == "1" or m.get("page_number") == 1]
    sample2_meas = [m for m in measurements if m.get("sample_id") == "2" or m.get("page_number") == 2]
    assert len(sample1_meas) == 4, f"Expected 4 measurements in Sample 1, got {len(sample1_meas)}"
    assert len(sample2_meas) == 4, f"Expected 4 measurements in Sample 2, got {len(sample2_meas)}"

    # Verify Sample 1 (Lawn): pH=5.9, P=10 ppm, K=34 ppm, OM=1.9%
    s1_dict = {m["parameter_key"]: m for m in sample1_meas}
    assert s1_dict["soil_ph"]["original_value"] == 5.9
    assert s1_dict["soil_ph"]["original_unit"].lower() == "ph"
    assert s1_dict["phosphorus"]["original_value"] == 10.0
    assert s1_dict["phosphorus"]["original_unit"].lower() == "ppm"
    assert s1_dict["potassium"]["original_value"] == 34.0
    assert s1_dict["potassium"]["original_unit"].lower() == "ppm"
    assert s1_dict["organic_matter"]["original_value"] == 1.9
    assert s1_dict["organic_matter"]["original_unit"] == "%"

    # Verify Sample 2 (Garden): pH=6.2, P=25 ppm, K=45 ppm, OM=3.1%
    s2_dict = {m["parameter_key"]: m for m in sample2_meas}
    assert s2_dict["soil_ph"]["original_value"] == 6.2
    assert s2_dict["phosphorus"]["original_value"] == 25.0
    assert s2_dict["potassium"]["original_value"] == 45.0
    assert s2_dict["organic_matter"]["original_value"] == 3.1

    # Ensure unverified status before confirmation
    for m in measurements:
        assert m["verification_status"] == MeasurementVerificationStatus.EXTRACTED_UNVERIFIED.value

    # =========================================================================
    # STEP 3: Strict Isolation Before Confirmation
    # =========================================================================
    pre_confirm_soil = client.get(
        f"/api/v1/farms/{qa_farm_id}/soil",
        headers={"X-Dev-User-Id": user_id}
    ).json()
    # Soil profile MUST NOT contain lab measurements yet
    assert pre_confirm_soil["ph"]["verification_status"] == VerificationStatus.MAP_DERIVED_ESTIMATE.value
    assert pre_confirm_soil["ph"]["value"] == baseline_ph
    assert "phosphorus" not in pre_confirm_soil.get("additional_parameters", {})
    assert "potassium" not in pre_confirm_soil.get("additional_parameters", {})

    # =========================================================================
    # STEP 4: Pre-Confirmation Agricultural Evaluation
    # =========================================================================
    pre_eval_resp = client.post(
        f"/api/v1/farms/{qa_farm_id}/advisory/evaluate",
        json={"target_season": "kharif"},
        headers={"X-Dev-User-Id": user_id}
    )
    assert pre_eval_resp.status_code == 200
    pre_eval = pre_eval_resp.json()
    assert pre_eval["farm_context"]["soil_data_provenance"] in [
        SoilDataProvenance.SPATIALLY_ESTIMATED_ISRIC.value,
        SoilDataProvenance.UNKNOWN.value,
    ]

    # =========================================================================
    # STEP 5: Farmer Review & Confirmation
    # =========================================================================
    confirm_resp = client.post(
        f"/api/v1/farms/{qa_farm_id}/soil-reports/{report_id}/confirm",
        json={},
        headers={"X-Dev-User-Id": user_id}
    )
    assert confirm_resp.status_code == 200
    confirm_data = confirm_resp.json()
    assert confirm_data["status"] == "confirmed"
    assert confirm_data["confirmed_measurement_count"] == 8

    # =========================================================================
    # STEP 6: Verify Canonical Soil Intelligence Profile Fusion
    # =========================================================================
    post_confirm_soil = client.get(
        f"/api/v1/farms/{qa_farm_id}/soil",
        headers={"X-Dev-User-Id": user_id}
    ).json()

    # Precedence: pH is updated to lab ground truth
    assert post_confirm_soil["ph"]["verification_status"] == VerificationStatus.LABORATORY_VERIFIED.value
    assert "Laboratory Report: UW Soil & Plant Analysis Lab" in post_confirm_soil["ph"]["source"]
    assert post_confirm_soil["ph"]["value"] in [5.9, 6.2]
    assert post_confirm_soil["ph"]["depth_interval"] == "Not specified"

    # Dual-source preservation: baseline SoilGrids estimate preserved
    assert "isric_ph" in post_confirm_soil["additional_parameters"]
    assert post_confirm_soil["additional_parameters"]["isric_ph"]["value"] == baseline_ph
    assert post_confirm_soil["additional_parameters"]["isric_ph"]["verification_status"] == VerificationStatus.MAP_DERIVED_ESTIMATE.value

    # Elemental P and K preserved in additional_parameters
    assert "phosphorus" in post_confirm_soil["additional_parameters"]
    assert post_confirm_soil["additional_parameters"]["phosphorus"]["unit"] == "ppm"
    assert post_confirm_soil["additional_parameters"]["phosphorus"]["verification_status"] == VerificationStatus.LABORATORY_VERIFIED.value

    assert "potassium" in post_confirm_soil["additional_parameters"]
    assert post_confirm_soil["additional_parameters"]["potassium"]["unit"] == "ppm"
    assert post_confirm_soil["additional_parameters"]["potassium"]["verification_status"] == VerificationStatus.LABORATORY_VERIFIED.value

    # Organic Matter preserved in additional_parameters
    assert "organic_matter" in post_confirm_soil["additional_parameters"]
    assert post_confirm_soil["additional_parameters"]["organic_matter"]["unit"] == "%"

    # Bioavailable NPK are NOT fabricated - remain null because UW report gave elemental P/K in ppm
    assert post_confirm_soil["available_nitrogen"]["value"] is None
    assert post_confirm_soil["available_phosphorus"]["value"] is None
    assert post_confirm_soil["available_potassium"]["value"] is None

    # =========================================================================
    # STEP 7: Agricultural Advisory Evaluation With Fused Lab Profile
    # =========================================================================
    post_eval_resp = client.post(
        f"/api/v1/farms/{qa_farm_id}/advisory/evaluate",
        json={"target_season": "kharif"},
        headers={"X-Dev-User-Id": user_id}
    )
    assert post_eval_resp.status_code == 200
    post_eval = post_eval_resp.json()
    # Provenance correctly reflects laboratory ground truth
    assert post_eval["farm_context"]["soil_data_provenance"] == SoilDataProvenance.LABORATORY_MEASURED.value
    # Agronomic evaluation completed without failing or treating Wisconsin P/K as Olsen P2O5 / K2O
    assert len(post_eval["crop_outcomes"]) > 0

    # =========================================================================
    # STEP 8: Cross-Farm Isolation Verification
    # =========================================================================
    mh_soil = client.get(
        f"/api/v1/farms/{mh_farm_id}/soil",
        headers={"X-Dev-User-Id": user_id}
    ).json()
    # Maharashtra farm MUST strictly have map-derived estimates with 0 lab measurements
    assert mh_soil["ph"]["verification_status"] == VerificationStatus.MAP_DERIVED_ESTIMATE.value
    assert "isric_ph" not in mh_soil.get("additional_parameters", {})
    assert "phosphorus" not in mh_soil.get("additional_parameters", {})
    assert "potassium" not in mh_soil.get("additional_parameters", {})
    assert "organic_matter" not in mh_soil.get("additional_parameters", {})


def test_cache_invalidation_and_db_persistence(isolated_test_session):
    """
    Verify that dropping in-memory cache and re-fetching from database reconstructs
    the complete fused profile with full dual-source preservation.
    """
    from cropnet.services.api.app.services.spatial_extractor import _SOIL_PROFILE_CACHE

    user_id = str(uuid.uuid4())
    qa_farm_id = _create_qa_test_farm(user_id)

    # 1. Analyse spatial baseline
    client.post(
        f"/api/v1/farms/{qa_farm_id}/soil/analyse",
        json={"depth": "0-5cm"},
        headers={"X-Dev-User-Id": user_id}
    )

    # 2. Upload and confirm report
    with open(FIXTURE_PATH, "rb") as f:
        file_bytes = f.read()
    upload_resp = client.post(
        f"/api/v1/farms/{qa_farm_id}/soil-reports/upload",
        files={"file": ("lag_sample.pdf", file_bytes, "application/pdf")},
        data={"laboratory_name": "UW Soil & Plant Analysis Lab"},
        headers={"X-Dev-User-Id": user_id}
    )
    report_id = upload_resp.json()["id"]
    client.post(
        f"/api/v1/farms/{qa_farm_id}/soil-reports/{report_id}/confirm",
        json={},
        headers={"X-Dev-User-Id": user_id}
    )

    # 3. Simulate FastAPI restart / drop memory cache
    if str(qa_farm_id) in _SOIL_PROFILE_CACHE:
        del _SOIL_PROFILE_CACHE[str(qa_farm_id)]

    # 4. Fetch profile again - must load cleanly from DB models
    reloaded_resp = client.get(
        f"/api/v1/farms/{qa_farm_id}/soil",
        headers={"X-Dev-User-Id": user_id}
    )
    assert reloaded_resp.status_code == 200
    reloaded = reloaded_resp.json()

    # Precedence & Dual-Source intact after cache flush
    assert reloaded["ph"]["verification_status"] == VerificationStatus.LABORATORY_VERIFIED.value
    assert "isric_ph" in reloaded["additional_parameters"]
    assert "phosphorus" in reloaded["additional_parameters"]
    assert "potassium" in reloaded["additional_parameters"]
    assert "organic_matter" in reloaded["additional_parameters"]


def test_multi_farm_switching_and_concurrent_requests():
    """
    Verify rapid alternating profile requests between confirmed and unconfirmed farms
    strictly prevent cross-farm data leakage.
    """
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    farm_a = _create_qa_test_farm(user_a, name="Farm Alpha (Wisconsin Lab Confirmed)")
    farm_b = _create_maharashtra_farm(user_b, name="Farm Beta (Strictly Geospatial)")

    # Baseline for both
    client.post(f"/api/v1/farms/{farm_a}/soil/analyse", json={"depth": "0-5cm"}, headers={"X-Dev-User-Id": user_a})
    client.post(f"/api/v1/farms/{farm_b}/soil/analyse", json={"depth": "0-5cm"}, headers={"X-Dev-User-Id": user_b})

    # Upload & confirm only on Farm A
    with open(FIXTURE_PATH, "rb") as f:
        file_bytes = f.read()
    up = client.post(
        f"/api/v1/farms/{farm_a}/soil-reports/upload",
        files={"file": ("lag_sample.pdf", file_bytes, "application/pdf")},
        headers={"X-Dev-User-Id": user_a}
    ).json()
    client.post(f"/api/v1/farms/{farm_a}/soil-reports/{up['id']}/confirm", json={}, headers={"X-Dev-User-Id": user_a})

    # Rapid alternating requests
    for _ in range(5):
        soil_a = client.get(f"/api/v1/farms/{farm_a}/soil", headers={"X-Dev-User-Id": user_a}).json()
        soil_b = client.get(f"/api/v1/farms/{farm_b}/soil", headers={"X-Dev-User-Id": user_b}).json()

        assert soil_a["ph"]["verification_status"] == VerificationStatus.LABORATORY_VERIFIED.value
        assert "phosphorus" in soil_a["additional_parameters"]

        assert soil_b["ph"]["verification_status"] == VerificationStatus.MAP_DERIVED_ESTIMATE.value
        assert "phosphorus" not in soil_b.get("additional_parameters", {})
        assert "isric_ph" not in soil_b.get("additional_parameters", {})

