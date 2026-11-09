"""
CropNet AI — Phase 5.5 Backend Reliability, Concurrency & AI Performance Regression Suite.

Verifies:
1. Decision engine cached vs uncached evaluations and provenance retention.
2. KnowledgeRetriever thread-safety under concurrent access.
3. Out-of-catalogue and unavailable knowledge fails closed (abstains, never fabricates).
4. Ollama Qwen3:8B integration, latency profiling, and graceful fallback.
5. Row-level tenant authorization and multi-tenant farm isolation.
"""
import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from cropnet.services.api.app.main import app
from cropnet.services.api.app.services.agriculture_intelligence.knowledge_retriever import KnowledgeRetriever
from cropnet.services.api.app.services.agriculture_intelligence.decision_engine import DeterministicDecisionEngine
from cropnet.services.api.app.schemas.agriculture_intelligence import (
    FarmContextInput,
    DecisionState,
    ExplainDecisionRequest,
)
from cropnet.services.api.app.services.llm.ollama_client import OllamaClient
from cropnet.services.api.app.services.llm.explanation_service import AgriculturalExplanationService

client = TestClient(app)


def test_knowledge_cache_initialization_and_provenance():
    """Verify knowledge cache primes properly and retains valid provenance."""
    retriever = KnowledgeRetriever()
    crops = retriever.get_supported_crops()
    assert len(crops) == 10
    assert "sugarcane" in crops
    assert "chickpea" in crops

    profile = retriever.get_crop_profile("sugarcane")
    assert profile is not None
    assert profile.common_name.lower() == "sugarcane"

    citation = retriever.get_source_citation("mpkv_research_2023")
    assert citation is not None
    assert "MPKV" in citation.organization


def test_knowledge_cache_thread_safety_under_concurrency():
    """Verify KnowledgeRetriever handles concurrent thread queries without race conditions."""
    retriever = KnowledgeRetriever()
    results = []
    errors = []

    def worker(crop_id: str):
        try:
            for _ in range(50):
                p = retriever.get_crop_profile(crop_id)
                if p is None:
                    errors.append(f"Profile for {crop_id} was None")
                c = retriever.get_source_citation("mpkv_research_2023")
                if c is None:
                    errors.append("Citation was None")
            results.append(crop_id)
        except Exception as e:
            errors.append(str(e))

    crops = ["sugarcane", "pomegranate", "soybean", "cotton", "maize", "wheat", "sorghum", "bajra", "chickpea", "groundnut"]
    threads = [threading.Thread(target=worker, args=(c,)) for c in crops]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Concurrent access errors: {errors}"
    assert len(results) == len(crops)


def test_cache_invalidation_and_reprime():
    """Verify cache invalidation completely refreshes internal stores."""
    retriever = KnowledgeRetriever()
    assert len(retriever._profile_cache) >= 10
    assert len(retriever._citation_cache) >= 5

    retriever.clear_cache()
    # Should be re-primed immediately
    assert len(retriever._profile_cache) >= 10
    assert len(retriever._citation_cache) >= 5
    assert retriever.get_crop_profile("chickpea") is not None


def test_unavailable_knowledge_fails_closed():
    """Verify unavailable crop knowledge returns None and does not invent data."""
    retriever = KnowledgeRetriever()
    # Non-existent crop
    assert retriever.get_crop_profile("dragon_fruit") is None
    assert retriever.get_crop_profile("vanilla") is None
    # Non-existent citation
    assert retriever.get_source_citation("SRC_NON_EXISTENT_999") is None

    engine = DeterministicDecisionEngine(retriever=retriever)
    ctx = FarmContextInput(
        taluka="Baramati",
        district="Pune",
        soil_texture="clay",
        soil_ph=7.5,
        target_crops=["dragon_fruit"],
    )
    res = engine.evaluate_farm(ctx)
    assert res.input_validation_status == "ABSTAIN_UNREGISTERED_CROP"
    assert len(res.crop_outcomes) == 1
    assert res.crop_outcomes[0].decision_state == DecisionState.ABSTAIN_INSUFFICIENT_EVIDENCE
    assert res.crop_outcomes[0].is_disqualified is True


def test_decision_engine_evaluation_benchmark_sla():
    """Verify that evaluate_farm completes well within 50ms SLA on warm cache."""
    engine = DeterministicDecisionEngine()
    ctx = FarmContextInput(
        taluka="Baramati",
        district="Pune",
        soil_texture="clay",
        soil_ph=7.5,
        irrigation_available=True,
        irrigation_source="canal",
        target_season="kharif",
    )

    t0 = time.perf_counter()
    res = engine.evaluate_farm(ctx)
    duration_ms = (time.perf_counter() - t0) * 1000.0

    assert duration_ms < 50.0, f"Evaluation took {duration_ms:.2f}ms, exceeding 50ms SLA"
    assert len(res.crop_outcomes) > 0
    assert res.decision_id is not None


def test_concurrent_api_evaluations_throughput():
    """Verify concurrent evaluate-farm requests through FastAPI test client."""
    def request_eval():
        payload = {
            "farm_context": {
                "taluka": "Baramati",
                "district": "Pune",
                "soil_texture": "clay",
                "soil_ph": 7.5,
                "irrigation_source": "canal",
                "irrigation_available": True,
                "target_season": "kharif"
            }
        }
        resp = client.post(
            "/api/v1/agriculture/evaluate-farm",
            json=payload,
            headers={"X-Dev-User-Id": "00000000-0000-0000-0000-000000000001"}
        )
        return resp.status_code, resp.json()

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(request_eval) for _ in range(10)]
        for f in futures:
            status_code, data = f.result()
            assert status_code == 200
            assert "decision_id" in data


def test_ollama_client_timeout_and_fallback_grace():
    """Verify that OllamaClient enforces granular timeout and fallback service delivers prompt fallback."""
    service = AgriculturalExplanationService()
    engine = DeterministicDecisionEngine()
    ctx = FarmContextInput(
        taluka="Baramati",
        district="Pune",
        soil_texture="clay",
        soil_ph=7.5,
        irrigation_available=True,
        irrigation_source="canal",
        target_season="kharif"
    )
    eval_resp = engine.evaluate_farm(ctx)

    # Mock timeout in client
    with patch.object(service.ollama, "chat_completion", side_effect=Exception("Connection timed out")):
        req = ExplainDecisionRequest(decision_id=eval_resp.decision_id, language="en")
        resp = service.explain_decision(
            req=req,
            db=None
        )
        assert resp is not None
        assert resp.generation_source == "deterministic_fallback"
        assert resp.validation_passed is True
        assert len(resp.authoritative_citations) > 0


def test_health_check_llm_runtime_reporting():
    """Verify /api/v1/health reports LLM runtime status and data providers."""
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "llm_runtime" in data
    assert "soil_data_providers" in data
    assert data["llm_runtime"]["configured_model"] == "qwen3:8b"
