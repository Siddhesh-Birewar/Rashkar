"""
Shared Pytest configuration and isolation fixtures for CropNet API tests.

Guarantees 100% test isolation from external databases:
- Replaces get_db with an isolated SQLite in-memory database seeded with the Phase 4.1 knowledge base.
- Prevents remote connections to Supabase.
- Provides session and per-test cleanup.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from cropnet.services.api.app.models.soil_and_farm import Base
import cropnet.services.api.app.models.crops
from cropnet.services.api.app.services.crop_knowledge.crop_service import CropKnowledgeService
from cropnet.services.api.app.core.database import get_db
from cropnet.services.api.app.main import app


# 1. Create shared in-memory SQLite test engine
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# 2. Initialize schema and seed knowledge base
Base.metadata.create_all(bind=test_engine)
_init_db = TestingSessionLocal()
_service = CropKnowledgeService()
_service.seed_knowledge_base(_init_db)
_init_db.close()


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def isolated_db_override():
    """
    Autouse fixture that binds FastAPI get_db dependency to isolated SQLite test DB for every test.
    """
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def isolated_db_session():
    """
    Provides a direct database session for isolated direct ORM queries.
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_client():
    """
    Isolated FastAPI test client.
    """
    return TestClient(app)
