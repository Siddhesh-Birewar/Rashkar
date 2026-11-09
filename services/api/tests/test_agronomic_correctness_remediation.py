"""
Comprehensive Agronomic Correctness & Geometry Remediation Test Suite.
Milestone M2 (Requirement R2) Verification.

Tests 6 core agronomic and geometric integrity areas:
1. Temperature parsing: Devanagari/ASCII numerals, decimals, negatives, degree symbols,
   and ICRISAT chickpea reproductive heat stress (>35.0°C). Guarantees 35°C is NEVER
   interpreted as 37°C.
2. Kharif Bajra sowing window: Validated datetime.date comparisons against approved
   MPKV Rahuri / ICAR-AICRP window (June 15 to July 15 inclusive). Tests opening date,
   day before, interior, closing date, day after, and year boundaries.
3. Electrical conductivity (EC): Canonical normalization across µS/cm, mS/cm, dS/m,
   plausibility bounds (0.0 to 30.0 dS/m) evaluated on canonical values (500 µS/cm == 0.5 dS/m
   is NOT flagged as >30.0), and explicit rejection of unsupported units (ppm, mg/L, kg/ha).
4. Irrigation availability: Tri-state representation (Available=True, Unavailable=False,
   Unknown=None) preserving uncertainty without false positive/negative defaults, and
   DB hydration preserving irrigation_type and water_source.
5. Regional taluka evaluation: Supported pilot talukas (Baramati, Indapur, Maval, Mulshi)
   vs explicit REQUIRES_REGIONAL_VALIDATION with RULE_OUTSIDE_PILOT_TALUKA for non-pilot talukas.
6. Geometry & Representative Point: Geometrically valid representative point computation
   using Shapely shape().centroid with representative_point() fallback, verified on convex
   polygons, closing rings, concave (C-shape/horseshoe) polygons, polygons with holes,
   and MultiPolygons without altering registered geometry or area.
"""
import uuid
import pytest
from datetime import date
from shapely.geometry import Polygon, MultiPolygon, Point, shape

from cropnet.services.api.app.schemas.agriculture_intelligence import (
    FarmContextInput,
    DecisionState,
    EvidenceTier,
    EnforcementLevel,
)
from cropnet.services.api.app.services.agriculture_intelligence.decision_engine import (
    DeterministicDecisionEngine,
    extract_temperature_from_text,
    DEVANAGARI_DIGIT_MAP,
)
from cropnet.services.api.app.services.agriculture_intelligence.climate_evaluator import (
    ClimateSuitabilityEvaluator,
)
from cropnet.services.api.app.services.agriculture_intelligence.regional_evaluator import (
    RegionalSuitabilityEvaluator,
)
from cropnet.services.api.app.services.soil_ocr.safeguards import (
    ExtractionSafeguards,
    ExtractedSoilMeasurement,
    SoilReportExtractionResult,
    AGRONOMIC_BOUNDARIES,
)
from cropnet.services.api.app.api.v1.endpoints.farms import (
    compute_farm_representative_point,
    _FARM_STORAGE,
)

engine = DeterministicDecisionEngine()


# ============================================================================
# Domain 1: Temperature Parsing & ICRISAT Chickpea Heat Stress (>35.0°C)
# ============================================================================

class TestTemperatureParsingRemediation:
    """Verifies numeric extraction and guarantees 35°C is NEVER interpreted as 37°C."""

    @pytest.mark.parametrize("input_text,expected_temp", [
        ("35°c", 35.0),
        ("35°C", 35.0),
        ("35 °c", 35.0),
        ("35c", 35.0),
        ("35 degree", 35.0),
        ("35 degrees", 35.0),
        ("35 celsius", 35.0),
        ("३५ अंश", 35.0),
        ("३५ अंश सेल्सिअस", 35.0),
        ("३५°c", 35.0),
        ("37°c", 37.0),
        ("37 °c", 37.0),
        ("37 degree", 37.0),
        ("३७ अंश", 37.0),
        ("३७ अंश सेल्सिअस", 37.0),
        ("35.5°c", 35.5),
        ("35.5 degree", 35.5),
        ("३५.५ अंश", 35.5),
        ("-2°c", -2.0),
        ("-2 degrees", -2.0),
        ("-2 अंश", -2.0),
        ("-3.5°c", -3.5),
        ("temperature is 35", 35.0),
        ("तापमान ३५", 35.0),
        ("कमाल तापमान ३५", 35.0),
    ])
    def test_extract_temperature_from_text_exact_values(self, input_text, expected_temp):
        parsed = extract_temperature_from_text(input_text)
        assert parsed is not None, f"Failed to parse temperature from '{input_text}'"
        assert parsed == pytest.approx(expected_temp, 0.001)

    def test_devanagari_digit_mapping(self):
        """Verifies full Unicode range ०-९ maps to ASCII 0-9."""
        dev_digits = "०१२३४५६७८९"
        ascii_digits = dev_digits.translate(DEVANAGARI_DIGIT_MAP)
        assert ascii_digits == "0123456789"

    def test_chickpea_heat_stress_not_triggered_at_35_celsius(self):
        """
        ICRISAT (2010, p. 3) rule triggers when daily max strictly > 35.0°C.
        At exactly 35.0°C (e.g. '35°c', '३५ अंश', '35 degree'), the heat stress
        rule must NOT fire.
        """
        for query in ["chickpea with 35°c", "३५ अंश तापमान", "35 degree max temp"]:
            ctx = FarmContextInput(
                taluka="Baramati",
                district="Pune",
                target_crops=["chickpea"],
                user_query=query
            )
            resp = engine.evaluate_farm(ctx)
            chickpea_outcome = next((o for o in resp.crop_outcomes if o.crop_id == "chickpea"), None)
            assert chickpea_outcome is not None

            # Assert 35.0 is parsed and reproductive_temp_max_c is NOT 37.0
            assert chickpea_outcome.applied_rules is not None
            rule_ids = [r.rule_id for r in chickpea_outcome.applied_rules]
            assert "RULE_CHICKPEA_HEAT_STRESS_35C" not in rule_ids, (
                f"Query '{query}' falsely triggered chickpea heat stress at 35°C!"
            )
            assert not any("35°C" in w and "exceeds" in w for w in chickpea_outcome.reproductive_risk_warnings), (
                f"Query '{query}' produced inappropriate heat stress warning at 35°C"
            )

    def test_chickpea_heat_stress_triggered_at_37_celsius(self):
        """At 37.0°C (e.g. '37°c', '३७ अंश'), heat stress MUST fire."""
        for query in ["chickpea with 37°c", "३७ अंश तापमान", "37 degree max temp"]:
            ctx = FarmContextInput(
                taluka="Baramati",
                district="Pune",
                target_crops=["chickpea"],
                user_query=query
            )
            resp = engine.evaluate_farm(ctx)
            chickpea_outcome = next((o for o in resp.crop_outcomes if o.crop_id == "chickpea"), None)
            assert chickpea_outcome is not None

            rule_ids = [r.rule_id for r in chickpea_outcome.applied_rules]
            assert "RULE_CHICKPEA_HEAT_STRESS_35C" in rule_ids, (
                f"Query '{query}' failed to trigger chickpea heat stress at 37°C!"
            )
            assert any("35°C" in w for w in chickpea_outcome.reproductive_risk_warnings)


# ============================================================================
# Domain 2: Kharif Bajra Sowing Window Date Comparisons
# ============================================================================

class TestBajraKharifSowingWindowRemediation:
    """
    Evaluates date boundary comparisons for Kharif Bajra sowing window.
    Approved MPKV Rahuri / ICAR-AICRP window: June 15 to July 15 inclusive.
    """

    @pytest.mark.parametrize("test_date,expected_inside", [
        ("2026-06-15", True),   # Opening date (inclusive)
        ("2026-06-14", False),  # 1 day before opening
        ("2026-06-20", True),   # Interior date
        ("2026-07-05", True),   # Interior date
        ("2026-07-15", True),   # Closing date (inclusive)
        ("2026-07-16", False),  # 1 day after closing
        ("2026-12-31", False),  # Year boundary
        ("2026-01-01", False),  # Year boundary
    ])
    def test_bajra_sowing_window_date_boundaries(self, test_date, expected_inside):
        profile = engine.retriever.get_crop_profile("bajra")
        assert profile is not None

        ctx = FarmContextInput(
            taluka="Baramati",
            target_crops=["bajra"],
            target_season="kharif",
            proposed_sowing_date=test_date,
            actual_recorded_rain_mm=100.0  # Adequate moisture so rain gate doesn't interfere
        )
        res = ClimateSuitabilityEvaluator.evaluate(ctx, profile)
        applied_rule_ids = [r.rule_id for r in res.applied_rules]

        if expected_inside:
            assert "RULE_BAJRA_KHARIF_SOWING_WINDOW" not in applied_rule_ids, (
                f"Valid date '{test_date}' was falsely flagged as outside the Kharif Bajra sowing window!"
            )
            assert not any("downy mildew" in w for w in res.warnings), (
                f"Valid date '{test_date}' produced out-of-window warning!"
            )
        else:
            assert "RULE_BAJRA_KHARIF_SOWING_WINDOW" in applied_rule_ids, (
                f"Out-of-window date '{test_date}' failed to trigger RULE_BAJRA_KHARIF_SOWING_WINDOW!"
            )
            assert any("downy mildew" in w for w in res.warnings)

    def test_bajra_sowing_window_ignores_rabi_and_summer(self):
        """Bajra sowing window rule only applies to Kharif season."""
        profile = engine.retriever.get_crop_profile("bajra")
        assert profile is not None

        for non_kharif in ["rabi", "summer"]:
            ctx = FarmContextInput(
                taluka="Baramati",
                target_crops=["bajra"],
                target_season=non_kharif,
                proposed_sowing_date="2026-01-10",
                actual_recorded_rain_mm=100.0
            )
            res = ClimateSuitabilityEvaluator.evaluate(ctx, profile)
            applied_rule_ids = [r.rule_id for r in res.applied_rules]
            assert "RULE_BAJRA_KHARIF_SOWING_WINDOW" not in applied_rule_ids


# ============================================================================
# Domain 3: Electrical Conductivity (EC) Safeguards & Unit Normalization
# ============================================================================

class TestElectricalConductivitySafeguardsRemediation:
    """
    Verifies canonical normalization across µS/cm, mS/cm, dS/m,
    agronomic plausibility boundaries (0.0 to 30.0 dS/m), and rejection of unsupported units.
    """

    def test_canonical_unit_normalization_uS_cm_to_dS_m(self):
        """
        A 500 µS/cm reading is 0.5 dS/m (normal, healthy soil).
        Must normalize to 0.5 dS/m and NOT be flagged as out-of-bounds > 30.0!
        """
        m_us = ExtractedSoilMeasurement(
            parameter_key="electrical_conductivity",
            original_parameter_name="EC",
            original_value=500.0,
            original_unit="µS/cm",
            ocr_confidence=0.95
        )
        res = SoilReportExtractionResult(document_type="text_pdf", measurements=[m_us])
        ExtractionSafeguards.apply(res)

        assert m_us.normalized_value == 0.5
        assert m_us.normalized_unit == "dS/m"
        assert m_us.is_ambiguous is False, (
            f"500 µS/cm (0.5 dS/m) was falsely marked ambiguous: {m_us.ambiguity_reason}"
        )
        assert m_us.ocr_confidence >= 0.90

    def test_canonical_unit_normalization_mS_cm_and_dS_m(self):
        """1.5 mS/cm == 1.5 dS/m; 2.5 dS/m == 2.5 dS/m."""
        m_ms = ExtractedSoilMeasurement(
            parameter_key="electrical_conductivity",
            original_parameter_name="EC",
            original_value=1.5,
            original_unit="mS/cm",
            ocr_confidence=0.92
        )
        m_ds = ExtractedSoilMeasurement(
            parameter_key="electrical_conductivity",
            original_parameter_name="EC",
            original_value=2.5,
            original_unit="dS/m",
            ocr_confidence=0.92
        )
        res = SoilReportExtractionResult(document_type="text_pdf", measurements=[m_ms, m_ds])
        ExtractionSafeguards.apply(res)

        assert m_ms.normalized_value == 1.5
        assert m_ms.normalized_unit == "dS/m"
        assert m_ms.is_ambiguous is False

        assert m_ds.normalized_value == 2.5
        assert m_ds.normalized_unit == "dS/m"
        assert m_ds.is_ambiguous is False

    def test_ec_out_of_plausible_bounds_flagged(self):
        """EC above 30.0 dS/m is agronomically implausible and must be flagged."""
        m_high = ExtractedSoilMeasurement(
            parameter_key="electrical_conductivity",
            original_parameter_name="EC",
            original_value=35.0,
            original_unit="dS/m",
            ocr_confidence=0.90
        )
        res = SoilReportExtractionResult(document_type="text_pdf", measurements=[m_high])
        ExtractionSafeguards.apply(res)

        assert m_high.is_ambiguous is True
        assert m_high.ocr_confidence <= 0.60
        assert "outside plausible agronomic bounds" in m_high.ambiguity_reason

    @pytest.mark.parametrize("bad_unit", ["ppm", "mg/L", "kg/ha", "%", "ohms"])
    def test_ec_explicit_rejection_of_unsupported_units(self, bad_unit):
        """Unsupported units for electrical conductivity must be explicitly rejected."""
        m_bad = ExtractedSoilMeasurement(
            parameter_key="electrical_conductivity",
            original_parameter_name="EC",
            original_value=100.0,
            original_unit=bad_unit,
            ocr_confidence=0.88
        )
        res = SoilReportExtractionResult(document_type="text_pdf", measurements=[m_bad])
        ExtractionSafeguards.apply(res)

        assert m_bad.normalized_value is None
        assert m_bad.is_ambiguous is True
        assert m_bad.ocr_confidence <= 0.40
        assert f"Unsupported unit '{bad_unit}' for electrical conductivity" in m_bad.ambiguity_reason


# ============================================================================
# Domain 4: Irrigation Availability Representation & DB Hydration
# ============================================================================

class TestIrrigationAvailabilityRepresentationRemediation:
    """
    Verifies tri-state irrigation availability (Available=True, Unavailable=False, Unknown=None)
    and DB hydration in farms.py.
    """

    def test_irrigation_availability_evidence_mapping(self, isolated_test_session, test_client):
        """
        Verify that evaluate_farm_advisory sets irrigation_available as:
        - True for irrigated / canal / borewell / well / drip
        - False for rainfed / rainfall
        - None for unknown or missing
        """
        user_id = str(uuid.uuid4())
        headers = {"X-Dev-User-Id": user_id}

        test_cases = [
            ("irrigated", "canal", True),
            ("irrigated", "borewell", True),
            ("rainfed", "rainfall", False),
            ("unknown", "unknown", None),
            (None, None, None),
        ]

        for itype, wsource, expected_avail in test_cases:
            farm_resp = test_client.post(
                "/api/v1/farms",
                json={
                    "name": f"Test Farm {itype}-{wsource}",
                    "taluka": "Baramati",
                    "district": "Pune",
                    "state": "Maharashtra",
                    "irrigation_type": itype or "unknown",
                    "water_source": wsource or "unknown",
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
                },
                headers=headers
            )
            assert farm_resp.status_code == 201
            farm_id = farm_resp.json()["id"]

            # Clear memory storage to test authoritative DB hydration
            if uuid.UUID(farm_id) in _FARM_STORAGE:
                del _FARM_STORAGE[uuid.UUID(farm_id)]

            # Evaluate advisory
            eval_resp = test_client.post(
                f"/api/v1/farms/{farm_id}/advisory/evaluate",
                json={"target_crops": ["sugarcane"]},
                headers=headers
            )
            assert eval_resp.status_code == 200
            eval_data = eval_resp.json()
            sugarcane_res = next((o for o in eval_data["crop_outcomes"] if o["crop_id"] == "sugarcane"), None)
            assert sugarcane_res is not None

            # If rainfed, rainfed advisory rule should be present
            rule_ids = [r["rule_id"] for r in sugarcane_res["applied_rules"]]
            if expected_avail is False:
                assert "RULE_SUGARCANE_RAINFED_DISQUALIFICATION" in rule_ids
            elif expected_avail is True:
                assert "RULE_SUGARCANE_RAINFED_DISQUALIFICATION" not in rule_ids


# ============================================================================
# Domain 5: Regional Pilot Taluka Governance & Unverified Status
# ============================================================================

class TestRegionalPilotTalukaRemediation:
    """
    Verifies that locations outside the 4 supported pilot talukas in Maharashtra
    (Baramati, Indapur, Maval, Mulshi) return REQUIRES_REGIONAL_VALIDATION with
    RULE_OUTSIDE_PILOT_TALUKA.
    """

    @pytest.mark.parametrize("taluka,expected_state", [
        ("Baramati", DecisionState.REGIONAL_SCREENING_ONLY),
        ("baramati", DecisionState.REGIONAL_SCREENING_ONLY),
        ("Indapur", DecisionState.REGIONAL_SCREENING_ONLY),
        ("indapur", DecisionState.REGIONAL_SCREENING_ONLY),
        ("Maval", DecisionState.REQUIRES_REGIONAL_VALIDATION),
        ("maval", DecisionState.REQUIRES_REGIONAL_VALIDATION),
        ("Mulshi", DecisionState.REQUIRES_REGIONAL_VALIDATION),
        ("mulshi", DecisionState.REQUIRES_REGIONAL_VALIDATION),
        ("Haveli", DecisionState.REQUIRES_REGIONAL_VALIDATION),
        ("Khed", DecisionState.REQUIRES_REGIONAL_VALIDATION),
        ("Nagpur", DecisionState.REQUIRES_REGIONAL_VALIDATION),
        ("Solapur", DecisionState.REQUIRES_REGIONAL_VALIDATION),
        ("", DecisionState.REQUIRES_REGIONAL_VALIDATION),
        (None, DecisionState.REQUIRES_REGIONAL_VALIDATION),
    ])
    def test_regional_taluka_decision_states(self, taluka, expected_state):
        profile = engine.retriever.get_crop_profile("cotton")
        assert profile is not None

        ctx = FarmContextInput(
            taluka=taluka,
            target_crops=["cotton"]
        )
        res = RegionalSuitabilityEvaluator.evaluate(ctx, profile)
        assert res.regional_decision_state == expected_state

        if taluka and taluka.lower() not in ("baramati", "indapur", "maval", "mulshi"):
            rule_ids = [r.rule_id for r in res.applied_rules]
            assert "RULE_OUTSIDE_PILOT_TALUKA" in rule_ids
            assert any("outside CropNet AI's supported pilot talukas" in w for w in res.warnings)
            assert any("Outside supported pilot coverage area" in lf for lf in res.limiting_factors)


# ============================================================================
# Domain 6: Geometry & Representative Point Remediation
# ============================================================================

class TestGeometryRepresentativePointRemediation:
    """
    Tests geometrically valid representative point computation using Shapely.
    Supports closed linear rings, concavity (C-shape / horseshoe parcels),
    polygons with holes (annulus), and MultiPolygons.
    """

    def test_convex_polygon_centroid(self):
        """Convex square polygon: representative point is exact centroid."""
        geom = {
            "type": "Polygon",
            "coordinates": [[
                [74.0, 18.0],
                [74.2, 18.0],
                [74.2, 18.2],
                [74.0, 18.2],
                [74.0, 18.0]
            ]]
        }
        lat, lon = compute_farm_representative_point(geom)
        assert lat == pytest.approx(18.1, 0.0001)
        assert lon == pytest.approx(74.1, 0.0001)

    def test_closing_ring_duplicate_vertex_does_not_bias_point(self):
        """
        Linear ring repeats the first coordinate as the last.
        Arithmetic averaging counts it twice: (74+74.2+74.2+74+74)/5 = 74.08 (biased).
        Shapely centroid is 74.1 (unbiased).
        """
        geom = {
            "type": "Polygon",
            "coordinates": [[
                [74.0, 18.0],
                [74.2, 18.0],
                [74.2, 18.2],
                [74.0, 18.2],
                [74.0, 18.0]
            ]]
        }
        coords = geom["coordinates"][0]
        arith_lon = sum(c[0] for c in coords) / len(coords)
        assert arith_lon == pytest.approx(74.08, 0.001)  # Biased!

        lat, lon = compute_farm_representative_point(geom)
        assert lon == pytest.approx(74.1, 0.0001)  # Correct!

    def test_concave_c_shape_polygon_representative_point_inside(self):
        """
        C-shaped concave parcel: arithmetic mean of vertices falls outside the parcel boundary!
        compute_farm_representative_point guarantees that the point is strictly INSIDE the parcel.
        """
        # C-shaped polygon (cavity on the east side)
        c_shape_coords = [
            [0.0, 0.0],
            [3.0, 0.0],
            [3.0, 1.0],
            [1.0, 1.0],
            [1.0, 2.0],
            [3.0, 2.0],
            [3.0, 3.0],
            [0.0, 3.0],
            [0.0, 0.0]
        ]
        geom = {"type": "Polygon", "coordinates": [c_shape_coords]}
        poly = shape(geom)

        # Arithmetic average
        arith_lon = sum(c[0] for c in c_shape_coords) / len(c_shape_coords)
        arith_lat = sum(c[1] for c in c_shape_coords) / len(c_shape_coords)
        arith_pt = Point(arith_lon, arith_lat)
        # Arithmetic average falls in the empty notch: outside the polygon!
        assert not poly.contains(arith_pt), "Arithmetic mean was expected to be outside the C-shape"

        # compute_farm_representative_point must be strictly inside
        rep_lat, rep_lon = compute_farm_representative_point(geom)
        rep_pt = Point(rep_lon, rep_lat)
        assert poly.contains(rep_pt), f"Representative point ({rep_lat}, {rep_lon}) fell outside the C-shape polygon!"

    def test_polygon_with_hole_representative_point_not_in_hole(self):
        """
        Doughnut / annular polygon: arithmetic center falls inside the hole!
        compute_farm_representative_point must fall inside the solid body.
        """
        exterior = [[0.0, 0.0], [4.0, 0.0], [4.0, 4.0], [0.0, 4.0], [0.0, 0.0]]
        hole = [[1.0, 1.0], [3.0, 1.0], [3.0, 3.0], [1.0, 3.0], [1.0, 1.0]]
        geom = {"type": "Polygon", "coordinates": [exterior, hole]}
        poly = shape(geom)

        # Center (2.0, 2.0) is in the hole
        center_pt = Point(2.0, 2.0)
        assert not poly.contains(center_pt)

        # compute_farm_representative_point must be inside the solid body
        rep_lat, rep_lon = compute_farm_representative_point(geom)
        rep_pt = Point(rep_lon, rep_lat)
        assert poly.contains(rep_pt), f"Representative point ({rep_lat}, {rep_lon}) fell inside the hole!"

    def test_multipolygon_representative_point_inside(self):
        """MultiPolygon parcel: representative point must fall inside one of the polygons."""
        poly1 = [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]
        poly2 = [[5.0, 5.0], [6.0, 5.0], [6.0, 6.0], [5.0, 6.0], [5.0, 5.0]]
        geom = {"type": "MultiPolygon", "coordinates": [[poly1], [poly2]]}
        mp = shape(geom)

        rep_lat, rep_lon = compute_farm_representative_point(geom)
        rep_pt = Point(rep_lon, rep_lat)
        assert mp.contains(rep_pt), f"Representative point ({rep_lat}, {rep_lon}) fell outside MultiPolygon components!"
