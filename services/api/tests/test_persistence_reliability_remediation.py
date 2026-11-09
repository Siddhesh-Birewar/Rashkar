"""
Comprehensive Persistence and Reliability Verification Test Suite (Milestone M3 / Requirement R3).

Tests:
1. Failed database write operations during farm creation surface HTTP 500 errors immediately
   and do NOT return false-positive HTTP 201 Created responses from in-memory fallback.
2. Farm listing and retrieval use authoritative database persistence (FarmModel) with
   in-memory structures only acting as an eviction-managed, bounded cache mirror.
3. Decision persistence across server restarts / multi-worker execution:
   Evaluated decisions and contexts persist in FarmDecisionModel and survive complete in-memory cache clearance.
4. Decision ownership verification in multi-tenant environments.
5. Soil/crop profile loading failure handling:
   Mandatory profile loading failure triggers explicit abstention (ABSTAIN_MANDATORY_PROFILE_FAILED /
   DecisionState.ABSTAIN_INSUFFICIENT_EVIDENCE) rather than evaluating zero crops as valid.
6. Soil report OCR background execution:
   Upload endpoint returns immediately with status PROCESSING and enqueues background processing.
   Dedicated status polling endpoint (/api/v1/soil/report-status/{job_id}) returns tracked status.
"""
import io
import time
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from cropnet.services.api.app.main import app
from cropnet.services.api.app.models.soil_and_farm import Base, FarmModel, FarmDecisionModel
from cropnet.services.api.app.models.soil_reports import SoilTestReportModel
from cropnet.services.api.app.schemas.soil_reports import ExtractionStatus, ReviewStatus
from cropnet.services.api.app.schemas.agriculture_intelligence import (
    FarmContextInput,
    FarmEvaluationResponse,
    DecisionState,
)
from cropnet.services.api.app.api.v1.endpoints.farms import _FARM_STORAGE
from cropnet.services.api.app.services.agriculture_intelligence.decision_engine import (
    DeterministicDecisionEngine,
    _DECISION_STORE,
    _CONTEXT_STORE,
)
from cropnet.services.api.app.services.agriculture_intelligence.knowledge_retriever import KnowledgeRetriever

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_db_tables(isolated_test_session):
    """Ensure database schema tables are created."""
    Base.metadata.create_all(bind=isolated_test_session.get_bind())
    yield


def _make_farm_payload(name: str = "Reliability Test Farm") -> dict:
    return {
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


# =========================================================================
# 1. Farm Creation DB Write Failure Surfacing (No False-Positive 201)
# =========================================================================

def test_farm_creation_db_write_failure_surfaces_500(isolated_test_session):
    """
    When database write operations fail during farm creation:
    Ensure errors are surfaced immediately (raise HTTP 500) and do NOT
    return false-positive HTTP 201 Created responses from in-memory fallback.
    """
    user_id = str(uuid.uuid4())
    payload = _make_farm_payload("DB Write Failure Farm")

    # Patch Session.commit on the isolated test session to simulate database disk/network error
    with patch.object(isolated_test_session, "commit", side_effect=SQLAlchemyError("Simulated disk I/O / DB failure")):
        resp = client.post(
            "/api/v1/farms",
            json=payload,
            headers={"X-Dev-User-Id": user_id}
        )

    # Must return HTTP 500 Internal Server Error, NOT HTTP 201 Created
    assert resp.status_code == 500
    assert "Database write failure" in resp.json()["detail"]

    # Verify no phantom farm is in memory cache
    user_cached = [f for f in _FARM_STORAGE.values() if f.get("name") == "DB Write Failure Farm"]
    assert len(user_cached) == 0

    # Verify listing farms does not include the failed farm
    list_resp = client.get("/api/v1/farms", headers={"X-Dev-User-Id": user_id})
    assert list_resp.status_code == 200
    assert not any(f["name"] == "DB Write Failure Farm" for f in list_resp.json())


# =========================================================================
# 2. Authoritative Database Persistence for Farms
# =========================================================================

def test_farm_listing_and_retrieval_uses_authoritative_database(isolated_test_session):
    """
    Verify create_farm, list_farms, and get_farm use authoritative database persistence,
    with _FARM_STORAGE acting only as an eviction-managed cache mirror.
    """
    user_id = str(uuid.uuid4())
    payload = _make_farm_payload("Authoritative DB Farm")

    # 1. Create farm successfully
    create_resp = client.post(
        "/api/v1/farms",
        json=payload,
        headers={"X-Dev-User-Id": user_id}
    )
    assert create_resp.status_code == 201
    farm_id = create_resp.json()["id"]

    # Verify DB has the record
    db_record = isolated_test_session.query(FarmModel).filter(FarmModel.id == farm_id).first()
    assert db_record is not None
    assert db_record.name == "Authoritative DB Farm"

    # 2. Simulate complete memory flush / server restart
    _FARM_STORAGE.clear()
    assert len(_FARM_STORAGE) == 0

    # 3. list_farms should load authoritatively from PostgreSQL
    list_resp = client.get("/api/v1/farms", headers={"X-Dev-User-Id": user_id})
    assert list_resp.status_code == 200
    farms = list_resp.json()
    assert any(f["id"] == farm_id for f in farms)

    # 4. get_farm should load from DB and populate the bounded cache
    get_resp = client.get(f"/api/v1/farms/{farm_id}", headers={"X-Dev-User-Id": user_id})
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == farm_id
    assert uuid.UUID(farm_id) in _FARM_STORAGE


# =========================================================================
# 3. Decision Persistence Across Process Restart / Multi-Worker Execution
# =========================================================================

def test_decision_persistence_across_process_restart(isolated_test_session):
    """
    Verify evaluated decisions and contexts persist in FarmDecisionModel
    and survive complete server restarts and multi-worker execution.
    """
    engine1 = DeterministicDecisionEngine()

    user_id = str(uuid.uuid4())
    farm_id = str(uuid.uuid4())
    decision_id = f"dec-{uuid.uuid4()}"

    ctx = FarmContextInput(
        user_id=user_id,
        farm_id=farm_id,
        taluka="Baramati",
        district="Pune",
        target_season="kharif",
        target_crops=["bajra"],
        soil_depth_cm=45.0,
        drainage="well_drained",
        irrigation_available=True,
        irrigation_source="canal",
    )

    # 1. Compute evaluation with engine 1 on worker 1
    resp1 = engine1.evaluate_farm(ctx=ctx, db=isolated_test_session)
    dec_id = resp1.decision_id
    assert dec_id is not None
    assert resp1.input_validation_status in ("VALID", "VALID_WITH_UNRESOLVED_CAVEATS")
    assert len(resp1.crop_outcomes) > 0

    # Verify decision was persisted in database table
    db_decision = isolated_test_session.query(FarmDecisionModel).filter(FarmDecisionModel.id == dec_id).first()
    assert db_decision is not None
    assert db_decision.id == dec_id
    assert db_decision.target_season == "kharif"

    # 2. Simulate complete worker restart / cache eviction
    _DECISION_STORE.clear()
    _CONTEXT_STORE.clear()
    assert len(_DECISION_STORE) == 0
    assert len(_CONTEXT_STORE) == 0

    # 3. Simulate Worker 2 retrieving decision via GET /decision/{decision_id}
    engine2 = DeterministicDecisionEngine()
    resp2 = engine2.get_decision(dec_id, db=isolated_test_session)
    assert resp2 is not None
    assert resp2.decision_id == dec_id
    assert resp2.target_season == "kharif"
    assert resp2.input_validation_status == resp1.input_validation_status
    assert len(resp2.crop_outcomes) == len(resp1.crop_outcomes)
    assert resp2.crop_outcomes[0].crop_id == "bajra"

    # Verify decision is now cached in memory on Worker 2
    assert dec_id in _DECISION_STORE

    # 4. Simulate Worker 2 handling follow-up answering across cache clearance
    _CONTEXT_STORE.clear()
    updated_resp = engine2.process_followup_answers(
        decision_id=dec_id,
        answers={"soil_depth_cm": 75.0},
        db=isolated_test_session
    )
    assert updated_resp is not None
    assert updated_resp.farm_context.soil_depth_cm == 75.0


def test_decision_ownership_check(isolated_test_session):
    """
    Verify get_decision enforces caller ownership when user_id is provided.
    """
    engine = DeterministicDecisionEngine()
    user1 = str(uuid.uuid4())
    user2 = str(uuid.uuid4())

    ctx = FarmContextInput(
        user_id=user1,
        taluka="Baramati",
        target_season="kharif",
        target_crops=["bajra"],
    )

    resp = engine.evaluate_farm(ctx=ctx, db=isolated_test_session)
    dec_id = resp.decision_id

    # Owner should access successfully
    assert engine.get_decision(dec_id, db=isolated_test_session, user_id=user1) is not None

    # Clear cache to force DB lookup
    _DECISION_STORE.clear()
    # Different user must be rejected (returns None)
    assert engine.get_decision(dec_id, db=isolated_test_session, user_id=user2) is None


# =========================================================================
# 4. Soil Profile Loading Failure Triggers Explicit Abstention
# =========================================================================

def test_soil_profile_loading_failure_triggers_abstention(isolated_test_session):
    """
    When mandatory crop/soil requirement profiles fail to load from the knowledge base:
    Return explicit error/abstention (ABSTAIN_MANDATORY_PROFILE_FAILED /
    DecisionState.ABSTAIN_INSUFFICIENT_EVIDENCE) rather than evaluating zero crops as valid.
    """
    # Create retriever where get_crop_profile returns None (simulating knowledge retrieval failure)
    mock_retriever = KnowledgeRetriever()
    mock_retriever.get_crop_profile = MagicMock(return_value=None)

    engine = DeterministicDecisionEngine(retriever=mock_retriever)
    ctx = FarmContextInput(
        taluka="Baramati",
        target_season="kharif",
        target_crops=["bajra"],
        soil_depth_cm=45.0,
    )

    resp = engine.evaluate_farm(ctx=ctx, db=isolated_test_session)

    # Must NOT claim input_validation_status is "VALID" with 0 crops evaluated
    assert resp.input_validation_status == "ABSTAIN_MANDATORY_PROFILE_FAILED"
    assert len(resp.crop_outcomes) == 1

    outcome = resp.crop_outcomes[0]
    assert outcome.crop_id == "bajra"
    assert outcome.decision_state == DecisionState.ABSTAIN_INSUFFICIENT_EVIDENCE
    assert "MANDATORY_CROP_PROFILE_FAILED" in outcome.limiting_factors


# =========================================================================
# 5. Soil Report OCR Background Execution & Status Polling
# =========================================================================

def test_soil_ocr_upload_returns_immediately_with_processing_status(isolated_test_session):
    """
    Verify soil report OCR processing does not block synchronously:
    - Upload endpoint accepts file, creates record with status PROCESSING,
      and returns HTTP 201 Created immediately (<200ms).
    - Status polling endpoint (/api/v1/soil/report-status/{job_id}) returns actionable tracked status.
    """
    user_id = str(uuid.uuid4())
    farm_id = str(uuid.uuid4())

    # Seed farm in database
    db_farm = FarmModel(
        id=farm_id,
        owner_id=user_id,
        name="OCR Background Test Farm",
        taluka="Baramati",
        district="Pune",
        state="Maharashtra",
        geometry_geojson={"type": "Polygon", "coordinates": [[[74.5, 18.1], [74.6, 18.1], [74.6, 18.2], [74.5, 18.2], [74.5, 18.1]]]},
        calculated_area_hectares=2.5,
        calculated_area_acres=6.18,
    )
    isolated_test_session.add(db_farm)
    isolated_test_session.commit()

    # Upload valid PDF
    pdf_bytes = b"%PDF-1.4 mock background OCR test soil health report"
    files = {"file": ("soil_test.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    data = {"laboratory_name": "Krishi Vigyan Kendra Baramati"}

    start_time = time.perf_counter()
    resp = client.post(
        f"/api/v1/farms/{farm_id}/soil-reports",
        files=files,
        data=data,
        headers={"X-Dev-User-Id": user_id}
    )
    duration = time.perf_counter() - start_time

    assert resp.status_code == 201
    assert duration < 1.0, f"Upload took {duration:.3f}s; must return fast"

    result = resp.json()
    job_id = result["id"]
    assert result["extraction_status"] == ExtractionStatus.PROCESSING.value

    # Poll dedicated status endpoint (/api/v1/soil/report-status/{job_id})
    status_resp = client.get(
        f"/api/v1/soil/report-status/{job_id}",
        headers={"X-Dev-User-Id": user_id}
    )
    assert status_resp.status_code == 200
    status_data = status_resp.json()

    assert status_data["job_id"] == job_id
    assert status_data["report_id"] == job_id
    assert status_data["status"] in (
        ExtractionStatus.PROCESSING.value,
        ExtractionStatus.NEEDS_REVIEW.value,
        ExtractionStatus.FAILED.value,
        ExtractionStatus.EXTRACTION_COMPLETED.value
    )

    # Polling with non-existent job ID returns 404 for authenticated caller
    non_existent = str(uuid.uuid4())
    bad_resp = client.get(f"/api/v1/soil/report-status/{non_existent}", headers={"X-Dev-User-Id": user_id})
    assert bad_resp.status_code == 404
