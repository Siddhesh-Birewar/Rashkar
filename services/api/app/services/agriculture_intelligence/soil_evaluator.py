"""
CropNet AI — Deterministic Soil Constraint Evaluator.

Evaluates soil pH, texture, depth, drainage, salinity, organic carbon,
and nutrient availability against verified crop requirements.
"""
from typing import List, Dict, Optional, Any
from cropnet.services.api.app.schemas.agriculture_intelligence import (
    FarmContextInput,
    AppliedRuleRecord,
    EvidenceTier,
    CitationMetadata
)
from cropnet.services.api.app.schemas.crop import CropFullProfileResponse
from cropnet.services.api.app.services.agriculture_intelligence.evidence_gate import EvidenceGate


class SoilEvaluationResult:
    def __init__(self, crop_id: str):
        self.crop_id = crop_id
        self.is_disqualified: bool = False
        self.limiting_factors: List[str] = []
        self.warnings: List[str] = []
        self.missing_parameters: List[str] = []
        self.applied_rules: List[AppliedRuleRecord] = []
        self.citations: List[CitationMetadata] = []


class SoilConstraintEvaluator:
    """
    Evaluates soil parameters deterministically against crop requirements.
    """

    @staticmethod
    def evaluate(
        ctx: FarmContextInput,
        profile: CropFullProfileResponse,
        citation: Optional[CitationMetadata] = None
    ) -> SoilEvaluationResult:
        res = SoilEvaluationResult(crop_id=profile.id)
        soil_req = profile.soil
        if not soil_req:
            res.missing_parameters.append("crop_soil_requirements")
            return res

        crop_id = profile.id
        primary_src_id = profile.sources[0].id if (profile.sources and len(profile.sources) > 0) else None
        tier = EvidenceGate.get_tier(soil_req.source_id or primary_src_id)

        # -------------------------------------------------------------
        # 1. Effective Soil Depth Constraint
        # -------------------------------------------------------------
        if ctx.soil_depth_cm is not None:
            min_depth = soil_req.min_soil_depth_cm
            # Pomegranate requires at least 45-60 cm depth; 20 cm depth over bedrock is a hard disqualifier
            if crop_id == "pomegranate" and ctx.soil_depth_cm < 45.0:
                res.is_disqualified = True
                msg = f"Soil depth of {ctx.soil_depth_cm} cm is critically inadequate for pomegranate (minimum 45–60 cm required). Shallow bedrock restricts taproot development and induces dieback."
                res.limiting_factors.append(msg)
                res.applied_rules.append(AppliedRuleRecord(
                    rule_id="RULE_SOIL_DEPTH_POMEGRANATE",
                    domain="Soil Intelligence",
                    parameter_checked="soil_depth_cm",
                    rule_statement="Pomegranate requires minimum 45–60 cm depth (ICAR-NRCP 2022)",
                    condition_met=False,
                    evidence_tier=tier,
                    citation=citation
                ))
            elif min_depth and ctx.soil_depth_cm < (min_depth * 0.5):
                # Severe depth deficit across other crops
                res.is_disqualified = True
                msg = f"Soil depth ({ctx.soil_depth_cm} cm) is severely below minimum required depth ({min_depth} cm)."
                res.limiting_factors.append(msg)
        else:
            res.missing_parameters.append("soil_depth_cm")

        # -------------------------------------------------------------
        # 2. Soil Drainage & Waterlogging Constraint
        # -------------------------------------------------------------
        drainage_val = ctx.drainage.lower() if ctx.drainage else ""
        has_standing_water = (ctx.standing_water_days or 0) >= 3 or ("waterlog" in drainage_val or "poor" in drainage_val)

        if has_standing_water:
            if crop_id in ("pomegranate", "chickpea"):
                res.is_disqualified = True
                reason = (
                    "Poor drainage / waterlogging violates mandatory aeration requirement. "
                    "In pomegranate, waterlogging triggers Phytophthora root rot and bacterial blight (ICAR-NRCP 2022). "
                    "In chickpea, water stagnation causes collar rot and rapid wilt (ICRISAT 2010)."
                )
                res.limiting_factors.append(reason)
                res.applied_rules.append(AppliedRuleRecord(
                    rule_id=f"RULE_DRAINAGE_{crop_id.upper()}",
                    domain="Soil Intelligence",
                    parameter_checked="drainage",
                    rule_statement="Mandatory well-drained soil; highly intolerant of standing water",
                    condition_met=False,
                    evidence_tier=tier,
                    citation=citation
                ))
        elif not ctx.drainage:
            res.missing_parameters.append("drainage")

        # -------------------------------------------------------------
        # 3. Soil pH Interpretation & Hard Bounds
        # -------------------------------------------------------------
        if ctx.soil_ph is not None:
            ph = ctx.soil_ph
            
            # Pomegranate pH rules (ICAR-NRCP 2022, p. 3)
            if crop_id == "pomegranate":
                best_min = soil_req.ph_best_suited_min or 6.5
                best_max = soil_req.ph_best_suited_max or 7.0
                tol_max = soil_req.ph_tolerable_max or 8.5
                
                if best_min <= ph <= best_max:
                    res.applied_rules.append(AppliedRuleRecord(
                        rule_id="RULE_PH_POMEGRANATE_OPTIMUM",
                        domain="Soil Intelligence",
                        parameter_checked="soil_ph",
                        rule_statement=f"Soil pH {ph} is within the best-suited range of 6.5–7.0 (ICAR-NRCP 2022)",
                        condition_met=True,
                        evidence_tier=tier,
                        citation=citation
                    ))
                elif best_max < ph <= tol_max:
                    res.warnings.append(
                        f"Soil pH {ph} is above optimum (6.5–7.0) but within tolerable upper limit (8.5). "
                        "High organic manuring and micronutrient management required (ICAR-NRCP 2022)."
                    )
                elif ph > tol_max:
                    res.is_disqualified = True
                    res.limiting_factors.append(
                        f"Soil pH {ph} exceeds upper tolerable limit of 8.5. Severe micronutrient lockout and lime chlorosis."
                    )
                elif ph < 6.5:
                    res.warnings.append(
                        f"Soil pH {ph} is below best-suited range (6.5–7.0). Authoritative lower tolerable limit is unverified (NULL)."
                    )

            # Chickpea pH rules (ICRISAT 2010, p. 8)
            elif crop_id == "chickpea":
                best_min = soil_req.ph_best_suited_min or 6.0
                best_max = soil_req.ph_best_suited_max or 8.0
                if best_min <= ph <= best_max:
                    res.applied_rules.append(AppliedRuleRecord(
                        rule_id="RULE_PH_CHICKPEA_BEST_SUITED",
                        domain="Soil Intelligence",
                        parameter_checked="soil_ph",
                        rule_statement=f"Soil pH {ph} is within best-suited range of 6.0–8.0 (ICRISAT 2010)",
                        condition_met=True,
                        evidence_tier=tier,
                        citation=citation
                    ))
                elif ph > 8.5:
                    res.is_disqualified = True
                    res.limiting_factors.append(
                        f"Soil pH {ph} is excessively alkaline for chickpea, impairing Rhizobium nodulation and iron uptake."
                    )
                elif ph < 6.0:
                    res.warnings.append(
                        f"Soil pH {ph} is acidic (< 6.0). Acidic soils inhibit chickpea nodulation and increase collar rot risk (ICRISAT 2010)."
                    )
        else:
            res.missing_parameters.append("soil_ph")

        # -------------------------------------------------------------
        # 4. Soil Texture Rules
        # -------------------------------------------------------------
        if ctx.soil_texture:
            tex = ctx.soil_texture.strip().lower()
            if crop_id == "pomegranate":
                if "light" in tex or "sandy loam" in tex or "gravel" in tex:
                    res.applied_rules.append(AppliedRuleRecord(
                        rule_id="RULE_TEXTURE_POMEGRANATE_LIGHT",
                        domain="Soil Intelligence",
                        parameter_checked="soil_texture",
                        rule_statement="Light soil is verified as most suitable for pomegranate (ICAR-NRCP 2022)",
                        condition_met=True,
                        evidence_tier=tier,
                        citation=citation
                    ))
                elif "heavy clay" in tex or "deep black" in tex:
                    res.warnings.append(
                        "Heavy clay / deep black Vertisols require ridge-and-furrow planting, subsoil drainage, and strict water regulation for pomegranate."
                    )
        else:
            res.missing_parameters.append("soil_texture")

        # -------------------------------------------------------------
        # 5. Salinity (Electrical Conductivity) Constraint
        # -------------------------------------------------------------
        q_lower = (ctx.user_query or "").lower()
        if ctx.electrical_conductivity_ds_m is not None:
            ec = ctx.electrical_conductivity_ds_m
            if crop_id == "chickpea" and ec >= 1.5:
                res.is_disqualified = True
                res.limiting_factors.append(
                    f"Soil Electrical Conductivity ({ec} dS/m) exceeds chickpea salinity threshold (1.5 dS/m). ICRISAT 2010 notes saline soil is unsuitable."
                )
        else:
            is_canal = (ctx.irrigation_source == "canal") or ("canal" in q_lower)
            is_well = (ctx.irrigation_source == "well") or ("well" in q_lower)
            if (ctx.taluka and ctx.taluka.lower() in ("indapur", "baramati")) and (is_canal or is_well):
                res.missing_parameters.append("electrical_conductivity_ds_m")
                if is_well and ("untested" in q_lower or "haven't tested" in q_lower or "not tested" in q_lower):
                    res.warnings.append(
                        "Water quality test is essential before continuous well irrigation in Baramati/Indapur "
                        "to prevent secondary soil salinization and sodicity (MPKV PoP 2023 / IIWBR 2022)."
                    )

        # -------------------------------------------------------------
        # 6. Nutrient Status (Available N & SOC)
        # -------------------------------------------------------------
        if ctx.available_nitrogen_kg_ha is not None:
            avail_n = ctx.available_nitrogen_kg_ha
            if avail_n < 280.0:
                res.warnings.append(
                    f"Available Nitrogen is Low ({avail_n} kg/ha < 280 kg/ha standard in MPKV PoP). Basal and split nitrogen fertilizer is mandatory."
                )
                res.applied_rules.append(AppliedRuleRecord(
                    rule_id="RULE_AVAILABLE_NITROGEN_DEFICIENCY",
                    domain="Soil Fertility Intelligence",
                    parameter_checked="available_nitrogen_kg_ha",
                    rule_statement="Available N < 280 kg/ha is Low; requires external nitrogen application (MPKV PoP 2023)",
                    condition_met=True,
                    evidence_tier=EvidenceTier.VERIFIED,
                    citation=citation
                ))
        
        if ctx.soil_organic_carbon_pct is not None:
            soc = ctx.soil_organic_carbon_pct
            if soc < 0.50:
                res.warnings.append(
                    f"Soil Organic Carbon is Low ({soc}% < 0.50% threshold for Maharashtra Vertisols). Incorporate 5–10 t/ha FYM or compost."
                )
                res.applied_rules.append(AppliedRuleRecord(
                    rule_id="RULE_SOIL_ORGANIC_CARBON_LOW",
                    domain="Soil Fertility Intelligence",
                    parameter_checked="soil_organic_carbon_pct",
                    rule_statement="SOC < 0.50% indicates low soil organic carbon in Maharashtra soils (MPKV PoP 2023)",
                    condition_met=True,
                    evidence_tier=EvidenceTier.VERIFIED,
                    citation=citation
                ))

        return res
