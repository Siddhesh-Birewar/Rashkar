"""
Deterministic Agricultural Water Intelligence Engine.

Implements:
1. Validated ionic unit conversions (mg/L <-> meq/L) using standard equivalent weights.
2. Validated SAR and RSC calculations with strict input verification.
3. Institutional water evaluation rules sourced directly from:
   - Bureau of Indian Standards IS 11624:2019 ("Guidelines for the Quality of Irrigation Water", First Revision)
   - ICAR - Central Soil Salinity Research Institute (CSSRI) Karnal:
     * Minhas, P.S. and Tyagi, N.K. (1998), "Guidelines for Irrigation with Saline and Alkali Waters",
       Technical Bulletin No. 1/98, CSSRI Karnal
     * Minhas, P.S. and Gupta, R.K. (1992), "Quality of Irrigation Water: Assessment and Management", ICAR New Delhi
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
    - Boron, Nitrate, Trace Elements -> mg/L
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

    # 4. pH, Boron, Nitrate, Trace Elements (IS 11624:2019 Table 6)
    if parameter_key == "ph":
        return round(original_value, 2), "pH"
    if parameter_key in (
        "boron", "nitrate", "fluoride", "iron", "zinc",
        "copper", "manganese", "arsenic", "lead", "cadmium", "chromium", "nickel"
    ):
        if unit_clean in ("mg/l", "ppm"):
            return round(original_value, 3), "mg/L"

    return original_value, original_unit


def calculate_sar_and_rsc(
    measurements: Dict[str, Dict[str, Any]],
    allow_carbonate_inference: bool = False,
) -> WaterCalculatedIndicators:
    """
    Computes Sodium Adsorption Ratio (SAR) and Residual Sodium Carbonate (RSC).

    Formulas:
    SAR = Na / sqrt((Ca + Mg) / 2)
    RSC = (CO3 + HCO3) - (Ca + Mg)

    Strict Validation Constraints:
    - All ions (Na, Ca, Mg, CO3, HCO3) must be in meq/L.
    - If required ions are missing or cannot be converted to meq/L, indicators are marked UNAVAILABLE or INCOMPLETE_INPUTS.
    - Missing carbonate (CO3) handling:
      * By default (allow_carbonate_inference=False), missing CO3 produces INCOMPLETE_INPUTS.
        Missing carbonate is NEVER silently assumed to be zero.
      * Laboratory-measured carbonate is ALWAYS preserved with LAB_MEASURED provenance and never overwritten.
      * If allow_carbonate_inference=True and pH < 8.3, inferred CO3=0.0 is marked INFERRED_APHA_2320B
        per APHA Standard Methods 2320 B / USDA Handbook 60 Method 82 phenolphthalein alkalinity endpoint.
      * If pH >= 8.3 or missing under inference mode, CO3 is not inferred and RSC returns INCOMPLETE_INPUTS.
    - Preserves calculation notes and exact inputs used.
    """
    inputs_used: Dict[str, Any] = {}
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

    # Validation check: reject negative ionic inputs
    invalid_negatives = []
    for ion_name, val in [("Na", na), ("Ca", ca), ("Mg", mg), ("CO3", co3), ("HCO3", hco3)]:
        if val is not None and val < 0:
            invalid_negatives.append(f"{ion_name}={val}")

    if invalid_negatives:
        notes.append(f"Calculation rejected: negative concentration encountered ({', '.join(invalid_negatives)}).")
        return WaterCalculatedIndicators(
            sar=None,
            sar_status="INVALID_INPUT",
            rsc=None,
            rsc_status="INVALID_INPUT",
            inputs_used=inputs_used,
            calculation_notes=notes,
        )

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

    # Carbonate (CO3) handling:
    co3_provenance = "NOT_PROVIDED"
    co3_effective = co3

    if co3 is not None:
        co3_provenance = "LAB_MEASURED"
        notes.append(f"Carbonate (CO3) preserved as laboratory-measured: {co3} meq/L.")
    elif allow_carbonate_inference:
        ph_item = measurements.get("ph")
        ph_val = ph_item.get("original_value") if ph_item else None
        if ph_val is not None and ph_val < 8.3:
            co3_effective = 0.0
            co3_provenance = "INFERRED_APHA_2320B"
            notes.append(
                f"Carbonate (CO3) not reported; inferred as 0.0 meq/L per APHA 2320 B / USDA Handbook 60 "
                f"phenolphthalein alkalinity titration convention (pH {ph_val} < 8.3)."
            )
        elif ph_val is not None and ph_val >= 8.3:
            notes.append(f"Carbonate (CO3) not reported; cannot assume 0.0 meq/L because pH is alkaline ({ph_val} >= 8.3).")
        else:
            notes.append("Carbonate (CO3) not reported and pH is unavailable; cannot infer 0.0 meq/L.")
    else:
        notes.append(
            "Carbonate (CO3) not reported by laboratory. Per BIS IS 11624:2019, RSC requires measured carbonate; "
            "automatic inference is disabled to prevent missing values silently becoming zero."
        )

    inputs_used["CO3_provenance"] = co3_provenance
    # Ensure missing carbonate does not silently become 0.0 in inputs_used
    inputs_used["CO3_meq_l"] = co3 if co3_provenance == "LAB_MEASURED" else (co3_effective if co3_provenance == "INFERRED_APHA_2320B" else None)

    if hco3 is not None and ca is not None and mg is not None and co3_effective is not None:
        rsc_val = round((co3_effective + hco3) - (ca + mg), 2)
        rsc_status = "AVAILABLE"
        notes.append(
            f"RSC calculated deterministically: {rsc_val} meq/L "
            f"(CO3={co3_effective} [{co3_provenance}], HCO3={hco3}, Ca={ca}, Mg={mg})."
        )
    elif rep_rsc is not None:
        rsc_val = float(rep_rsc)
        rsc_status = "REPORTED"
        notes.append(f"RSC taken directly from laboratory report: {rsc_val} meq/L.")
    else:
        rsc_status = "INCOMPLETE_INPUTS"
        missing_rsc = [k for k, v in [("HCO3", hco3), ("Ca", ca), ("Mg", mg)] if v is None]
        if co3_effective is None and "CO3" not in missing_rsc:
            missing_rsc.append("CO3")
        notes.append(f"RSC unavailable: missing required constituents ({', '.join(missing_rsc)}).")

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
    - Bureau of Indian Standards IS 11624:2019 ("Guidelines for the Quality of Irrigation Water", First Revision)
    - ICAR - Central Soil Salinity Research Institute (CSSRI) Karnal Guidelines:
      Minhas & Tyagi (1998) Technical Bulletin No. 1/98 & Minhas & Gupta (1992)
    """

    @classmethod
    def evaluate(
        cls,
        measurements: Dict[str, Dict[str, Any]],
        farm_id: str,
        water_source_id: Optional[str] = None,
        soil_clay_percent: Optional[float] = None,
        annual_rainfall_mm: Optional[float] = None,
        allow_carbonate_inference: bool = False,
    ) -> WaterQualityEvaluationResponse:
        evaluations: List[WaterRuleEvaluationItem] = []

        # 1. Compute SAR and RSC
        calc_indices = calculate_sar_and_rsc(
            measurements,
            allow_carbonate_inference=allow_carbonate_inference,
        )

        # 2. Evaluate Salinity Hazard (EC) - IS 11624:2019 Clause 5.1.1
        ec_val: Optional[float] = None
        ec_item = measurements.get("electrical_conductivity")
        if ec_item and ec_item.get("normalized_value") is not None:
            ec = float(ec_item["normalized_value"])
            ec_val = ec
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
                    rule_id="BIS-11624-2019-CL-5.1.1-EC",
                    source_citation="Bureau of Indian Standards IS 11624:2019 (First Revision), Clause 5.1.1",
                    applicable_standard="BIS IS 11624:2019",
                    management_guidance=guide,
                    scope_and_limitations="Applies to mineral soils under typical semi-arid Indian irrigation conditions.",
                )
            )

        # 3. Evaluate Sodicity Hazard (SAR) - IS 11624:2019 Clause 5.1.3
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
                    rule_id="BIS-11624-2019-CL-5.1.3-SAR",
                    source_citation="Bureau of Indian Standards IS 11624:2019 (First Revision), Clause 5.1.3",
                    applicable_standard="BIS IS 11624:2019",
                    management_guidance=guide,
                    scope_and_limitations="Texture-dependent: clay soils are significantly more sensitive to SAR than sandy loams.",
                )
            )

        # 4. Evaluate Carbonate Hazard (RSC) - ICAR-CSSRI Tech Bulletin 1/98 & IS 11624:2019 Clause 5.1.4
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
                    rule_id="CSSRI-TECH-BULL-1-98-RSC",
                    source_citation="ICAR-Central Soil Salinity Research Institute (CSSRI) Karnal, Technical Bulletin No. 1/98 (Minhas & Tyagi 1998) & BIS IS 11624:2019 Clause 5.1.4",
                    applicable_standard="ICAR-CSSRI Karnal & BIS IS 11624:2019",
                    management_guidance=guide,
                    scope_and_limitations="Directly affects soil permeability and pH through sodium accumulation in root zone.",
                )
            )

        # 5. Table 1: Combined EC/SAR/RSC Classification of Poor-Quality Groundwaters (IS 11624:2019 Table 1)
        if ec_val is not None and sar_val is not None and rsc_val is not None:
            # Group A: Saline Waters (RSC < 2.5 meq/L)
            if rsc_val < 2.5:
                if sar_val < 10.0:
                    if ec_val < 2.0:
                        group_name = "Good Water"
                        group_lvl = WaterQualityHazardLevel.SAFE
                        group_guide = "Suitable for all crops on all soils without danger of salinity or sodicity."
                    elif ec_val <= 4.0:
                        group_name = "Marginally Saline"
                        group_lvl = WaterQualityHazardLevel.MARGINAL
                        group_guide = "Suitable for crops with moderate salt tolerance on permeable soils. Good drainage required."
                    else:
                        group_name = "Saline Water"
                        group_lvl = WaterQualityHazardLevel.HIGH
                        group_guide = "Requires salt-tolerant crops, good internal soil drainage, and leaching fraction."
                else:  # sar_val >= 10.0
                    group_name = "High-SAR Saline"
                    group_lvl = WaterQualityHazardLevel.HAZARDOUS
                    group_guide = "High sodium and salinity hazard. Gypsum amendment required to displace exchangeable sodium, plus adequate leaching."
            else:
                # Group B: Alkali Waters (RSC >= 2.5 meq/L)
                if sar_val < 10.0:
                    if rsc_val <= 4.0:
                        group_name = "Marginally Alkali"
                        group_lvl = WaterQualityHazardLevel.MARGINAL
                        group_guide = "Gypsum amendment recommended to neutralize excess residual alkalinity and prevent sodification."
                    else:
                        group_name = "Alkali Water"
                        group_lvl = WaterQualityHazardLevel.HIGH
                        group_guide = "Regular gypsum amendment or sulfuric acid treatment needed to precipitate carbonates and lower RSC below 2.5."
                else:  # sar_val >= 10.0
                    group_name = "High-SAR Alkali"
                    group_lvl = WaterQualityHazardLevel.HAZARDOUS
                    group_guide = "Severely poor quality water. Continuous gypsum amendment, organic matter additions, and deep drainage strictly required."

            evaluations.append(
                WaterRuleEvaluationItem(
                    parameter_key="is11624_table1_combined_group",
                    parameter_name="IS 11624:2019 Table 1 Combined Groundwater Group",
                    observed_value=ec_val,
                    observed_unit="EC dS/m",
                    hazard_level=group_lvl,
                    hazard_title=f"Table 1 Group: {group_name}",
                    rule_id="BIS-11624-2019-TAB1-COMBINED",
                    source_citation="Bureau of Indian Standards IS 11624:2019 (First Revision), Table 1 & Clause 5.1",
                    applicable_standard="BIS IS 11624:2019",
                    management_guidance=group_guide,
                    scope_and_limitations="Combined institutional classification integrating EC, SAR, and RSC into poor-quality groundwater categories.",
                )
            )
        else:
            # When any constituent of Table 1 is missing, mark unverified
            missing_tab1 = []
            if ec_val is None:
                missing_tab1.append("EC")
            if sar_val is None:
                missing_tab1.append("SAR")
            if rsc_val is None:
                missing_tab1.append("RSC")

            evaluations.append(
                WaterRuleEvaluationItem(
                    parameter_key="is11624_table1_combined_group",
                    parameter_name="IS 11624:2019 Table 1 Combined Groundwater Group",
                    observed_value=None,
                    observed_unit=None,
                    hazard_level=WaterQualityHazardLevel.UNVERIFIED,
                    hazard_title="Table 1 Combined Classification Unverified (Incomplete Inputs)",
                    rule_id="BIS-11624-2019-TAB1-COMBINED",
                    source_citation="Bureau of Indian Standards IS 11624:2019 (First Revision), Table 1 & Clause 5.1",
                    applicable_standard="BIS IS 11624:2019",
                    management_guidance=(
                        f"Definitive poor-quality groundwater grouping under BIS IS 11624:2019 Table 1 requires all three "
                        f"indicators: EC, SAR, and RSC. Currently missing: {', '.join(missing_tab1)}."
                    ),
                    scope_and_limitations="Conditional assessment: marked unverified pending complete water laboratory measurements.",
                )
            )

        # 6. Evaluate Boron Toxicity (Table 2 & Clause 5.1.6)
        boron_item = measurements.get("boron")
        if boron_item and boron_item.get("normalized_value") is not None:
            b_val = float(boron_item["normalized_value"])
            if b_val < 1.0:
                lvl = WaterQualityHazardLevel.SAFE
                title = "Class 1: Low Boron (<1.0 mg/L - Safe for all crops)"
                guide = "Boron concentration is within normal non-toxic limits."
            elif b_val <= 2.0:
                lvl = WaterQualityHazardLevel.MARGINAL
                title = "Class 2: Medium Boron (1.0 - 2.0 mg/L - Sensitive crops caution)"
                guide = "May cause leaf tip necrosis in sensitive crops (citrus, grapes, pulses). Tolerant crops (sugar beet, wheat) remain unaffected."
            elif b_val <= 4.0:
                lvl = WaterQualityHazardLevel.HIGH
                title = "Class 3: High Boron (2.0 - 4.0 mg/L - High Restriction)"
                guide = "Exceeds tolerance for semi-tolerant and sensitive crops. Requires high leaching fraction and tolerant crops."
            else:
                lvl = WaterQualityHazardLevel.HAZARDOUS
                title = "Class 4: Very High Boron (>4.0 mg/L - Toxic)"
                guide = "Severe boron toxicity for most Indian agricultural crops. Causes severe chlorosis and yield loss."

            evaluations.append(
                WaterRuleEvaluationItem(
                    parameter_key="boron",
                    parameter_name="Boron (B)",
                    observed_value=b_val,
                    observed_unit="mg/L",
                    hazard_level=lvl,
                    hazard_title=title,
                    rule_id="BIS-11624-2019-TAB2-BORON",
                    source_citation="Bureau of Indian Standards IS 11624:2019 (First Revision), Table 2 & Clause 5.1.6",
                    applicable_standard="BIS IS 11624:2019",
                    management_guidance=guide,
                    scope_and_limitations="Toxicity symptoms appear on older leaf tips and margins first.",
                )
            )

        # 7. Evaluate Chloride Toxicity (ICAR-CSSRI Tech Bull 1/98)
        cl_item = measurements.get("chloride")
        if cl_item and cl_item.get("normalized_value") is not None:
            cl_val = float(cl_item["normalized_value"])
            if cl_val < 4.0:
                lvl = WaterQualityHazardLevel.SAFE
                title = "Safe Chloride Level (<4.0 meq/L)"
                guide = "No restriction on use for furrow or drip irrigation."
            elif cl_val <= 10.0:
                lvl = WaterQualityHazardLevel.RESTRICTED
                title = "Slight to Moderate Restriction (4.0 - 10.0 meq/L)"
                guide = "Avoid overhead sprinkler irrigation on sensitive crops to prevent foliar absorption and burning."
            else:
                lvl = WaterQualityHazardLevel.HAZARDOUS
                title = "Severe Chloride Toxicity Risk (>10.0 meq/L)"
                guide = "High chloride hazard for sensitive crops. Use only surface/drip methods with salt-tolerant varieties."

            evaluations.append(
                WaterRuleEvaluationItem(
                    parameter_key="chloride",
                    parameter_name="Chloride (Cl-)",
                    observed_value=cl_val,
                    observed_unit="meq/L",
                    hazard_level=lvl,
                    hazard_title=title,
                    rule_id="CSSRI-TECH-BULL-1-98-CHLORIDE",
                    source_citation="ICAR-Central Soil Salinity Research Institute (CSSRI) Karnal, Technical Bulletin No. 1/98: 'Guidelines for Irrigation with Saline and Alkali Waters' (Minhas & Tyagi 1998)",
                    applicable_standard="ICAR-CSSRI Karnal & BIS IS 11624:2019",
                    management_guidance=guide,
                    scope_and_limitations="Overhead sprinkler irrigation significantly increases foliar injury risk.",
                )
            )

        # 8. Evaluate Trace Elements (IS 11624:2019 Table 6 & Clause 5.1.7.1)
        # Maximum permissible concentrations:
        trace_limits = {
            "fluoride": (1.0, "Fluoride (F-)"),
            "iron": (5.0, "Iron (Fe)"),
            "zinc": (2.0, "Zinc (Zn)"),
            "copper": (0.2, "Copper (Cu)"),
            "manganese": (0.2, "Manganese (Mn)"),
            "arsenic": (0.1, "Arsenic (As)"),
            "lead": (5.0, "Lead (Pb)"),
            "cadmium": (0.01, "Cadmium (Cd)"),
            "chromium": (0.1, "Chromium (Cr)"),
            "nickel": (0.2, "Nickel (Ni)"),
        }
        for trace_key, (max_perm, display_name) in trace_limits.items():
            t_item = measurements.get(trace_key)
            if t_item and t_item.get("normalized_value") is not None:
                t_val = float(t_item["normalized_value"])
                if t_val <= max_perm:
                    lvl = WaterQualityHazardLevel.SAFE
                    title = f"Within Permissible Limit ({t_val} <= {max_perm} mg/L)"
                    guide = f"{display_name} concentration is within safe threshold for continuous irrigation."
                else:
                    lvl = WaterQualityHazardLevel.HAZARDOUS
                    title = f"Exceeds Permissible Limit ({t_val} > {max_perm} mg/L)"
                    guide = f"{display_name} exceeds maximum permissible concentration under IS 11624:2019 Table 6. Risk of phytotoxicity and soil accumulation."

                evaluations.append(
                    WaterRuleEvaluationItem(
                        parameter_key=trace_key,
                        parameter_name=display_name,
                        observed_value=t_val,
                        observed_unit="mg/L",
                        hazard_level=lvl,
                        hazard_title=title,
                        rule_id=f"BIS-11624-2019-TAB6-{trace_key.upper()}",
                        source_citation="Bureau of Indian Standards IS 11624:2019 (First Revision), Table 6 & Clause 5.1.7.1",
                        applicable_standard="BIS IS 11624:2019",
                        management_guidance=guide,
                        scope_and_limitations="Trace element toxicity depends on soil pH, organic matter, and irrigation duration.",
                    )
                )

        # 9. Evaluate Soil Texture and Rainfall Suitability (IS 11624:2019 Tables 3, 4, 5 & Clauses 6.1 - 6.4)
        if soil_clay_percent is not None and annual_rainfall_mm is not None and ec_val is not None:
            # Texture categories per Table 3:
            # <10% clay (coarse), 10-20% (semi-coarse), 20-30% (semi-fine), >30% (fine/Vertisols)
            if soil_clay_percent > 30.0:
                ec_limit = 1.5 if annual_rainfall_mm < 550.0 else 2.0
                tex_desc = "Fine Textured (>30% clay / Vertisols)"
            elif soil_clay_percent > 20.0:
                ec_limit = 2.0 if annual_rainfall_mm < 550.0 else 3.0
                tex_desc = "Semi-Fine Textured (20-30% clay)"
            elif soil_clay_percent > 10.0:
                ec_limit = 3.0 if annual_rainfall_mm < 550.0 else 4.5
                tex_desc = "Semi-Coarse Textured (10-20% clay)"
            else:
                ec_limit = 4.0 if annual_rainfall_mm < 550.0 else 6.0
                tex_desc = "Coarse Textured (<10% clay)"

            if ec_val <= ec_limit:
                tex_lvl = WaterQualityHazardLevel.SAFE
                tex_title = f"Suitable for {tex_desc} (EC {ec_val} <= {ec_limit} dS/m)"
                tex_guide = f"Water EC is within safe limits for {tex_desc} at annual rainfall {annual_rainfall_mm:.0f} mm."
            else:
                tex_lvl = WaterQualityHazardLevel.HIGH
                tex_title = f"Exceeds Texture Limit for {tex_desc} (EC {ec_val} > {ec_limit} dS/m)"
                tex_guide = f"Water EC exceeds recommended limit ({ec_limit} dS/m) for {tex_desc} under {annual_rainfall_mm:.0f} mm rainfall. Clay dispersion and salinization risk."

            evaluations.append(
                WaterRuleEvaluationItem(
                    parameter_key="soil_texture_rainfall_suitability",
                    parameter_name="IS 11624:2019 Tables 3-5 Soil Texture & Rainfall Suitability",
                    observed_value=ec_val,
                    observed_unit="EC dS/m",
                    hazard_level=tex_lvl,
                    hazard_title=tex_title,
                    rule_id="BIS-11624-2019-TAB3-5-SUITABILITY",
                    source_citation="Bureau of Indian Standards IS 11624:2019 (First Revision), Clauses 6.1-6.4 & Tables 3-5",
                    applicable_standard="BIS IS 11624:2019",
                    management_guidance=tex_guide,
                    scope_and_limitations=f"Evaluated against verified farm soil clay ({soil_clay_percent:.1f}%) and annual rainfall ({annual_rainfall_mm:.0f} mm).",
                )
            )
        else:
            # Mark unverified when soil texture (% clay) or rainfall is missing
            evaluations.append(
                WaterRuleEvaluationItem(
                    parameter_key="soil_texture_rainfall_suitability",
                    parameter_name="IS 11624:2019 Tables 3-5 Soil Texture & Rainfall Suitability",
                    observed_value=None,
                    observed_unit=None,
                    hazard_level=WaterQualityHazardLevel.UNVERIFIED,
                    hazard_title="Conditional Suitability (Soil Texture and Rainfall Required)",
                    rule_id="BIS-11624-2019-TAB3-5-CONDITIONAL",
                    source_citation="Bureau of Indian Standards IS 11624:2019 (First Revision), Clauses 6.1-6.4 & Tables 3, 4, 5",
                    applicable_standard="BIS IS 11624:2019",
                    management_guidance=(
                        "Definitive agronomic suitability under BIS IS 11624:2019 Clauses 6.1-6.4 (Tables 3, 4, 5) requires "
                        "farm soil texture (% clay) and mean annual rainfall. In fine-textured soils (>30% clay / Vertisols), "
                        "permissible EC and SAR limits are significantly reduced compared to coarse-textured soils (<10% clay)."
                    ),
                    scope_and_limitations="Conditional assessment: marked unverified pending verified farm soil clay percentage and rainfall records.",
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
                "(BIS IS 11624:2019 and ICAR-CSSRI Karnal Technical Bulletin No. 1/98). "
                "It provides agronomic guidance and management options, not a single universal score."
            ),
        )
