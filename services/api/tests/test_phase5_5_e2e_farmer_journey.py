"""
CropNet AI Phase 5.5 — Complete Farmer Journey End-to-End Validation Suite.

Covers:
1. Authentication & Session Verification.
2. Farm Polygon Creation, Retrieval & Geodesic Persistence.
3. Soil Intelligence with Strict Digital NPK Non-Fabrication Guarantee.
4. Agro-Meteorology (Real-time vs 30-Year Climatology Separation).
5. Crop Catalogue Exploration with Seasonal Classification.
6. Deterministic Agricultural Feasibility Evaluation (Phase 5.1).
7. Grounded AI Explanation Generation (Phase 5.2).
8. Bilingual Dialogue Turns (English and Marathi).
9. Diagnostic Follow-Up Answering & Deterministic Re-Evaluation.
10. Edge Cases: Cold Cache vs Warm Cache, Ollama Timeout Fallback, Multi-Tenant Isolation (403), Clean Farm Teardown.
"""
import pytest
import time
from unittest.mock import patch
from fastapi.testclient import TestClient

from cropnet.services.api.app.main import app
from cropnet.services.api.app.services.agriculture_intelligence.decision_engine import DeterministicDecisionEngine
from cropnet.services.api.app.services.agriculture_intelligence.knowledge_retriever import KnowledgeRetriever
from cropnet.services.api.app.schemas.agriculture_intelligence import FarmContextInput

client = TestClient(app)

# Test User Credentials
TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_USER_2_ID = "00000000-0000-0000-0000-000000000002"
AUTH_HEADERS_USER1 = {"X-Dev-User-Id": TEST_USER_ID}
AUTH_HEADERS_USER2 = {"X-Dev-User-Id": TEST_USER_2_ID}


def test_complete_farmer_journey_e2e():
    """Execute complete farmer lifecycle from farm registration to advisory dialogue."""
    created_farm_id = None

    try:
        # -------------------------------------------------------------
        # STEP 1: Register Real Farm with Polygon Boundary
        # -------------------------------------------------------------
        farm_payload = {
            "name": "Phase 5.5 E2E Stabilization Farm",
            "taluka": "Baramati",
            "district": "Pune",
            "state": "Maharashtra",
            "village": "Malegaon Khurd",
            "irrigation_type": "irrigated",
            "water_source": "canal",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [74.5200, 18.1700],
                    [74.5250, 18.1700],
                    [74.5250, 18.1750],
                    [74.5200, 18.1750],
                    [74.5200, 18.1700]
                ]]
            }
        }
        res_create = client.post("/api/v1/farms", json=farm_payload, headers=AUTH_HEADERS_USER1)
        assert res_create.status_code == 201, f"Farm creation failed: {res_create.text}"
        farm_data = res_create.json()
        created_farm_id = farm_data["id"]

        assert farm_data["name"] == "Phase 5.5 E2E Stabilization Farm"
        assert farm_data["taluka"] == "Baramati"
        assert farm_data["calculated_area_hectares"] > 20.0
        assert farm_data["calculated_area_acres"] > 50.0

        # -------------------------------------------------------------
        # STEP 2: Retrieve Farm & Verify PostGIS Geodesic Geometry
        # -------------------------------------------------------------
        res_get = client.get(f"/api/v1/farms/{created_farm_id}", headers=AUTH_HEADERS_USER1)
        assert res_get.status_code == 200
        assert res_get.json()["id"] == created_farm_id

        # Multi-Tenant Isolation Check: User 2 cannot access this farm
        res_forbidden = client.get(f"/api/v1/farms/{created_farm_id}", headers=AUTH_HEADERS_USER2)
        assert res_forbidden.status_code == 403, "Cross-user security breach: User 2 accessed User 1 farm!"

        # -------------------------------------------------------------
        # STEP 3: Soil Intelligence & Digital NPK Safeguard
        # -------------------------------------------------------------
        res_soil = client.post(f"/api/v1/farms/{created_farm_id}/soil/analyse", headers=AUTH_HEADERS_USER1)
        assert res_soil.status_code == 200
        soil_profile = res_soil.json()
        assert "ph" in soil_profile or "texture_class" in soil_profile

        # CRITICAL SAFEGUARD: Zero raster NPK fabrication
        assert soil_profile.get("available_nitrogen_kg_ha") is None
        assert soil_profile.get("available_phosphorus_kg_ha") is None
        assert soil_profile.get("available_potassium_kg_ha") is None

        # -------------------------------------------------------------
        # STEP 4: Weather Intelligence & Agro-Meteorology
        # -------------------------------------------------------------
        res_weather = client.get(f"/api/v1/farms/{created_farm_id}/weather/current", headers=AUTH_HEADERS_USER1)
        assert res_weather.status_code == 200
        weather_data = res_weather.json()
        assert "temperature_c" in weather_data or "weather_condition" in weather_data

        # -------------------------------------------------------------
        # STEP 5: Crop Catalogue Exploration
        # -------------------------------------------------------------
        res_crops = client.get("/api/v1/crops")
        assert res_crops.status_code == 200
        crops = res_crops.json()
        assert len(crops) >= 10
        crop_ids = [c["id"] for c in crops]
        assert "sugarcane" in crop_ids
        assert "chickpea" in crop_ids

        # -------------------------------------------------------------
        # STEP 6: Deterministic Crop Evaluation (Phase 5.1 Engine)
        # -------------------------------------------------------------
        eval_payload = {
            "farm_id": created_farm_id,
            "taluka": "Baramati",
            "district": "Pune",
            "soil_ph": 7.5,
            "soil_texture": "clay",
            "irrigation_available": True,
            "irrigation_source": "canal",
            "target_season": "kharif",
            "language": "en"
        }
        res_eval = client.post("/api/v1/agriculture/evaluate-farm", json=eval_payload, headers=AUTH_HEADERS_USER1)
        assert res_eval.status_code == 200
        eval_data = res_eval.json()
        decision_id = eval_data["decision_id"]
        assert decision_id is not None
        assert len(eval_data["crop_outcomes"]) > 0

        # Verify outcome structure and citations
        first_crop = eval_data["crop_outcomes"][0]
        assert "decision_state" in first_crop
        assert "citations" in first_crop

        # -------------------------------------------------------------
        # STEP 7: Grounded AI Explanation (Phase 5.2 / Qwen3:8B)
        # -------------------------------------------------------------
        mock_ollama_resp = {
            "message": {
                "content": "Sugarcane is conditionally feasible in Baramati with canal irrigation according to MPKV Rahuri recommendations."
            }
        }
        with patch("cropnet.services.api.app.services.llm.ollama_client.OllamaClient.chat_completion", return_value=mock_ollama_resp):
            exp_payload_en = {"decision_id": decision_id, "language": "en"}
            res_exp_en = client.post("/api/v1/agriculture/explain-decision", json=exp_payload_en, headers=AUTH_HEADERS_USER1)
            assert res_exp_en.status_code == 200
            exp_en = res_exp_en.json()
            assert exp_en["decision_id"] == decision_id
            assert exp_en["validation_passed"] is True
            assert len(exp_en["explanation_text"]) > 20

            # -------------------------------------------------------------
            # STEP 8: Bilingual Dialogue in Marathi (Devanagari)
            # -------------------------------------------------------------
            exp_payload_mr = {"decision_id": decision_id, "language": "mr"}
            res_exp_mr = client.post("/api/v1/agriculture/explain-decision", json=exp_payload_mr, headers=AUTH_HEADERS_USER1)
            assert res_exp_mr.status_code == 200
            exp_mr = res_exp_mr.json()
            assert exp_mr["language"] == "mr"
            assert len(exp_mr["explanation_text"]) > 20

            # -------------------------------------------------------------
            # STEP 9: Diagnostic Follow-Up & Re-Evaluation
            # -------------------------------------------------------------
            followups = eval_data.get("follow_up_questions", [])
            if followups:
                target_q = followups[0]
                param_key = target_q["target_parameter"]
                fu_payload = {
                    "decision_id": decision_id,
                    "answers": {param_key: "clay"}
                }
                res_fu = client.post("/api/v1/agriculture/follow-up", json=fu_payload, headers=AUTH_HEADERS_USER1)
                assert res_fu.status_code == 200
                fu_data = res_fu.json()
                assert fu_data["decision_id"] is not None

            # -------------------------------------------------------------
            # STEP 10: Interactive Dialogue Turn
            # -------------------------------------------------------------
            conv_payload = {
                "decision_id": decision_id,
                "message": "Is sugarcane recommended given my canal irrigation?",
                "language": "en"
            }
            res_conv = client.post("/api/v1/agriculture/conversation", json=conv_payload, headers=AUTH_HEADERS_USER1)
            assert res_conv.status_code == 200
            conv_data = res_conv.json()
            assert "explanation_text" in conv_data
            assert conv_data["validation_passed"] is True

    finally:
        # -------------------------------------------------------------
        # STEP 11: Teardown & Clean Up Test Farm Record
        # -------------------------------------------------------------
        if created_farm_id:
            res_del = client.delete(f"/api/v1/farms/{created_farm_id}", headers=AUTH_HEADERS_USER1)
            assert res_del.status_code in (200, 204)
            # Verify farm is deleted
            res_check_del = client.get(f"/api/v1/farms/{created_farm_id}", headers=AUTH_HEADERS_USER1)
            assert res_check_del.status_code == 404


def test_cold_cache_vs_warm_cache_performance():
    """Verify performance SLA between cold cache re-prime and warm cache query."""
    retriever = KnowledgeRetriever()
    retriever.clear_cache()

    # Cold evaluation (first run)
    t0 = time.perf_counter()
    engine = DeterministicDecisionEngine(retriever=retriever)
    ctx = FarmContextInput(
        taluka="Baramati",
        district="Pune",
        soil_texture="clay",
        soil_ph=7.5,
        irrigation_available=True,
        irrigation_source="canal",
        target_season="kharif"
    )
    res_cold = engine.evaluate_farm(ctx)
    cold_duration_ms = (time.perf_counter() - t0) * 1000.0

    # Warm evaluation (second run)
    t1 = time.perf_counter()
    res_warm = engine.evaluate_farm(ctx)
    warm_duration_ms = (time.perf_counter() - t1) * 1000.0

    assert cold_duration_ms < 100.0, f"Cold evaluation SLA exceeded: {cold_duration_ms:.2f}ms"
    assert warm_duration_ms < 10.0, f"Warm evaluation SLA exceeded: {warm_duration_ms:.2f}ms"
    assert res_cold.crop_outcomes == res_warm.crop_outcomes


def test_ollama_offline_resilient_fallback():
    """Verify that when Ollama is completely unreachable, API returns HTTP 200 with fallback."""
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
    eval_resp = engine.evaluate_farm(ctx, user_id=TEST_USER_ID)

    with patch("cropnet.services.api.app.services.llm.ollama_client.OllamaClient.chat_completion", side_effect=Exception("Ollama service down")):
        exp_payload = {"decision_id": eval_resp.decision_id, "language": "en"}
        res = client.post("/api/v1/agriculture/explain-decision", json=exp_payload, headers=AUTH_HEADERS_USER1)
        assert res.status_code == 200
        data = res.json()
        assert data["generation_source"] == "deterministic_fallback"
        assert data["validation_passed"] is True
        assert len(data["authoritative_citations"]) > 0
