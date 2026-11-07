"""
Pytest suite for Soil OCR and Structured Report Extraction Pipeline.
Tests document modality detection, Ollama OCR client, deterministic parser,
agronomic safeguards, ambiguity detection, and benchmark metrics.
"""

import os
import io
import sys
import pytest
from PIL import Image

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.services.soil_ocr.models import (
    SoilReportExtractionResult,
    SoilReportMetadata,
    ExtractedSoilMeasurement,
    ReportExtractionStatus,
    MeasurementVerificationStatus,
    ParameterExtractionStatus,
    CANONICAL_NUTRIENT_KEYS,
    PARAMETER_ALIASES,
)
from app.services.soil_ocr.ollama_client import OllamaOCRClient, register_mock_transcription
from app.services.soil_ocr.parser import SoilReportParser
from app.services.soil_ocr.safeguards import ExtractionSafeguards, AGRONOMIC_BOUNDARIES
from app.services.soil_ocr.extractor import SoilOCRExtractor
from tests.evaluation.evaluate_soil_ocr import run_evaluation

CORPUS_DIR = os.path.join(os.path.dirname(__file__), "evaluation", "soil_reports_corpus")


@pytest.fixture
def parser():
    return SoilReportParser()


@pytest.fixture
def mock_ollama_client():
    return OllamaOCRClient(mock_mode=True)


@pytest.fixture
def live_ollama_client():
    return OllamaOCRClient(mock_mode=False)


@pytest.fixture
def mock_extractor(mock_ollama_client, parser):
    return SoilOCRExtractor(ollama_client=mock_ollama_client, parser=parser)


# ============================================================================
# 1. Document Modality & Routing Tests
# ============================================================================

def test_text_pdf_routing(mock_extractor):
    """Test text-based PDF routes directly to parser without vision OCR."""
    pdf_path = os.path.join(CORPUS_DIR, "tc01_shc_pune_digital.pdf")
    with open(pdf_path, "rb") as f:
        data = f.read()

    res = mock_extractor.extract(data, filename="tc01_shc_pune_digital.pdf")
    assert res.document_type == "text_pdf"
    assert res.extraction_status in (ReportExtractionStatus.EXTRACTION_COMPLETED.value, ReportExtractionStatus.NEEDS_REVIEW.value)
    assert res.total_parameters_detected >= 10
    assert res.get_measurement("soil_ph") is not None
    assert res.get_measurement("soil_ph").original_value == 7.65


def test_scanned_pdf_routing(mock_extractor):
    """Test scanned PDF extracts embedded raster images and invokes OCR."""
    pdf_path = os.path.join(CORPUS_DIR, "tc02_kvk_baramati_scanned.pdf")
    with open(pdf_path, "rb") as f:
        data = f.read()

    res = mock_extractor.extract(data, filename="tc02_kvk_baramati_scanned.pdf")
    assert res.document_type == "scanned_pdf"
    assert res.total_parameters_detected >= 6
    assert res.get_measurement("electrical_conductivity") is not None


def test_image_jpeg_routing(mock_extractor):
    """Test JPEG image validation and OCR execution."""
    jpg_path = os.path.join(CORPUS_DIR, "tc04_soil_card_photo.jpg")
    with open(jpg_path, "rb") as f:
        data = f.read()

    res = mock_extractor.extract(data, filename="tc04_soil_card_photo.jpg")
    assert res.document_type == "image_jpeg"
    assert res.total_parameters_detected >= 6


def test_image_png_routing(mock_extractor):
    """Test PNG image validation and OCR execution."""
    png_path = os.path.join(CORPUS_DIR, "tc05_lab_report_glare.png")
    with open(png_path, "rb") as f:
        data = f.read()

    res = mock_extractor.extract(data, filename="tc05_lab_report_glare.png")
    assert res.document_type == "image_png"
    assert res.total_parameters_detected >= 5


def test_negative_control_invoice_rejection(mock_extractor):
    """Test non-soil document (purchase invoice) is rejected with zero false parameters."""
    inv_path = os.path.join(CORPUS_DIR, "tc10_fertilizer_invoice.pdf")
    with open(inv_path, "rb") as f:
        data = f.read()

    res = mock_extractor.extract(data, filename="tc10_fertilizer_invoice.pdf")
    assert res.extraction_status == ReportExtractionStatus.FAILED.value
    assert res.total_parameters_detected == 0
    assert len(res.measurements) == 0


def test_empty_and_unsupported_file_handling(mock_extractor):
    """Test empty payload and unsupported file extensions."""
    res_empty = mock_extractor.extract(b"", filename="empty.pdf")
    assert res_empty.extraction_status == ReportExtractionStatus.FAILED.value

    res_unsupported = mock_extractor.extract(b"hello world", filename="notes.docx")
    assert res_unsupported.document_type == "unsupported"
    assert res_unsupported.extraction_status == ReportExtractionStatus.FAILED.value


# ============================================================================
# 2. Ollama OCR Client Tests
# ============================================================================

def test_ollama_client_mock_mode():
    """Test deterministic mock transcription behavior."""
    client = OllamaOCRClient(mock_mode=True)
    assert not client.is_available()  # Mock mode always reports False for live

    img = Image.new("RGB", (100, 100), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    text = client.transcribe_image(buf.getvalue())
    assert "pH" in text
    assert "Available Nitrogen" in text


def test_ollama_client_offline_fallback():
    """Test client falls back to mock when server is unreachable."""
    client = OllamaOCRClient(host="http://127.0.0.1:9999", fallback_on_offline=True)
    img = Image.new("RGB", (100, 100), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    text = client.transcribe_image(buf.getvalue())
    assert text is not None
    assert len(text) > 0


def test_ollama_client_custom_mock_registration():
    """Test registering custom image transcriptions in mock registry."""
    test_hash = "mock_hash_12345"
    custom_md = "# CUSTOM LAB REPORT\npH: 6.8\nEC: 0.40 dS/m"
    register_mock_transcription(test_hash, custom_md)

    client = OllamaOCRClient(mock_mode=True)
    # sha256 check
    import hashlib
    dummy_bytes = b"sample_image_data_xyz"
    h = hashlib.sha256(dummy_bytes).hexdigest()
    register_mock_transcription(h, custom_md)

    res = client._mock_transcribe(dummy_bytes)
    assert res == custom_md


# ============================================================================
# 3. Deterministic Parser Tests
# ============================================================================

def test_parse_markdown_table(parser):
    """Test Markdown pipe table parsing."""
    table_text = """
| Parameter | Result | Unit | Rating |
| :--- | :--- | :--- | :--- |
| Soil pH | 7.60 | pH | Normal |
| Available Nitrogen (N) | 225.0 | kg/ha | Medium |
| Available Phosphorus (P2O5) | 19.4 | kg/ha | Medium |
| Available Potassium (K2O) | 350.0 | kg/ha | High |
"""
    meta, measurements = parser.parse(table_text)
    assert len(measurements) == 4
    ph = next(m for m in measurements if m.parameter_key == "soil_ph")
    assert ph.original_value == 7.60
    assert ph.original_unit == "pH"

    n = next(m for m in measurements if m.parameter_key == "available_nitrogen")
    assert n.original_value == 225.0
    assert n.original_unit == "kg/ha"


def test_parse_html_table(parser):
    """Test HTML table parsing produced by vision OCR models."""
    html_text = """
<table>
  <thead>
    <tr><th>Parameter</th><th>Result</th><th>Unit</th></tr>
  </thead>
  <tbody>
    <tr><td>Soil pH</td><td>7.80</td><td>pH</td></tr>
    <tr><td>Electrical Conductivity (EC)</td><td>0.45</td><td>dS/m</td></tr>
    <tr><td>Organic Carbon (OC)</td><td>0.62</td><td>%</td></tr>
  </tbody>
</table>
"""
    meta, measurements = parser.parse(html_text)
    assert len(measurements) == 3
    keys = [m.parameter_key for m in measurements]
    assert "soil_ph" in keys
    assert "electrical_conductivity" in keys
    assert "organic_carbon" in keys


def test_parse_multi_depth_table(parser):
    """Test multi-depth table column parsing (0-15 cm and 15-30 cm)."""
    text = """
Parameter 0-15 cm 15-30 cm Unit
pH (1:2.5) 7.70 8.00 pH
Organic Carbon (OC) 0.55 0.38 %
Available Nitrogen (N) 220.0 140.0 kg/ha
"""
    meta, measurements = parser.parse(text)
    assert len(measurements) == 6
    depths = {m.sample_depth for m in measurements}
    assert "0-15 cm" in depths
    assert "15-30 cm" in depths


def test_parse_metadata_fields(parser):
    """Test metadata extraction from header text."""
    header = """
DISTRICT SOIL TESTING LABORATORY, PUNE
Laboratory: District Soil Testing Laboratory, Pune
Farmer Name: Vitthalrao Patil
Sample ID: MH-PUN-2024-8841
Report Date: 15/04/2024
Collection Date: 05/04/2024
Sampling Depth: 0-15 cm
Sampling Point: Plot 4B, North Field
Village: Baramati, Taluka: Baramati, District: Pune, State: Maharashtra
"""
    meta = parser._parse_metadata(header)
    assert meta.laboratory_name == "District Soil Testing Laboratory, Pune"
    assert meta.farmer_name == "Vitthalrao Patil"
    assert meta.sample_id == "MH-PUN-2024-8841"
    assert meta.report_date == "2024-04-15"
    assert meta.collection_date == "2024-04-05"
    assert meta.sample_depth == "0-15 cm"
    assert meta.village == "Baramati"
    assert meta.district == "Pune"


# ============================================================================
# 4. Safeguards 1 through 8 Tests
# ============================================================================

def test_safeguard_1_do_not_zero_missing_values():
    """Safeguard 1: Missing values must remain None (NOT_REPORTED), never 0.0."""
    m_missing = ExtractedSoilMeasurement(
        parameter_key="zinc",
        original_parameter_name="Available Zinc (Zn)",
        original_value=None,
        original_unit=None,
    )
    result = SoilReportExtractionResult(
        document_type="text_pdf",
        measurements=[m_missing],
    )
    ExtractionSafeguards.apply(result)

    assert result.measurements[0].original_value is None
    assert result.measurements[0].normalized_value is None
    assert result.measurements[0].extraction_status == ParameterExtractionStatus.NOT_REPORTED.value


def test_safeguard_2_no_silent_unit_conversions():
    """Safeguard 2: Disallow conversions across non-1:1 bases (e.g. kg/ha to ppm)."""
    m_kgha = ExtractedSoilMeasurement(
        parameter_key="available_nitrogen",
        original_parameter_name="Available Nitrogen",
        original_value=200.0,
        original_unit="kg/ha",
    )
    m_ec_ms = ExtractedSoilMeasurement(
        parameter_key="electrical_conductivity",
        original_parameter_name="EC",
        original_value=1.5,
        original_unit="mS/cm",
    )
    m_ec_us = ExtractedSoilMeasurement(
        parameter_key="electrical_conductivity",
        original_parameter_name="EC",
        original_value=500.0,
        original_unit="uS/cm",
    )
    result = SoilReportExtractionResult(
        document_type="text_pdf",
        measurements=[m_kgha, m_ec_ms, m_ec_us],
    )
    ExtractionSafeguards.apply(result)

    # kg/ha remains kg/ha
    assert result.measurements[0].normalized_value == 200.0
    assert result.measurements[0].normalized_unit == "kg/ha"

    # 1 mS/cm == 1 dS/m
    assert result.measurements[1].normalized_value == 1.5
    assert result.measurements[1].normalized_unit == "dS/m"

    # 500 uS/cm == 0.5 dS/m
    assert result.measurements[2].normalized_value == 0.5
    assert result.measurements[2].normalized_unit == "dS/m"


def test_safeguard_3_total_nitrogen_vs_available_nitrogen():
    """Safeguard 3: DO NOT infer Available Nitrogen from Total Nitrogen."""
    m_tot = ExtractedSoilMeasurement(
        parameter_key="total_nitrogen",
        original_parameter_name="Total Nitrogen",
        original_value=0.08,
        original_unit="%",
    )
    result = SoilReportExtractionResult(
        document_type="text_pdf",
        measurements=[m_tot],
    )
    ExtractionSafeguards.apply(result)

    # Available nitrogen must NOT be created or inferred
    avail_n = result.get_measurement("available_nitrogen")
    assert avail_n is None
    assert any("Safeguard 3 active" in w for w in result.warnings)


def test_safeguard_4_oxide_vs_elemental_forms():
    """Safeguard 4: Flag elemental P or K reported instead of standard oxide."""
    m_p_elem = ExtractedSoilMeasurement(
        parameter_key="available_phosphorus",
        original_parameter_name="Available Phosphorus (elemental P)",
        original_value=10.0,
        original_unit="kg/ha",
    )
    result = SoilReportExtractionResult(
        document_type="text_pdf",
        measurements=[m_p_elem],
    )
    ExtractionSafeguards.apply(result)

    assert result.measurements[0].is_ambiguous is True
    assert "Elemental Phosphorus" in result.measurements[0].ambiguity_reason


def test_safeguard_5_unusual_concentration_units():
    """Safeguard 5: Flag unusual concentration units for farmer review."""
    m_unusual = ExtractedSoilMeasurement(
        parameter_key="sulphur",
        original_parameter_name="Sulphur",
        original_value=15.0,
        original_unit="mg/L",  # Unusual volume unit for soil test
    )
    result = SoilReportExtractionResult(
        document_type="text_pdf",
        measurements=[m_unusual],
    )
    ExtractionSafeguards.apply(result)

    assert result.measurements[0].is_ambiguous is True
    assert "Unusual concentration unit" in result.measurements[0].ambiguity_reason


def test_safeguard_6_do_not_infer_sample_depth():
    """Safeguard 6: DO NOT guess sample depth if absent from document."""
    meta = SoilReportMetadata(sample_depth=None)
    result = SoilReportExtractionResult(
        document_type="text_pdf",
        metadata=meta,
        measurements=[],
    )
    ExtractionSafeguards.apply(result)

    assert result.metadata.sample_depth is None


def test_safeguard_7_ambiguity_and_anomaly_detection():
    """Safeguard 7: Detect ambiguous values, digits, and out-of-range anomalies."""
    # Out of range pH (< 3.0 or > 11.0)
    m_ph_extreme = ExtractedSoilMeasurement(
        parameter_key="soil_ph",
        original_parameter_name="pH",
        original_value=1.8,
        original_unit="pH",
    )
    # OCR confusion P206
    m_p206 = ExtractedSoilMeasurement(
        parameter_key="available_phosphorus",
        original_parameter_name="Available Phosphorus (P206)",
        original_value=16.0,
        original_unit="kg/ha",
        is_ambiguous=True,
        ambiguity_reason="OCR digit confusion detected: P206 for P2O5",
    )
    result = SoilReportExtractionResult(
        document_type="image_png",
        measurements=[m_ph_extreme, m_p206],
    )
    ExtractionSafeguards.apply(result)

    assert result.is_ambiguous is True
    assert result.ambiguous_parameters_count == 2
    assert result.extraction_status == ReportExtractionStatus.NEEDS_REVIEW.value
    assert result.measurements[0].is_ambiguous is True
    assert "outside plausible agronomic bounds" in result.measurements[0].ambiguity_reason


def test_safeguard_8_decouple_ocr_confidence_from_verification():
    """Safeguard 8: OCR confidence is decoupled from farmer verification (EXTRACTED_UNVERIFIED)."""
    m_perfect = ExtractedSoilMeasurement(
        parameter_key="soil_ph",
        original_parameter_name="pH",
        original_value=7.4,
        original_unit="pH",
        ocr_confidence=1.0,
        is_ambiguous=False,
    )
    result = SoilReportExtractionResult(
        document_type="text_pdf",
        measurements=[m_perfect],
    )
    ExtractionSafeguards.apply(result)

    # Verification status MUST remain EXTRACTED_UNVERIFIED despite 1.0 confidence!
    assert result.measurements[0].verification_status == MeasurementVerificationStatus.EXTRACTED_UNVERIFIED.value
    assert result.measurements[0].verification_status != MeasurementVerificationStatus.FARMER_CONFIRMED.value


# ============================================================================
# 5. Full Evaluation Benchmark Suite Test
# ============================================================================

def test_full_corpus_evaluation_benchmark():
    """
    Executes the 10-report evaluation benchmark suite and verifies that all
    target metrics pass (FEA, NEA, MAPE, UEA, SMA, TEA, ADR).
    """
    metrics = run_evaluation(corpus_dir=CORPUS_DIR, mock_mode=False)
    assert metrics["all_passed"] is True, f"Benchmark failed: {metrics}"
    assert metrics["fea"] >= 90.0
    assert metrics["nea"] >= 95.0
    assert metrics["mape"] <= 5.0
    assert metrics["uea"] >= 95.0
    assert metrics["sma"] >= 85.0
    assert metrics["tea"] >= 90.0
    assert metrics["adr"] >= 90.0


# ============================================================================
# 6. Real-World Multi-Sample Soil Laboratory PDF Regression Test
# ============================================================================

def test_uw_extension_lag_sample_multi_sample_extraction():
    """
    Regression test fixture: lag_sample.pdf (UW Soil & Plant Analysis Lab).
    Verifies:
    1. Multi-page horizontal/columnar table parsing without zero-parameter failure.
    2. Distinction between Sample 1 (Lawn, Page 1) and Sample 2 (Garden, Page 2).
    3. Strict agronomic guardrails:
       - No fertilizer dosage recommendations extracted into soil chemistry.
       - SOM is strictly organic_matter (not silently converted to organic_carbon).
       - No fabricated EC, depth, or Available Nitrogen.
       - Decoupled verification status (EXTRACTED_UNVERIFIED).
    """
    pdf_path = os.path.join(CORPUS_DIR, "lag_sample.pdf")
    if not os.path.exists(pdf_path):
        pdf_path = "/Users/siddheshbirewar/Downloads/lag_sample.pdf"
    assert os.path.exists(pdf_path), f"Fixture not found at {pdf_path}"

    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    extractor = SoilOCRExtractor()
    result = extractor.extract(file_bytes=file_bytes, filename="lag_sample.pdf")

    assert result.extraction_status == ReportExtractionStatus.EXTRACTION_COMPLETED.value
    assert len(result.measurements) == 8, f"Expected 8 measurements, found {len(result.measurements)}"

    # Metadata extraction (Phase 5.6.3: strict provenance, no date or depth conflation)
    assert result.metadata.laboratory_name == "UW Soil & Plant Analysis Lab"
    assert result.metadata.sample_id == "54321"
    assert result.metadata.lab_number == "54321"
    assert result.metadata.farmer_name == "Bucky Badger"
    assert result.metadata.district == "Dane"
    assert result.metadata.date_received == "2007-08-01"
    assert result.metadata.date_processed == "2007-08-10"
    assert result.metadata.report_date == "2007-08-10"
    assert result.metadata.collection_date is None  # Strictly not in document, must not map from date_received
    assert result.metadata.sample_depth is None     # Strictly unstated, must not default or infer
    assert result.metadata.depth_provenance == "UNKNOWN"

    # Separate Sample 1 (Lawn, Page 1) and Sample 2 (Garden, Page 2)
    s1_meas = {m.parameter_key: m for m in result.measurements if m.sample_id == "1" or m.page_number == 1}
    s2_meas = {m.parameter_key: m for m in result.measurements if m.sample_id == "2" or m.page_number == 2}

    assert len(s1_meas) == 4
    assert len(s2_meas) == 4

    # Sample 1 (Lawn) Assertions - Phase 5.6.3: strictly elemental phosphorus & potassium
    assert s1_meas["soil_ph"].original_value == 5.9
    assert s1_meas["phosphorus"].original_value == 10.0
    assert s1_meas["phosphorus"].original_unit == "ppm"
    assert s1_meas["potassium"].original_value == 34.0
    assert s1_meas["potassium"].original_unit == "ppm"
    assert s1_meas["organic_matter"].original_value == 1.9
    assert s1_meas["organic_matter"].original_unit == "%"
    assert s1_meas["soil_ph"].sample_designation == "Lawn"

    # Sample 2 (Garden) Assertions - Phase 5.6.3: strictly elemental phosphorus & potassium
    assert s2_meas["soil_ph"].original_value == 6.2
    assert s2_meas["phosphorus"].original_value == 25.0
    assert s2_meas["phosphorus"].original_unit == "ppm"
    assert s2_meas["potassium"].original_value == 45.0
    assert s2_meas["potassium"].original_unit == "ppm"
    assert s2_meas["organic_matter"].original_value == 3.1
    assert s2_meas["organic_matter"].original_unit == "%"
    assert s2_meas["soil_ph"].sample_designation == "Garden"

    # Agronomic Invariant Checks:
    all_keys = [m.parameter_key for m in result.measurements]
    all_values = [m.original_value for m in result.measurements]

    # 1. No fertilizer application dosage (0.30 lbs N, 1.0 lbs P2O5, 1.5 lbs K2O) leaked into measurements
    assert 0.3 not in all_values and 0.30 not in all_values
    assert 1.5 not in all_values

    # 2. No unverified organic_carbon conversion
    assert "organic_carbon" not in all_keys

    # 3. No unverified conversion of elemental P/K to available P2O5/K2O
    assert "available_phosphorus" not in all_keys
    assert "available_potassium" not in all_keys

    # 4. No hallucinated unmeasured parameters
    assert "available_nitrogen" not in all_keys
    assert "electrical_conductivity" not in all_keys

    # 5. Decoupled verification status
    for m in result.measurements:
        assert m.verification_status == MeasurementVerificationStatus.EXTRACTED_UNVERIFIED.value
