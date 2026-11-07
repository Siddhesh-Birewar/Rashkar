"""
Deterministic Agricultural Water Intelligence Engine.

Implements:
1. Validated ionic unit conversions (mg/L <-> meq/L) using standard equivalent weights.
2. Validated SAR and RSC calculations with strict input verification.
3. Institutional water evaluation rules sourced directly from:
   - BIS IS 11624:1986 ("Guidelines for the quality of irrigation water")
   - ICAR - Central Soil Salinity Research Institute (CSSRI) Karnal (Minhas & Gupta 1992, CSSRI Bulletin No. 2/98)
4. Contextual CGWB regional groundwater data handling with non-fabrication safeguards.
"""
import math
from typing import Dict, Any, List, Optional, Tuple
from cropnet.services.api.app.schemas.water import (
    CANONICAL_WATER_PARAMETERS,
    WaterCalculatedIndicators,
    WaterQualityHazardLevel,
    WaterRuleEvaluationItem,
    WaterQualityEvaluationResponse,
)


def normalize_water_measurement(
    parameter_key: str,
    original_value: Optional[float],
    original_unit: str,
) -> Tuple[Optional[float], Optional[str]]:
    """
    Normalizes a water measurement to standard agricultural water units:
    - Cations and anions -> meq/L
    - Electrical Conductivity -> dS/m
    - TDS -> mg/L
    - pH, SAR -> unitless
    - Boron, Nitrate -> mg/L
    Returns (normalized_value, normalized_unit) or (original_value, original_unit) if no conversion applies.
    """
    if original_value is None:
        return None, None

    unit_clean = original_unit.strip().lower()
    param_info = CANONICAL_WATER_PARAMETERS.get(parameter_key)
    if not param_info:
        return original_value, original_unit

    # 1. Electrical Conductivity (EC): convert µS/cm or uS/cm -> dS/m
    if parameter_key == "electrical_conductivity":
        if "µs/cm" in unit_clean or "us/cm" in unit_clean or "microsiemens" in unit_clean:
            return round(original_value / 1000.0, 3), "dS/m"
        elif "ds/m" in unit_clean or "ms/cm" in unit_clean or "millisiemens" in unit_clean:
            return round(original_value, 3), "dS/m"
        return original_value, original_unit

    # 2. TDS: convert g/L -> mg/L
    if parameter_key == "tds":
        if unit_clean in ("g/l", "g/liter", "grams/liter"):
            return round(original_value * 1000.0, 1), "mg/L"
        elif unit_clean in ("mg/l", "ppm", "parts per million"):
            return round(original_value, 1), "mg/L"
        return original_value, original_unit

    # 3. Ionic parameters with equivalent weights
    eq_wt = param_info.get("equivalent_weight")
    if eq_wt is not None:
        # If already in meq/L
        if unit_clean in ("meq/l", "meq/liter", "me/l", "meql"):
            return round(original_value, 3), "meq/L"
        # If in mg/L or ppm, convert to meq/L = (mg/L) / eq_wt
        elif unit_clean in ("mg/l", "ppm", "mg/liter"):
            converted = original_value / eq_wt
            return round(converted, 3), "meq/L"

    # 4. pH, Boron, Nitrate, SAR, RSC
    if parameter_key == "ph":
        return round(original_value, 2), "pH"
    if parameter_key in ("boron", "nitrate"):
        if unit_clean in ("mg/l", "ppm"):
            return round(original_value, 3), "mg/L"

    return original_value, original_unit


def calculate_sar_and_rsc(
    measurements: Dict[str, Dict[str, Any]]
) -> WaterCalculatedIndicators:
    """
    Computes Sodium Adsorption Ratio (SAR) and Residual Sodium Carbonate (RSC).

    Formulas:
    SAR = Na / sqrt((Ca + Mg) / 2)
    RSC = (CO3 + HCO3) - (Ca + Mg)

    Strict Validation Constraints:
    - All ions (Na, Ca, Mg, CO3, HCO3) must be in meq/L.
    - If required ions are missing or cannot be converted to meq/L, indicators are marked UNAVAILABLE.
    - Preserves calculation notes and exact inputs used.
    """
    inputs_used: Dict[str, Optional[float]] = {}
    notes: List[str] = []

    def get_meq_l(key: str) -> Optional[float]:
        item = measurements.get(key)
        if not item:
            return None
        norm_val = item.get("normalized_value")
        norm_unit = item.get("normalized_unit", "").strip().lower()
        if norm_val is not None and norm_unit in ("meq/l", "me/l"):
            return float(norm_val)
        # Attempt fallback conversion if original unit is mg/L
        orig_val = item.get("original_value")
        orig_unit = str(item.get("original_unit", "")).strip().lower()
        if orig_val is not None:
            n_val, n_unit = normalize_water_measurement(key, float(orig_val), orig_unit)
            if n_val is not None and n_unit == "meq/L":
                return float(n_val)
        return None

    na = get_meq_l("sodium")
    ca = get_meq_l("calcium")
    mg = get_meq_l("magnesium")
    co3 = get_meq_l("carbonate")
    hco3 = get_meq_l("bicarbonate")

    inputs_used["Na_meq_l"] = na
    inputs_used["Ca_meq_l"] = ca
    inputs_used["Mg_meq_l"] = mg
    inputs_used["CO3_meq_l"] = co3
    inputs_used["HCO3_meq_l"] = hco3

    # Check if report explicitly provides pre-calculated SAR or RSC
    rep_sar = measurements.get("sar", {}).get("original_value")
    rep_rsc = measurements.get("rsc", {}).get("original_value")

    # 1. SAR Calculation
    sar_val: Optional[float] = None
    sar_status: str = "UNAVAILABLE"

    if na is not None and ca is not None and mg is not None:
        ca_plus_mg = ca + mg
        if ca_plus_mg > 0:
            sar_val = round(na / math.sqrt(ca_plus_mg / 2.0), 2)
            sar_status = "AVAILABLE"
            notes.append(f"SAR calculated deterministically: {sar_val} (Na={na}, Ca={ca}, Mg={mg} meq/L).")
        else:
            sar_status = "ZERO_DIVISOR"
            notes.append("SAR calculation aborted: (Ca + Mg) sum is zero or negative.")
    elif rep_sar is not None:
        sar_val = float(rep_sar)
        sar_status = "REPORTED"
        notes.append(f"SAR taken directly from laboratory report: {sar_val}.")
    else:
        sar_status = "INCOMPLETE_INPUTS"
        missing_sar = [k for k, v in [("Na", na), ("Ca", ca), ("Mg", mg)] if v is None]
        notes.append(f"SAR unavailable: missing essential ionic constituents ({', '.join(missing_sar)}).")

    # 2. RSC Calculation
    rsc_val: Optional[float] = None
    rsc_status: str = "UNAVAILABLE"

    # In many standard reports, carbonate (CO3) is 0 at pH < 8.3
    # If CO3 is absent from report, we treat as 0 ONLY if HCO3, Ca, and Mg are present and report indicates pH < 8.3
    co3_effective = co3
    if co3_effective is None and hco3 is not None:
        ph_item = measurements.get("ph")
        ph_val = ph_item.get("original_value") if ph_item else None
        if ph_val is not None and ph_val < 8.3:
            co3_effective = 0.0
            notes.append(f"Carbonate (CO3) not detected or absent; assumed 0.0 meq/L based on pH {ph_val} < 8.3.")

    if hco3 is not None and ca is not None and mg is not None and co3_effective is not None:
        rsc_val = round((co3_effective + hco3) - (ca + mg), 2)
        rsc_status = "AVAILABLE"
        notes.append(f"RSC calculated deterministically: {rsc_val} meq/L (CO3={co3_effective}, HCO3={hco3}, Ca={ca}, Mg={mg}).")
    elif rep_rsc is not None:
        rsc_val = float(rep_rsc)
        rsc_status = "REPORTED"
        notes.append(f"RSC taken directly from laboratory report: {rsc_val} meq/L.")
    else:
        rsc_status = "INCOMPLETE_INPUTS"
        missing_rsc = [k for k, v in [("HCO3", hco3), ("Ca", ca), ("Mg", mg)] if v is None]
        notes.append(f"RSC unavailable: missing required anions/cations ({', '.join(missing_rsc)}).")

    return WaterCalculatedIndicators(
        sar=sar_val,
        sar_status=sar_status,
        rsc=rsc_val,
        rsc_status=rsc_status,
        inputs_used=inputs_used,
        calculation_notes=notes,
    )


class WaterQualityEvaluator:
    """
    Evaluates irrigation water quality against institutional Indian standards:
    - BIS IS 11624:1986 ('Guidelines for the quality of irrigation water')
    - ICAR - Central Soil Salinity Research Institute (CSSRI) Karnal Guidelines
    """

    @classmethod
    def evaluate(
        cls,
        measurements: Dict[str, Dict[str, Any]],
        farm_id: str,
        water_source_id: Optional[str] = None,
    ) -> WaterQualityEvaluationResponse:
        evaluations: List[WaterRuleEvaluationItem] = []

        # 1. Compute SAR and RSC
        calc_indices = calculate_sar_and_rsc(measurements)

        # 2. Evaluate Salinity Hazard (EC)
        ec_item = measurements.get("electrical_conductivity")
        if ec_item and ec_item.get("normalized_value") is not None:
            ec = float(ec_item["normalized_value"])
            if ec < 1.5:
                lvl = WaterQualityHazardLevel.LOW
                title = "Low Salinity (Class 1 - Safe)"
                guide = "Water can be used for irrigation with most crops on most soils without developing salinity."
            elif ec <= 3.0:
                lvl = WaterQualityHazardLevel.MEDIUM
                title = "Medium Salinity (Class 2 - Moderate Restriction)"
                guide = "Water can be used on soils with moderate drainage. Leaching fraction required for salt-sensitive crops."
            elif ec <= 5.0:
                lvl = WaterQualityHazardLevel.HIGH
                title = "High Salinity (Class 3 - High Restriction)"
                guide = "Requires good drainage, high leaching fraction, and salt-tolerant crops (e.g. barley, cotton, wheat)."
            else:
                lvl = WaterQualityHazardLevel.VERY_HIGH
                title = "Very High Salinity (Class 4 - Hazardous)"
                guide = "Unsuitable for irrigation under ordinary conditions. Permissible only on permeable soils with high rainfall/dilution."

            evaluations.append(
                WaterRuleEvaluationItem(
                    parameter_key="electrical_conductivity",
                    parameter_name="Electrical Conductivity (EC)",
                    observed_value=ec,
                    observed_unit="dS/m",
                    hazard_level=lvl,
                    hazard_title=title,
                    rule_id="BIS-11624-TAB1-EC",
                    source_citation="Bureau of Indian Standards IS 11624:1986, Table 1 (Salinity Classes)",
                    applicable_standard="BIS IS 11624:1986",
                    management_guidance=guide,
                    scope_and_limitations="Applies to mineral soils under typical semi-arid Indian irrigation conditions.",
                )
            )

        # 3. Evaluate Sodicity Hazard (SAR)
        sar_val = calc_indices.sar
        if sar_val is not None:
            if sar_val < 10.0:
                lvl = WaterQualityHazardLevel.LOW
                title = "Low Sodium Hazard (S1 - Safe)"
                guide = "Can be used for irrigation on almost all soils with little danger of harmful sodification."
            elif sar_val <= 18.0:
                lvl = WaterQualityHazardLevel.MEDIUM
                title = "Medium Sodium Hazard (S2 - Moderate Sodicity)"
                guide = "Appreciable sodium hazard in fine-textured soils (clay/vertisols). Manageable on coarse/organic soils with good permeability. Gypsum amendment may be needed."
            elif sar_val <= 26.0:
                lvl = WaterQualityHazardLevel.HIGH
                title = "High Sodium Hazard (S3 - High Sodicity)"
                guide = "Produces harmful sodicity in most soils. Requires special soil management, good drainage, organic matter, and gypsum application."
            else:
                lvl = WaterQualityHazardLevel.VERY_HIGH
                title = "Very High Sodium Hazard (S4 - Hazardous)"
                guide = "Generally unsuitable for irrigation without severe soil degradation, unless gypsum is applied continuously with adequate drainage."

            evaluations.append(
                WaterRuleEvaluationItem(
                    parameter_key="sar",
                    parameter_name="Sodium Adsorption Ratio (SAR)",
                    observed_value=sar_val,
                    observed_unit="ratio",
                    hazard_level=lvl,
                    hazard_title=title,
                    rule_id="BIS-11624-TAB2-SAR",
                    source_citation="Bureau of Indian Standards IS 11624:1986, Table 2 & ICAR-CSSRI Karnal",
                    applicable_standard="BIS IS 11624:1986",
                    management_guidance=guide,
                    scope_and_limitations="Texture-dependent: clay soils are significantly more sensitive to SAR than sandy loams.",
                )
            )

        # 4. Evaluate Carbonate Hazard (RSC)
        rsc_val = calc_indices.rsc
        if rsc_val is not None:
            if rsc_val < 1.25:
                lvl = WaterQualityHazardLevel.SAFE
                title = "Safe (Low Alkalinity Hazard)"
                guide = "Water can be used safely without risk of residual sodium carbonate accumulation."
            elif rsc_val <= 2.50:
                lvl = WaterQualityHazardLevel.MARGINAL
                title = "Marginal (Moderate Alkalinity Hazard)"
                guide = f"Marginal quality. Caution required. Recommended gypsum application: {(rsc_val - 1.25) * 86.0:.1f} kg gypsum per hectare per 10 cm irrigation depth."
            else:
                lvl = WaterQualityHazardLevel.HAZARDOUS
                title = "Unsuitable (High Alkalinity Hazard)"
                guide = f"Hazardous water. Calcium and magnesium will precipitate as carbonates, causing severe dispersion and crusting. Required gypsum amendment: {(rsc_val - 1.25) * 86.0:.1f} kg/ha/irrigation or water treatment required."

            evaluations.append(
                WaterRuleEvaluationItem(
                    parameter_key="rsc",
                    parameter_name="Residual Sodium Carbonate (RSC)",
                    observed_value=rsc_val,
                    observed_unit="meq/L",
                    hazard_level=lvl,
                    hazard_title=title,
                    rule_id="CSSRI-RSC-GUIDELINE",
                    source_citation="ICAR-Central Soil Salinity Research Institute (CSSRI) Karnal, Bulletin 2/98 & BIS 11624:1986 Table 3",
                    applicable_standard="ICAR-CSSRI Karnal & BIS IS 11624:1986",
                    management_guidance=guide,
                    scope_and_limitations="Directly affects soil permeability and pH through sodium accumulation in root zone.",
                )
            )

        # 5. Evaluate Boron Toxicity (if measured)
        boron_item = measurements.get("boron")
        if boron_item and boron_item.get("normalized_value") is not None:
            b_val = float(boron_item["normalized_value"])
            if b_val < 1.0:
                lvl = WaterQualityHazardLevel.SAFE
                title = "Safe for all crops"
                guide = "Boron concentration is within normal non-toxic limits."
            elif b_val <= 2.0:
                lvl = WaterQualityHazardLevel.MARGINAL
                title = "Marginal - Sensitive crops caution"
                guide = "May cause leaf tip necrosis in sensitive crops (citrus, grapes, pulses). Tolerant crops (sugar beet, wheat) remain unaffected."
            else:
                lvl = WaterQualityHazardLevel.HAZARDOUS
                title = "Toxic Boron Concentration"
                guide = "Exceeds tolerance for most Indian crops. Causes chlorosis and yield loss."

            evaluations.append(
                WaterRuleEvaluationItem(
                    parameter_key="boron",
                    parameter_name="Boron (B)",
                    observed_value=b_val,
                    observed_unit="mg/L",
                    hazard_level=lvl,
                    hazard_title=title,
                    rule_id="BIS-11624-BORON",
                    source_citation="BIS IS 11624:1986, Table 4 (Boron Tolerances)",
                    applicable_standard="BIS IS 11624:1986",
                    management_guidance=guide,
                    scope_and_limitations="Toxicity symptoms appear on older leaf tips and margins first.",
                )
            )

        # 6. Evaluate Chloride Toxicity (if measured)
        cl_item = measurements.get("chloride")
        if cl_item and cl_item.get("normalized_value") is not None:
            cl_val = float(cl_item["normalized_value"])
            if cl_val < 4.0:
                lvl = WaterQualityHazardLevel.SAFE
                title = "Safe Chloride Level"
                guide = "No restriction on use for furrow or drip irrigation."
            elif cl_val <= 10.0:
                lvl = WaterQualityHazardLevel.RESTRICTED
                title = "Slight to Moderate Restriction"
                guide = "Avoid overhead sprinkler irrigation on sensitive crops to prevent foliar absorption and burning."
            else:
                lvl = WaterQualityHazardLevel.HAZARDOUS
                title = "Severe Chloride Toxicity Risk"
                guide = "High chloride hazard for sensitive crops. Use only surface/drip methods with salt-tolerant varieties."

            evaluations.append(
                WaterRuleEvaluationItem(
                    parameter_key="chloride",
                    parameter_name="Chloride (Cl-)",
                    observed_value=cl_val,
                    observed_unit="meq/L",
                    hazard_level=lvl,
                    hazard_title=title,
                    rule_id="ICAR-CSSRI-CHLORIDE",
                    source_citation="ICAR-CSSRI Guidelines for Saline Water Use in Agriculture (1998)",
                    applicable_standard="ICAR-CSSRI Karnal",
                    management_guidance=guide,
                    scope_and_limitations="Overhead sprinkler irrigation significantly increases foliar injury risk.",
                )
            )

        crop_sensitivities = {
            "Sensitive": "Pulses (Chickpea, Green gram), Citrus, Strawberry, Onion, Sesame",
            "Semi-Tolerant": "Wheat, Rice, Maize, Sorghum, Tomato, Potato, Sugarcane",
            "Tolerant": "Barley, Cotton, Mustard, Sugar beet, Date palm",
        }

        from datetime import datetime
        return WaterQualityEvaluationResponse(
            farm_id=farm_id,
            water_source_id=water_source_id,
            evaluation_timestamp=datetime.utcnow(),
            evaluations=evaluations,
            calculated_indices=calc_indices,
            soil_drainage_caution=(
                "Irrigation water hazard is highly coupled to soil texture and drainage. "
                "Clay soils (Vertisols) require lower salinity and sodicity thresholds compared to sandy soils. "
                "Ensure periodic sub-surface drainage checks and avoid waterlogging with high-EC water."
            ),
            crop_sensitivity_overview=crop_sensitivities,
            regional_cgwb_context={
                "data_source": "Central Ground Water Board (CGWB) District Groundwater Yearbook",
                "classification_scope": "REGIONAL_CONTEXT_ONLY",
                "notice": (
                    "Regional aquifer data from CGWB monitoring wells provides contextual background on regional "
                    "salinity/fluoride trends and MUST NOT be substituted for an actual laboratory analysis of this farm's water source."
                ),
            },
            disclaimer=(
                "Water suitability evaluation is deterministic and derived strictly from institutional guidelines "
                "(BIS IS 11624:1986 and ICAR-CSSRI Karnal). It provides agronomic guidance and management options, "
                "not a single universal score."
            ),
        )
