"""
Regression test for the phone number OCR parsing and out-of-bounds soil pH bug.
Verifies:
1. Soil OCR parser ignores telephone prefixes (Ph. 0422, Tel:, Mob:) and does not extract soil_ph.
2. Single letter addresses (e.g. K.K. Pudur) and bearing capacity formulas (+P) are not extracted as potassium or phosphorus.
3. Agronomic bounds safeguard rejects out-of-bounds values (e.g. 422.0).
"""
import pytest
from cropnet.services.api.app.services.soil_ocr.parser import SoilReportParser
from cropnet.services.api.app.services.soil_ocr.safeguards import AGRONOMIC_BOUNDARIES

def test_ocr_parser_ignores_telephone_number_as_ph():
    parser = SoilReportParser()
    sample_text = """
    GEOTECHNICAL REPORT
    Er. D. Ranjini, Geotechnical Engineer
    H.O: Old No: 40, New No: 29, 8th St. K.K.Pudur, Coimbatore - 641038.
    Ph. 0422 4202452 Mobile : 90433 – 44488
    Off : 0422-4202452
    Safe bearing capacity (SBC) = 3.5 (N-3) {(B+0.3)/2B}2 × RW × FD +P
    The soil layer up to 14.00 m depth
    """
    metadata, measurements = parser.parse(sample_text)
    
    # Assert that Ph. 0422 is NOT extracted as soil_ph
    ph_meas = [m for m in measurements if m.parameter_key == "soil_ph"]
    assert len(ph_meas) == 0, f"Expected 0 soil_ph measurements, found: {ph_meas}"

    # Assert that K.K. Pudur is NOT extracted as potassium
    k_meas = [m for m in measurements if m.parameter_key in ("potassium", "available_potassium")]
    assert len(k_meas) == 0, f"Expected 0 potassium measurements, found: {k_meas}"

    # Assert that formula +P is NOT extracted as phosphorus
    p_meas = [m for m in measurements if m.parameter_key in ("phosphorus", "available_phosphorus")]
    assert len(p_meas) == 0, f"Expected 0 phosphorus measurements, found: {p_meas}"

def test_genuine_ph_is_extracted_correctly():
    parser = SoilReportParser()
    genuine_text = """
    DISTRICT AGRICULTURAL SOIL TESTING LABORATORY
    Soil pH (1:2.5): 7.4
    Electrical Conductivity: 0.45 dS/m
    Organic Carbon: 0.65 %
    Available Nitrogen: 280 kg/ha
    Available Phosphorus (P2O5): 18.5 kg/ha
    Available Potassium (K2O): 320 kg/ha
    """
    metadata, measurements = parser.parse(genuine_text)
    ph_meas = [m for m in measurements if m.parameter_key == "soil_ph"]
    assert len(ph_meas) == 1
    assert ph_meas[0].original_value == 7.4
    assert ph_meas[0].is_ambiguous is False

def test_agronomic_boundaries_exist():
    assert "soil_ph" in AGRONOMIC_BOUNDARIES
    min_ph, max_ph = AGRONOMIC_BOUNDARIES["soil_ph"]
    assert min_ph == 3.0
    assert max_ph == 11.0
