"""Seed idempotency & schema persistence tests for RASHKAR canonical knowledge tables."""

from datetime import date
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from cropnet.services.api.app.models.soil_and_farm import Base, FarmModel
from cropnet.services.api.app.rashkar.engines.income import EXTENDED_OPPORTUNITY_CATALOG
from cropnet.services.api.app.rashkar.models import (
    RashkarAdvisoryCatalogueModel,
    RashkarAgronomicThresholdModel,
    RashkarCanonicalCropModel,
    RashkarCropCycleModel,
    RashkarCropStageModel,
    RashkarFarmerResourceProfileModel,
    RashkarIncomeOpportunityModel,
    RashkarIncomeScenarioModel,
    RashkarSavedIncomePlanModel,
)
from cropnet.services.api.app.rashkar.seed import seed_rashkar_reference_data


@pytest.fixture()
def rashkar_session():
    """Isolated in-memory SQLite database with FK cascades enabled."""
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    session.execute(text("PRAGMA foreign_keys=ON"))
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def test_seed_rashkar_reference_data_idempotent(rashkar_session):
    """Running the seeder twice populates exact expected counts with zero duplicates."""
    first = seed_rashkar_reference_data(rashkar_session)
    second = seed_rashkar_reference_data(rashkar_session)

    assert first == second
    assert rashkar_session.query(RashkarCanonicalCropModel).count() == 38
    assert rashkar_session.query(RashkarCropStageModel).count() == 6
    assert rashkar_session.query(RashkarAgronomicThresholdModel).count() == 4
    assert rashkar_session.query(RashkarAdvisoryCatalogueModel).count() == 2
    assert (
        rashkar_session.query(RashkarIncomeOpportunityModel).count()
        == len(EXTENDED_OPPORTUNITY_CATALOG)
    )
    # Seeder must NEVER fabricate demo farms or active crop cycles
    assert rashkar_session.query(FarmModel).count() == 0
    assert rashkar_session.query(RashkarCropCycleModel).count() == 0


def test_seeded_crop_stages_and_thresholds_match_7b5641e(rashkar_session):
    """Verify canonical crop attributes, stages, thresholds, and advisories are exact."""
    seed_rashkar_reference_data(rashkar_session)

    pioneer = (
        rashkar_session.query(RashkarCanonicalCropModel)
        .filter(RashkarCanonicalCropModel.is_pioneer_pilot_crop == True)  # noqa: E712
        .all()
    )
    assert {c.crop_code for c in pioneer} == {"soybean", "cotton", "jowar", "sugarcane"}

    soy_pod = (
        rashkar_session.query(RashkarAgronomicThresholdModel)
        .filter(
            RashkarAgronomicThresholdModel.crop_code == "soybean",
            RashkarAgronomicThresholdModel.stage_code == "R3_POD_FILLING",
        )
        .first()
    )
    assert soy_pod is not None
    assert soy_pod.tmax_critical_damage == 35.0
    assert soy_pod.critical_heat_duration_hrs == 4

    cot_flower = (
        rashkar_session.query(RashkarAgronomicThresholdModel)
        .filter(
            RashkarAgronomicThresholdModel.crop_code == "cotton",
            RashkarAgronomicThresholdModel.stage_code == "FLOWERING_BOLL_DEV",
            RashkarAgronomicThresholdModel.tmax_critical_damage.isnot(None),
        )
        .first()
    )
    assert cot_flower is not None
    assert cot_flower.tmax_critical_damage == 38.0
    assert cot_flower.critical_heat_duration_hrs == 3


def test_crop_cycles_and_profile_cascade_delete_with_farm(rashkar_session):
    """Deleting a canonical CropNet farm cascades cleanly to RASHKAR child tables."""
    seed_rashkar_reference_data(rashkar_session)
    opp_id = EXTENDED_OPPORTUNITY_CATALOG[0].opportunity_id

    farm = FarmModel(
        id="farm-rashkar-test-01",
        owner_id="owner-test-01",
        name="Mulshi Test Farm",
        district="Pune",
        taluka="Mulshi",
        state="Maharashtra",
        geometry_geojson={
            "type": "Polygon",
            "coordinates": [[[73.5, 18.5], [73.501, 18.5], [73.501, 18.501], [73.5, 18.501], [73.5, 18.5]]],
        },
        calculated_area_hectares=1.21,
        calculated_area_acres=3.0,
        centroid_latitude=18.5,
        centroid_longitude=73.5,
    )
    rashkar_session.add(farm)
    rashkar_session.flush()

    cycle_old = RashkarCropCycleModel(
        id="cycle-old",
        farm_id=farm.id,
        owner_id=farm.owner_id,
        crop_code="soybean",
        sowing_date=date(2025, 6, 20),
        season="kharif",
        is_active=False,
    )
    cycle_active = RashkarCropCycleModel(
        id="cycle-active",
        farm_id=farm.id,
        owner_id=farm.owner_id,
        crop_code="cotton",
        sowing_date=date(2026, 6, 15),
        season="kharif",
        is_active=True,
    )
    profile = RashkarFarmerResourceProfileModel(
        farm_id=farm.id,
        owner_id=farm.owner_id,
        available_investment_inr=0.0,
        age_range="46-55",
        work_preference="manage_supervise",
        payback_horizon="3_to_6_months",
        family_management_role="family_member",
        current_crop_code="cotton",
        current_crop_stage="FLOWERING_BOLL_DEV",
    )
    scenario = RashkarIncomeScenarioModel(
        scenario_id="scn-01",
        owner_id=farm.owner_id,
        farm_id=farm.id,
        opportunity_id=opp_id,
        custom_budget_inr=25000.0,
        calculated_capex_inr=15000.0,
        calculated_opex_annual_inr=5000.0,
        calculated_gross_revenue_inr=45000.0,
        calculated_net_profit_annual_inr=40000.0,
    )
    saved_plan = RashkarSavedIncomePlanModel(
        plan_id="plan-01",
        owner_id=farm.owner_id,
        farm_id=farm.id,
        opportunity_id=opp_id,
        opportunity_title="Test Opportunity",
        category="very_low_cost",
        chosen_budget_inr=25000.0,
        projected_annual_profit_inr=40000.0,
    )
    rashkar_session.add_all([cycle_old, cycle_active, profile, scenario, saved_plan])
    rashkar_session.commit()

    assert (
        rashkar_session.query(RashkarCropCycleModel)
        .filter(RashkarCropCycleModel.farm_id == farm.id)
        .count()
        == 2
    )

    rashkar_session.delete(farm)
    rashkar_session.commit()

    assert rashkar_session.query(RashkarCropCycleModel).count() == 0
    assert rashkar_session.query(RashkarFarmerResourceProfileModel).count() == 0
    assert rashkar_session.query(RashkarIncomeScenarioModel).count() == 0
    assert rashkar_session.query(RashkarSavedIncomePlanModel).count() == 0
