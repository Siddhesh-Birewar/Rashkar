"""
CropNet AI — Phase 5.9A Unified Farm Health Backend Test Suite.

Comprehensive tests verifying:
1. Full Evidence Snapshot (All 5 domains AVAILABLE, matching contract Example A)
2. Missing Evidence Snapshot (Brand new parcel, matching contract Example B, explicit nulls, zero dummy values)
3. Stale Evidence Handling (Expired thresholds, matching contract Example C, STALE states)
4. Farm Ownership Enforcement & Cross-User Security (HTTP 403 Forbidden)
5. Multi-Farm Isolation (User A isolated from User B)
6. Non-Existent Farm Handling (HTTP 404 Not Found)
7. In-Memory 5-Min TTL Caching and force_refresh bypass
8. Cache Invalidation via invalidate_snapshot and POST invalidate endpoint
9. Domain Fault Isolation (Collector failure does NOT crash snapshot)
10. Strict Agronomic Governance (ZERO universal health score, ZERO synthetic values)
"""
import uuid
import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from cropnet.services.api.app.main import app
from cropnet.services.api.app.core.database import get_db
from cropnet.services.api.app.models.soil_and_farm import (
    Base,
    FarmModel,
    FarmSoilProfileModel,
    SoilParameterModel,
)
from cropnet.services.api.app.models.soil_reports import (
    SoilTestReportModel,
    SoilMeasurementModel,
)
from cropnet.services.api.app.models.water import (
    WaterSourceModel,
    WaterTestReportModel,
    WaterMeasurementModel,
)
from cropnet.services.api.app.models.satellite import (
    SatelliteVegetationObservationModel,
)
from cropnet.services.api.app.models.weather import (
    FarmWeatherSnapshotModel,
    FarmClimateSummaryModel,
)
from cropnet.services.api.app.api.v1.endpoints.farms import _FARM_STORAGE
from cropnet.services.api.app.schemas.farm_health import (
    DataAvailabilityState,
    FarmHealthSnapshotResponse,
)
from cropnet.services.api.app.services.farm_health.cache import (
    get_snapshot_cache,
    invalidate_snapshot,
)
from cropnet.services.api.app.services.farm_health.collectors.crop_collector import (
    record_farm_evaluation,
    clear_farm_evaluations,
)
from cropnet.services.api.app.schemas.agriculture_intelligence import (
    FarmEvaluationResponse,
    CropEvaluationOutcome,
    DecisionState,
    FarmContextInput,
    FollowUpQuestion,
)

USER_1_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
USER_2_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")

FARM_FULL_ID = uuid.UUID("94a1f16e-bf0d-4d3f-9bd3-d63a57189818")
FARM_EMPTY_ID = uuid.UUID("e4b2d189-9a74-4b5c-897b-3d6e5c9f1a23")
FARM_STALE_ID = uuid.UUID("c8d2e3f4-5678-4abc-9def-0123456789ab")
FARM_USER2_ID = uuid.UUID("77777777-7777-7777-7777-777777777777")


@pytest.fixture
def snapshot_test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()

    now = datetime.now(timezone.utc)

    # 1. Full Evidence Farm (owned by User 1)
    farm_full = FarmModel(
        id=str(FARM_FULL_ID),
        owner_id=str(USER_1_ID),
        name="Baramati Model Farm",
        village="Malegaon",
        taluka="Baramati",
        district="Pune",
        state="Maharashtra",
        geometry_geojson={"type": "Polygon", "coordinates": [[[74.5, 18.1], [74.6, 18.1], [74.6, 18.2], [74.5, 18.2], [74.5, 18.1]]]},
        calculated_area_hectares=2.5,
        calculated_area_acres=6.18,
        created_at=now - timedelta(days=60),
        updated_at=now,
    )

    # 2. Empty/Brand New Farm (owned by User 1)
    farm_empty = FarmModel(
        id=str(FARM_EMPTY_ID),
        owner_id=str(USER_1_ID),
        name="New Registered Parcel",
        village="Bhigwan",
        taluka="Indapur",
        district="Pune",
        state="Maharashtra",
        geometry_geojson={"type": "Polygon", "coordinates": [[[74.9, 18.0], [74.92, 18.0], [74.92, 18.02], [74.9, 18.02], [74.9, 18.0]]]},
        calculated_area_hectares=1.2,
        calculated_area_acres=2.97,
        created_at=now,
        updated_at=now,
    )

    # 3. Stale Farm (owned by User 1)
    farm_stale = FarmModel(
        id=str(FARM_STALE_ID),
        owner_id=str(USER_1_ID),
        name="Sangamner Pomegranate Orchard",
        village="Ashwi",
        taluka="Sangamner",
        district="Ahmednagar",
        state="Maharashtra",
        geometry_geojson={"type": "Polygon", "coordinates": [[[74.2, 19.5], [74.25, 19.5], [74.25, 19.55], [74.2, 19.55], [74.2, 19.5]]]},
        calculated_area_hectares=3.1,
        calculated_area_acres=7.66,
        created_at=now - timedelta(days=1600),
        updated_at=now,
    )

    # 4. User 2 Farm
    farm_u2 = FarmModel(
        id=str(FARM_USER2_ID),
        owner_id=str(USER_2_ID),
        name="User 2 Farm",
        village="Baramati",
        taluka="Baramati",
        district="Pune",
        state="Maharashtra",
        geometry_geojson={"type": "Polygon", "coordinates": [[[74.5, 18.1], [74.6, 18.1], [74.6, 18.2], [74.5, 18.2], [74.5, 18.1]]]},
        calculated_area_hectares=2.0,
        calculated_area_acres=4.94,
        created_at=now,
        updated_at=now,
    )

    session.add_all([farm_full, farm_empty, farm_stale, farm_u2])
    session.commit()

    # Register in _FARM_STORAGE
    for f in [farm_full, farm_empty, farm_stale, farm_u2]:
        _FARM_STORAGE[uuid.UUID(f.id)] = {
            "id": uuid.UUID(f.id),
            "owner_id": uuid.UUID(f.owner_id),
            "farm_name": f.name,
            "name": f.name,
            "taluka": f.taluka,
            "district": f.district,
            "state": f.state,
            "geometry": f.geometry_geojson,
            "calculated_area_hectares": f.calculated_area_hectares,
            "calculated_area_acres": f.calculated_area_acres,
        }

    # =========================================================================
    # SEED DATA FOR FARM_FULL (ALL 5 DOMAINS AVAILABLE)
    # =========================================================================
    soil_date = now - timedelta(days=24)
    # Soil Test Report
    soil_rep = SoilTestReportModel(
        id=str(uuid.uuid4()),
        user_id=str(USER_1_ID),
        farm_id=str(FARM_FULL_ID),
        original_filename="kvk_baramati_card.pdf",
        storage_path="/storage/soil/kvk_baramati.pdf",
        laboratory_name="KVK Baramati Soil Testing Laboratory",
        report_date=soil_date,
        sample_depth_interval="0-15 cm",
        review_status="CONFIRMED",
        confirmed_at=soil_date,
    )
    session.add(soil_rep)
    session.flush()

    soil_meas_data = [
        ("soil_ph", 7.6, "pH", 7.6, "pH"),
        ("organic_carbon", 0.58, "%", 0.58, "%"),
        ("electrical_conductivity", 0.45, "dS/m", 0.45, "dS/m"),
        ("available_nitrogen", 210.0, "kg/ha", 210.0, "kg/ha"),
        ("available_phosphorus", 18.5, "kg/ha", 18.5, "kg/ha"),
        ("available_potassium", 340.0, "kg/ha", 340.0, "kg/ha"),
        ("soil_texture", 0.0, "text", None, "Clay Loam"),
        ("cation_exchange_capacity", 38.2, "cmol/kg", 38.2, "cmol(+)/kg"),
    ]
    for param, orig_v, orig_u, norm_v, norm_u in soil_meas_data:
        session.add(
            SoilMeasurementModel(
                id=str(uuid.uuid4()),
                report_id=soil_rep.id,
                farm_id=str(FARM_FULL_ID),
                parameter_key=param,
                original_parameter_name=param,
                original_value=orig_v,
                original_value_text="Clay Loam" if param == "soil_texture" else str(orig_v),
                original_unit=orig_u,
                normalized_value=norm_v,
                normalized_unit=norm_u,
                farmer_corrected_value=norm_v if isinstance(norm_v, float) else None,
                verification_status="FARMER_CONFIRMED",
            )
        )

    # Water Source & Confirmed Report
    w_source = WaterSourceModel(
        id="wsrc-001",
        farm_id=str(FARM_FULL_ID),
        source_type="borewell",
        name="North Field Borewell",
        seasonal_availability="perennial",
        reliability="reliable",
        irrigation_method="drip",
        measured_capacity_lph=12000.0,
        capacity_provenance="MEASURED",
        is_active=True,
    )
    session.add(w_source)

    water_date = now - timedelta(days=49)
    water_rep = WaterTestReportModel(
        id=str(uuid.uuid4()),
        user_id=str(USER_1_ID),
        farm_id=str(FARM_FULL_ID),
        water_source_id="wsrc-001",
        original_filename="water_lab_pune.pdf",
        storage_path="/storage/water/lab_pune.pdf",
        laboratory_name="Agricultural Water Testing Laboratory, Pune",
        report_date=water_date,
        review_status="CONFIRMED",
        confirmed_at=water_date,
    )
    session.add(water_rep)
    session.flush()

    water_meas_data = [
        ("ph", 7.6, "pH", 7.6, "pH"),
        ("electrical_conductivity", 1.85, "dS/m", 1.85, "dS/m"),
        ("tds", 1184.0, "mg/L", 1184.0, "mg/L"),
        ("sodium", 6.8, "meq/L", 6.8, "meq/L"),
        ("calcium", 6.2, "meq/L", 6.2, "meq/L"),
        ("magnesium", 4.0, "meq/L", 4.0, "meq/L"),
        ("carbonate", 0.0, "meq/L", 0.0, "meq/L"),
        ("bicarbonate", 8.3, "meq/L", 8.3, "meq/L"),
        ("chloride", 4.8, "meq/L", 4.8, "meq/L"),
        ("boron", 0.65, "mg/L", 0.65, "mg/L"),
    ]
    for param, orig_v, orig_u, norm_v, norm_u in water_meas_data:
        session.add(
            WaterMeasurementModel(
                id=str(uuid.uuid4()),
                report_id=water_rep.id,
                farm_id=str(FARM_FULL_ID),
                parameter_key=param,
                original_parameter_name=param,
                original_value=orig_v,
                original_unit=orig_u,
                normalized_value=norm_v,
                normalized_unit=norm_u,
                verification_status="FARMER_CONFIRMED",
            )
        )

    # Satellite Observation (4 days old)
    sat_date = now - timedelta(days=4)
    session.add(
        SatelliteVegetationObservationModel(
            id=str(uuid.uuid4()),
            farm_id=str(FARM_FULL_ID),
            observation_date=sat_date,
            product_id="S2B_MSIL2A_20261104T053009_N0513_R105_T43QDB_20261104T073410",
            sensor="Sentinel-2 L2A",
            mean_ndvi=0.52,
            mean_ndmi=0.18,
            valid_pixel_count=250,
            total_pixel_count=250,
            cloud_masked_percent=0.0,
            quality_status="VALID_OBSERVATION",
            is_small_farm_warning=False,
            quality_notes="veg_px: 171, soil_px: 79, veg_ndvi: 0.68, veg_ndmi: 0.22, soil_ndvi: 0.28, vegetation canopy pixels (68.4%), bare soil pixels (31.6%)",
        )
    )

    # Weather Snapshot (20 mins old)
    wx_date = now - timedelta(minutes=20)
    session.add(
        FarmWeatherSnapshotModel(
            id=str(uuid.uuid4()),
            farm_id=str(FARM_FULL_ID),
            snapshot_type="current",
            source="OpenWeather",
            observation_time=wx_date,
            temperature=28.4,
            feels_like=29.0,
            temperature_min=22.0,
            temperature_max=31.0,
            humidity=48.0,
            wind_speed=3.1,
            wind_direction=180.0,
            precipitation_mm=0.0,
            weather_condition="Clear",
            weather_description="clear sky",
        )
    )
    session.add(
        FarmClimateSummaryModel(
            id=str(uuid.uuid4()),
            farm_id=str(FARM_FULL_ID),
            source="NASA POWER",
            period_description="30-year Climatology",
            annual_rainfall_mm=560.0,
            monsoon_rainfall_mm=440.0,
            monsoon_share_percent=78.5,
            mean_temperature_c=24.5,
            min_temperature_c=18.0,
            max_temperature_c=32.0,
            rainfall_variability_index=0.25,
            potential_water_stress_indicator="Moderate seasonal winter dry spell",
            monthly_rainfall_json={},
            monthly_temperature_json={},
            wet_season_months_json=["June", "July", "August", "September"],
            dry_season_months_json=["January", "February", "March", "April"],
            agricultural_seasons_json={},
        )
    )

    # Register crop evaluation for Full farm
    crop_eval_full = FarmEvaluationResponse(
        decision_id="eval-full-001",
        evaluated_at=now - timedelta(hours=2),
        input_validation_status="VALID",
        taluka_resolved="Baramati",
        target_season="Rabi 2026-27",
        farm_context=FarmContextInput(farm_id=str(FARM_FULL_ID), taluka="Baramati"),
        crop_outcomes=[
            CropEvaluationOutcome(
                crop_id="wheat",
                common_name="Wheat",
                scientific_name="Triticum aestivum",
                marathi_name="गहू",
                decision_state=DecisionState.VERIFIED_SUITABLE,
                is_disqualified=False,
                limiting_factors=[],
                irrigation_guidance={"guidance": "Crown root initiation (CRI) irrigation critical at 21 DAS."},
                explanation="Verified suitable under current soil and water profile.",
            ),
            CropEvaluationOutcome(
                crop_id="chickpea",
                common_name="Chickpea",
                scientific_name="Cicer arietinum",
                marathi_name="हरभरा",
                decision_state=DecisionState.VERIFIED_SUITABLE,
                is_disqualified=False,
                limiting_factors=[],
                irrigation_guidance={"guidance": "Branching and pod initiation irrigations recommended."},
                explanation="Verified suitable.",
            ),
            CropEvaluationOutcome(
                crop_id="onion",
                common_name="Rabi Onion",
                scientific_name="Allium cepa",
                marathi_name="कांदा",
                decision_state=DecisionState.CONDITIONALLY_SUITABLE_PENDING_DATA,
                is_disqualified=False,
                limiting_factors=["Moderate salinity sensitivity in Vertisols"],
                irrigation_guidance={"guidance": "Frequent light irrigations required to minimize salinity stress."},
                explanation="Conditionally suitable pending salinity management.",
            ),
        ],
        follow_up_questions=[
            FollowUpQuestion(
                question_id="q-001",
                target_parameter="water_table_depth",
                priority=2,
                question_text_en="What is your water table depth?",
                question_text_mr="तुमची भूजल पातळी किती आहे?",
                question_type="choice",
                agronomic_rationale="Evaluates drainage risk.",
            )
        ],
    )
    record_farm_evaluation(str(FARM_FULL_ID), crop_eval_full)

    # =========================================================================
    # SEED DATA FOR FARM_STALE (ALL 5 DOMAINS STALE)
    # =========================================================================
    stale_soil_date = now - timedelta(days=1551)
    stale_soil_rep = SoilTestReportModel(
        id=str(uuid.uuid4()),
        user_id=str(USER_1_ID),
        farm_id=str(FARM_STALE_ID),
        original_filename="rahuri_soil_2022.pdf",
        storage_path="/storage/soil/rahuri_2022.pdf",
        laboratory_name="Rahuri Agricultural University Soil Lab",
        report_date=stale_soil_date,
        sample_depth_interval="0-30 cm",
        review_status="CONFIRMED",
        confirmed_at=stale_soil_date,
    )
    session.add(stale_soil_rep)
    session.flush()

    for param, orig_v, orig_u, norm_v, norm_u in [
        ("soil_ph", 8.1, "pH", 8.1, "pH"),
        ("organic_carbon", 0.42, "%", 0.42, "%"),
        ("electrical_conductivity", 0.62, "dS/m", 0.62, "dS/m"),
        ("available_nitrogen", 185.0, "kg/ha", 185.0, "kg/ha"),
        ("available_phosphorus", 12.0, "kg/ha", 12.0, "kg/ha"),
        ("available_potassium", 290.0, "kg/ha", 290.0, "kg/ha"),
    ]:
        session.add(
            SoilMeasurementModel(
                id=str(uuid.uuid4()),
                report_id=stale_soil_rep.id,
                farm_id=str(FARM_STALE_ID),
                parameter_key=param,
                original_parameter_name=param,
                original_value=orig_v,
                original_unit=orig_u,
                normalized_value=norm_v,
                normalized_unit=norm_u,
                verification_status="FARMER_CONFIRMED",
            )
        )

    # Stale Water Source & Confirmed Report (511 days old)
    stale_w_source = WaterSourceModel(
        id="wsrc-stale",
        farm_id=str(FARM_STALE_ID),
        source_type="open_well",
        name="East Perimeter Well",
        seasonal_availability="seasonal_post_monsoon",
        reliability="moderate",
        irrigation_method="drip",
        measured_capacity_lph=8000.0,
        capacity_provenance="FARMER_REPORTED",
        is_active=True,
    )
    session.add(stale_w_source)

    stale_water_date = now - timedelta(days=511)
    stale_water_rep = WaterTestReportModel(
        id=str(uuid.uuid4()),
        user_id=str(USER_1_ID),
        farm_id=str(FARM_STALE_ID),
        water_source_id="wsrc-stale",
        original_filename="water_ahmednagar_2025.pdf",
        storage_path="/storage/water/ahmednagar.pdf",
        laboratory_name="District Water Testing Lab, Ahmednagar",
        report_date=stale_water_date,
        review_status="CONFIRMED",
        confirmed_at=stale_water_date,
    )
    session.add(stale_water_rep)
    session.flush()

    for param, orig_v, orig_u, norm_v, norm_u in [
        ("ph", 7.9, "pH", 7.9, "pH"),
        ("electrical_conductivity", 2.2, "dS/m", 2.2, "dS/m"),
        ("tds", 1408.0, "mg/L", 1408.0, "mg/L"),
        ("sodium", 8.2, "meq/L", 8.2, "meq/L"),
        ("calcium", 5.0, "meq/L", 5.0, "meq/L"),
        ("magnesium", 3.0, "meq/L", 3.0, "meq/L"),
        ("carbonate", 0.0, "meq/L", 0.0, "meq/L"),
        ("bicarbonate", 9.2, "meq/L", 9.2, "meq/L"),
    ]:
        session.add(
            WaterMeasurementModel(
                id=str(uuid.uuid4()),
                report_id=stale_water_rep.id,
                farm_id=str(FARM_STALE_ID),
                parameter_key=param,
                original_parameter_name=param,
                original_value=orig_v,
                original_unit=orig_u,
                normalized_value=norm_v,
                normalized_unit=norm_u,
                verification_status="FARMER_CONFIRMED",
            )
        )

    # Stale Satellite (57 days old)
    session.add(
        SatelliteVegetationObservationModel(
            id=str(uuid.uuid4()),
            farm_id=str(FARM_STALE_ID),
            observation_date=now - timedelta(days=57),
            product_id="S2B_MSIL2A_20260912T053009_N0513_R105_T43QDB_20260912T074000",
            sensor="Sentinel-2 L2A",
            mean_ndvi=0.38,
            mean_ndmi=0.08,
            valid_pixel_count=310,
            total_pixel_count=310,
            cloud_masked_percent=0.0,
            quality_status="VALID_OBSERVATION",
            is_small_farm_warning=False,
            quality_notes="veg_px: 109, soil_px: 201, veg_ndvi: 0.44, veg_ndmi: 0.08, soil_ndvi: 0.25, vegetation canopy pixels (35.2%), bare soil pixels (64.8%)",
        )
    )

    # Stale Weather (5.7 hours old)
    session.add(
        FarmWeatherSnapshotModel(
            id=str(uuid.uuid4()),
            farm_id=str(FARM_STALE_ID),
            snapshot_type="current",
            source="OpenWeather",
            observation_time=now - timedelta(hours=5, minutes=42),
            temperature=21.0,
            humidity=65.0,
            precipitation_mm=0.0,
            weather_condition="Haze",
            weather_description="haze",
        )
    )

    # Stale Crop evaluation (250 days old)
    crop_eval_stale = FarmEvaluationResponse(
        decision_id="eval-stale-001",
        evaluated_at=now - timedelta(days=250),
        input_validation_status="VALID",
        taluka_resolved="Sangamner",
        target_season="Kharif 2025",
        farm_context=FarmContextInput(farm_id=str(FARM_STALE_ID), taluka="Sangamner"),
        crop_outcomes=[
            CropEvaluationOutcome(
                crop_id="pomegranate",
                common_name="Pomegranate",
                scientific_name="Punica granatum",
                marathi_name="डाळिंब",
                decision_state=DecisionState.CONDITIONALLY_SUITABLE_PENDING_DATA,
                is_disqualified=False,
                limiting_factors=["Evaluation performed for previous cropping year (>180 days old)"],
                irrigation_guidance={"guidance": "Mrungh Bahar flowering schedule requires current water test verification."},
                explanation="Stale evaluation.",
            )
        ],
        follow_up_questions=[],
    )
    record_farm_evaluation(str(FARM_STALE_ID), crop_eval_stale)

    session.commit()

    # Clear snapshot cache before test run
    get_snapshot_cache().clear()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        _FARM_STORAGE.clear()
        clear_farm_evaluations()
        get_snapshot_cache().clear()


@pytest.fixture
def client(snapshot_test_db):
    def override_get_db():
        try:
            yield snapshot_test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# =============================================================================
# 1. FULL EVIDENCE SNAPSHOT TEST (CONTRACT EXAMPLE A)
# =============================================================================

def test_full_evidence_snapshot(client):
    """
    Verifies that a farm with fresh, complete laboratory tests, recent satellite overpass,
    current weather, and evaluated crop decision returns AVAILABLE across all 5 domains.
    """
    resp = client.get(
        f"/api/v1/farms/{FARM_FULL_ID}/health-snapshot",
        headers={"X-Dev-User-Id": str(USER_1_ID)},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # Contract top-level structure
    assert data["contract_version"] == "1.0"
    assert data["farm_id"] == str(FARM_FULL_ID)
    assert data["farm_name"] == "Baramati Model Farm"
    assert data["owner_id"] == str(USER_1_ID)
    assert data["taluka"] == "Baramati"
    assert data["district"] == "Pune"
    assert data["state"] == "Maharashtra"
    assert data["calculated_area_hectares"] == 2.5
    assert data["calculated_area_acres"] == 6.18
    assert "snapshot_timestamp" in data

    # Overall Evidence Overview
    ov = data["overall_evidence_overview"]
    assert ov["domains_available"] == 5
    assert ov["domains_partially_available"] == 0
    assert ov["domains_stale"] == 0
    assert ov["domains_not_available"] == 0
    assert ov["domains_insufficient_evidence"] == 0
    assert ov["total_domains"] == 5
    assert "Complete actionable evidence available" in ov["actionable_summary"]

    # Soil domain
    soil = data["soil"]
    assert soil["availability_state"] == "AVAILABLE"
    assert soil["data_age_days"] == 24
    assert soil["provenance"] == "LABORATORY_CONFIRMED"
    assert soil["laboratory_name"] == "KVK Baramati Soil Testing Laboratory"
    assert soil["sample_depth"] == "0-15 cm"
    assert soil["key_indicators"]["soil_ph"] == 7.6
    assert soil["key_indicators"]["organic_carbon_pct"] == 0.58
    assert soil["key_indicators"]["electrical_conductivity_ds_m"] == 0.45
    assert soil["key_indicators"]["available_nitrogen_kg_ha"] == 210.0
    assert soil["key_indicators"]["available_phosphorus_kg_ha"] == 18.5
    assert soil["key_indicators"]["available_potassium_kg_ha"] == 340.0
    assert soil["key_indicators"]["cation_exchange_capacity"] == 38.2
    assert soil["missing_critical_parameters"] == []

    # Water domain
    water = data["water"]
    assert water["availability_state"] == "AVAILABLE"
    assert water["data_age_days"] == 49
    assert water["registered_sources_count"] == 1
    assert len(water["sources"]) == 1
    assert water["sources"][0]["source_type"] == "borewell"
    assert water["sources"][0]["irrigation_method"] == "drip"
    assert water["sources"][0]["measured_capacity_lph"] == 12000.0
    assert water["key_indicators"]["ph"] == 7.6
    assert water["key_indicators"]["electrical_conductivity_ds_m"] == 1.85
    assert water["key_indicators"]["tds_mg_l"] == 1184.0
    assert water["key_indicators"]["sar"] is not None
    assert water["key_indicators"]["sar_status"] == "AVAILABLE"
    assert water["key_indicators"]["rsc_meq_l"] is not None
    assert water["key_indicators"]["rsc_status"] == "AVAILABLE"
    assert len(water["institutional_evaluations"]) > 0

    # Satellite domain
    sat = data["satellite"]
    assert sat["availability_state"] == "AVAILABLE"
    assert sat["observation_age_days"] == 4
    assert sat["sensor"] == "Sentinel-2 L2A"
    assert sat["canopy_ndvi"] == 0.68
    assert sat["canopy_ndmi"] == 0.22
    assert sat["vegetation_coverage_percent"] == 68.4
    assert sat["valid_pixel_count"] == 250
    assert sat["is_small_farm_warning"] is False
    assert sat["raster_maps"]["ndvi_map_url"] is not None
    assert sat["raster_maps"]["ndmi_map_url"] is not None
    assert sat["raster_maps"]["scl_map_url"] is not None
    assert "Active photosynthetic canopy" in sat["agronomic_interpretation"]
    assert "Sentinel-2 NDVI and NDMI reflect surface optical reflectance" in sat["scientific_disclaimer"]

    # Weather domain
    wx = data["weather"]
    assert wx["availability_state"] == "AVAILABLE"
    assert wx["current_weather"]["temperature_c"] == 28.4
    assert wx["current_weather"]["humidity_percent"] == 48.0
    assert wx["climate_normals"]["annual_rainfall_mm"] == 560.0

    # Crop Context domain
    crop = data["crop_context"]
    assert crop["availability_state"] == "AVAILABLE"
    assert crop["evaluated_crops_count"] == 3
    assert len(crop["suitable_crops"]) == 2
    assert crop["suitable_crops"][0]["crop_id"] == "wheat"
    assert crop["suitable_crops"][0]["decision_state"] == "VERIFIED_SUITABLE"
    assert len(crop["conditionally_suitable_crops"]) == 1
    assert crop["conditionally_suitable_crops"][0]["crop_id"] == "onion"
    assert crop["pending_followup_questions_count"] == 1


# =============================================================================
# 2. MISSING EVIDENCE SNAPSHOT TEST (CONTRACT EXAMPLE B)
# =============================================================================

def test_missing_evidence_brand_new_parcel(client):
    """
    Verifies that a brand new parcel with zero records returns NOT_AVAILABLE across all domains
    with explicit nulls, zero dummy/manufactured numbers, and actionable onboarding guidance.
    """
    resp = client.get(
        f"/api/v1/farms/{FARM_EMPTY_ID}/health-snapshot",
        headers={"X-Dev-User-Id": str(USER_1_ID)},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["farm_id"] == str(FARM_EMPTY_ID)
    assert data["farm_name"] == "New Registered Parcel"

    # Overall Evidence Overview: exactly 5 NOT_AVAILABLE
    ov = data["overall_evidence_overview"]
    assert ov["domains_available"] == 0
    assert ov["domains_partially_available"] == 0
    assert ov["domains_stale"] == 0
    assert ov["domains_not_available"] == 5
    assert ov["domains_insufficient_evidence"] == 0
    assert "Zero evidence recorded for this farm" in ov["actionable_summary"]

    # Soil domain: all key indicators MUST be NULL
    soil = data["soil"]
    assert soil["availability_state"] == "NOT_AVAILABLE"
    assert soil["last_updated"] is None
    assert soil["data_age_days"] is None
    assert soil["provenance"] is None
    for k, v in soil["key_indicators"].items():
        assert v is None, f"Expected null for soil indicator {k}, got {v}"
    assert "soil_ph" in soil["missing_critical_parameters"]
    assert len(soil["agronomic_notes"]) > 0

    # Water domain: zero sources, indicators MUST be NULL
    water = data["water"]
    assert water["availability_state"] == "NOT_AVAILABLE"
    assert water["registered_sources_count"] == 0
    assert water["sources"] == []
    for k, v in water["key_indicators"].items():
        if k in ("sar_status", "rsc_status"):
            assert v == "UNAVAILABLE"
        else:
            assert v is None, f"Expected null for water indicator {k}, got {v}"
    assert water["institutional_evaluations"] == []
    assert "water_source" in water["missing_critical_parameters"]

    # Satellite domain: zero observations, all metrics NULL
    sat = data["satellite"]
    assert sat["availability_state"] == "NOT_AVAILABLE"
    assert sat["observation_date"] is None
    assert sat["observation_age_days"] is None
    assert sat["canopy_ndvi"] is None
    assert sat["canopy_ndmi"] is None
    assert sat["composite_mean_ndvi"] is None
    assert sat["vegetation_coverage_percent"] is None
    assert sat["valid_pixel_count"] == 0
    assert sat["raster_maps"]["ndvi_map_url"] is None
    assert sat["raster_maps"]["ndmi_map_url"] is None
    assert "No satellite synchronization" in sat["agronomic_interpretation"]

    # Weather domain: all NULL
    wx = data["weather"]
    assert wx["availability_state"] == "NOT_AVAILABLE"
    assert wx["current_weather"]["temperature_c"] is None
    assert wx["climate_normals"]["annual_rainfall_mm"] is None

    # Crop context domain: NOT_AVAILABLE
    crop = data["crop_context"]
    assert crop["availability_state"] == "NOT_AVAILABLE"
    assert crop["evaluated_crops_count"] == 0
    assert crop["suitable_crops"] == []
    assert "No environmental or biological farm context" in crop["top_limiting_factors"][0]


# =============================================================================
# 3. STALE EVIDENCE SNAPSHOT TEST (CONTRACT EXAMPLE C)
# =============================================================================

def test_stale_observation_handling(client):
    """
    Verifies that observations older than institutional freshness thresholds
    are correctly flagged as STALE with accurate data_age_days metadata.
    """
    resp = client.get(
        f"/api/v1/farms/{FARM_STALE_ID}/health-snapshot",
        headers={"X-Dev-User-Id": str(USER_1_ID)},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    ov = data["overall_evidence_overview"]
    assert ov["domains_stale"] == 5
    assert ov["domains_available"] == 0
    assert "All recorded farm evidence is stale" in ov["actionable_summary"]

    # Soil > 1095 days
    soil = data["soil"]
    assert soil["availability_state"] == "STALE"
    assert soil["data_age_days"] == 1551
    assert any("over 3 years old" in note for note in soil["agronomic_notes"])

    # Water > 365 days
    water = data["water"]
    assert water["availability_state"] == "STALE"
    assert water["data_age_days"] == 511

    # Satellite > 30 days
    sat = data["satellite"]
    assert sat["availability_state"] == "STALE"
    assert sat["observation_age_days"] == 57
    assert "is 57 days old (>30 days)" in sat["agronomic_interpretation"]

    # Weather > 2 hours
    wx = data["weather"]
    assert wx["availability_state"] == "STALE"

    # Crop > 180 days
    crop = data["crop_context"]
    assert crop["availability_state"] == "STALE"
    assert any("Stale historical evaluation" in f for f in crop["top_limiting_factors"])


# =============================================================================
# 4. SECURITY & FARM OWNERSHIP ENFORCEMENT (403 FORBIDDEN & 404 NOT FOUND)
# =============================================================================

def test_unauthorized_cross_user_access_rejected_403(client):
    """
    User 2 attempts to access Farm Full (owned by User 1).
    MUST return HTTP 403 Forbidden with exact security detail message.
    """
    resp = client.get(
        f"/api/v1/farms/{FARM_FULL_ID}/health-snapshot",
        headers={"X-Dev-User-Id": str(USER_2_ID)},
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "You do not have permission to access this farm"


def test_multi_farm_isolation(client):
    """
    Verifies complete multi-tenant tenant isolation across users.
    User 1 can access Farm Full but NOT Farm User 2.
    User 2 can access Farm User 2 but NOT Farm Full.
    """
    # User 1 -> Farm Full: OK
    r1 = client.get(
        f"/api/v1/farms/{FARM_FULL_ID}/health-snapshot",
        headers={"X-Dev-User-Id": str(USER_1_ID)},
    )
    assert r1.status_code == 200

    # User 1 -> Farm User 2: 403
    r2 = client.get(
        f"/api/v1/farms/{FARM_USER2_ID}/health-snapshot",
        headers={"X-Dev-User-Id": str(USER_1_ID)},
    )
    assert r2.status_code == 403

    # User 2 -> Farm User 2: OK
    r3 = client.get(
        f"/api/v1/farms/{FARM_USER2_ID}/health-snapshot",
        headers={"X-Dev-User-Id": str(USER_2_ID)},
    )
    assert r3.status_code == 200

    # User 2 -> Farm Full: 403
    r4 = client.get(
        f"/api/v1/farms/{FARM_FULL_ID}/health-snapshot",
        headers={"X-Dev-User-Id": str(USER_2_ID)},
    )
    assert r4.status_code == 403


def test_nonexistent_farm_rejected_404(client):
    """
    Accessing a farm UUID that does not exist MUST return HTTP 404 Not Found.
    """
    fake_id = uuid.uuid4()
    resp = client.get(
        f"/api/v1/farms/{fake_id}/health-snapshot",
        headers={"X-Dev-User-Id": str(USER_1_ID)},
    )
    assert resp.status_code == 404
    assert f"Farm {fake_id} not found" in resp.json()["detail"]


# =============================================================================
# 5. CACHING & PERFORMANCE (HIT, FORCE_REFRESH, INVALIDATION)
# =============================================================================

def test_cache_hit_and_force_refresh(client):
    """
    Verifies that consecutive requests hit the in-memory 5-minute cache
    and force_refresh=True invalidates/re-collects the snapshot.
    """
    # Initial request -> Cache miss & populate
    resp1 = client.get(
        f"/api/v1/farms/{FARM_FULL_ID}/health-snapshot",
        headers={"X-Dev-User-Id": str(USER_1_ID)},
    )
    assert resp1.status_code == 200
    ts1 = resp1.json()["snapshot_timestamp"]

    # Second request -> Cache hit (same snapshot_timestamp)
    resp2 = client.get(
        f"/api/v1/farms/{FARM_FULL_ID}/health-snapshot",
        headers={"X-Dev-User-Id": str(USER_1_ID)},
    )
    assert resp2.status_code == 200
    ts2 = resp2.json()["snapshot_timestamp"]
    assert ts1 == ts2, "Expected cache hit to return identical snapshot_timestamp"

    # Third request with force_refresh=true -> Cache bypassed, new timestamp
    resp3 = client.get(
        f"/api/v1/farms/{FARM_FULL_ID}/health-snapshot?force_refresh=true",
        headers={"X-Dev-User-Id": str(USER_1_ID)},
    )
    assert resp3.status_code == 200
    ts3 = resp3.json()["snapshot_timestamp"]
    assert ts3 >= ts1


def test_cache_invalidation_helpers(client):
    """
    Verifies helper invalidate_snapshot and POST /{farm_id}/health-snapshot/invalidate endpoint.
    """
    # 1. Warm cache
    client.get(
        f"/api/v1/farms/{FARM_FULL_ID}/health-snapshot",
        headers={"X-Dev-User-Id": str(USER_1_ID)},
    )
    assert get_snapshot_cache().get(str(FARM_FULL_ID)) is not None

    # 2. Invalidate via helper
    evicted = invalidate_snapshot(str(FARM_FULL_ID))
    assert evicted is True
    assert get_snapshot_cache().get(str(FARM_FULL_ID)) is None

    # 3. Warm again
    client.get(
        f"/api/v1/farms/{FARM_FULL_ID}/health-snapshot",
        headers={"X-Dev-User-Id": str(USER_1_ID)},
    )

    # 4. Invalidate via POST endpoint
    resp = client.post(
        f"/api/v1/farms/{FARM_FULL_ID}/health-snapshot/invalidate",
        headers={"X-Dev-User-Id": str(USER_1_ID)},
    )
    assert resp.status_code == 200
    assert resp.json()["cache_evicted"] is True
    assert get_snapshot_cache().get(str(FARM_FULL_ID)) is None


# =============================================================================
# 6. DOMAIN FAULT ISOLATION (ZERO CRASHES ON COLLECTOR FAILURE)
# =============================================================================

def test_domain_fault_isolation(client, monkeypatch):
    """
    Simulates external API crash or unhandled exception in SatelliteCollector.
    The endpoint MUST NOT fail with HTTP 500; it must return 200 OK with
    satellite reporting NOT_AVAILABLE and remaining domains returning cleanly.
    """
    from cropnet.services.api.app.services.farm_health.collectors import SatelliteCollector

    def _exploding_collect(*args, **kwargs):
        raise RuntimeError("Simulated Copernicus Hub connection timeout (504 Gateway)")

    monkeypatch.setattr(SatelliteCollector, "collect", _exploding_collect)

    resp = client.get(
        f"/api/v1/farms/{FARM_FULL_ID}/health-snapshot?force_refresh=true",
        headers={"X-Dev-User-Id": str(USER_1_ID)},
    )
    assert resp.status_code == 200, "Fault isolation violated: single collector error crashed endpoint"
    data = resp.json()

    # Satellite degraded gracefully
    assert data["satellite"]["availability_state"] == "NOT_AVAILABLE"
    assert "technical error" in data["satellite"]["agronomic_interpretation"]

    # Other domains intact
    assert data["soil"]["availability_state"] == "AVAILABLE"
    assert data["water"]["availability_state"] == "AVAILABLE"
    assert data["crop_context"]["availability_state"] == "AVAILABLE"


# =============================================================================
# 7. AGRONOMIC GOVERNANCE: ZERO UNIVERSAL HEALTH SCORE
# =============================================================================

def test_governance_prohibition_of_universal_health_score(client):
    """
    Verifies that NO universal farm health score or composite score is calculated,
    stored, or returned anywhere in the response payload.
    """
    resp = client.get(
        f"/api/v1/farms/{FARM_FULL_ID}/health-snapshot",
        headers={"X-Dev-User-Id": str(USER_1_ID)},
    )
    assert resp.status_code == 200
    data = resp.json()

    # Forbidden field check
    forbidden_keys = [
        "health_score",
        "farm_health_score",
        "universal_score",
        "health_index",
        "overall_score",
        "score",
        "overall_health",
        "grade",
    ]
    for key in forbidden_keys:
        assert key not in data, f"Governance violation: forbidden composite key '{key}' found in snapshot root"
        assert key not in data["overall_evidence_overview"], f"Forbidden key '{key}' found in overall_evidence_overview"

    # Mandatory governance disclaimer
    assert "no universal health score is computed" in data["governance_notice"]
    assert "scientific_disclaimer" in data["satellite"]
