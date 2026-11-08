import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from backend.app.main import app
from backend.app.db.session import Base, get_db
from backend.app.db.models.registry import DatasetRegistryModel
from backend.app.db.models.farm import FarmerModel, FarmModel, FarmPlotModel, CropCycleModel, SoilProfileModel
from backend.app.db.models.crop_knowledge import (
    CanonicalCropMasterModel,
    CropStageReferenceModel,
    AgronomicThresholdRegistryModel,
    AgronomicAdvisoryCatalogueModel
)
from backend.app.db.models.risk import (
    YieldAssessmentLogModel,
    WorkerHazardAuditLogModel,
    CropHeatAssessmentLogModel
)
from backend.app.db.models.income import IncomeOpportunityModel, IncomeScenarioModel
from backend.app.db.models.pmfby import CropLossCaseModel
from backend.app.db.models.assistant import AssistantSessionModel, AssistantMessageModel
from backend.app.db.init_db import (
    seed_canonical_crops,
    seed_crop_stages,
    seed_agronomic_thresholds,
    seed_advisories,
    seed_demo_farmer_and_farm,
    seed_income_opportunities
)

# Test SQLite in-memory engine
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_canonical_crops(db)
    seed_crop_stages(db)
    seed_agronomic_thresholds(db)
    seed_advisories(db)
    seed_demo_farmer_and_farm(db)
    seed_income_opportunities(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
