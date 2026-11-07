"""
Tests for Dual-Source Agricultural Intelligence Fusion (Phase 5.6 Part 3).

Verifies:
1. Dual-source preservation: ISRIC SoilGrids modelled estimates remain intact.
2. Precedence rule: Confirmed laboratory measurements prioritize over SoilGrids for unified profile.
3. Strict isolation: Unconfirmed lab reports/measurements (NEEDS_REVIEW / EXTRACTED_UNVERIFIED)
   MUST NOT enter unified profile or agricultural evaluation.
4. Rule compatibility: Micronutrients (Zn, Fe, Mn, Cu, B, S) are preserved in additional_parameters
   without causing invalid input errors in SoilConstraintEvaluator.
5. Advisory evaluation fusion: POST /farms/{farm_id}/advisory/evaluate and /evaluate-farm
   automatically detect confirmed lab measurements and set soil_data_provenance = LABORATORY_MEASURED.
"""
import uuid
from datetime import datetime
from shapely.geometry import Polygon
import pytest
from fastapi.testclient import TestClient

from cropnet.services.api.app.models.soil_and_farm import Base
from cropnet.services.api.app.models.soil_reports import SoilTestReportModel, SoilMeasurementModel
from cropnet.services.api.app.schemas.soil_reports import (
    ExtractionStatus,
    ReviewStatus,
    MeasurementVerificationStatus,
)
from cropnet.services.api.app.schemas.soil import (
    VerificationStatus,
    ParameterAvailability,
    SoilAnalyseRequest,
)
from cropnet.services.api.app.schemas.agriculture_intelligence import (
    SoilDataProvenance,
    FarmContextInput,
)
from cropnet.services.api.app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_fusion_tables(isolated_test_session):
    """Ensure all database tables exist in the isolated test engine."""
    Base.metadata.create_all(bind=isolated_test_session.get_bind())
    yield


def _create_farm(owner_id: str, name: str = "Baramati Fusion Farm") -> str:
    payload = {
        "name": name,
        "taluka": "Baramati",
        "district": "Pune",
        "state": "Maharashtra",
        "village": "Malegaon",
        "irrigation_type": "irrigated",
        "water_source": "canal",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [74.525, 18.175],
                [74.535, 18.175],
                [74.535, 18.185],
                [74.525, 18.185],
                [74.525, 18.175]
            ]]
        }
    }
    resp = client.post("/api/v1/farms", json=payload, headers={"X-Dev-User-Id": owner_id})
    assert resp.status_code == 201, f"Failed to create farm: {resp.text}"
    return resp.json()["id"]


def test_dual_source_soilgrids_baseline_when_no_lab_reports():
    """Verify SoilGrids baseline profile when no lab reports exist."""
    user_id = str(uuid.uuid4())
    farm_id = _create_farm(user_id)

    # 1. Trigger spatial soil analysis
    analyse_resp = client.post(
        f"/api/v1/farms/{farm_id}/soil/analyse",
        json={"depth": "0-5cm"},
        headers={"X-Dev-User-Id": user_id}
    )
    assert analyse_resp.status_code == 200
    profile = analyse_resp.json()
    assert profile["is_map_derived"] is True
    assert profile["source_dataset"] == "ISRIC SoilGrids 2.0"
    assert profile["ph"] is not None
    assert profile["ph"]["verification_status"] == VerificationStatus.MAP_DERIVED_ESTIMATE.value
    # Bioavailable NPK are strictly null in modelled estimates
    assert profile["available_nitrogen"]["value"] is None
    assert profile["available_phosphorus"]["value"] is None
    assert profile["available_potassium"]["value"] is None

    # 2. GET /farms/{farm_id}/soil returns the baseline
    get_resp = client.get(f"/api/v1/farms/{farm_id}/soil", headers={"X-Dev-User-Id": user_id})
    assert get_resp.status_code == 200
    baseline = get_resp.json()
    assert baseline["ph"]["verification_status"] == VerificationStatus.MAP_DERIVED_ESTIMATE.value


def test_strict_isolation_unconfirmed_reports_ignored(isolated_test_session):
    """Verify that unconfirmed reports (NEEDS_REVIEW) are strictly isolated from GET /farms/{farm_id}/soil."""
    user_id = str(uuid.uuid4())
    farm_id = _create_farm(user_id)

    # Create spatial profile
    client.post(
        f"/api/v1/farms/{farm_id}/soil/analyse",
        json={"depth": "0-5cm"},
        headers={"X-Dev-User-Id": user_id}
    )

    # Insert an unconfirmed soil report (NEEDS_REVIEW) with EXTRACTED_UNVERIFIED measurements
    report_id = str(uuid.uuid4())
    report = SoilTestReportModel(
        id=report_id,
        user_id=user_id,
        farm_id=farm_id,
        original_filename="pending_review.pdf",
        storage_path=f"{farm_id}/{report_id}/pending_review.pdf",
        laboratory_name="Unverified Soil Lab",
        extraction_status=ExtractionStatus.NEEDS_REVIEW.value,
        review_status=ReviewStatus.NEEDS_REVIEW.value,
    )
    isolated_test_session.add(report)

    meas = SoilMeasurementModel(
        id=str(uuid.uuid4()),
        report_id=report_id,
        farm_id=farm_id,
        parameter_key="soil_ph",
        original_parameter_name="Soil pH",
        original_value=4.5,
        original_unit="pH",
        verification_status=MeasurementVerificationStatus.EXTRACTED_UNVERIFIED.value,
    )
    isolated_test_session.add(meas)
    isolated_test_session.commit()

    # GET /soil must NOT use the unconfirmed 4.5 pH
    resp = client.get(f"/api/v1/farms/{farm_id}/soil", headers={"X-Dev-User-Id": user_id})
    assert resp.status_code == 200
    profile = resp.json()
    assert profile["ph"]["verification_status"] == VerificationStatus.MAP_DERIVED_ESTIMATE.value
    assert profile["ph"]["value"] != 4.5  # Lab value was NOT applied


def test_precedence_and_dual_source_preservation_with_confirmed_report(isolated_test_session):
    """Verify precedence of confirmed lab measurements and preservation of SoilGrids records."""
    user_id = str(uuid.uuid4())
    farm_id = _create_farm(user_id)

    # 1. Generate SoilGrids baseline profile
    client.post(
        f"/api/v1/farms/{farm_id}/soil/analyse",
        json={"depth": "0-5cm"},
        headers={"X-Dev-User-Id": user_id}
    )

    # 2. Insert a CONFIRMED laboratory report with confirmed measurements
    report_id = str(uuid.uuid4())
    report = SoilTestReportModel(
        id=report_id,
        user_id=user_id,
        farm_id=farm_id,
        original_filename="kvk_baramati_confirmed.pdf",
        storage_path=f"{farm_id}/{report_id}/kvk_baramati_confirmed.pdf",
        laboratory_name="KVK Baramati Certified Testing Lab",
        report_date=datetime(2026, 10, 15),
        sample_depth_interval="0-15cm",
        extraction_status=ExtractionStatus.CONFIRMED.value,
        review_status=ReviewStatus.CONFIRMED.value,
    )
    isolated_test_session.add(report)

    # Confirmed lab parameters: pH, Available N, P, K, SOC, and Zinc
    m_ph = SoilMeasurementModel(
        id=str(uuid.uuid4()),
        report_id=report_id,
        farm_id=farm_id,
        parameter_key="soil_ph",
        original_parameter_name="Soil pH (1:2.5)",
        original_value=7.4,
        original_unit="pH",
        normalized_value=7.4,
        normalized_unit="pH",
        verification_status=MeasurementVerificationStatus.FARMER_CONFIRMED.value,
    )
    m_soc = SoilMeasurementModel(
        id=str(uuid.uuid4()),
        report_id=report_id,
        farm_id=farm_id,
        parameter_key="organic_carbon",
        original_parameter_name="Organic Carbon",
        original_value=0.65,
        original_unit="%",
        normalized_value=0.65,
        normalized_unit="%",
        verification_status=MeasurementVerificationStatus.FARMER_CONFIRMED.value,
    )
    m_n = SoilMeasurementModel(
        id=str(uuid.uuid4()),
        report_id=report_id,
        farm_id=farm_id,
        parameter_key="available_nitrogen",
        original_parameter_name="Available Nitrogen",
        original_value=275.0,
        original_unit="kg/ha",
        normalized_value=275.0,
        normalized_unit="kg/ha",
        verification_status=MeasurementVerificationStatus.FARMER_CONFIRMED.value,
    )
    m_p = SoilMeasurementModel(
        id=str(uuid.uuid4()),
        report_id=report_id,
        farm_id=farm_id,
        parameter_key="available_phosphorus",
        original_parameter_name="Available P (P2O5)",
        original_value=22.5,
        original_unit="kg/ha",
        normalized_value=22.5,
        normalized_unit="kg/ha",
        verification_status=MeasurementVerificationStatus.FARMER_CONFIRMED.value,
    )
    m_k = SoilMeasurementModel(
        id=str(uuid.uuid4()),
        report_id=report_id,
        farm_id=farm_id,
        parameter_key="available_potassium",
        original_parameter_name="Available K (K2O)",
        original_value=310.0,
        original_unit="kg/ha",
        normalized_value=310.0,
        normalized_unit="kg/ha",
        verification_status=MeasurementVerificationStatus.FARMER_CONFIRMED.value,
    )
    m_zn = SoilMeasurementModel(
        id=str(uuid.uuid4()),
        report_id=report_id,
        farm_id=farm_id,
        parameter_key="zinc",
        original_parameter_name="DTPA Zinc (Zn)",
        original_value=0.85,
        original_unit="mg/kg",
        normalized_value=0.85,
        normalized_unit="mg/kg",
        verification_status=MeasurementVerificationStatus.FARMER_CONFIRMED.value,
    )
    isolated_test_session.add_all([m_ph, m_soc, m_n, m_p, m_k, m_zn])
    isolated_test_session.commit()

    # 3. GET /farms/{farm_id}/soil must prioritize lab measurements
    resp = client.get(f"/api/v1/farms/{farm_id}/soil", headers={"X-Dev-User-Id": user_id})
    assert resp.status_code == 200
    fused = resp.json()

    # Precedence: pH is laboratory verified
    assert fused["ph"]["value"] == 7.4
    assert fused["ph"]["verification_status"] == VerificationStatus.LABORATORY_VERIFIED.value
    assert "Laboratory Report: KVK Baramati" in fused["ph"]["source"]

    # Dual-source preservation: SoilGrids estimate preserved in additional_parameters
    assert "isric_ph" in fused["additional_parameters"]
    assert fused["additional_parameters"]["isric_ph"]["verification_status"] == VerificationStatus.MAP_DERIVED_ESTIMATE.value

    # Precedence: Bioavailable NPK unlocked by lab
    assert fused["available_nitrogen"]["value"] == 275.0
    assert fused["available_nitrogen"]["verification_status"] == VerificationStatus.LABORATORY_VERIFIED.value
    assert fused["available_phosphorus"]["value"] == 22.5
    assert fused["available_phosphorus"]["verification_status"] == VerificationStatus.LABORATORY_VERIFIED.value
    assert fused["available_potassium"]["value"] == 310.0
    assert fused["available_potassium"]["verification_status"] == VerificationStatus.LABORATORY_VERIFIED.value

    # Micronutrient (Zinc) preserved in additional_parameters
    assert "zinc" in fused["additional_parameters"]
    assert fused["additional_parameters"]["zinc"]["value"] == 0.85
    assert fused["additional_parameters"]["zinc"]["verification_status"] == VerificationStatus.LABORATORY_VERIFIED.value


def test_advisory_evaluation_fuses_confirmed_lab_measurements(isolated_test_session):
    """Verify that advisory evaluation uses LABORATORY_MEASURED provenance when confirmed lab report exists."""
    user_id = str(uuid.uuid4())
    farm_id = _create_farm(user_id)

    # Insert confirmed lab report
    report_id = str(uuid.uuid4())
    report = SoilTestReportModel(
        id=report_id,
        user_id=user_id,
        farm_id=farm_id,
        original_filename="confirmed_lab.pdf",
        storage_path=f"{farm_id}/{report_id}/confirmed_lab.pdf",
        laboratory_name="Pune Agricultural College Lab",
        report_date=datetime(2026, 9, 20),
        extraction_status=ExtractionStatus.CONFIRMED.value,
        review_status=ReviewStatus.CONFIRMED.value,
    )
    isolated_test_session.add(report)

    m_ph = SoilMeasurementModel(
        id=str(uuid.uuid4()),
        report_id=report_id,
        farm_id=farm_id,
        parameter_key="soil_ph",
        original_parameter_name="pH",
        original_value=7.8,
        original_unit="pH",
        verification_status=MeasurementVerificationStatus.FARMER_CONFIRMED.value,
    )
    m_ec = SoilMeasurementModel(
        id=str(uuid.uuid4()),
        report_id=report_id,
        farm_id=farm_id,
        parameter_key="electrical_conductivity",
        original_parameter_name="EC",
        original_value=0.45,
        original_unit="dS/m",
        verification_status=MeasurementVerificationStatus.FARMER_CONFIRMED.value,
    )
    m_n = SoilMeasurementModel(
        id=str(uuid.uuid4()),
        report_id=report_id,
        farm_id=farm_id,
        parameter_key="available_nitrogen",
        original_parameter_name="Available N",
        original_value=260.0,
        original_unit="kg/ha",
        verification_status=MeasurementVerificationStatus.FARMER_CONFIRMED.value,
    )
    isolated_test_session.add_all([m_ph, m_ec, m_n])
    isolated_test_session.commit()

    # 1. Call POST /farms/{farm_id}/advisory/evaluate
    eval_resp = client.post(
        f"/api/v1/farms/{farm_id}/advisory/evaluate",
        json={"target_season": "kharif"},
        headers={"X-Dev-User-Id": user_id}
    )
    assert eval_resp.status_code == 200
    decision = eval_resp.json()
    ctx = decision["farm_context"]
    assert ctx["soil_data_provenance"] == SoilDataProvenance.LABORATORY_MEASURED.value
    assert ctx["soil_ph"] == 7.8
    assert ctx["electrical_conductivity_ds_m"] == 0.45
    assert ctx["available_nitrogen_kg_ha"] == 260.0

    # 2. Call POST /api/v1/agriculture/evaluate-farm with farm_id
    eval_direct = client.post(
        "/api/v1/agriculture/evaluate-farm",
        json={"farm_id": farm_id, "taluka": "Baramati", "target_season": "kharif"},
        headers={"X-Dev-User-Id": user_id}
    )
    assert eval_direct.status_code == 200
    ctx_direct = eval_direct.json()["farm_context"]
    assert ctx_direct["soil_data_provenance"] == SoilDataProvenance.LABORATORY_MEASURED.value
    assert ctx_direct["soil_ph"] == 7.8
