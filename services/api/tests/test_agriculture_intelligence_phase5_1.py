"""
CropNet AI — Phase 5.1 Deterministic Agriculture Intelligence Test Suite.

Validates:
1. Farm context validation, contradiction detection, and Total N vs Available N separation.
2. Soil, climate, water, and regional constraint evaluation.
3. Decoupled irrigation schedules and Bahar daily tree water tables.
4. Standardized machine-readable decision states (VERIFIED_SUITABLE, UNSUITABLE_VERIFIED_CONSTRAINT, etc.).
5. Evidence gating (unverified sources cannot enforce hard disqualifications).
6. Follow-up question selection and state re-evaluation.
7. Full API endpoint lifecycle (evaluate-farm, decision inspection, follow-up).
"""
import pytest
from fastapi.testclient import TestClient

from cropnet.services.api.app.main import app
from cropnet.services.api.app.schemas.agriculture_intelligence import (
    FarmContextInput,
    DecisionState,
    SoilDataProvenance,
    EvidenceTier,
    FollowUpAnswerRequest
)
from cropnet.services.api.app.services.agriculture_intelligence.decision_engine import DeterministicDecisionEngine
from cropnet.services.api.app.services.agriculture_intelligence.evidence_gate import EvidenceGate, SOURCE_TIER_MAPPING

client = TestClient(app)
engine = DeterministicDecisionEngine()


def test_evidence_gate_mappings_and_permissions():
    """Verify 4-tier evidence gating rules and permission boundaries."""
    assert EvidenceGate.get_tier("mpkv_research_2023") == EvidenceTier.VERIFIED
    assert EvidenceGate.get_tier("icrisat_chickpea_2010") == EvidenceTier.VERIFIED
    assert EvidenceGate.get_tier("icar_nrcp_manage_2022") == EvidenceTier.VERIFIED
    assert EvidenceGate.get_tier("mpkv_pop_2023") == EvidenceTier.VERIFIED
    
    assert EvidenceGate.get_tier("icar_cicr_cotton_2022") == EvidenceTier.CONDITIONALLY_SUPPORTED
    assert EvidenceGate.get_tier("iisr_brochure_glance") == EvidenceTier.UNVERIFIED_BIBLIOGRAPHIC
    assert EvidenceGate.get_tier("non_existent_source") == EvidenceTier.UNSUPPORTED

    # Hard disqualification permission
    assert EvidenceGate.can_enforce_hard_disqualification(EvidenceTier.VERIFIED) is True
    assert EvidenceGate.can_enforce_hard_disqualification(EvidenceTier.CONDITIONALLY_SUPPORTED) is True
    assert EvidenceGate.can_enforce_hard_disqualification(EvidenceTier.UNVERIFIED_BIBLIOGRAPHIC) is False
    assert EvidenceGate.can_enforce_hard_disqualification(EvidenceTier.UNSUPPORTED) is False


def test_farm_context_contradiction_detection():
    """Verify detection of physical and chemical input contradictions."""
    # Coarse sand + 14 days standing water
    ctx = FarmContextInput(
        taluka="Baramati",
        soil_texture="Coarse sand",
        standing_water_days=14,
        target_crops=["bajra"]
    )
    res = engine.evaluate_farm(ctx)
    assert res.input_validation_status == "CONTRADICTORY_INPUTS_DETECTED"
    assert len(res.contradictions_detected) > 0
    assert "Coarse sandy soil reported with 14 days standing" in res.contradictions_detected[0]

    # pH 8.3 described as acidic with lime application planned
    ctx_ph = FarmContextInput(
        taluka="Baramati",
        soil_ph=8.3,
        user_query="My soil pH is 8.3, quite acidic, can I add lime?"
    )
    res_ph = engine.evaluate_farm(ctx_ph)
    assert any("alkaline/calcareous" in c for c in res_ph.contradictions_detected)


def test_total_nitrogen_vs_available_nitrogen_separation():
    """Verify that Total N is never treated as Available N and urea need is flagged."""
    ctx = FarmContextInput(
        taluka="Baramati",
        soil_texture="Clay (Vertisol)",
        soil_ph=7.8,
        total_nitrogen_pct=0.06,
        available_nitrogen_kg_ha=185.0, # Low < 280 kg/ha
        target_crops=["sorghum"],
        target_season="rabi"
    )
    res = engine.evaluate_farm(ctx)
    sorghum_outcome = next(o for o in res.crop_outcomes if o.crop_id == "sorghum")
    # Low nitrogen warning must be present
    assert any("Available Nitrogen is Low" in w for w in sorghum_outcome.uncertainty_notes)
    assert any("280 kg/ha standard" in w for w in sorghum_outcome.uncertainty_notes)


def test_pomegranate_hard_depth_and_drainage_disqualification():
    """Verify pomegranate disqualification under poor drainage with depth triggering pit planting advisory."""
    ctx = FarmContextInput(
        taluka="Indapur",
        soil_ph=6.8, # Ideal pH
        soil_depth_cm=20.0, # Shallow (< 1 m)
        drainage="Poor / Waterlogged",
        target_crops=["pomegranate"]
    )
    res = engine.evaluate_farm(ctx)
    pom_outcome = next(o for o in res.crop_outcomes if o.crop_id == "pomegranate")
    assert pom_outcome.is_disqualified is True
    assert pom_outcome.decision_state == DecisionState.UNSUITABLE_VERIFIED_CONSTRAINT
    assert any("Poor drainage" in f or "Waterlogging" in f for f in pom_outcome.limiting_factors)
    assert any("pit planting" in w.lower() or "depth" in w.lower() for w in pom_outcome.uncertainty_notes)


def test_pomegranate_daily_water_table_indexing():
    """Verify 4-year-old tree daily water schedule in October under Mrig Bahar."""
    ctx = FarmContextInput(
        taluka="Baramati",
        target_crops=["pomegranate"],
        target_bahar="mrig_bahar",
        tree_age_years=4
    )
    res = engine.evaluate_farm(ctx)
    pom_outcome = next(o for o in res.crop_outcomes if o.crop_id == "pomegranate")
    dwt = pom_outcome.pomegranate_daily_water
    assert dwt is not None
    assert dwt["unit"] == "liters_per_tree_per_day"
    assert dwt["bahar"] == "mrig_bahar"
    assert dwt["tree_age_years"] == 4
    assert dwt["annual_water_mm"] is None # Preserved as NULL
    assert "28.3 to 34.2 L/tree/day" in dwt["october_range_liters_day"]


def test_pomegranate_bahar_selection_under_summer_water_scarcity():
    """Verify recommendation of Hasta Bahar over Ambia Bahar when water runs out post-Feb."""
    ctx = FarmContextInput(
        taluka="Baramati",
        target_crops=["pomegranate"],
        water_scarcity_period="post_february_summer"
    )
    res = engine.evaluate_farm(ctx)
    pom_outcome = next(o for o in res.crop_outcomes if o.crop_id == "pomegranate")
    guidance = pom_outcome.irrigation_guidance
    assert guidance is not None
    assert "Hasta Bahar" in guidance["recommended_bahar"]
    assert "Ambia Bahar" in guidance["disqualified_bahar"]


def test_chickpea_reproductive_thermal_stress_thresholds():
    """Verify ICRISAT 2010 reproductive temperature thresholds (>35°C max and <15°C mean)."""
    # Max temp 37°C during flowering
    ctx_heat = FarmContextInput(
        taluka="Baramati",
        target_crops=["chickpea"],
        growth_stage="flowering",
        forecast_max_temp_c=37.0
    )
    res_heat = engine.evaluate_farm(ctx_heat)
    chk_heat = next(o for o in res_heat.crop_outcomes if o.crop_id == "chickpea")
    assert len(chk_heat.reproductive_risk_warnings) > 0
    assert any("35°C threshold" in w and "flower drop" in w for w in chk_heat.reproductive_risk_warnings)

    # Low temperature mean < 15°C (max 20°C, min 8°C -> mean 14°C)
    ctx_cold = FarmContextInput(
        taluka="Baramati",
        target_crops=["chickpea"],
        growth_stage="flowering",
        forecast_max_temp_c=20.0,
        forecast_min_temp_c=8.0
    )
    res_cold = engine.evaluate_farm(ctx_cold)
    chk_cold = next(o for o in res_cold.crop_outcomes if o.crop_id == "chickpea")
    assert len(chk_cold.reproductive_risk_warnings) > 0
    assert any("15°C threshold" in w and "flower abortion" in w for w in chk_cold.reproductive_risk_warnings)


def test_chickpea_decoupled_irrigation_and_rainfall_suspension():
    """Verify decoupled ICRISAT & MPKV schedules and rain-aware suspension."""
    ctx = FarmContextInput(
        taluka="Baramati",
        target_crops=["chickpea"],
        days_after_sowing=22,
        forecast_rain_mm_48h=50.0 # 50 mm heavy rain forecast
    )
    res = engine.evaluate_farm(ctx)
    chk_outcome = next(o for o in res.crop_outcomes if o.crop_id == "chickpea")
    guidance = chk_outcome.irrigation_guidance
    assert guidance["management_strategy"] == "DECOUPLED_FRAMEWORKS"
    assert "ICRISAT" in guidance["icrisat_2010_framework"]["source"]
    assert "MPKV" in guidance["mpkv_2023_framework"]["source"]
    assert "Do NOT combine both into 4 irrigations" in guidance["anti_blending_warning"]
    # Rainfall suspension advisory must be triggered
    assert any("SUSPEND and POSTPONE planned irrigation" in w or "POSTPONE" in w for w in chk_outcome.uncertainty_notes)


def test_sugarcane_summer_water_depletion_disqualification():
    """Verify sugarcane disqualification when well water dries by February."""
    ctx = FarmContextInput(
        taluka="Indapur",
        target_crops=["sugarcane"],
        irrigation_capacity="seasonal_dry_by_february"
    )
    res = engine.evaluate_farm(ctx)
    cane = next(o for o in res.crop_outcomes if o.crop_id == "sugarcane")
    assert cane.is_disqualified is True
    assert cane.decision_state == DecisionState.UNSUITABLE_VERIFIED_CONSTRAINT
    assert any("exhausted by February coincides with the critical summer tillering" in f for f in cane.limiting_factors)


def test_kharif_dry_sowing_rainfall_gate():
    """Verify block on dry sowing before monsoon arrives relying on 30-year climatology."""
    ctx = FarmContextInput(
        taluka="Baramati",
        target_crops=["groundnut"],
        target_season="kharif",
        proposed_sowing_date="2026-06-05",
        monsoon_arrived=False,
        actual_recorded_rain_mm=10.0 # Insufficient soaking rain
    )
    res = engine.evaluate_farm(ctx)
    gnut = next(o for o in res.crop_outcomes if o.crop_id == "groundnut")
    assert gnut.is_disqualified is True
    assert gnut.decision_state == DecisionState.UNSUITABLE_VERIFIED_CONSTRAINT
    assert any("75–100 mm actual recorded soaking rainfall" in f for f in gnut.limiting_factors)


def test_regional_screening_vs_validation_pilot_talukas():
    """Verify Baramati is regional_screening and Maval is requires_regional_validation."""
    # Baramati (Plain/Scarcity Zone)
    ctx_bar = FarmContextInput(taluka="Baramati", target_crops=["cotton"])
    res_bar = engine.evaluate_farm(ctx_bar)
    cot_bar = next(o for o in res_bar.crop_outcomes if o.crop_id == "cotton")
    assert cot_bar.decision_state == DecisionState.REGIONAL_SCREENING_ONLY
    assert any("macro-zonal agroecological baseline" in w for w in cot_bar.uncertainty_notes)

    # Maval (Western Ghats Transition)
    ctx_mav = FarmContextInput(taluka="Maval", target_crops=["chickpea"])
    res_mav = engine.evaluate_farm(ctx_mav)
    chk_mav = next(o for o in res_mav.crop_outcomes if o.crop_id == "chickpea")
    assert chk_mav.decision_state == DecisionState.REQUIRES_REGIONAL_VALIDATION


def test_abstention_on_zero_context_and_unregistered_crop():
    """Verify abstention when context is empty or crop is unregistered."""
    # Empty context
    empty_ctx = FarmContextInput()
    res_empty = engine.evaluate_farm(empty_ctx)
    assert res_empty.input_validation_status == "ABSTAIN_ZERO_CONTEXT"
    assert len(res_empty.crop_outcomes) == 0
    assert len(res_empty.follow_up_questions) >= 3

    # Unregistered crop (Dragon fruit)
    ctx_ooc = FarmContextInput(
        taluka="Indapur",
        user_query="Give me the fertilization schedule for Dragon Fruit"
    )
    res_ooc = engine.evaluate_farm(ctx_ooc)
    assert res_ooc.input_validation_status == "ABSTAIN_UNREGISTERED_CROP"
    assert res_ooc.crop_outcomes[0].decision_state == DecisionState.ABSTAIN_INSUFFICIENT_EVIDENCE
    assert "not registered in CropNet's 10 priority crops" in res_ooc.crop_outcomes[0].limiting_factors[0]


def test_followup_question_selection_and_priority():
    """Verify clinical follow-up question selection prioritizing depth and drainage."""
    ctx = FarmContextInput(
        taluka="Baramati",
        soil_ph=7.5,
        target_crops=["pomegranate"]
        # Missing soil_depth_cm, drainage, target_bahar
    )
    res = engine.evaluate_farm(ctx)
    q_ids = [q.question_id for q in res.follow_up_questions]
    assert "Q_SOIL_DEPTH" in q_ids
    assert "Q_DRAINAGE_CONDITION" in q_ids
    assert "Q_POMEGRANATE_BAHAR" in q_ids
    # Priority ordering
    assert res.follow_up_questions[0].priority == 1


def test_api_endpoints_lifecycle():
    """Verify HTTP lifecycle across evaluate-farm, decision inspection, and follow-up."""
    # 1. POST /api/v1/agriculture/evaluate-farm
    eval_payload = {
        "taluka": "Baramati",
        "soil_ph": 7.8,
        "soil_texture": "Clay loam",
        "target_crops": ["chickpea"],
        "target_season": "rabi",
        "language": "en"
    }
    resp1 = client.post("/api/v1/agriculture/evaluate-farm", json=eval_payload)
    assert resp1.status_code == 200
    data1 = resp1.json()
    dec_id = data1["decision_id"]
    assert dec_id.startswith("dec_")
    assert len(data1["crop_outcomes"]) == 1
    chk_res = data1["crop_outcomes"][0]
    assert chk_res["crop_id"] == "chickpea"
    assert "governance_notice" in data1

    # 2. GET /api/v1/agriculture/decision/{decision_id}
    resp2 = client.get(f"/api/v1/agriculture/decision/{dec_id}")
    assert resp2.status_code == 200
    assert resp2.json()["decision_id"] == dec_id

    # 3. POST /api/v1/agriculture/follow-up
    followup_payload = {
        "decision_id": dec_id,
        "answers": {
            "soil_depth_cm": "Deep (> 60 cm)",
            "drainage": "Well-drained (water clears within 24h)"
        }
    }
    resp3 = client.post("/api/v1/agriculture/follow-up", json=followup_payload)
    assert resp3.status_code == 200
    data3 = resp3.json()
    assert data3["decision_id"] != dec_id # New updated evaluation ID
    assert len(data3["crop_outcomes"]) == 1
