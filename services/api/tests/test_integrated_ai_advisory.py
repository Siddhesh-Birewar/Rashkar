"""
CropNet AI — Phase 6.0 Integrated AI Agricultural Advisory Test Suite.

Verifies:
1. Multi-domain snapshot context ingestion by FarmContextBuilder:
   - Full evidence snapshot (all 5 domains AVAILABLE)
   - Missing evidence snapshot (5 domains NOT_AVAILABLE, strictly null values, zero fabricated data)
   - Stale evidence snapshot (STALE observations with age metadata)
   - Token budget / compact representation (< 1500 tokens)
   - Query domain classification across soil, water, satellite, weather, crop, and cross-domain inquiries.
2. Cross-domain agronomic dialogue & explanation in English and Marathi:
   - Water salinity (EC 1.85 dS/m) limiting salt-sensitive onion under BIS IS 11624:2019
   - Rainfall deficit impacting wheat water requirements
   - Pure canopy Sentinel-2 Class 4 NDVI (0.68) vs bare-soil inter-row paths (0.28)
   - Missing evidence honest disclosure (unmeasured water/soil tests)
   - Vernacular Marathi precision (सामू, क्षारता, कॅनॉपी NDVI, पाण्याचा निचरा).
3. Agronomic guardrails & safeguards:
   - Prohibition on determining suitability (strictly governed by DeterministicDecisionEngine)
   - Rejection of decision state reversals/overrides
   - Rejection of fabricated fertilizer dosages (e.g. 120 kg urea)
   - Rejection of fabricated chemical pesticide/fungicide spray measurements (e.g. 2.5 ml/L)
   - Rejection of diagnosing disease pathogens from satellite optical reflectance without scientific disclaimer
   - Mandatory scientific disclaimer for satellite vegetation inquiries.
4. Multi-turn conversation continuity and follow-up question isolation:
   - Natural language diagnostic intent detection (drainage, depth, salinity, well depth, irrigation)
   - Deterministic engine re-evaluation hook
   - Diagnostic question isolation (answered question removed, remaining isolated)
   - Updated guidance reflecting deterministic re-evaluation
   - Vernacular Marathi multi-turn diagnostic handling.
5. Structured advisory card generation and offline deterministic fallback parity.
6. Local Qwen3:8B inference (live or mocked fallback).
"""
import sys
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, MagicMock

import pytest

# Ensure cropnet imports resolve to this worktree root
worktree_root = Path(__file__).resolve().parents[3]
if "cropnet" not in sys.modules:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "cropnet",
        str(worktree_root / "__init__.py"),
        submodule_search_locations=[str(worktree_root)]
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["cropnet"] = mod
    spec.loader.exec_module(mod)

from cropnet.services.api.app.schemas.agriculture_intelligence import (
    FarmContextInput,
    FarmEvaluationResponse,
    SoilDataProvenance,
    DecisionState,
    ExplainDecisionRequest,
    ConversationRequest,
    ConversationMessage,
    FollowUpQuestion,
    StructuredAdvisoryCard
)
from cropnet.services.api.app.services.agriculture_intelligence.decision_engine import (
    DeterministicDecisionEngine,
    _DECISION_STORE
)
from cropnet.services.api.app.services.llm.farm_context_builder import FarmContextBuilder
from cropnet.services.api.app.services.llm.prompt_builder import ExplanationPromptBuilder
from cropnet.services.api.app.services.llm.explanation_service import AgriculturalExplanationService
from cropnet.services.api.app.services.llm.guardrail_validator import GuardrailValidator
from cropnet.services.api.app.services.llm.template_fallback import TemplateFallbackGenerator
from cropnet.services.api.app.services.llm.ollama_client import OllamaClient


# ---------------------------------------------------------------------------
# Canonical Snapshot Payloads (Matching Shared Contract Specification 1.0)
# ---------------------------------------------------------------------------

def get_full_evidence_snapshot() -> Dict[str, Any]:
    """Canonical Example A: Full Evidence Verified Farm."""
    return {
        "contract_version": "1.0",
        "farm_id": "94a1f16e-bf0d-4d3f-9bd3-d63a57189818",
        "farm_name": "Baramati Model Farm",
        "owner_id": "00000000-0000-0000-0000-000000000001",
        "taluka": "Baramati",
        "district": "Pune",
        "state": "Maharashtra",
        "calculated_area_hectares": 2.5,
        "calculated_area_acres": 6.18,
        "snapshot_timestamp": "2026-11-08T11:45:00Z",
        "overall_evidence_overview": {
            "domains_available": 5,
            "domains_partially_available": 0,
            "domains_stale": 0,
            "domains_not_available": 0,
            "domains_insufficient_evidence": 0,
            "total_domains": 5,
            "actionable_summary": "Complete actionable evidence available across all 5 domains. No blocking data gaps."
        },
        "soil": {
            "availability_state": "AVAILABLE",
            "last_updated": "2026-10-15T09:30:00Z",
            "data_age_days": 24,
            "provenance": "MIXED_DUAL_SOURCE",
            "laboratory_name": "KVK Baramati Soil Testing Laboratory",
            "sample_depth": "0-15 cm",
            "key_indicators": {
                "soil_ph": 7.6,
                "organic_carbon_pct": 0.58,
                "electrical_conductivity_ds_m": 0.45,
                "available_nitrogen_kg_ha": 210.0,
                "available_phosphorus_kg_ha": 18.5,
                "available_potassium_kg_ha": 340.0,
                "soil_texture": "Clay Loam",
                "cation_exchange_capacity": 38.2
            },
            "missing_critical_parameters": [],
            "agronomic_notes": [
                "Farmer-confirmed physical laboratory test from KVK Baramati.",
                "Soil organic carbon is moderate (0.58%); nitrogen is low."
            ]
        },
        "water": {
            "availability_state": "AVAILABLE",
            "last_updated": "2026-09-20T14:15:00Z",
            "data_age_days": 49,
            "registered_sources_count": 1,
            "sources": [
                {
                    "source_id": "wsrc-001",
                    "source_type": "borewell",
                    "name": "North Field Borewell",
                    "seasonal_availability": "perennial",
                    "reliability": "reliable",
                    "irrigation_method": "drip",
                    "measured_capacity_lph": 12000.0,
                    "capacity_provenance": "MEASURED"
                }
            ],
            "laboratory_name": "Agricultural Water Testing Laboratory, Pune",
            "key_indicators": {
                "ph": 7.6,
                "electrical_conductivity_ds_m": 1.85,
                "tds_mg_l": 1184.0,
                "sar": 3.01,
                "sar_status": "AVAILABLE",
                "rsc_meq_l": -1.9,
                "rsc_status": "AVAILABLE",
                "chloride_meq_l": 4.8,
                "boron_mg_l": 0.65
            },
            "institutional_evaluations": [
                {
                    "parameter_key": "electrical_conductivity",
                    "parameter_name": "Electrical Conductivity (EC)",
                    "hazard_level": "MEDIUM",
                    "hazard_title": "Medium Salinity (Class 2 - Moderate Restriction)",
                    "standard_applied": "BIS IS 11624:2019",
                    "management_guidance": "Water can be used on soils with moderate drainage. Leaching fraction required for salt-sensitive crops."
                },
                {
                    "parameter_key": "sar",
                    "parameter_name": "Sodium Adsorption Ratio (SAR)",
                    "hazard_level": "LOW",
                    "hazard_title": "Low Sodium Hazard (S1 - Safe)",
                    "standard_applied": "BIS IS 11624:2019",
                    "management_guidance": "Can be used for irrigation on almost all soils with little danger of harmful sodification."
                }
            ],
            "missing_critical_parameters": []
        },
        "satellite": {
            "availability_state": "AVAILABLE",
            "observation_date": "2026-11-04T05:43:53Z",
            "observation_age_days": 4,
            "sensor": "Sentinel-2 L2A",
            "product_id": "S2B_MSIL2A_20261104T053009_N0513_R105_T43QDB",
            "canopy_ndvi": 0.68,
            "canopy_ndmi": 0.22,
            "composite_mean_ndvi": 0.52,
            "bare_soil_mean_ndvi": 0.28,
            "vegetation_coverage_percent": 68.4,
            "bare_soil_coverage_percent": 31.6,
            "cloud_masked_percent": 0.0,
            "valid_pixel_count": 250,
            "quality_status": "VALID_OBSERVATION",
            "is_small_farm_warning": False,
            "agronomic_interpretation": "Active photosynthetic canopy covering 68.4% of parcel. High vegetative biomass vigor (canopy NDVI 0.68).",
            "scientific_disclaimer": "Sentinel-2 NDVI and NDMI reflect surface optical reflectance (10m GSD). They are indirect canopy vigor indicators, NOT direct disease pathogen or yield diagnoses."
        },
        "weather": {
            "availability_state": "AVAILABLE",
            "last_updated": "2026-11-08T11:30:00Z",
            "current_weather": {
                "observation_time": "2026-11-08T11:20:00Z",
                "temperature_c": 28.4,
                "humidity_percent": 48.0,
                "precipitation_mm": 0.0,
                "wind_speed_ms": 3.1,
                "weather_condition": "Clear",
                "weather_description": "clear sky"
            },
            "forecast": {
                "forecast_days_count": 5,
                "next_48h_rain_expected_mm": 0.0,
                "temp_min_c": 17.5,
                "temp_max_c": 31.0,
                "weather_alerts": []
            },
            "climate_normals": {
                "annual_rainfall_mm": 560.0,
                "monsoon_rainfall_mm": 440.0,
                "mean_temperature_c": 24.5,
                "potential_water_stress_indicator": "Moderate seasonal winter dry spell"
            }
        },
        "crop_context": {
            "availability_state": "AVAILABLE",
            "evaluated_at": "2026-11-08T10:00:00Z",
            "target_season": "Rabi 2026-27",
            "taluka_resolved": "Baramati",
            "evaluated_crops_count": 3,
            "suitable_crops": [
                {
                    "crop_id": "wheat",
                    "common_name": "Wheat",
                    "marathi_name": "गहू",
                    "decision_state": "VERIFIED_SUITABLE",
                    "limiting_factors": [],
                    "irrigation_guidance": "Crown root initiation (CRI) irrigation critical at 21 DAS."
                },
                {
                    "crop_id": "chickpea",
                    "common_name": "Chickpea",
                    "marathi_name": "हरभरा",
                    "decision_state": "VERIFIED_SUITABLE",
                    "limiting_factors": [],
                    "irrigation_guidance": "Branching and pod initiation irrigations recommended."
                }
            ],
            "conditionally_suitable_crops": [
                {
                    "crop_id": "onion",
                    "common_name": "Rabi Onion",
                    "marathi_name": "कांदा",
                    "decision_state": "CONDITIONALLY_SUITABLE_PENDING_DATA",
                    "limiting_factors": [
                        "Water EC 1.85 dS/m creates moderate salinity stress for onion in Vertisols"
                    ],
                    "irrigation_guidance": "Frequent light irrigations required to minimize salinity stress."
                }
            ],
            "disqualified_crops": [],
            "abstain_crops": [],
            "top_limiting_factors": [
                "Water EC 1.85 dS/m requires leaching fraction for salt-sensitive crops"
            ],
            "pending_followup_questions_count": 1
        },
        "governance_notice": "CropNet AI provides independent, evidence-gated agricultural domain summaries. In accordance with institutional agricultural guidelines, no universal health score is computed."
    }


def get_missing_evidence_snapshot() -> Dict[str, Any]:
    """Canonical Example B: Brand New Farm with Zero Recorded Evidence."""
    return {
        "contract_version": "1.0",
        "farm_id": "e4b2d189-9a74-4b5c-897b-3d6e5c9f1a23",
        "farm_name": "New Registered Parcel",
        "owner_id": "00000000-0000-0000-0000-000000000001",
        "taluka": "Indapur",
        "district": "Pune",
        "state": "Maharashtra",
        "calculated_area_hectares": 1.2,
        "calculated_area_acres": 2.97,
        "snapshot_timestamp": "2026-11-08T11:45:00Z",
        "overall_evidence_overview": {
            "domains_available": 0,
            "domains_partially_available": 0,
            "domains_stale": 0,
            "domains_not_available": 5,
            "domains_insufficient_evidence": 0,
            "total_domains": 5,
            "actionable_summary": "Zero evidence recorded for this farm. Immediate actions required: 1) Run soil analysis, 2) Register water source, 3) Sync satellite."
        },
        "soil": {
            "availability_state": "NOT_AVAILABLE",
            "last_updated": None,
            "data_age_days": None,
            "provenance": None,
            "laboratory_name": None,
            "sample_depth": None,
            "key_indicators": {
                "soil_ph": None,
                "organic_carbon_pct": None,
                "electrical_conductivity_ds_m": None,
                "available_nitrogen_kg_ha": None,
                "available_phosphorus_kg_ha": None,
                "available_potassium_kg_ha": None,
                "soil_texture": None,
                "cation_exchange_capacity": None
            },
            "missing_critical_parameters": [
                "soil_ph", "organic_carbon", "nitrogen", "phosphorus", "potassium", "texture"
            ],
            "agronomic_notes": [
                "No soil profile has been generated or uploaded for this farm.",
                "Action required: Upload a certified laboratory soil test report or trigger spatial analysis."
            ]
        },
        "water": {
            "availability_state": "NOT_AVAILABLE",
            "last_updated": None,
            "data_age_days": None,
            "registered_sources_count": 0,
            "sources": [],
            "laboratory_name": None,
            "key_indicators": {
                "ph": None,
                "electrical_conductivity_ds_m": None,
                "tds_mg_l": None,
                "sar": None,
                "sar_status": "UNAVAILABLE",
                "rsc_meq_l": None,
                "rsc_status": "UNAVAILABLE",
                "chloride_meq_l": None,
                "boron_mg_l": None
            },
            "institutional_evaluations": [],
            "missing_critical_parameters": ["water_source", "electrical_conductivity", "sar", "rsc"]
        },
        "satellite": {
            "availability_state": "NOT_AVAILABLE",
            "observation_date": None,
            "observation_age_days": None,
            "sensor": "Sentinel-2 L2A",
            "canopy_ndvi": None,
            "canopy_ndmi": None,
            "composite_mean_ndvi": None,
            "bare_soil_mean_ndvi": None,
            "vegetation_coverage_percent": None,
            "bare_soil_coverage_percent": None,
            "cloud_masked_percent": None,
            "valid_pixel_count": 0,
            "quality_status": None,
            "is_small_farm_warning": False,
            "agronomic_interpretation": "No satellite synchronization has been performed for this farm boundary.",
            "scientific_disclaimer": "Sentinel-2 NDVI and NDMI reflect surface optical reflectance (10m GSD). They are indirect canopy vigor indicators, NOT direct disease pathogen or yield diagnoses."
        },
        "weather": {
            "availability_state": "NOT_AVAILABLE",
            "last_updated": None,
            "current_weather": {},
            "forecast": {},
            "climate_normals": {}
        },
        "crop_context": {
            "availability_state": "NOT_AVAILABLE",
            "evaluated_at": None,
            "target_season": None,
            "taluka_resolved": "Indapur",
            "evaluated_crops_count": 0,
            "suitable_crops": [],
            "conditionally_suitable_crops": [],
            "disqualified_crops": [],
            "abstain_crops": [],
            "top_limiting_factors": ["No environmental farm context available to evaluate crop suitability."],
            "pending_followup_questions_count": 0
        },
        "governance_notice": "CropNet AI provides independent, evidence-gated agricultural domain summaries. In accordance with institutional agricultural guidelines, no universal health score is computed."
    }


def get_stale_evidence_snapshot() -> Dict[str, Any]:
    """Canonical Example C: Farm with Historical Data Exceeding Validity Thresholds."""
    return {
        "contract_version": "1.0",
        "farm_id": "c8d2e3f4-5678-4abc-9def-0123456789ab",
        "farm_name": "Sangamner Pomegranate Orchard",
        "owner_id": "00000000-0000-0000-0000-000000000001",
        "taluka": "Sangamner",
        "district": "Ahmednagar",
        "state": "Maharashtra",
        "calculated_area_hectares": 3.1,
        "calculated_area_acres": 7.66,
        "snapshot_timestamp": "2026-11-08T11:45:00Z",
        "overall_evidence_overview": {
            "domains_available": 0,
            "domains_partially_available": 0,
            "domains_stale": 5,
            "domains_not_available": 0,
            "domains_insufficient_evidence": 0,
            "total_domains": 5,
            "actionable_summary": "All recorded farm evidence is stale (>30 days for satellite, >1 year for water, >3 years for soil). Re-synchronization recommended."
        },
        "soil": {
            "availability_state": "STALE",
            "last_updated": "2022-08-10T10:00:00Z",
            "data_age_days": 1551,
            "provenance": "LABORATORY_CONFIRMED",
            "laboratory_name": "Rahuri Agricultural University Soil Lab",
            "sample_depth": "0-30 cm",
            "key_indicators": {
                "soil_ph": 8.1,
                "organic_carbon_pct": 0.42,
                "electrical_conductivity_ds_m": 0.62,
                "soil_texture": "Clay"
            },
            "missing_critical_parameters": [],
            "agronomic_notes": [
                "Soil laboratory test report is over 3 years old (1551 days). Nutrient levels may have shifted significantly."
            ]
        },
        "water": {
            "availability_state": "STALE",
            "last_updated": "2025-06-15T11:30:00Z",
            "data_age_days": 511,
            "registered_sources_count": 1,
            "sources": [
                {
                    "source_id": "wsrc-088",
                    "source_type": "open_well",
                    "name": "East Perimeter Well",
                    "seasonal_availability": "seasonal_post_monsoon",
                    "reliability": "moderate",
                    "irrigation_method": "drip",
                    "measured_capacity_lph": 8000.0,
                    "capacity_provenance": "FARMER_REPORTED"
                }
            ],
            "laboratory_name": "District Water Testing Lab, Ahmednagar",
            "key_indicators": {
                "ph": 7.9,
                "electrical_conductivity_ds_m": 2.2,
                "tds_mg_l": 1408.0,
                "sar": 4.1
            },
            "institutional_evaluations": [
                {
                    "parameter_key": "electrical_conductivity",
                    "parameter_name": "Electrical Conductivity (EC)",
                    "hazard_level": "MEDIUM",
                    "hazard_title": "Medium Salinity (Class 2 - Moderate Restriction)",
                    "standard_applied": "BIS IS 11624:2019",
                    "management_guidance": "Test is 511 days old. Groundwater salinity fluctuates after monsoon recharge; re-testing required."
                }
            ],
            "missing_critical_parameters": []
        },
        "satellite": {
            "availability_state": "STALE",
            "observation_date": "2026-09-12T05:40:02Z",
            "observation_age_days": 57,
            "sensor": "Sentinel-2 L2A",
            "canopy_ndvi": 0.44,
            "canopy_ndmi": 0.08,
            "composite_mean_ndvi": 0.38,
            "bare_soil_mean_ndvi": 0.25,
            "vegetation_coverage_percent": 35.2,
            "bare_soil_coverage_percent": 64.8,
            "cloud_masked_percent": 0.0,
            "valid_pixel_count": 310,
            "quality_status": "VALID_OBSERVATION",
            "is_small_farm_warning": False,
            "agronomic_interpretation": "Satellite observation is 57 days old (>30 days). Historical canopy vigor may not reflect current stage.",
            "scientific_disclaimer": "Sentinel-2 NDVI and NDMI reflect surface optical reflectance (10m GSD). They are indirect canopy vigor indicators, NOT direct disease pathogen or yield diagnoses."
        },
        "weather": {
            "availability_state": "STALE",
            "last_updated": "2026-11-08T06:00:00Z",
            "current_weather": {
                "temperature_c": 21.0,
                "humidity_percent": 65.0,
                "precipitation_mm": 0.0,
                "weather_condition": "Haze"
            },
            "forecast": {},
            "climate_normals": {
                "annual_rainfall_mm": 520.0
            }
        },
        "crop_context": {
            "availability_state": "STALE",
            "evaluated_at": "2025-07-01T08:00:00Z",
            "target_season": "Kharif 2025",
            "taluka_resolved": "Sangamner",
            "evaluated_crops_count": 1,
            "suitable_crops": [],
            "conditionally_suitable_crops": [
                {
                    "crop_id": "pomegranate",
                    "common_name": "Pomegranate",
                    "marathi_name": "डाळिंब",
                    "decision_state": "CONDITIONALLY_SUITABLE_PENDING_DATA",
                    "limiting_factors": [
                        "Evaluation performed for previous cropping year (>180 days old)"
                    ],
                    "irrigation_guidance": "Mrungh Bahar flowering schedule requires current water test verification."
                }
            ],
            "disqualified_crops": [],
            "abstain_crops": [],
            "top_limiting_factors": [
                "Stale historical evaluation: Run updated crop suitability evaluation for current season."
            ],
            "pending_followup_questions_count": 1
        },
        "governance_notice": "CropNet AI provides independent, evidence-gated agricultural domain summaries. In accordance with institutional agricultural guidelines, no universal health score is computed."
    }


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def engine():
    return DeterministicDecisionEngine()


@pytest.fixture
def service(engine):
    return AgriculturalExplanationService(decision_engine=engine)


# ===========================================================================
# 1. Multi-Domain Snapshot Context Ingestion by FarmContextBuilder
# ===========================================================================

def test_farm_context_builder_ingests_full_evidence_snapshot():
    """Verify FarmContextBuilder consumes Example A full snapshot across all 5 domains."""
    snap = get_full_evidence_snapshot()
    ctx = FarmContextBuilder.build_farm_context(
        farm_id=snap["farm_id"],
        snapshot=snap,
        query="Can I grow wheat with my current soil and water?",
        language="en"
    )

    # 1. Evidence overview presence
    assert "evidence_overview" in ctx or "overall_evidence_overview" in ctx
    eo = ctx.get("evidence_overview") or ctx.get("overall_evidence_overview")
    assert eo["domains_available"] == 5
    assert eo["total_domains"] == 5

    # 2. Soil domain
    soil = ctx["soil_intelligence"]
    assert soil["availability_state"] == "AVAILABLE"
    assert soil["provenance"] == "MIXED_DUAL_SOURCE"
    assert soil["key_indicators"]["soil_ph"] == 7.6
    assert soil["key_indicators"]["available_nitrogen_kg_ha"] == 210.0

    # 3. Water domain
    water = ctx["water_intelligence"]
    assert water["availability_state"] == "AVAILABLE"
    assert water["key_indicators"]["electrical_conductivity_ds_m"] == 1.85
    assert water["key_indicators"]["sar"] == 3.01
    assert len(water["institutional_evaluations"]) >= 1

    # 4. Satellite domain (pure Class 4 canopy segregated from bare soil)
    sat = ctx["satellite_intelligence"]
    assert sat["canopy_ndvi"] == 0.68
    assert sat["bare_soil_mean_ndvi"] == 0.28
    assert sat["scientific_disclaimer"] is not None

    # 5. Weather domain
    wx = ctx["weather_intelligence"]
    assert wx["current_weather"]["temperature_c"] == 28.4


def test_farm_context_builder_ingests_missing_evidence_snapshot():
    """Verify FarmContextBuilder handles missing domains honestly with zero manufactured values."""
    snap = get_missing_evidence_snapshot()
    ctx = FarmContextBuilder.build_farm_context(
        farm_id=snap["farm_id"],
        snapshot=snap,
        query="What is my soil and water condition?",
        language="en"
    )

    soil = ctx["soil_intelligence"]
    assert soil["availability_state"] == "NOT_AVAILABLE"
    # Never fabricated default values
    assert "soil_ph" not in soil.get("key_indicators", {})
    assert len(soil.get("missing_critical_parameters", [])) >= 5

    water = ctx["water_intelligence"]
    assert water["availability_state"] == "NOT_AVAILABLE"
    assert len(water.get("sources", [])) == 0

    sat = ctx["satellite_intelligence"]
    assert sat["availability_state"] == "NOT_AVAILABLE"
    assert sat.get("canopy_ndvi") is None


def test_farm_context_builder_ingests_stale_evidence_snapshot():
    """Verify FarmContextBuilder tracks stale evidence states and observation age metadata."""
    snap = get_stale_evidence_snapshot()
    ctx = FarmContextBuilder.build_farm_context(
        farm_id=snap["farm_id"],
        snapshot=snap,
        query="Is my historical soil test still valid?",
        language="en"
    )

    soil = ctx["soil_intelligence"]
    assert soil["availability_state"] == "STALE"
    assert soil["data_age_days"] == 1551

    water = ctx["water_intelligence"]
    assert water["availability_state"] == "STALE"
    assert water["data_age_days"] == 511

    sat = ctx["satellite_intelligence"]
    assert sat["availability_state"] == "STALE"
    assert sat["observation_age_days"] == 57


def test_farm_context_builder_compact_token_budget():
    """Verify multi-domain compact context stays well below LLM context overflow (< 1500 tokens)."""
    snap = get_full_evidence_snapshot()
    ctx = FarmContextBuilder.build_farm_context(
        farm_id=snap["farm_id"],
        snapshot=snap,
        query="Can I grow chickpea with clay loam soil and borewell water?",
        language="en"
    )
    dumped = json.dumps(ctx, ensure_ascii=False)
    # 1 token is roughly 4 characters in English JSON
    estimated_tokens = len(dumped) / 3.5
    assert estimated_tokens < 1200, f"Context exceeded token budget: {estimated_tokens:.1f} tokens"


def test_farm_context_builder_domain_classification():
    """Verify query domain routing including cross-domain detection."""
    # Cross-domain inquiry (soil + water)
    cd1 = FarmContextBuilder.classify_query_domain("Can I grow chickpea with clay soil and borewell water?")
    assert cd1 == "cross_domain_inquiry"

    # Cross-domain in Marathi (soil + water + crop)
    cd2 = FarmContextBuilder.classify_query_domain("काळी माती आणि विहिरीच्या पाण्याने कांदा पिकेल का?")
    assert cd2 == "cross_domain_inquiry"

    # Single domain inquiries
    assert FarmContextBuilder.classify_query_domain("What is my soil pH and organic carbon?") == "soil_inquiry"
    assert FarmContextBuilder.classify_query_domain("Is borewell water EC safe for irrigation?") == "water_inquiry"
    assert FarmContextBuilder.classify_query_domain("Explain Sentinel-2 canopy NDVI vigor") == "satellite_inquiry"
    assert FarmContextBuilder.classify_query_domain("What is the 5-day weather forecast?") == "weather_inquiry"


# ===========================================================================
# 2. Multi-Domain Agronomic Dialogue & Explanation (English & Marathi)
# ===========================================================================

def test_explain_decision_with_multi_domain_snapshot(engine, service):
    """Verify explanation generation grounded in multi-domain snapshot evidence."""
    snap = get_full_evidence_snapshot()

    # Create deterministic decision
    ctx_input = FarmContextInput(
        taluka="Baramati",
        soil_ph=7.6,
        electrical_conductivity_ds_m=1.85,
        drainage="moderate",
        irrigation_source="borewell",
        target_season="rabi",
        target_crops=["wheat"],
        soil_data_provenance=SoilDataProvenance.LABORATORY_MEASURED
    )
    decision = engine.evaluate_farm(ctx_input)

    req = ExplainDecisionRequest(
        decision_id=decision.decision_id,
        language="en",
        focus_crop="wheat"
    )
    mock_payload = json.dumps({
        "title": "Baramati Wheat Cultivation Advisory",
        "direct_answer": "Wheat is suitable in Baramati with irrigation EC 1.85 dS/m under moderate drainage.",
        "what_this_means": "Soil pH 7.6 and water salinity are favorable for Rabi wheat.",
        "what_needs_attention": ["Schedule CRI irrigation at 21 DAS"],
        "next_steps": ["Monitor canopy NDVI vigor"]
    })
    with patch.object(service.ollama, "chat_completion", return_value={"success": True, "content": mock_payload, "error": None}):
        resp = service.explain_decision(req, snapshot=snap)

    assert resp is not None
    assert resp.decision_id == decision.decision_id
    assert resp.validation_passed is True

    # Card verification
    card = resp.structured_card
    assert card is not None
    assert "wheat" in card.title.lower() or "baramati" in card.title.lower()

    # Verified observations must contain multi-domain pills
    obs_params = [o.parameter.lower() for o in card.observations]
    assert any("ph" in p for p in obs_params)
    assert any("salinity" in p or "ec" in p for p in obs_params)
    assert any("canopy" in p or "ndvi" in p for p in obs_params)


def test_explain_decision_marathi_vernacular_with_snapshot(engine, service):
    """Verify authentic Marathi terminology and structure in multi-domain explanation."""
    snap = get_full_evidence_snapshot()

    ctx_input = FarmContextInput(
        taluka="Baramati",
        soil_ph=7.6,
        electrical_conductivity_ds_m=1.85,
        drainage="moderate",
        irrigation_source="borewell",
        target_season="rabi",
        target_crops=["wheat"],
        soil_data_provenance=SoilDataProvenance.LABORATORY_MEASURED
    )
    decision = engine.evaluate_farm(ctx_input)

    req = ExplainDecisionRequest(
        decision_id=decision.decision_id,
        language="mr",
        focus_crop="wheat"
    )
    mock_mr_payload = json.dumps({
        "title": "बारामती गहू पीक सल्ला",
        "direct_answer": "बारामती तालुक्यातील तुमच्या काळ्या मातीत गहू पीक योग्य आहे. मातीचा सामू 7.6 अनुकूल आहे.",
        "what_this_means": "मातीचा सामू आणि विहिरीची पाण्याची क्षारता संतुलित आहे.",
        "what_needs_attention": ["मुकुट मूळ फुटण्याच्या अवस्थेत 21 दिवसांनी सिंचन द्या"],
        "next_steps": ["पेरणीपूर्वी बियाण्यास बीजप्रक्रिया करा"]
    })
    with patch.object(service.ollama, "chat_completion", return_value={"success": True, "content": mock_mr_payload, "error": None}):
        resp = service.explain_decision(req, snapshot=snap)

    assert resp is not None
    assert resp.language == "mr"
    card = resp.structured_card
    assert card is not None

    # Marathi agricultural terminology verification
    assert "गहू" in card.title or "बारामती" in card.title
    obs_params = [o.parameter for o in card.observations]
    assert any("सामू" in p for p in obs_params)
    assert any("क्षारता" in p for p in obs_params)


def test_explain_missing_evidence_honest_disclosure(engine, service):
    """Verify AI honestly discloses missing lab tests and recommends testing without inventing data."""
    snap = get_missing_evidence_snapshot()

    ctx_input = FarmContextInput(
        taluka="Indapur",
        soil_ph=None,
        target_season="rabi",
        target_crops=["chickpea"],
        soil_data_provenance=SoilDataProvenance.SPATIALLY_ESTIMATED_ISRIC
    )
    decision = engine.evaluate_farm(ctx_input)

    req = ExplainDecisionRequest(
        decision_id=decision.decision_id,
        language="en"
    )
    mock_missing_payload = json.dumps({
        "title": "Indapur Farm Soil & Water Test Verification",
        "direct_answer": "No laboratory soil or water test is recorded for this farm; pending verification.",
        "what_this_means": "Environmental farm evidence is insufficient to confirm suitability without laboratory tests.",
        "what_needs_attention": ["Upload certified laboratory soil test report"],
        "next_steps": ["Collect 0-15 cm composite soil sample"]
    })
    with patch.object(service.ollama, "chat_completion", return_value={"success": True, "content": mock_missing_payload, "error": None}):
        resp = service.explain_decision(req, snapshot=snap)

    assert resp is not None
    card = resp.structured_card
    assert card is not None
    # Must communicate need for testing or insufficient evidence
    combined = (resp.explanation_text + " " + card.direct_answer + " " + card.what_this_means).lower()
    assert any(k in combined for k in ["pending", "diagnostic", "test", "verification", "insufficient"])


# ===========================================================================
# 3. Agronomic Guardrails & Safeguards
# ===========================================================================

def test_guardrail_validator_rejects_suitability_reversal(engine):
    """Guardrail: Claiming a disqualified crop is suitable must be rejected."""
    ctx_input = FarmContextInput(
        taluka="Indapur",
        soil_ph=7.5,
        electrical_conductivity_ds_m=3.5, # Disqualifies chickpea (EC >= 2.0)
        drainage="well_drained",
        irrigation_source="drip",
        target_season="rabi",
        target_crops=["chickpea"],
        soil_data_provenance=SoilDataProvenance.LABORATORY_MEASURED
    )
    decision = engine.evaluate_farm(ctx_input)
    assert decision.crop_outcomes[0].is_disqualified is True

    # Attempt to reverse decision state in generated text
    fake_text = "Good news! Chickpea is highly suitable and recommended for your farm. Plant it right now."
    res = GuardrailValidator.validate(fake_text, decision, language="en")
    assert res.is_valid is False
    assert any("decision state contradiction" in v.lower() for v in res.violations)


def test_guardrail_validator_rejects_fabricated_fertilizer_dosages(engine):
    """Guardrail: Chemical fertilizer dosages not in payload must be rejected."""
    ctx_input = FarmContextInput(
        taluka="Baramati",
        soil_ph=7.2,
        target_season="rabi",
        target_crops=["wheat"],
        soil_data_provenance=SoilDataProvenance.LABORATORY_MEASURED
    )
    decision = engine.evaluate_farm(ctx_input)

    fake_text = "Wheat is suitable. Apply 120 kg urea and 60 kg DAP per hectare at sowing."
    res = GuardrailValidator.validate(fake_text, decision, language="en")
    assert res.is_valid is False
    assert any("fertilizer" in v.lower() for v in res.violations)


def test_guardrail_validator_rejects_chemical_spray_measurements(engine, service):
    """Guardrail: Chemical pesticide/fungicide spray measurements (e.g. ml/L) must be rejected."""
    ctx_input = FarmContextInput(
        taluka="Baramati",
        soil_ph=7.2,
        target_season="rabi",
        target_crops=["pomegranate"],
        soil_data_provenance=SoilDataProvenance.LABORATORY_MEASURED
    )
    decision = engine.evaluate_farm(ctx_input)

    fake_spray_text = (
        "Pomegranate needs protection. Spray 2.5 ml per liter chlorpyrifos and 2 gm per liter copper oxychloride."
    )
    res = service.validate_explanation_guardrails(fake_spray_text, decision, language="en")
    assert res.is_valid is False
    assert any("spray measurement" in v.lower() for v in res.violations)


def test_guardrail_validator_rejects_satellite_pathogen_diagnosis_without_disclaimer(engine, service):
    """Guardrail: Diagnosing disease pathogens from satellite optical reflectance alone must be rejected."""
    ctx_input = FarmContextInput(
        taluka="Baramati",
        soil_ph=7.4,
        target_season="rabi",
        target_crops=["pomegranate"],
        soil_data_provenance=SoilDataProvenance.LABORATORY_MEASURED
    )
    decision = engine.evaluate_farm(ctx_input)

    # Claim satellite NDVI diagnoses wilt pathogen without scientific disclaimer
    fake_sat_text = "Sentinel-2 satellite NDVI shows your pomegranate orchard has Fusarium wilt bacterial blight."
    res = service.validate_explanation_guardrails(
        fake_sat_text,
        decision,
        language="en",
        user_message="Can satellite diagnose blight in my orchard?"
    )
    assert res.is_valid is False
    assert any("satellite pathogen diagnosis" in v.lower() for v in res.violations)


def test_guardrail_validator_accepts_satellite_pathogen_with_scientific_disclaimer(engine, service):
    """Guardrail: Mentioning disease with mandatory scientific disclaimer must be accepted."""
    ctx_input = FarmContextInput(
        taluka="Baramati",
        soil_ph=7.4,
        target_season="rabi",
        target_crops=["pomegranate"],
        soil_data_provenance=SoilDataProvenance.LABORATORY_MEASURED
    )
    decision = engine.evaluate_farm(ctx_input)

    compliant_sat_text = (
        "Optical satellite imagery shows canopy NDVI vigor is 0.68. "
        "Sentinel-2 NDVI and NDMI reflect surface optical reflectance (10m GSD). "
        "They are indirect canopy vigor indicators, NOT direct disease pathogen or yield diagnoses. "
        "Satellite imagery cannot diagnose specific root rot or fungal pathogens."
    )
    res = service.validate_explanation_guardrails(
        compliant_sat_text,
        decision,
        language="en",
        user_message="Can satellite detect wilt?",
        farm_context={"satellite_intelligence": {"canopy_ndvi": 0.68}}
    )
    assert res.is_valid is True


# ===========================================================================
# 4. Multi-Turn Conversation Continuity & Diagnostic Follow-up Isolation
# ===========================================================================

def test_multiturn_detect_answer_intent_drainage(service):
    """Verify natural language answers to drainage question are detected."""
    pending = [
        FollowUpQuestion(
            question_id="q_drainage",
            target_parameter="drainage",
            priority=1,
            question_type="choice",
            question_text_en="How is your field drainage?",
            question_text_mr="पाण्याचा निचरा कसा आहे?",
            options=["good", "poor"],
            agronomic_rationale="Vertisol drainage check"
        )
    ]

    # English: poor drainage
    d1 = service.detect_answer_intent("Water stays standing in the field for 2 days after watering", pending)
    assert d1.get("drainage") == "poor"
    assert d1.get("water_table_depth") == "shallow"

    # English: good drainage
    d2 = service.detect_answer_intent("There is no standing water, it drains quickly", pending)
    assert d2.get("drainage") == "good"
    assert d2.get("water_table_depth") == "deep"

    # Marathi: poor drainage
    d3 = service.detect_answer_intent("शेतात पाणी २ दिवस साचून राहते, निचरा होत नाही", pending)
    assert d3.get("drainage") == "poor"

    # Marathi: good drainage
    d4 = service.detect_answer_intent("शेतात पाणी साचत नाही, निचरा चांगला होतो", pending)
    assert d4.get("drainage") == "good"


def test_multiturn_detect_answer_intent_salinity_and_depth(service):
    """Verify intent detection for salinity, depth, and well depth."""
    pending = [
        FollowUpQuestion(
            question_id="q_depth",
            target_parameter="soil_depth_cm",
            priority=2,
            question_type="numeric",
            question_text_en="Depth?",
            question_text_mr="मातीची खोली किती आहे?",
            options=[],
            agronomic_rationale="Soil depth determination"
        ),
        FollowUpQuestion(
            question_id="q_sal",
            target_parameter="electrical_conductivity_ds_m",
            priority=1,
            question_type="numeric",
            question_text_en="Salinity?",
            question_text_mr="पाणी क्षारयुक्त आहे का?",
            options=[],
            agronomic_rationale="Salinity check"
        ),
        FollowUpQuestion(
            question_id="q_well",
            target_parameter="well_depth_m",
            priority=2,
            question_type="numeric",
            question_text_en="Well depth?",
            question_text_mr="विहिरीची खोली किती आहे?",
            options=[],
            agronomic_rationale="Well depth check"
        )
    ]

    # Salinity
    d1 = service.detect_answer_intent("The borewell water is sweet and low in salt", pending)
    assert d1.get("electrical_conductivity_ds_m") == 0.6

    d2 = service.detect_answer_intent("पाणी थोडे क्षारयुक्त व खारट आहे", pending)
    assert d2.get("electrical_conductivity_ds_m") == 2.5

    # Depth
    d3 = service.detect_answer_intent("जमीन काळी भारी आणि खोल आहे", pending)
    assert d3.get("soil_depth_cm") == 75.0


def test_multiturn_conversation_deterministic_reevaluation_and_question_isolation(engine, service):
    """
    Test full multi-turn dialogue cycle:
    Turn 1: Initial evaluation returns conditionally suitable with pending drainage question.
    Turn 2: Farmer answers 'Water stays for 2 days'.
    Service detects poor drainage, deterministically re-evaluates, isolates answered question,
    and updates guidance.
    """
    # 1. Initial evaluation
    ctx_input = FarmContextInput(
        taluka="Baramati",
        soil_ph=7.8,
        soil_texture="clay",
        target_season="rabi",
        target_crops=["pomegranate"],
        soil_data_provenance=SoilDataProvenance.LABORATORY_MEASURED
    )
    decision = engine.evaluate_farm(ctx_input)
    assert decision.crop_outcomes[0].decision_state in (
        DecisionState.CONDITIONALLY_SUITABLE_PENDING_DATA,
        DecisionState.REGIONAL_SCREENING_ONLY
    )
    initial_q_count = len(decision.follow_up_questions)
    assert initial_q_count >= 1

    # 2. Conversational turn: farmer reports poor drainage
    conv_req = ConversationRequest(
        decision_id=decision.decision_id,
        message="In our orchard, water stays standing for 2 days after canal irrigation.",
        language="en",
        history=[
            ConversationMessage(role="user", content="Is pomegranate suitable for my orchard?"),
            ConversationMessage(role="assistant", content="Pomegranate requires verification of drainage.")
        ]
    )

    mock_llm_json = json.dumps({
        "title": "Baramati Orchard Drainage Advisory",
        "direct_answer": "Waterlogging for 2 days indicates poor drainage, which restricts pomegranate cultivation.",
        "what_this_means": "Vertisol black soils with poor drainage cause root asphyxiation and collar rot in pomegranate.",
        "what_needs_attention": ["Install field drainage tile channels"],
        "next_steps": ["Consult local agricultural officer"]
    })
    with patch.object(service.ollama, "chat_completion", return_value={"success": True, "content": mock_llm_json, "error": None}):
        resp = service.handle_conversation(conv_req)

    assert resp is not None
    assert resp.validation_passed is True

    # 3. Verify deterministic re-evaluation occurred in session store
    updated_decision = engine.get_decision(resp.decision_id)
    assert updated_decision is not None
    # Drainage parameter was recorded
    assert updated_decision.farm_context.drainage == "poor"

    # 4. In Vertisol clay with poor drainage, pomegranate has severe root asphyxiation / collar rot risk
    outcome = updated_decision.crop_outcomes[0]
    assert any("drain" in f.lower() or "ill-drained" in f.lower() for f in outcome.limiting_factors)

    # 5. Question isolation: drainage question has been answered and is no longer pending
    pending_params = [q.target_parameter for q in resp.follow_up_questions]
    assert "drainage" not in pending_params


def test_multiturn_conversation_marathi_continuity(engine, service):
    """Verify Marathi multi-turn diagnostic response re-evaluates deterministically."""
    ctx_input = FarmContextInput(
        taluka="Baramati",
        soil_ph=7.8,
        soil_texture="clay",
        target_season="rabi",
        target_crops=["pomegranate"],
        soil_data_provenance=SoilDataProvenance.LABORATORY_MEASURED
    )
    decision = engine.evaluate_farm(ctx_input)

    conv_req = ConversationRequest(
        decision_id=decision.decision_id,
        message="शेतात पाणी २ दिवस साचून राहते, निचरा होत नाही.",
        language="mr",
        history=[]
    )

    mock_mr_json = json.dumps({
        "title": "डाळिंब पीक पाणी निचरा मर्यादा",
        "direct_answer": "शेतात २ दिवस पाणी साचून राहिल्यास डाळिंब पीक अयोग्य ठरते. काळ्या मातीत पाण्याचा निचरा योग्य असणे अनिवार्य आहे.",
        "what_this_means": "खराब निचऱ्यामुळे झाडांची मुळे गुदमरतात आणि मर रोगाचा धोका वाढतो.",
        "what_needs_attention": ["शेतात चर खोदून अतिरिक्त पाण्याचा निचरा करा"],
        "next_steps": ["हलक्या निचऱ्याच्या जमिनीत डाळिंब लागवडीचा विचार करा"]
    })
    with patch.object(service.ollama, "chat_completion", return_value={"success": True, "content": mock_mr_json, "error": None}):
        resp = service.handle_conversation(conv_req)

    assert resp is not None
    assert resp.language == "mr"
    card = resp.structured_card
    assert card is not None
    assert "अयोग्य" in card.direct_answer or "मर्यादा" in card.direct_answer or "निचरा" in card.direct_answer


# ===========================================================================
# 5. Live / Mocked Qwen3:8B Verification
# ===========================================================================

def test_qwen3_8b_live_or_verified_fallback(engine, service):
    """
    Test end-to-end execution with local Ollama Qwen3:8B if available,
    or verify structured fallback response if offline.
    """
    snap = get_full_evidence_snapshot()
    ctx_input = FarmContextInput(
        taluka="Baramati",
        soil_ph=7.6,
        electrical_conductivity_ds_m=1.85,
        target_season="rabi",
        target_crops=["wheat"],
        soil_data_provenance=SoilDataProvenance.LABORATORY_MEASURED
    )
    decision = engine.evaluate_farm(ctx_input)

    req = ExplainDecisionRequest(
        decision_id=decision.decision_id,
        language="en",
        focus_crop="wheat"
    )

    ollama = OllamaClient()
    resp = service.explain_decision(req, snapshot=snap)

    assert resp is not None
    assert resp.validation_passed is True
    assert resp.generation_source in ("llm_qwen3_8b", "deterministic_fallback")

    # If live Ollama is running and answered
    if resp.generation_source == "llm_qwen3_8b":
        # Must not contain markdown headings
        assert "###" not in resp.explanation_text
        assert "####" not in resp.explanation_text
        # Structured card fields must be populated
        assert resp.structured_card.title
        assert resp.structured_card.direct_answer
        assert resp.structured_card.what_this_means
    else:
        # Fallback card verified
        assert resp.structured_card is not None
        assert "CropNet" in resp.structured_card.title or "Wheat" in resp.structured_card.title
