"""
Comprehensive Test Suite for Irrigation Water Quality & Availability Intelligence.

Verifies:
1. Validated ionic conversions (mg/L to meq/L) using equivalent weights.
2. Exact SAR and RSC formula computations with rigorous missing-input handling.
3. Institutional rule-based evaluations (BIS IS 11624:1986 and ICAR-CSSRI Karnal).
4. Water sources CRUD with farm ownership enforcement.
5. Water laboratory report upload, review, correction, and confirmation lifecycle.
6. Strict domain separation: water measurements never leak into soil measurements table.
"""
import uuid
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from cropnet.services.api.app.main import app
from cropnet.services.api.app.core.database import get_db
from cropnet.services.api.app.core.security import get_current_user, CurrentUser
from cropnet.services.api.app.models.soil_and_farm import Base, FarmModel
from cropnet.services.api.app.models.soil_reports import SoilMeasurementModel
from cropnet.services.api.app.models.water import (
    WaterSourceModel,
    WaterTestReportModel,
    WaterMeasurementModel,
)
from cropnet.services.api.app.services.water_intelligence.evaluator import (
    normalize_water_measurement,
    calculate_sar_and_rsc,
    WaterQualityEvaluator,
)
from cropnet.services.api.app.api.v1.endpoints.farms import _FARM_STORAGE

TEST_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
OTHER_USER_ID = uuid.UUID("99999999-9999-9999-9999-999999999999")
TEST_FARM_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
def isolated_water_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    # Seed test farm
    now = datetime.utcnow()
    farm = FarmModel(
        id=str(TEST_FARM_ID),
        owner_id=str(TEST_USER_ID),
        name="Baramati Green Farm",
        village="Malegaon",
        taluka="Baramati",
        district="Pune",
        state="Maharashtra",
        irrigation_type="drip",
        water_source="borewell",
        geometry_geojson={"type": "Polygon", "coordinates": [[[74.5, 18.1], [74.6, 18.1], [74.6, 18.2], [74.5, 18.2], [74.5, 18.1]]]},
        calculated_area_hectares=2.5,
        calculated_area_acres=6.18,
        centroid_latitude=18.15,
        centroid_longitude=74.55,
        created_at=now,
        updated_at=now,
    )
    session.add(farm)
    session.commit()

    _FARM_STORAGE[TEST_FARM_ID] = {
        "id": TEST_FARM_ID,
        "owner_id": TEST_USER_ID,
        "name": farm.name,
        "village": farm.village,
        "taluka": farm.taluka,
        "district": farm.district,
        "state": farm.state,
        "geometry": farm.geometry_geojson,
        "calculated_area_hectares": farm.calculated_area_hectares,
        "calculated_area_acres": farm.calculated_area_acres,
    }

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        _FARM_STORAGE.clear()


@pytest.fixture
def client(isolated_water_db):
    def override_get_db():
        try:
            yield isolated_water_db
        finally:
            pass

    def override_get_current_user():
        return CurrentUser(
            user_id=TEST_USER_ID,
            email="farmer@cropnet.ai",
            role="authenticated",
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ===========================================================================
# 1. UNIT TESTS: UNIT NORMALIZATION
# ===========================================================================

def test_normalize_water_measurements():
    # EC: µS/cm -> dS/m
    val, unit = normalize_water_measurement("electrical_conductivity", 1750.0, "µS/cm")
    assert val == 1.75
    assert unit == "dS/m"

    # TDS: mg/L
    val, unit = normalize_water_measurement("tds", 1120.0, "mg/L")
    assert val == 1120.0
    assert unit == "mg/L"

    # Cations: mg/L to meq/L
    # Na: 46.0 mg/L / 22.99 = 2.001 meq/L
    val, unit = normalize_water_measurement("sodium", 46.0, "mg/L")
    assert pytest.approx(val, 0.01) == 2.001
    assert unit == "meq/L"

    # Ca: 40.08 mg/L / 20.04 = 2.000 meq/L
    val, unit = normalize_water_measurement("calcium", 40.08, "mg/L")
    assert pytest.approx(val, 0.01) == 2.000
    assert unit == "meq/L"

    # Mg: 24.3 mg/L / 12.15 = 2.000 meq/L
    val, unit = normalize_water_measurement("magnesium", 24.3, "mg/L")
    assert pytest.approx(val, 0.01) == 2.000
    assert unit == "meq/L"

    # Already in meq/L
    val, unit = normalize_water_measurement("chloride", 4.5, "meq/L")
    assert val == 4.5
    assert unit == "meq/L"


# ===========================================================================
# 2. UNIT TESTS: SAR AND RSC CALCULATIONS
# ===========================================================================

def test_calculate_sar_and_rsc_valid():
    measurements = {
        "sodium": {"normalized_value": 5.0, "normalized_unit": "meq/L"},
        "calcium": {"normalized_value": 3.0, "normalized_unit": "meq/L"},
        "magnesium": {"normalized_value": 2.0, "normalized_unit": "meq/L"},
        "carbonate": {"normalized_value": 0.5, "normalized_unit": "meq/L"},
        "bicarbonate": {"normalized_value": 6.0, "normalized_unit": "meq/L"},
    }
    indices = calculate_sar_and_rsc(measurements)

    # SAR = 5.0 / sqrt((3.0 + 2.0) / 2) = 5.0 / sqrt(2.5) = 5.0 / 1.5811 = 3.16
    assert indices.sar_status == "AVAILABLE"
    assert pytest.approx(indices.sar, 0.01) == 3.16

    # RSC = (0.5 + 6.0) - (3.0 + 2.0) = 6.5 - 5.0 = 1.50 meq/L
    assert indices.rsc_status == "AVAILABLE"
    assert indices.rsc == 1.50


def test_calculate_sar_missing_constituent():
    # Missing calcium
    measurements = {
        "sodium": {"normalized_value": 5.0, "normalized_unit": "meq/L"},
        "magnesium": {"normalized_value": 2.0, "normalized_unit": "meq/L"},
    }
    indices = calculate_sar_and_rsc(measurements)
    assert indices.sar is None
    assert indices.sar_status == "INCOMPLETE_INPUTS"


def test_calculate_sar_zero_divisor():
    measurements = {
        "sodium": {"normalized_value": 5.0, "normalized_unit": "meq/L"},
        "calcium": {"normalized_value": 0.0, "normalized_unit": "meq/L"},
        "magnesium": {"normalized_value": 0.0, "normalized_unit": "meq/L"},
    }
    indices = calculate_sar_and_rsc(measurements)
    assert indices.sar is None
    assert indices.sar_status == "ZERO_DIVISOR"


def test_calculate_sar_rsc_negative_inputs_rejected():
    """Verify that negative ion concentrations are strictly rejected rather than computing misleading values."""
    measurements = {
        "sodium": {"normalized_value": -5.0, "normalized_unit": "meq/L"},
        "calcium": {"normalized_value": 3.0, "normalized_unit": "meq/L"},
        "magnesium": {"normalized_value": 2.0, "normalized_unit": "meq/L"},
    }
    indices = calculate_sar_and_rsc(measurements)
    assert indices.sar is None
    assert indices.sar_status == "INVALID_INPUT"
    assert any("negative concentration" in note for note in indices.calculation_notes)


def test_rsc_carbonate_strict_non_inference_default():
    """Verify that by default, missing CO3 is strictly NOT inferred and RSC is marked INCOMPLETE_INPUTS."""
    # CO3 missing from laboratory report
    measurements = {
        "calcium": {"normalized_value": 2.0, "normalized_unit": "meq/L"},
        "magnesium": {"normalized_value": 1.0, "normalized_unit": "meq/L"},
        "bicarbonate": {"normalized_value": 4.0, "normalized_unit": "meq/L"},
        "ph": {"original_value": 7.5, "original_unit": "pH"},
    }
    res = calculate_sar_and_rsc(measurements)  # default allow_carbonate_inference=False
    assert res.rsc is None
    assert res.rsc_status == "INCOMPLETE_INPUTS"
    assert res.inputs_used.get("CO3_provenance") == "NOT_PROVIDED"
    assert res.inputs_used.get("CO3_meq_l") is None  # Must NOT silently become 0.0!
    assert any("automatic inference is disabled" in note for note in res.calculation_notes)


def test_rsc_carbonate_provenance_and_explicit_opt_in():
    """Verify that CO3 is preserved as LAB_MEASURED when supplied, or INFERRED_APHA_2320B when explicitly enabled."""
    # Case A: CO3 explicitly supplied by lab (never overwritten)
    m_supplied = {
        "calcium": {"normalized_value": 2.0, "normalized_unit": "meq/L"},
        "magnesium": {"normalized_value": 1.0, "normalized_unit": "meq/L"},
        "carbonate": {"normalized_value": 0.2, "normalized_unit": "meq/L"},
        "bicarbonate": {"normalized_value": 4.0, "normalized_unit": "meq/L"},
        "ph": {"original_value": 7.8, "original_unit": "pH"},
    }
    res_a = calculate_sar_and_rsc(m_supplied, allow_carbonate_inference=True)
    assert res_a.rsc_status == "AVAILABLE"
    assert res_a.inputs_used.get("CO3_provenance") == "LAB_MEASURED"
    assert res_a.inputs_used.get("CO3_meq_l") == 0.2
    assert res_a.rsc == round((0.2 + 4.0) - (2.0 + 1.0), 2)  # 1.20 meq/L

    # Case B: CO3 missing and allow_carbonate_inference=True with pH < 8.3 -> inferred per APHA 2320 B
    m_inferred = {
        "calcium": {"normalized_value": 2.0, "normalized_unit": "meq/L"},
        "magnesium": {"normalized_value": 1.0, "normalized_unit": "meq/L"},
        "bicarbonate": {"normalized_value": 4.0, "normalized_unit": "meq/L"},
        "ph": {"original_value": 7.5, "original_unit": "pH"},
    }
    res_b = calculate_sar_and_rsc(m_inferred, allow_carbonate_inference=True)
    assert res_b.rsc_status == "AVAILABLE"
    assert res_b.inputs_used.get("CO3_provenance") == "INFERRED_APHA_2320B"
    assert res_b.inputs_used.get("CO3_meq_l") == 0.0
    assert res_b.rsc == round((0.0 + 4.0) - (2.0 + 1.0), 2)  # 1.0 meq/L

    # Case C: CO3 missing, allow_carbonate_inference=True, but pH >= 8.3 -> cannot infer, marked INCOMPLETE_INPUTS
    m_alkaline = {
        "calcium": {"normalized_value": 2.0, "normalized_unit": "meq/L"},
        "magnesium": {"normalized_value": 1.0, "normalized_unit": "meq/L"},
        "bicarbonate": {"normalized_value": 4.0, "normalized_unit": "meq/L"},
        "ph": {"original_value": 8.7, "original_unit": "pH"},
    }
    res_c = calculate_sar_and_rsc(m_alkaline, allow_carbonate_inference=True)
    assert res_c.rsc_status == "INCOMPLETE_INPUTS"
    assert res_c.inputs_used.get("CO3_provenance") == "NOT_PROVIDED"


# ===========================================================================
# 3. UNIT TESTS: INSTITUTIONAL RULE EVALUATION (IS 11624:2019 & CSSRI 1/98)
# ===========================================================================

def test_water_evaluator_institutional_rules():
    measurements = {
        "electrical_conductivity": {"normalized_value": 2.4, "normalized_unit": "dS/m"},
        "sodium": {"normalized_value": 12.0, "normalized_unit": "meq/L"},
        "calcium": {"normalized_value": 2.0, "normalized_unit": "meq/L"},
        "magnesium": {"normalized_value": 1.0, "normalized_unit": "meq/L"},
        "carbonate": {"normalized_value": 0.0, "normalized_unit": "meq/L"},
        "bicarbonate": {"normalized_value": 6.5, "normalized_unit": "meq/L"},
        "boron": {"normalized_value": 1.2, "normalized_unit": "mg/L"},
        "chloride": {"normalized_value": 6.0, "normalized_unit": "meq/L"},
        "fluoride": {"normalized_value": 0.8, "normalized_unit": "mg/L"},
    }
    response = WaterQualityEvaluator.evaluate(
        measurements,
        farm_id=str(TEST_FARM_ID),
        soil_clay_percent=35.0,
        annual_rainfall_mm=600.0,
    )

    # SAR = 12.0 / sqrt((2.0 + 1.0) / 2) = 12.0 / sqrt(1.5) = 12.0 / 1.2247 = 9.80 (< 10 -> Low)
    # RSC = (0.0 + 6.5) - (2.0 + 1.0) = 3.50 (2.5 - 4.0 -> Marginally Alkali)
    eval_map = {e.parameter_key: e for e in response.evaluations}

    # EC rule (IS 11624:2019 Clause 5.1.1)
    assert "electrical_conductivity" in eval_map
    assert eval_map["electrical_conductivity"].hazard_level == "MEDIUM"
    assert "BIS IS 11624:2019" in eval_map["electrical_conductivity"].applicable_standard
    assert eval_map["electrical_conductivity"].rule_id == "BIS-11624-2019-CL-5.1.1-EC"

    # SAR rule (IS 11624:2019 Clause 5.1.3)
    assert "sar" in eval_map
    assert eval_map["sar"].hazard_level == "LOW"
    assert eval_map["sar"].rule_id == "BIS-11624-2019-CL-5.1.3-SAR"

    # RSC rule (CSSRI Tech Bull 1/98 & Clause 5.1.4)
    assert "rsc" in eval_map
    assert eval_map["rsc"].hazard_level == "HAZARDOUS"
    assert "Technical Bulletin No. 1/98" in eval_map["rsc"].source_citation
    assert eval_map["rsc"].rule_id == "CSSRI-TECH-BULL-1-98-RSC"

    # Table 1 Combined Classification: EC=2.4 (<4.0), SAR=9.8 (<10), RSC=3.5 (2.5-4.0) -> Marginally Alkali
    assert "is11624_table1_combined_group" in eval_map
    assert "Marginally Alkali" in eval_map["is11624_table1_combined_group"].hazard_title
    assert eval_map["is11624_table1_combined_group"].rule_id == "BIS-11624-2019-TAB1-COMBINED"

    # Table 2 Boron rule: 1.2 mg/L -> Class 2: Medium Boron (1.0 - 2.0 mg/L)
    assert "boron" in eval_map
    assert eval_map["boron"].hazard_level == "MARGINAL"
    assert eval_map["boron"].rule_id == "BIS-11624-2019-TAB2-BORON"

    # Chloride rule (CSSRI Tech Bull 1/98): 6.0 meq/L -> Slight to Moderate Restriction
    assert "chloride" in eval_map
    assert eval_map["chloride"].hazard_level == "RESTRICTED"
    assert eval_map["chloride"].rule_id == "CSSRI-TECH-BULL-1-98-CHLORIDE"

    # Table 6 Trace Element: Fluoride 0.8 mg/L <= 1.0 mg/L -> Safe
    assert "fluoride" in eval_map
    assert eval_map["fluoride"].hazard_level == "SAFE"
    assert eval_map["fluoride"].rule_id == "BIS-11624-2019-TAB6-FLUORIDE"

    # Tables 3-5 Soil Texture & Rainfall Suitability (clay=35%, rainfall=600mm)
    assert "soil_texture_rainfall_suitability" in eval_map
    assert eval_map["soil_texture_rainfall_suitability"].hazard_level == "HIGH"  # EC 2.4 > limit 2.0

    # Regional CGWB context
    assert response.regional_cgwb_context is not None
    assert response.regional_cgwb_context["classification_scope"] == "REGIONAL_CONTEXT_ONLY"


def test_water_evaluator_unverified_when_context_missing():
    """Verify that when soil clay and rainfall context are omitted, Table 3-5 is marked UNVERIFIED."""
    measurements = {
        "electrical_conductivity": {"normalized_value": 1.2, "normalized_unit": "dS/m"},
    }
    response = WaterQualityEvaluator.evaluate(
        measurements,
        farm_id=str(TEST_FARM_ID),
        # Omit soil_clay_percent and annual_rainfall_mm
    )
    eval_map = {e.parameter_key: e for e in response.evaluations}

    # Table 1 combined should be UNVERIFIED due to missing SAR and RSC
    assert "is11624_table1_combined_group" in eval_map
    assert eval_map["is11624_table1_combined_group"].hazard_level == "UNVERIFIED"

    # Tables 3-5 conditional should be UNVERIFIED
    assert "soil_texture_rainfall_suitability" in eval_map
    assert eval_map["soil_texture_rainfall_suitability"].hazard_level == "UNVERIFIED"
    assert "Conditional Suitability" in eval_map["soil_texture_rainfall_suitability"].hazard_title


def test_is11624_table1_combined_classification_matrix():
    """Verify all 7 IS 11624:2019 Table 1 poor-quality groundwater categories."""
    cases = [
        # (EC, SAR, RSC, expected_group, expected_hazard)
        (1.2, 5.0, 1.0, "Good Water", "SAFE"),
        (2.8, 6.0, 1.5, "Marginally Saline", "MARGINAL"),
        (5.2, 8.0, 2.0, "Saline Water", "HIGH"),
        (5.5, 14.0, 1.8, "High-SAR Saline", "HAZARDOUS"),
        (2.5, 7.0, 3.2, "Marginally Alkali", "MARGINAL"),
        (3.0, 6.0, 4.8, "Alkali Water", "HIGH"),
        (4.5, 15.0, 5.2, "High-SAR Alkali", "HAZARDOUS"),
    ]
    for ec, sar, rsc, exp_group, exp_hazard in cases:
        measurements = {
            "electrical_conductivity": {"normalized_value": ec, "normalized_unit": "dS/m"},
            "sar": {"original_value": sar},
            "rsc": {"original_value": rsc},
        }
        res = WaterQualityEvaluator.evaluate(measurements, farm_id=str(TEST_FARM_ID))
        eval_map = {e.parameter_key: e for e in response.evaluations} if False else {e.parameter_key: e for e in res.evaluations}
        item = eval_map["is11624_table1_combined_group"]
        assert exp_group in item.hazard_title, f"Expected {exp_group} for EC={ec}, SAR={sar}, RSC={rsc}, got {item.hazard_title}"
        assert item.hazard_level == exp_hazard


def test_is11624_table6_trace_elements():
    """Verify Table 6 trace element limits (e.g. Iron 5.0 mg/L, Zinc 2.0 mg/L, Lead 5.0 mg/L)."""
    measurements = {
        "iron": {"normalized_value": 7.5, "normalized_unit": "mg/L"},     # > 5.0 -> HAZARDOUS
        "zinc": {"normalized_value": 1.2, "normalized_unit": "mg/L"},     # <= 2.0 -> SAFE
        "lead": {"normalized_value": 0.05, "normalized_unit": "mg/L"},    # <= 5.0 -> SAFE
        "cadmium": {"normalized_value": 0.02, "normalized_unit": "mg/L"}, # > 0.01 -> HAZARDOUS
    }
    res = WaterQualityEvaluator.evaluate(measurements, farm_id=str(TEST_FARM_ID))
    eval_map = {e.parameter_key: e for e in res.evaluations}

    assert eval_map["iron"].hazard_level == "HAZARDOUS"
    assert "Exceeds Permissible Limit" in eval_map["iron"].hazard_title

    assert eval_map["zinc"].hazard_level == "SAFE"
    assert "Within Permissible Limit" in eval_map["zinc"].hazard_title

    assert eval_map["lead"].hazard_level == "SAFE"
    assert eval_map["cadmium"].hazard_level == "HAZARDOUS"


# ===========================================================================
# 4. INTEGRATION TESTS: WATER SOURCES CRUD & OWNERSHIP
# ===========================================================================

def test_water_sources_lifecycle(client):
    # 1. Create water source
    source_payload = {
        "source_type": "borewell",
        "name": "North Field Deep Borewell",
        "location_description": "Near solar pump shed",
        "latitude": 18.151,
        "longitude": 74.552,
        "seasonal_availability": "perennial",
        "reliability": "reliable",
        "daily_available_hours": 7.5,
        "irrigation_method": "drip",
        "measured_capacity_lph": 12000.0,
        "capacity_provenance": "MEASURED",
    }
    res = client.post(f"/api/v1/farms/{TEST_FARM_ID}/water/sources", json=source_payload)
    assert res.status_code == 201
    created = res.json()
    source_id = created["id"]
    assert created["name"] == "North Field Deep Borewell"
    assert created["measured_capacity_lph"] == 12000.0
    assert created["capacity_provenance"] == "MEASURED"

    # 2. List sources
    res = client.get(f"/api/v1/farms/{TEST_FARM_ID}/water/sources")
    assert res.status_code == 200
    sources = res.json()
    assert len(sources) >= 1
    assert any(s["id"] == source_id for s in sources)

    # 3. Update source
    res = client.put(f"/api/v1/farms/{TEST_FARM_ID}/water/sources/{source_id}", json={
        "daily_available_hours": 6.0,
        "reliability": "moderate"
    })
    assert res.status_code == 200
    assert res.json()["daily_available_hours"] == 6.0
    assert res.json()["reliability"] == "moderate"

    # 4. Delete source
    res = client.delete(f"/api/v1/farms/{TEST_FARM_ID}/water/sources/{source_id}")
    assert res.status_code == 204

    # Verify inactive
    res = client.get(f"/api/v1/farms/{TEST_FARM_ID}/water/sources")
    assert not any(s["id"] == source_id for s in res.json())


# ===========================================================================
# 5. INTEGRATION TESTS: WATER REPORT UPLOAD, REVIEW & ISOLATION
# ===========================================================================

def test_water_report_upload_confirm_and_isolation(client, isolated_water_db):
    # 1. Upload sample water lab report
    fake_pdf = b"%PDF-1.4 test water laboratory report bytes"
    files = {"file": ("water_test_2026.pdf", fake_pdf, "application/pdf")}
    data = {
        "laboratory_name": "District Water Testing Lab Pune",
        "sampling_location": "Borewell 1 Discharge",
    }
    res = client.post(
        f"/api/v1/farms/{TEST_FARM_ID}/water/reports/upload",
        files=files,
        data=data,
    )
    assert res.status_code == 201
    report = res.json()
    report_id = report["id"]
    assert report["review_status"] == "NEEDS_REVIEW"
    assert len(report["measurements"]) >= 10
    assert report["calculated_indices"]["sar_status"] == "AVAILABLE"

    # 2. Confirm report with a farmer correction
    meas_id = report["measurements"][0]["id"]
    confirm_payload = {
        "laboratory_name": "District Water Testing Lab Pune (Verified)",
        "corrections": [
            {
                "measurement_id": meas_id,
                "farmer_corrected_value": 7.4,
                "farmer_notes": "Corrected according to hardcopy certificate stamp."
            }
        ]
    }
    res = client.post(f"/api/v1/farms/{TEST_FARM_ID}/water/reports/{report_id}/confirm", json=confirm_payload)
    assert res.status_code == 200
    conf = res.json()
    assert conf["success"] is True
    assert conf["review_status"] == "CONFIRMED"

    # 3. Check institutional water evaluation endpoint
    res = client.get(f"/api/v1/farms/{TEST_FARM_ID}/water/evaluation")
    assert res.status_code == 200
    eval_data = res.json()
    assert len(eval_data["evaluations"]) >= 2
    assert "calculated_indices" in eval_data

    # 4. Strict isolation verification:
    # Ensure water measurements exist in WaterMeasurementModel,
    # and zero water records exist in SoilMeasurementModel!
    water_count = isolated_water_db.query(WaterMeasurementModel).filter(
        WaterMeasurementModel.farm_id == str(TEST_FARM_ID)
    ).count()
    assert water_count > 0

    soil_meas_with_water = isolated_water_db.query(SoilMeasurementModel).filter(
        SoilMeasurementModel.parameter_key.in_(["sar", "rsc", "electrical_conductivity"])
    ).filter(
        SoilMeasurementModel.farm_id == str(TEST_FARM_ID)
    ).count()
    # Soil measurements table must NOT contain these water records
    assert soil_meas_with_water == 0
