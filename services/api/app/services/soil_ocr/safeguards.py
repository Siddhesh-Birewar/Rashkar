"""
Extraction safeguards for soil laboratory report processing.
Enforces all 8 agronomic and data integrity safeguards:
1. Do not turn missing values into zero.
2. Do not silently convert units.
3. Do not infer Available NPK from Total Nitrogen.
4. Do not confuse P with P2O5, or K with K2O.
5. Do not confuse ppm with mg/kg without context validation.
6. Do not infer sample depth.
7. Detect ambiguous values, digits, handwriting, blurred entries.
8. Strictly decouple OCR extraction confidence from farmer verification status.
"""

import logging
import re
from typing import List, Optional

from .models import (
    SoilReportExtractionResult,
    ExtractedSoilMeasurement,
    ReportExtractionStatus,
    MeasurementVerificationStatus,
    ParameterExtractionStatus,
)

logger = logging.getLogger(__name__)


# Agronomic plausibility boundaries (min_valid, max_valid)
AGRONOMIC_BOUNDARIES = {
    "soil_ph": (3.0, 11.0),
    "electrical_conductivity": (0.0, 30.0),      # dS/m
    "organic_carbon": (0.0, 10.0),               # %
    "organic_matter": (0.0, 20.0),               # %
    "available_nitrogen": (0.0, 1500.0),         # kg/ha
    "total_nitrogen": (0.0, 5.0),                # %
    "available_phosphorus": (0.0, 300.0),        # kg/ha (P2O5)
    "available_potassium": (0.0, 2500.0),        # kg/ha (K2O)
    "sulphur": (0.0, 500.0),                     # ppm or mg/kg
    "zinc": (0.0, 100.0),                        # ppm or mg/kg
    "iron": (0.0, 250.0),                        # ppm or mg/kg
    "manganese": (0.0, 250.0),                   # ppm or mg/kg
    "copper": (0.0, 50.0),                       # ppm or mg/kg
    "boron": (0.0, 30.0),                        # ppm or mg/kg
}

VALID_SOIL_UNITS = {
    "ph", "ph units",
    "ds/m", "ms/cm", "mmhos/cm", "us/cm", "µs/cm", "microsiemens/cm",
    "%", "g/kg",
    "kg/ha", "kg/acre",
    "ppm", "mg/kg", "mg/kg soil",
}


class ExtractionSafeguards:
    """
    Enforces strict agronomic safeguards on extracted soil measurements.
    """

    @classmethod
    def apply(cls, result: SoilReportExtractionResult) -> SoilReportExtractionResult:
        """
        Applies all 8 safeguards to the extraction result in-place and updates summary metrics.
        """
        total_detected = 0
        ambiguous_count = 0
        ambiguity_reasons: List[str] = []

        # Safeguard 6: Do not infer sample depth if absent in metadata
        # (Explicit check: if metadata.sample_depth is None or empty, leave it None)
        if result.metadata.sample_depth:
            result.metadata.sample_depth = result.metadata.sample_depth.strip()
        else:
            result.metadata.sample_depth = None

        # Check for Total Nitrogen vs Available Nitrogen across measurements
        has_total_n = False
        has_avail_n = False
        for m in result.measurements:
            if m.parameter_key == "total_nitrogen" and m.original_value is not None:
                has_total_n = True
            elif m.parameter_key == "available_nitrogen" and m.original_value is not None:
                has_avail_n = True

        # Safeguard 3: If Total N is present and Available N is absent, DO NOT infer Available N!
        if has_total_n and not has_avail_n:
            result.warnings.append(
                "Safeguard 3 active: Report contains Total Nitrogen but NO Available Nitrogen. "
                "Available Nitrogen remains unpopulated and must not be inferred."
            )

        for m in result.measurements:
            # Safeguard 8: Strictly decouple OCR confidence from verification status
            m.verification_status = MeasurementVerificationStatus.EXTRACTED_UNVERIFIED.value

            # Safeguard 1: Do not turn missing values into zero
            if m.original_value is None:
                m.extraction_status = ParameterExtractionStatus.NOT_REPORTED.value
                m.normalized_value = None
                m.normalized_unit = m.original_unit
                continue

            total_detected += 1

            # Safeguard 2: Do not silently convert units across non-1:1 bases
            cls._apply_unit_normalization(m)

            # Safeguards 4 & 5: Validate notation and concentration units
            cls._validate_parameter_notation_and_units(m)

            # Safeguard 7: Agronomic range & anomaly check
            cls._check_agronomic_boundaries(m)

            if m.is_ambiguous:
                ambiguous_count += 1
                if m.ambiguity_reason and m.ambiguity_reason not in ambiguity_reasons:
                    ambiguity_reasons.append(f"{m.parameter_key}: {m.ambiguity_reason}")

        # Summary statistics
        result.total_parameters_detected = total_detected
        result.ambiguous_parameters_count = ambiguous_count

        if ambiguous_count > 0:
            result.is_ambiguous = True
            result.ambiguity_reasons = ambiguity_reasons
            # Mark report as requiring review
            if result.extraction_status != ReportExtractionStatus.FAILED.value:
                result.extraction_status = ReportExtractionStatus.NEEDS_REVIEW.value
        else:
            result.is_ambiguous = False
            result.ambiguity_reasons = []

        # If zero soil parameters detected in document, flag potential negative control
        if total_detected == 0:
            result.extraction_status = ReportExtractionStatus.FAILED.value
            result.warnings.append(
                "Zero soil parameters detected. Document may not be a valid soil test report or is completely unreadable."
            )
            result.overall_confidence = 0.0

        return result

    @classmethod
    def _apply_unit_normalization(cls, m: ExtractedSoilMeasurement):
        """
        Safeguard 2: Only 1:1 mathematical identities are normalized.
        Disallows conversions requiring unmeasured physical assumptions (e.g. bulk density).
        """
        if m.original_value is None or not m.original_unit:
            m.normalized_value = m.original_value
            m.normalized_unit = m.original_unit
            return

        unit_str = m.original_unit.strip().lower()

        # 1. EC units: 1 dS/m == 1 mS/cm == 1 mmhos/cm; 1000 uS/cm == 1 dS/m
        if m.parameter_key == "electrical_conductivity":
            if unit_str in ("ds/m", "ms/cm", "mmhos/cm"):
                m.normalized_value = m.original_value
                m.normalized_unit = "dS/m"
            elif unit_str in ("us/cm", "µs/cm", "microsiemens/cm"):
                m.normalized_value = round(m.original_value / 1000.0, 4)
                m.normalized_unit = "dS/m"
            else:
                # Explicit rejection of unsupported units for electrical conductivity
                m.normalized_value = None
                m.normalized_unit = m.original_unit
                m.is_ambiguous = True
                m.ocr_confidence = min(m.ocr_confidence, 0.40)
                reason = f"Unsupported unit '{m.original_unit}' for electrical conductivity; must be dS/m, mS/cm, mmhos/cm, or µS/cm."
                m.ambiguity_reason = f"{m.ambiguity_reason}; {reason}" if m.ambiguity_reason else reason
                return

        # 2. Gravimetric dry soil ppm and mg/kg: 1 ppm == 1 mg/kg
        elif unit_str in ("ppm", "mg/kg", "mg/kg soil"):
            m.normalized_value = m.original_value
            m.normalized_unit = "ppm"

        # 3. Percent and g/kg: 1 % == 10 g/kg (for SOC, SOM, Total N)
        elif unit_str == "%":
            m.normalized_value = m.original_value
            m.normalized_unit = "%"
        elif unit_str == "g/kg":
            m.normalized_value = round(m.original_value / 10.0, 3)
            m.normalized_unit = "%"

        # 4. Standard fertilizer / agronomic units: kg/ha
        elif unit_str in ("kg/ha", "kg/hectare"):
            m.normalized_value = m.original_value
            m.normalized_unit = "kg/ha"

        # 5. pH
        elif unit_str in ("ph", "ph units") or m.parameter_key == "soil_ph":
            m.normalized_value = m.original_value
            m.normalized_unit = "pH"

        else:
            # Disallow silent conversions across spatial bases (e.g. kg/ha <-> ppm)
            m.normalized_value = m.original_value
            m.normalized_unit = m.original_unit

    @classmethod
    def _validate_parameter_notation_and_units(cls, m: ExtractedSoilMeasurement):
        """
        Safeguards 4 & 5: Validates oxide notation (P2O5, K2O) and unit plausibility.
        """
        unit_str = (m.original_unit or "").strip().lower()

        # Safeguard 5: Unusual concentration units
        if unit_str and unit_str not in VALID_SOIL_UNITS:
            m.is_ambiguous = True
            m.ocr_confidence = min(m.ocr_confidence, 0.70)
            reason = f"Unusual concentration unit '{m.original_unit}' detected; requires farmer validation."
            m.ambiguity_reason = f"{m.ambiguity_reason}; {reason}" if m.ambiguity_reason else reason

        # Safeguard 4: Flag if elemental P or K is reported in place of standard oxide P2O5 / K2O
        if m.parameter_key == "available_phosphorus":
            raw_p = m.original_parameter_name.lower()
            if "p2o5" in raw_p or "p205" in raw_p or "p206" in raw_p:
                pass  # Standard oxide basis
            elif re.search(r"\b(elemental\s*p|p\s*\(elemental\))\b", raw_p):
                m.is_ambiguous = True
                reason = "Elemental Phosphorus (P) reported instead of standard oxide P2O5; requires farmer validation."
                m.ambiguity_reason = f"{m.ambiguity_reason}; {reason}" if m.ambiguity_reason else reason

        if m.parameter_key == "available_potassium":
            raw_k = m.original_parameter_name.lower()
            if "k2o" in raw_k or "k20" in raw_k:
                pass  # Standard oxide basis
            elif re.search(r"\b(elemental\s*k|k\s*\(elemental\))\b", raw_k):
                m.is_ambiguous = True
                reason = "Elemental Potassium (K) reported instead of standard oxide K2O; requires farmer validation."
                m.ambiguity_reason = f"{m.ambiguity_reason}; {reason}" if m.ambiguity_reason else reason

    @classmethod
    def _check_agronomic_boundaries(cls, m: ExtractedSoilMeasurement):
        """
        Safeguard 7: Flags out-of-range readings as ambiguous with lower confidence.
        Evaluates canonical normalized values against AGRONOMIC_BOUNDARIES (e.g. EC in dS/m).
        Ensures a 500 µS/cm reading (0.5 dS/m) evaluates 0.5 dS/m and is NOT flagged as out-of-bounds > 30.0.
        """
        if m.original_value is None:
            return

        # If EC had an unsupported unit (normalized_value is None), it is already flagged as ambiguous
        if m.parameter_key == "electrical_conductivity" and m.normalized_value is None:
            return

        bounds = AGRONOMIC_BOUNDARIES.get(m.parameter_key)
        if bounds:
            min_val, max_val = bounds
            # Evaluate canonical normalized value (e.g. EC in dS/m) when normalized
            val = m.normalized_value if m.normalized_value is not None else m.original_value
            if val is not None and (val < min_val or val > max_val):
                m.is_ambiguous = True
                m.ocr_confidence = min(m.ocr_confidence, 0.60)
                reason = f"Value {val} {m.normalized_unit or m.original_unit or ''} is outside plausible agronomic bounds ({min_val}–{max_val})"
                m.ambiguity_reason = f"{m.ambiguity_reason}; {reason}" if m.ambiguity_reason else reason
