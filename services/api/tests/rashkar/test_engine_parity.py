"""1:1 Parity & Zero-Fabrication verification suite comparing RASHKAR 7b5641e vs CropNet."""

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import shutil
import sys
import types
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from cropnet.services.api.app.models.soil_and_farm import Base, FarmModel
from cropnet.services.api.app.rashkar.data import MAHARASHTRA_APY_CANONICAL_CSV
from cropnet.services.api.app.rashkar.engines import (
    CROP_SPECIES_PHYSIOLOGY,
    CropHeatEngine,
    CropStageService,
    EXTENDED_OPPORTUNITY_CATALOG,
    IncomeEngine,
    IncomeFinancialService,
    OpportunityFeasibilityEngine,
    WorkerHeatEngine,
    YieldRiskEngine,
    apply_topographic_lapse_downscaling,
    calculate_noaa_heat_index,
    calculate_utci_approx,
    calculate_wbgt,
    compute_crop_heat_vulnerability_score,
    compute_personalized_worker_heat_strain_score,
    dew_point_c,
    get_opportunity_by_id,
)
from cropnet.services.api.app.rashkar.models import (
    RashkarCropCycleModel,
    RashkarCropHeatLogModel,
    RashkarWorkerHazardAuditLogModel,
    RashkarYieldAssessmentLogModel,
)
from cropnet.services.api.app.rashkar.schemas import (
    CropHeatAssessmentRequest,
    FarmerResourceProfile,
    WorkerHeatAssessmentRequest,
)
from cropnet.services.api.app.rashkar.seed import seed_rashkar_reference_data


SNAPSHOT_ROOT = Path(
    "/Users/siddheshbirewar/.gemini/antigravity/brain/"
    "ee291428-4c13-4698-b1ae-642f4c613070/scratch/rashkar_7b5641e"
)


@pytest.fixture(scope="module")
def rashkar_7b5641e_env(tmp_path_factory):
    """
    Safely loads the read-only 7b5641e `backend.*` package against an isolated
    in-memory SQLite engine without touching Postgres or host disk files.
    """
    if not SNAPSHOT_ROOT.exists():
        pytest.skip(f"7b5641e reference snapshot not present at {SNAPSHOT_ROOT}")

    tmp_dir = tmp_path_factory.mktemp("rashkar_7b5641e_csv")
    apy_dir = tmp_dir / "APY_CANONICAL"
    apy_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        MAHARASHTRA_APY_CANONICAL_CSV, apy_dir / "maharashtra_apy_canonical.csv"
    )

    ref_engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    ref_base = declarative_base()
    ref_session_factory = sessionmaker(
        autocommit=False, autoflush=False, bind=ref_engine
    )

    # Inject a synthetic `backend.app.db.session` BEFORE importing `backend.app.*`
    # so 7b5641e does not open a localhost PostgreSQL socket or disk SQLite file.
    snapshot_str = str(SNAPSHOT_ROOT)
    inserted_path = False
    if snapshot_str not in sys.path:
        sys.path.insert(0, snapshot_str)
        inserted_path = True

    session_mod = types.ModuleType("backend.app.db.session")
    session_mod.Base = ref_base
    session_mod.engine = ref_engine
    session_mod.SessionLocal = ref_session_factory
    session_mod.get_engine = lambda: ref_engine

    def _get_db():
        db = ref_session_factory()
        try:
            yield db
        finally:
            db.close()

    session_mod.get_db = _get_db

    # Ensure package skeleton resolves cleanly before installing mocked session submodule
    import importlib

    importlib.import_module("backend")
    importlib.import_module("backend.app")
    importlib.import_module("backend.app.db")
    sys.modules["backend.app.db.session"] = session_mod

    from backend.app.core.config import settings as ref_settings
    from backend.app.db import init_db as ref_init_db
    from backend.app.db.models.farm import (
        CropCycleModel as RefCropCycleModel,
        FarmerModel as RefFarmerModel,
        FarmModel as RefFarmModel,
        FarmPlotModel as RefFarmPlotModel,
    )

    ref_settings.PROCESSED_DATA_DIR = tmp_dir
    ref_base.metadata.create_all(bind=ref_engine)

    ref_db = ref_session_factory()
    ref_init_db.seed_canonical_crops(ref_db)
    ref_init_db.seed_crop_stages(ref_db)
    ref_init_db.seed_agronomic_thresholds(ref_db)
    ref_init_db.seed_advisories(ref_db)

    ref_farmer = RefFarmerModel(
        farmer_id="ref_farmer_1",
        full_name="Reference Farmer",
        phone_number="+910000000000",
        state="Maharashtra",
        district="Pune",
        taluka="Baramati",
        village="Malegaon",
    )
    ref_farm = RefFarmModel(
        farm_id="ref_farm_1",
        owner_id="ref_farmer_1",
        farm_name="Parity Reference Farm",
        district="Pune",
        taluka="Baramati",
        village="Malegaon",
        latitude=18.1512,
        longitude=74.5768,
        total_area_acres=3.0,
    )
    ref_plot = RefFarmPlotModel(
        plot_id="ref_plot_1",
        farm_id="ref_farm_1",
        plot_name="Primary Plot",
        area_acres=3.0,
        irrigation_type="drip",
    )
    ref_db.add_all([ref_farmer, ref_farm, ref_plot])
    ref_db.commit()

    yield {
        "db": ref_db,
        "RefCropCycleModel": RefCropCycleModel,
        "tmp_csv_dir": tmp_dir,
    }

    ref_db.close()
    ref_engine.dispose()
    if inserted_path and snapshot_str in sys.path:
        sys.path.remove(snapshot_str)


@pytest.fixture()
def cropnet_db():
    """Isolated CropNet in-memory SQLite session seeded with RASHKAR reference tables."""
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    session.execute(text("PRAGMA foreign_keys=ON"))
    seed_rashkar_reference_data(session)

    farm = FarmModel(
        id="cn_farm_1",
        owner_id="cn_owner_1",
        name="Parity Reference Farm",
        district="Pune",
        taluka="Baramati",
        village="Malegaon",
        state="Maharashtra",
        irrigation_type="drip",
        geometry_geojson={
            "type": "Polygon",
            "coordinates": [[[74.576, 18.151], [74.577, 18.151], [74.577, 18.152], [74.576, 18.152], [74.576, 18.151]]],
        },
        calculated_area_hectares=1.21,
        calculated_area_acres=3.0,
        centroid_latitude=18.1512,
        centroid_longitude=74.5768,
    )
    session.add(farm)
    session.commit()

    try:
        yield session, farm
    finally:
        session.close()
        engine.dispose()


def test_wbgt_and_thermal_indices_exact_parity(rashkar_7b5641e_env):
    """Physics WBGT solver, Heat Index, UTCI, lapse downscaling, and strain scores match 1:1."""
    from backend.app.services import (
        thermal_indices_service as ref_ti,
        wbgt_solver as ref_wbgt,
    )

    cases = [
        (38.5, 42.0, 2.2, 820.0, True),
        (33.0, 78.0, 1.0, 350.0, True),
        (29.5, 55.0, 1.5, 600.0, False),
        (43.2, 18.0, 3.8, 940.0, True),
    ]
    for ta, rh, wind, solar, in_sun in cases:
        cn_res = calculate_wbgt(
            temp_c=ta, rh_pct=rh, wind_speed_ms=wind, solar_irradiance_wm2=solar, in_sun=in_sun
        )
        ref_res = ref_wbgt.calculate_wbgt(
            temp_c=ta, rh_pct=rh, wind_speed_ms=wind, solar_irradiance_wm2=solar, in_sun=in_sun
        )
        assert cn_res == ref_res
        assert dew_point_c(ta, rh) == ref_wbgt.dew_point_c(ta, rh)
        assert calculate_noaa_heat_index(ta, rh) == ref_ti.calculate_noaa_heat_index(ta, rh)
        assert calculate_utci_approx(ta, rh, wind, solar) == ref_ti.calculate_utci_approx(
            ta, rh, wind, solar
        )

    assert apply_topographic_lapse_downscaling(37.4, 560.0, 540.0) == (
        ref_ti.apply_topographic_lapse_downscaling(37.4, 560.0, 540.0)
    )
    assert compute_personalized_worker_heat_strain_score(29.8, 26.0, "heavy", False, 52, 6.0) == (
        ref_ti.compute_personalized_worker_heat_strain_score(
            29.8, 26.0, "heavy", False, 52, 6.0
        )
    )
    assert compute_crop_heat_vulnerability_score(39.0, 30.0, 35.0, "flowering", "dry", False) == (
        ref_ti.compute_crop_heat_vulnerability_score(
            39.0, 30.0, 35.0, "flowering", "dry", False
        )
    )


def test_worker_heat_engine_parity_and_missing_weather_honesty(
    rashkar_7b5641e_env, cropnet_db
):
    """Worker heat timeline, ACGIH thresholds, CAV adjustments, and DB audit logs match 7b5641e."""
    from backend.app.schemas.worker_heat import WorkerHeatAssessmentRequest as RefReq
    from backend.app.services.worker_heat_engine import WorkerHeatEngine as RefWorkerEngine
    import torch

    try:
        torch.set_num_threads(1)
    except RuntimeError:
        pass

    cn_session, farm = cropnet_db
    hourly_feed = [
        {"air_temp_c": 34.0 + i * 0.7, "relative_humidity_pct": 46.0 - i * 2.0, "wind_speed_ms": 2.0, "solar_irradiance_wm2": 720.0 + i * 25.0}
        for i in range(7)
    ]

    for workload, clothing, acclim, sun_exp, dur in [
        ("heavy", "standard_work_clothes", True, "direct_sun", 4.0),
        ("moderate", "impermeable_vapor_barrier", False, "partial_shade", 8.5),
    ]:
        cn_req = WorkerHeatAssessmentRequest(
            farm_id=farm.id,
            latitude=18.1512,
            longitude=74.5768,
            taluka="Baramati",
            workload_category=workload,
            clothing_type=clothing,
            is_acclimatised=acclim,
            sun_exposure=sun_exp,
            exposure_duration_hours=dur,
        )
        ref_req = RefReq(
            latitude=18.1512,
            longitude=74.5768,
            taluka="Baramati",
            workload_category=workload,
            clothing_type=clothing,
            is_acclimatised=acclim,
            sun_exposure=sun_exp,
            exposure_duration_hours=dur,
        )

        cn_out = WorkerHeatEngine.assess_worker_heat_hazard(
            request=cn_req,
            farm_context={
                "farm_id": farm.id,
                "owner_id": farm.owner_id,
                "farm_name": farm.name,
                "taluka": farm.taluka,
                "elevation_m": 560.0,
                "grid_elevation_m": 540.0,
            },
            weather_hourly=hourly_feed,
            db=cn_session,
        )
        ref_out = RefWorkerEngine.assess_worker_heat_hazard(
            request=ref_req,
            db=None,
            weather_hourly_override=hourly_feed,
        )

        assert cn_out.status == "OK"
        assert cn_out.audit_logged is True
        assert cn_out.clothing_cav_c == ref_out.clothing_cav_c
        assert cn_out.screening_threshold_c == ref_out.screening_threshold_c
        assert cn_out.max_wbgt_effective_c == ref_out.max_wbgt_effective_c
        assert cn_out.max_hazard_level_in_window == ref_out.max_hazard_level_in_window
        assert cn_out.threshold_difference_c == ref_out.threshold_difference_c
        assert cn_out.threshold_comparison_state == ref_out.threshold_comparison_state
        assert cn_out.shift_exceeds_forecast_coverage == ref_out.shift_exceeds_forecast_coverage
        assert (
            cn_out.personalized_heat_strain_score["score_0_100"]
            == ref_out.personalized_heat_strain_score["score_0_100"]
        )
        assert len(cn_out.hourly_projections) == 7
        for cn_h, ref_h in zip(cn_out.hourly_projections, ref_out.hourly_projections):
            assert cn_h.wbgt_estimated_c == ref_h.wbgt_estimated_c
            assert cn_h.wbgt_effective_c == ref_h.wbgt_effective_c
            assert cn_h.heat_index_c == ref_h.heat_index_c
            assert cn_h.utci_c == ref_h.utci_c
            assert cn_h.hazard_level == ref_h.hazard_level
            assert cn_h.exceeds_screening_threshold == ref_h.exceeds_screening_threshold
            assert cn_h.work_rest_cycle == ref_h.work_rest_cycle

    assert cn_session.query(RashkarWorkerHazardAuditLogModel).count() == 2

    # Missing weather must refuse cleanly instead of fabricating temperatures
    no_weather = WorkerHeatEngine.assess_worker_heat_hazard(
        request=WorkerHeatAssessmentRequest(
            farm_id=farm.id, latitude=18.1512, longitude=74.5768
        ),
        farm_context={"farm_id": farm.id, "owner_id": farm.owner_id},
        weather_hourly=None,
        db=cn_session,
    )
    assert no_weather.status == "WEATHER_UNAVAILABLE"
    assert no_weather.current_wbgt_estimated_c is None
    assert no_weather.hourly_projections == []
    assert no_weather.audit_logged is False


def test_crop_stage_and_crop_heat_engine_parity_and_no_active_crop(
    rashkar_7b5641e_env, cropnet_db
):
    """Crop stages, thermal thresholds, 4-day outlook, expiry, and honest missing-crop handling."""
    from backend.app.schemas.crop_heat import CropHeatAssessmentRequest as RefHeatReq
    from backend.app.services.crop_heat_engine import CropHeatEngine as RefCropHeatEngine
    from backend.app.services.crop_stage_service import CropStageService as RefStageSvc

    assert len(CROP_SPECIES_PHYSIOLOGY) >= 12
    assert "rice" in CROP_SPECIES_PHYSIOLOGY

    cn_session, farm = cropnet_db
    ref_db = rashkar_7b5641e_env["db"]
    RefCycle = rashkar_7b5641e_env["RefCropCycleModel"]

    today_ist = datetime.now(timezone(timedelta(hours=5, minutes=30))).date()
    sowing_60d = today_ist - timedelta(days=60)
    sowing_expired = today_ist - timedelta(days=140)

    # 1. Stage parity across DAS + farmer override + expiry
    for sowing_d, override in [
        (today_ist - timedelta(days=20), None),
        (today_ist - timedelta(days=40), None),
        (sowing_60d, None),
        (sowing_60d, "R1_FLOWERING"),
        (sowing_expired, None),
    ]:
        cn_st = CropStageService.estimate_crop_stage(
            cn_session, "soybean", sowing_d, override
        )
        ref_st = RefStageSvc.estimate_crop_stage(ref_db, "soybean", sowing_d, override)
        assert cn_st["stage_code"] == ref_st["stage_code"]
        assert cn_st["stage_source"] == ref_st["stage_source"]
        assert cn_st["heat_sensitivity"] == ref_st["heat_sensitivity"]
        assert cn_st["drought_sensitivity"] == ref_st["drought_sensitivity"]
        assert cn_st["is_expired"] == ref_st["is_expired"]

    # 2. Missing active crop must NEVER fall back to soybean
    no_crop_resp = CropHeatEngine.assess_crop_heat_risk(
        request=CropHeatAssessmentRequest(farm_id=farm.id, forecast_tmax_c=38.0),
        farm_context={"farm_id": farm.id, "owner_id": farm.owner_id, "farm_name": farm.name},
        crop_cycle=None,
        db=cn_session,
    )
    assert no_crop_resp.has_active_crop is False
    assert no_crop_resp.needs_crop_registration is True
    assert no_crop_resp.status == "NO_ACTIVE_CROP"
    assert no_crop_resp.crop_code is None

    # 3. Missing weather must fail cleanly
    cn_cycle = RashkarCropCycleModel(
        id="cn_cycle_soy_1",
        farm_id=farm.id,
        owner_id=farm.owner_id,
        crop_code="soybean",
        sowing_date=sowing_60d,
        season="kharif",
        planted_area_acres=3.0,
        irrigation_type="drip",
        is_active=True,
    )
    cn_session.add(cn_cycle)
    cn_session.commit()

    no_fc = CropHeatEngine.assess_crop_heat_risk(
        request=CropHeatAssessmentRequest(farm_id=farm.id),
        farm_context={"farm_id": farm.id, "owner_id": farm.owner_id, "farm_name": farm.name},
        crop_cycle=cn_cycle,
        weather_forecast=None,
        db=cn_session,
    )
    assert no_fc.status == "WEATHER_UNAVAILABLE"

    # 4. Exact numerical parity on active soybean R3_POD_FILLING (DB threshold = 35.0 C)
    ref_cycle = RefCycle(
        cycle_id="ref_cycle_soy_1",
        plot_id="ref_plot_1",
        crop_code="soybean",
        season="kharif",
        sowing_date=sowing_60d,
        planted_area_acres=3.0,
        is_active=True,
    )
    ref_db.add(ref_cycle)
    ref_db.commit()

    cn_heat = CropHeatEngine.assess_crop_heat_risk(
        request=CropHeatAssessmentRequest(
            farm_id=farm.id, forecast_tmax_c=38.5, forecast_tmin_c=24.0
        ),
        farm_context={
            "farm_id": farm.id,
            "owner_id": farm.owner_id,
            "farm_name": farm.name,
            "irrigation_type": "drip",
            "elevation_m": 560.0,
            "grid_elevation_m": 540.0,
        },
        crop_cycle=cn_cycle,
        weather_forecast={"relative_humidity_pct": 35.0, "provider": "IMD_Test"},
        db=cn_session,
    )
    ref_heat = RefCropHeatEngine.assess_crop_heat_risk(
        db=ref_db,
        request=RefHeatReq(
            farm_id="ref_farm_1",
            plot_id="ref_plot_1",
            forecast_tmax_c=38.5,
            forecast_tmin_c=24.0,
        ),
    )

    assert cn_heat.status == "OK"
    assert cn_heat.growth_stage_code == ref_heat.growth_stage_code == "R3_POD_FILLING"
    assert cn_heat.critical_tmax_threshold_c == ref_heat.critical_tmax_threshold_c == 35.0
    assert cn_heat.daytime_heat_stress_level == ref_heat.daytime_heat_stress_level
    assert cn_heat.overall_crop_heat_risk == ref_heat.overall_crop_heat_risk
    assert cn_heat.hours_above_critical == ref_heat.hours_above_critical
    assert cn_heat.warm_night_respiration_hazard == ref_heat.warm_night_respiration_hazard
    assert cn_heat.warm_night_penalty_score == ref_heat.warm_night_penalty_score
    assert cn_heat.cumulative_heat_units_gdd == ref_heat.cumulative_heat_units_gdd
    assert (
        cn_heat.personalized_crop_vulnerability_score["score_0_100"]
        == ref_heat.personalized_crop_vulnerability_score["score_0_100"]
    )
    assert [i.intervention_id for i in cn_heat.recommended_interventions] == [
        i.intervention_id for i in ref_heat.recommended_interventions
    ]
    assert [(d.tmax_c, d.tmin_c, d.risk_category) for d in cn_heat.daily_outlook] == [
        (d.tmax_c, d.tmin_c, d.risk_category) for d in ref_heat.daily_outlook
    ]
    assert cn_heat.peak_vpd_kpa is not None
    assert cn_session.query(RashkarCropHeatLogModel).count() == 1


def test_yield_risk_apy_parity_and_zero_fabrication(
    rashkar_7b5641e_env, cropnet_db, tmp_path
):
    """APY CSV lookup, percentiles, statewide fallback, missing CSV honesty, and risk screening."""
    from backend.app.services.yield_risk_engine import YieldRiskEngine as RefYieldEngine

    cn_session, farm = cropnet_db
    ref_db = rashkar_7b5641e_env["db"]

    for district, crop_code in [
        ("Pune", "soybean"),
        ("Pune", "cotton"),
        ("Pune", "gram"),
        ("Sindhudurg", "cotton"),
    ]:
        cn_base = YieldRiskEngine.calculate_apy_district_baseline(
            district=district, crop_code=crop_code, db=cn_session
        )
        ref_base = RefYieldEngine.calculate_apy_district_baseline(
            district=district, crop_code=crop_code, db=ref_db
        )
        for field in (
            "status",
            "geographical_unit",
            "sample_seasons_count",
            "historical_mean_t_ha",
            "historical_median_t_ha",
            "historical_p10_t_ha",
            "historical_p90_t_ha",
            "min_recorded_t_ha",
            "max_recorded_t_ha",
            "historical_std_dev",
        ):
            assert cn_base[field] == ref_base[field]
        assert cn_base["historical_p25_t_ha"] is not None
        assert (
            cn_base["historical_p10_t_ha"]
            <= cn_base["historical_p25_t_ha"]
            <= cn_base["historical_median_t_ha"]
            <= cn_base["historical_p90_t_ha"]
        )

    # Chickpea alias resolves identically to gram
    chickpea_base = YieldRiskEngine.calculate_apy_district_baseline(
        "Pune", "chickpea", db=cn_session
    )
    gram_base = YieldRiskEngine.calculate_apy_district_baseline(
        "Pune", "gram", db=cn_session
    )
    assert chickpea_base["historical_mean_t_ha"] == gram_base["historical_mean_t_ha"]

    # Missing APY CSV must return unavailable with None values (zero fake 1.25 / 1.42)
    missing_base = YieldRiskEngine.calculate_apy_district_baseline(
        "Pune", "soybean", apy_csv_path=tmp_path / "missing_apy.csv"
    )
    assert missing_base["status"] == "unavailable"
    assert missing_base["historical_mean_t_ha"] is None
    assert missing_base["historical_median_t_ha"] is None

    # Full 5-dimension risk screening parity + honest missing soil handling
    sowing_d = date.today() - timedelta(days=42)
    weather_summary = {
        "consecutive_dry_days": 14,
        "rolling_3d_rain_mm": 5.0,
        "tmax_recent_c": 38.5,
        "rh_recent_pct": 52.0,
        "data_source": "IMD_TEST",
    }
    cn_cycle = RashkarCropCycleModel(
        id="cn_yr_cycle_1",
        farm_id=farm.id,
        owner_id=farm.owner_id,
        crop_code="soybean",
        sowing_date=sowing_d,
        season="kharif",
        planted_area_acres=3.0,
        irrigation_type="drip",
        is_active=True,
    )
    cn_session.add(cn_cycle)
    cn_session.commit()

    full_soil = {
        "ph": 7.4,
        "texture_class": "Clay Loam",
        "organic_carbon_pct": 0.72,
        "cation_exchange_capacity": 40.0,
        "available_water_capacity": 150.0,
        "depth_cm": 95.0,
    }
    cn_yr = YieldRiskEngine.assess_yield_risk(
        farm_context={
            "farm_id": farm.id,
            "owner_id": farm.owner_id,
            "farm_name": farm.name,
            "district": "Pune",
            "taluka": "Baramati",
        },
        crop_cycle=cn_cycle,
        soil_profile=full_soil,
        weather_summary=weather_summary,
        db=cn_session,
    )
    ref_yr = RefYieldEngine.assess_yield_risk(
        db=ref_db,
        farm_id="ref_farm_1",
        plot_id="ref_plot_1",
        crop_code="soybean",
        sowing_date=sowing_d,
        district="Pune",
        taluka="Baramati",
        weather_summary=weather_summary,
        soil_profile_override=full_soil,
    )

    assert cn_yr.status == "OK"
    assert cn_yr.audit_logged is True
    assert cn_yr.ml_prediction_gate["farm_level_supervised_model"] == "LOCKED_PENDING_CCE_LABELS"
    assert [
        (r.risk_dimension, r.risk_level) for r in cn_yr.risks
    ] == [
        (r["risk_dimension"], r["risk_level"]) for r in ref_yr["risks"]
    ]
    assert cn_yr.suitability_analysis.soil_ph == 7.4
    assert cn_yr.yield_baseline.historical_mean_t_ha == ref_yr["yield_baseline"].historical_mean_t_ha
    assert cn_session.query(RashkarYieldAssessmentLogModel).count() == 1

    # Unsampled soil must keep numeric metrics as None instead of inventing defaults
    unsampled_yr = YieldRiskEngine.assess_yield_risk(
        farm_context={
            "farm_id": farm.id,
            "owner_id": farm.owner_id,
            "farm_name": farm.name,
            "district": "Pune",
            "taluka": "Baramati",
        },
        crop_cycle=cn_cycle,
        soil_profile=None,
        weather_summary=weather_summary,
        db=cn_session,
    )
    assert unsampled_yr.suitability_analysis.soil_ph is None
    assert unsampled_yr.suitability_analysis.organic_carbon_pct is None
    assert unsampled_yr.suitability_analysis.cation_exchange_capacity is None
    assert unsampled_yr.suitability_analysis.available_water_capacity_mm_m is None
    assert unsampled_yr.suitability_analysis.effective_rooting_depth_cm is None

    # No active crop & missing weather refusal
    assert (
        YieldRiskEngine.assess_yield_risk(
            farm_context={"farm_id": farm.id, "owner_id": farm.owner_id},
            crop_cycle=None,
        ).status
        == "NO_ACTIVE_CROP"
    )
    assert (
        YieldRiskEngine.assess_yield_risk(
            farm_context={"farm_id": farm.id, "owner_id": farm.owner_id},
            crop_cycle=cn_cycle,
            weather_summary=None,
        ).status
        == "WEATHER_UNAVAILABLE"
    )


def test_extra_income_engine_parity(rashkar_7b5641e_env):
    """Extra Income feasibility ranking, age/personalization, and financials match 7b5641e."""
    from backend.app.schemas.income import FarmerResourceProfile as RefProfile
    from backend.app.services.income_financial_service import (
        IncomeFinancialService as RefFinancialSvc,
    )
    from backend.app.services.income_knowledge_catalog import (
        EXTENDED_OPPORTUNITY_CATALOG as REF_CATALOG,
    )
    from backend.app.services.opportunity_feasibility_engine import (
        OpportunityFeasibilityEngine as RefFeasibility,
    )

    assert len(EXTENDED_OPPORTUNITY_CATALOG) == len(REF_CATALOG)

    # 1. Zero-cash farmer
    zero_kw = dict(
        available_investment_inr=0.0,
        monthly_operating_budget_inr=0.0,
        field_bunds_available=True,
        crop_byproducts=["soybean_straw", "cow_dung"],
        existing_livestock="indigenous_cows",
        water_availability="seasonal_canal",
        family_labor_hours_day=3.0,
    )
    cn_zero = OpportunityFeasibilityEngine.discover_and_rank_opportunities(
        FarmerResourceProfile(**zero_kw)
    )
    ref_zero = RefFeasibility.discover_and_rank_opportunities(RefProfile(**zero_kw))
    assert [
        (d.opportunity.opportunity_id, d.suitability_score, d.feasibility_category)
        for d in cn_zero
    ] == [
        (d.opportunity.opportunity_id, d.suitability_score, d.feasibility_category)
        for d in ref_zero
    ]

    # 2. Age >= 65 not disqualified + supervisory labor check + onion intercrop block
    elder_kw = dict(
        age_range="above_65",
        work_preference="daily_physical",
        available_investment_inr=15000.0,
        monthly_operating_budget_inr=1000.0,
        available_land_acres=0.5,
        unused_land_acres=0.2,
        field_bunds_available=True,
        water_availability="seasonal_canal",
        family_labor_hours_day=3.0,
    )
    opp_bund = get_opportunity_by_id("OPP_FIELD_BUND_DRUMSTICK_01")
    assert opp_bund is not None
    cn_elder = OpportunityFeasibilityEngine.evaluate_opportunity(
        opp_bund, FarmerResourceProfile(**elder_kw)
    )
    assert cn_elder.is_feasible is True

    # 3. 3-scenario financial simulation & comparison parity
    cn_fin = IncomeFinancialService.calculate_financials(
        opportunity_id="OPP_OSMANABADI_GOAT_10_PLUS_1",
        custom_budget_inr=90000.0,
        water_availability="reliable_year_round",
    )
    ref_fin = RefFinancialSvc.calculate_financials(
        opportunity_id="OPP_OSMANABADI_GOAT_10_PLUS_1",
        custom_budget_inr=90000.0,
        water_availability="reliable_year_round",
    )
    assert cn_fin.calculated_capex_inr == ref_fin.calculated_capex_inr
    assert cn_fin.calculated_opex_annual_inr == ref_fin.calculated_opex_annual_inr
    assert cn_fin.calculated_net_profit_annual_inr == ref_fin.calculated_net_profit_annual_inr
    assert cn_fin.calculated_break_even_months == ref_fin.calculated_break_even_months
    assert cn_fin.monthly_cash_flows == ref_fin.monthly_cash_flows

    cmp_rows = IncomeEngine.compare_opportunities(
        ["OPP_FIELD_BUND_DRUMSTICK_01", "OPP_OSMANABADI_GOAT_10_PLUS_1"],
        custom_budget=60000.0,
    )
    assert len(cmp_rows) == 2
