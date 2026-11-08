"""
Comprehensive Test Suite for Indian Soil Health Card Corpus & OCR Extraction Validation.

Verifies:
1. Extraction accuracy for 12 standard parameters from National Soil Health Card (SHC).
2. Recognition of bilingual and Marathi terminology from Maharashtra agricultural reports (KVK Baramati, MPKV Rahuri).
3. Preservation of Wisconsin regression fixture (lag_sample.pdf, 8 measurements across 2 samples).
4. Strict prevention of false positives: fertilizer recommendation doses (Urea, SSP, MOP, खत शिफारशी)
   must NEVER leak into measured soil nutrients.
5. Strict nutrient semantic preservation: Total N vs Available N, P vs P2O5, K vs K2O, OC vs OM.
"""
import os
import json
import pytest
from pathlib import Path

from cropnet.services.api.app.services.soil_ocr.extractor import SoilOCRExtractor
from cropnet.services.api.app.services.soil_ocr.parser import SoilReportParser
from cropnet.services.api.app.services.soil_ocr.ollama_client import OllamaOCRClient

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "soil_reports"
GROUND_TRUTH_PATH = FIXTURES_DIR / "ground_truth_corpus.json"


@pytest.fixture(scope="module")
def ground_truth():
    with open(GROUND_TRUTH_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def extractor():
    client = OllamaOCRClient(mock_mode=True)
    return SoilOCRExtractor(ollama_client=client)


# ===========================================================================
# 1. WISCONSIN REGRESSION FIXTURE (lag_sample.pdf)
# ===========================================================================

def test_wisconsin_lag_sample_regression_preserved(extractor):
    """
    Ensure the UW Soil & Plant Analysis Lab regression document extracts all 8 measurements
    across Sample 1 (Lawn) and Sample 2 (Garden) without regressions.
    """
    pdf_path = FIXTURES_DIR / "lag_sample.pdf"
    assert pdf_path.exists(), "lag_sample.pdf fixture must exist."

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    res = extractor.extract(pdf_bytes, "lag_sample.pdf")
    assert res.extraction_status == "EXTRACTION_COMPLETED"
    assert len(res.measurements) == 8, f"Expected 8 measurements across 2 samples, got {len(res.measurements)}"

    # Sample 1 (Lawn)
    s1 = [m for m in res.measurements if m.page_number == 1 or "Lawn" in (m.sample_designation or "")]
    s1_map = {m.parameter_key: m.original_value for m in s1}
    assert s1_map.get("soil_ph") == 5.9
    assert s1_map.get("phosphorus") == 10.0
    assert s1_map.get("potassium") == 34.0
    assert s1_map.get("organic_matter") == 1.9

    # Sample 2 (Garden)
    s2 = [m for m in res.measurements if m.page_number == 2 or "Garden" in (m.sample_designation or "")]
    s2_map = {m.parameter_key: m.original_value for m in s2}
    assert s2_map.get("soil_ph") == 6.2
    assert s2_map.get("phosphorus") == 25.0
    assert s2_map.get("potassium") == 45.0
    assert s2_map.get("organic_matter") == 3.1


# ===========================================================================
# 2. NATIONAL SOIL HEALTH CARD (12 PARAMETERS)
# ===========================================================================

def test_indian_soil_health_card_extraction(extractor):
    """
    Test extraction of the official 12-parameter Indian Soil Health Card format.
    Verifies that macronutrients (N, P, K), secondary (S), micronutrients (Zn, Fe, Cu, Mn, B),
    and physical properties (pH, EC, OC) are accurately extracted.
    """
    pdf_path = FIXTURES_DIR / "synthetic_format_indian_soil_health_card.pdf"
    assert pdf_path.exists()

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    res = extractor.extract(pdf_bytes, "synthetic_format_indian_soil_health_card.pdf")
    assert res.extraction_status == "EXTRACTION_COMPLETED"

    meas_map = {m.parameter_key: m for m in res.measurements}

    # Core parameters
    assert "soil_ph" in meas_map
    assert meas_map["soil_ph"].original_value == 7.65
    assert meas_map["soil_ph"].original_unit == "pH"

    assert "electrical_conductivity" in meas_map
    assert meas_map["electrical_conductivity"].original_value == 0.38
    assert meas_map["electrical_conductivity"].original_unit in ("dS/m", "ds/m")

    assert "organic_carbon" in meas_map
    assert meas_map["organic_carbon"].original_value == 0.52
    assert meas_map["organic_carbon"].original_unit == "%"

    assert "available_nitrogen" in meas_map
    assert meas_map["available_nitrogen"].original_value == 195.0
    assert meas_map["available_nitrogen"].original_unit == "kg/ha"

    assert "available_phosphorus" in meas_map
    assert meas_map["available_phosphorus"].original_value == 16.4
    assert meas_map["available_phosphorus"].original_unit == "kg/ha"

    assert "available_potassium" in meas_map
    assert meas_map["available_potassium"].original_value == 340.0
    assert meas_map["available_potassium"].original_unit == "kg/ha"

    # Secondary & Micronutrients
    assert "sulphur" in meas_map
    assert meas_map["sulphur"].original_value == 8.2

    assert "zinc" in meas_map
    assert meas_map["zinc"].original_value == 0.55

    assert "iron" in meas_map
    assert meas_map["iron"].original_value == 3.8

    assert "manganese" in meas_map
    assert meas_map["manganese"].original_value == 6.2

    assert "copper" in meas_map
    assert meas_map["copper"].original_value == 1.4

    assert "boron" in meas_map
    assert meas_map["boron"].original_value == 0.45


# ===========================================================================
# 3. FERTILIZER RECOMMENDATION SAFEGUARD
# ===========================================================================

def test_prevention_of_fertilizer_recommendation_leakage(extractor):
    """
    Critical Safeguard:
    The Indian Soil Health Card contains a 'Fertilizer Recommendations' table
    listing recommended doses of Urea (110 kg/ha), SSP (125 kg/ha), and MOP (40 kg/ha).
    Ensure that NONE of these recommended doses are extracted as measured soil nutrients!
    """
    pdf_path = FIXTURES_DIR / "synthetic_format_indian_soil_health_card.pdf"
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    res = extractor.extract(pdf_bytes, "synthetic_format_indian_soil_health_card.pdf")

    # None of the measured values should match 110, 125, or 40 from the fertilizer recommendation section
    reported_values = [m.original_value for m in res.measurements]
    assert 110.0 not in reported_values, "Recommended Urea dose leaked into soil measurements!"
    assert 125.0 not in reported_values, "Recommended SSP dose leaked into soil measurements!"
    assert 40.0 not in reported_values, "Recommended MOP dose leaked into soil measurements!"


# ===========================================================================
# 4. MAHARASHTRA STATE LAB (MPKV RAHURI) EXTRACTION
# ===========================================================================

def test_maharashtra_mpkv_rahuri_marathi_report(extractor):
    """
    Test extraction of MPKV Rahuri state university soil testing report.
    """
    pdf_path = FIXTURES_DIR / "synthetic_format_maharashtra_mpkv_marathi.pdf"
    assert pdf_path.exists()

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    res = extractor.extract(pdf_bytes, "synthetic_format_maharashtra_mpkv_marathi.pdf")
    assert res.extraction_status == "EXTRACTION_COMPLETED"

    meas_map = {m.parameter_key: m for m in res.measurements}
    assert "soil_ph" in meas_map
    assert meas_map["soil_ph"].original_value == 8.1

    assert "electrical_conductivity" in meas_map
    assert meas_map["electrical_conductivity"].original_value == 0.28

    assert "organic_carbon" in meas_map
    assert meas_map["organic_carbon"].original_value == 0.65

    assert "available_nitrogen" in meas_map
    assert meas_map["available_nitrogen"].original_value == 245.0

    assert "available_phosphorus" in meas_map
    assert meas_map["available_phosphorus"].original_value == 22.5

    assert "available_potassium" in meas_map
    assert meas_map["available_potassium"].original_value == 410.0

    assert "zinc" in meas_map
    assert meas_map["zinc"].original_value == 0.75


# ===========================================================================
# 5. MARATHI BILINGUAL TERMINOLOGY PARSING & SAFEGUARDS
# ===========================================================================

def test_marathi_bilingual_token_parsing_and_safeguards():
    """
    Verifies parser recognition of Devnagari Marathi soil parameter terminology,
    and safeguards that reject fertilizer dosage lines from parameter parsing.
    """
    parser = SoilReportParser()
    marathi_text = """
    माती परीक्षण प्रयोगशाळा, कृषी विज्ञान केंद्र, बारामती
    माती नमुना तपासणी अहवाल
    शेतकऱ्याचे नाव: रमेश शिंदे
    गाव: माळेगाव, तालुका: बारामती, जिल्हा: पुणे
    तपासणी निकाल:
    सामू (pH): 7.8
    विद्युत वाहकता (EC): 0.45 dS/m
    सेंद्रिय कर्ब (OC): 0.48 %
    उपलब्ध नत्र: 210.0 kg/ha
    उपलब्ध स्फुरद: 18.0 kg/ha
    उपलब्ध पालाश: 310.0 kg/ha
    गंधक: 9.5 ppm
    जस्त / झिंक: 0.62 ppm
    लोह: 4.8 ppm

    खत शिफारशी (Fertilizer Recommendations):
    युरिया: 100 किलो/एकर
    सिंगल सुपर फॉस्फेट (SSP): 150 किलो/एकर
    म्युरेट ऑफ पोटॅश (MOP): 50 किलो/एकर
    शेणखत: 5 टन/एकर
    """
    metadata, measurements = parser.parse(marathi_text)
    assert len(measurements) >= 8

    meas_map = {m.parameter_key: m for m in measurements}
    assert meas_map["soil_ph"].original_value == 7.8
    assert meas_map["electrical_conductivity"].original_value == 0.45
    assert meas_map["organic_carbon"].original_value == 0.48
    assert meas_map["available_nitrogen"].original_value == 210.0
    assert meas_map["available_phosphorus"].original_value == 18.0
    assert meas_map["available_potassium"].original_value == 310.0
    assert meas_map["sulphur"].original_value == 9.5
    assert meas_map["zinc"].original_value == 0.62
    assert meas_map["iron"].original_value == 4.8

    # Ensure fertilizer dosage values (100, 150, 50, 5) were NOT extracted!
    vals = [m.original_value for m in measurements]
    assert 100.0 not in vals
    assert 150.0 not in vals
    assert 50.0 not in vals


# ===========================================================================
# 6. NUTRIENT SEMANTIC PRESERVATION TESTS
# ===========================================================================

def test_corpus_provenance_classification(ground_truth):
    """
    Verify that every document in the ground truth corpus is explicitly classified
    into authentic public institutional documents vs synthetic benchmark fixtures,
    and that synthetic benchmarks carry explicit limitation warnings.
    """
    assert "provenance_policy" in ground_truth
    reports_map = {r["fixture_id"]: r for r in ground_truth["reports"]}

    # Authentic Wisconsin document
    assert "WI-UW-REGRESSION" in reports_map
    uw = reports_map["WI-UW-REGRESSION"]
    assert uw["provenance_type"] == "AUTHENTIC_PUBLIC_DOCUMENT"
    assert "University of Wisconsin" in uw["provenance_description"]

    # Synthetic format fixtures
    synthetic_ids = ["IN-SHC-NATIONAL", "MH-MPKV-RAHURI", "MH-KVK-BARAMATI"]
    for sid in synthetic_ids:
        assert sid in reports_map, f"Fixture {sid} missing from corpus"
        entry = reports_map[sid]
        assert entry["provenance_type"] == "SYNTHETIC_BENCHMARK_FIXTURE"
        assert "LIMITATION" in entry["provenance_description"]
        assert entry["filename"].startswith("synthetic_format_")


def test_kvk_baramati_bilingual_extraction(extractor):
    """
    Verify extraction of synthetic bilingual Marathi/English report (KVK Baramati).
    """
    pdf_path = FIXTURES_DIR / "synthetic_format_maharashtra_kvk_baramati.pdf"
    assert pdf_path.exists()
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    res = extractor.extract(pdf_bytes, "synthetic_format_maharashtra_kvk_baramati.pdf")
    assert res.extraction_status == "EXTRACTION_COMPLETED"
    assert len(res.measurements) >= 6
    meas_map = {m.parameter_key: m for m in res.measurements}
    assert meas_map["soil_ph"].original_value == 7.65
    assert meas_map["electrical_conductivity"].original_value == 0.38
    assert meas_map["organic_carbon"].original_value == 0.52
    assert meas_map["available_nitrogen"].original_value == 195.0
    assert meas_map["available_phosphorus"].original_value == 16.4
    assert meas_map["available_potassium"].original_value == 340.0


# ===========================================================================
# 6. NUTRIENT SEMANTIC PRESERVATION TESTS
# ===========================================================================

def test_nutrient_semantic_isolation():
    """
    Ensure the parser preserves distinct chemical identities:
    - total_nitrogen is distinct from available_nitrogen
    - phosphorus is distinct from available_phosphorus (P vs P2O5)
    - potassium is distinct from available_potassium (K vs K2O)
    - organic_carbon is distinct from organic_matter (OC vs OM)
    """
    parser = SoilReportParser()

    # Total N vs Available N
    k1, _, _ = parser._identify_parameter("Total Nitrogen: 0.12%")
    k2, _, _ = parser._identify_parameter("Available Nitrogen: 220 kg/ha")
    assert k1 == "total_nitrogen"
    assert k2 == "available_nitrogen"
    assert k1 != k2

    # P vs P2O5
    k3, _, _ = parser._identify_parameter("Phosphorus [P]: 15 ppm")
    k4, _, _ = parser._identify_parameter("Available Phosphorus (P2O5): 35 kg/ha")
    assert k3 == "phosphorus"
    assert k4 == "available_phosphorus"
    assert k3 != k4

    # K vs K2O
    k5, _, _ = parser._identify_parameter("Potassium [K]: 50 ppm")
    k6, _, _ = parser._identify_parameter("Available Potassium (K2O): 280 kg/ha")
    assert k5 == "potassium"
    assert k6 == "available_potassium"
    assert k5 != k6

    # OC vs OM
    k7, _, _ = parser._identify_parameter("Organic Carbon (OC): 0.65%")
    k8, _, _ = parser._identify_parameter("Organic Matter (OM): 2.4%")
    assert k7 == "organic_carbon"
    assert k8 == "organic_matter"
    assert k7 != k8
