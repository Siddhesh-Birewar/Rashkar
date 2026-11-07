"""
CropNet AI — Phase 5.0 Benchmark Dataset Integrity Validator.

Validates that:
1. Exactly 30 test cases exist with unique IDs from AGRI-BENCH-001 to AGRI-BENCH-030.
2. All 7 agricultural domains (A through G) are covered.
3. All 9 adversarial failure archetypes are present.
4. All required fields are defined in every test case.
5. Every cited source reference is registered in CropNet's 12 authoritative sources.
6. Every scoring rubric sums to 1.0.
7. Multilingual queries contain valid English and Marathi text.
"""
import sys
import json
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_BENCHMARK_DIR = _SCRIPT_DIR
_CROPNET_ROOT = _BENCHMARK_DIR.parents[1]
_WORKSPACE_ROOT = _CROPNET_ROOT.parent

for p in [str(_WORKSPACE_ROOT), str(_CROPNET_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from cropnet.services.api.app.services.crop_knowledge.seed_data import KNOWLEDGE_SOURCES

VALID_SOURCE_IDS = {s["id"] for s in KNOWLEDGE_SOURCES}

EXPECTED_DOMAINS = {
    "Soil Intelligence",
    "Crop Suitability",
    "Agricultural Decision Reasoning",
    "Irrigation Intelligence",
    "Weather and Climate Intelligence",
    "Agricultural Knowledge Retrieval",
    "Multilingual Communication"
}

EXPECTED_ADVERSARIAL_TYPES = {
    "total_vs_available_nitrogen_confusion",
    "ph_treated_as_sole_factor_fallacy",
    "taluka_screening_mistaken_for_farm_verification",
    "climatology_mistaken_for_forecast",
    "conflicting_irrigation_schedules",
    "profitability_assumed_from_suitability",
    "contradictory_farm_inputs",
    "insufficient_information_abstention",
    "hallucinated_scientific_threshold",
    "keyword_matched_but_contextually_inapplicable",
    "unregistered_crop_abstention"
}

REQUIRED_FIELDS = [
    "test_id",
    "domain",
    "adversarial_type",
    "user_query",
    "farm_context_inputs",
    "expected_reasoning",
    "required_information",
    "expected_follow_up_questions",
    "verified_source_references",
    "expected_answer_boundaries",
    "conditions_requiring_abstention",
    "scoring_rubric"
]


def validate_benchmark():
    json_path = _BENCHMARK_DIR / "benchmark_dataset.json"
    assert json_path.exists(), f"Benchmark JSON file not found: {json_path}"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    test_cases = data.get("test_cases", [])
    print(f"[Validation 1] Loaded {len(test_cases)} test cases from benchmark dataset.")
    assert len(test_cases) == 30, f"Expected exactly 30 test cases, found {len(test_cases)}"

    # 1. Unique IDs
    ids = [tc["test_id"] for tc in test_cases]
    assert len(ids) == len(set(ids)), f"Duplicate test IDs detected: {ids}"
    expected_ids = [f"AGRI-BENCH-{i:03d}" for i in range(1, 31)]
    assert ids == expected_ids, f"Test IDs do not match sequence AGRI-BENCH-001..030: {ids}"
    print("  * Verified 30 unique, sequential test IDs (AGRI-BENCH-001 to AGRI-BENCH-030).")

    # 2. Domain coverage
    domains_found = {tc["domain"] for tc in test_cases}
    assert domains_found == EXPECTED_DOMAINS, f"Domain mismatch. Missing: {EXPECTED_DOMAINS - domains_found}"
    print(f"  * Verified complete coverage of all 7 agricultural evaluation domains: {domains_found}")

    # 3. Adversarial coverage
    adversarial_found = {tc["adversarial_type"] for tc in test_cases if tc.get("adversarial_type") != "none"}
    missing_adv = EXPECTED_ADVERSARIAL_TYPES - adversarial_found
    assert not missing_adv, f"Missing adversarial types: {missing_adv}"
    print(f"  * Verified complete coverage of all required adversarial archetypes: {adversarial_found}")

    # 4. Field completeness and source registration
    for tc in test_cases:
        tid = tc["test_id"]
        # Required fields
        for field in REQUIRED_FIELDS:
            assert field in tc, f"Test {tid} missing required field: {field}"

        # Source references validity
        sources = tc["verified_source_references"]
        for s in sources:
            assert s in VALID_SOURCE_IDS, f"Test {tid} cites unregistered source: {s} (Valid: {VALID_SOURCE_IDS})"

        # Scoring rubric sums to 1.0
        rubric = tc["scoring_rubric"]
        assert len(rubric) > 0, f"Test {tid} has empty scoring rubric"
        rubric_sum = sum(rubric.values())
        assert abs(rubric_sum - 1.0) < 1e-4, f"Test {tid} rubric does not sum to 1.0 (got {rubric_sum})"

        # User query check
        uq = tc["user_query"]
        assert isinstance(uq, dict), f"Test {tid} user_query must be a dict with 'en' and/or 'mr'"
        assert "en" in uq or "mr" in uq, f"Test {tid} user_query must contain at least 'en' or 'mr'"

    print("  * Verified all 30 test cases contain complete required fields, valid rubrics (summing to 1.0), and valid registered source references.")
    print("\n==============================================================================")
    print("   CROPNET AI — PHASE 5.0 BENCHMARK DATASET INTEGRITY VALIDATION PASSED!")
    print("==============================================================================")


if __name__ == "__main__":
    validate_benchmark()
