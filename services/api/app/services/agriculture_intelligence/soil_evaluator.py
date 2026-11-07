"""
CropNet AI — Deterministic Soil Constraint Evaluator.

Evaluates soil pH, texture, depth, drainage, salinity, organic carbon,
and nutrient availability against verified crop requirements.
Phase 5.1.2: Hardened evidence boundaries, removed unsupported 3-day waterlogging
and pH > 8.5 disqualification thresholds.
"""
from typing import List, Dict, Optional, Any
from cropnet.services.api.app.schemas.agriculture_intelligence import (
    FarmContextInput,
    AppliedRuleRecord,
    EvidenceTier,
    EnforcementLevel,
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
        # 1. Effective Soil Depth (Diagnostic Evaluation)
        # -------------------------------------------------------------
        if ctx.soil_depth_cm is not None:
            min_depth = soil_req.min_soil_depth_cm
            if crop_id == "pomegranate":
                # ICAR-NRCP & MANAGE 2022 (pp. 9–10) establishes pit planting for shallow/rocky soil
                if ctx.soil_depth_cm < 100.0:
                    msg = (
                        f"Effective soil depth ({ctx.soil_depth_cm} cm) is below 1 m. "
                        "According to ICAR-NRCP & MANAGE 2022 (pp. 9–10), if soil is not deep or is rocky/gravelly up to 1 m depth, "
                        "planting must be performed in pits (1m x 1m x 1m) filled with 1:1 soil:sand/murrum and organic compost. "
                        "Trench planting (0.75m x 0.75m) is restricted to soils deeper than 1 m. "
                        "Depth does not categorically disqualify the parcel, but mandates specialized pit preparation."
                    )
                    res.warnings.append(msg)
                    res.applied_rules.append(AppliedRuleRecord(
                        rule_id="RULE_SOIL_DEPTH_POMEGRANATE",
                        domain="Soil Intelligence",
                        parameter_checked="soil_depth_cm",
                        rule_statement="Pit planting (1m x 1m x 1m) required when soil depth is < 1 m or rocky (ICAR-NRCP 2022, pp. 9–10)",
                        condition_met=True,
                        evidence_tier=tier,
                        citation=citation,
                        claim_verification_status="VERIFIED",
                        source_id="icar_nrcp_manage_2022",
                        document_title="Pomegranate Cultivation, Processing and Value Addition: A Training Manual",
                        section_or_pages="pp. 9–10",
                        supporting_statement="If soil is not deep or is rocky/gravelly up to 1 m depth, planting is done in pits of 1m x 1m x 1m size.",
                        applicability_conditions="soil_depth_cm < 100",
                        enforcement_level=EnforcementLevel.ADVISORY_ONLY,
                        can_trigger_disqualification=False
                    ))
                else:
                    res.applied_rules.append(AppliedRuleRecord(
                        rule_id="RULE_SOIL_DEPTH_POMEGRANATE",
                        domain="Soil Intelligence",
                        parameter_checked="soil_depth_cm",
                        rule_statement="Deep soil (> 1 m) allows trench planting (0.75m x 0.75m) per ICAR-NRCP 2022",
                        condition_met=True,
                        evidence_tier=tier,
                        citation=citation,
                        claim_verification_status="VERIFIED",
                        source_id="icar_nrcp_manage_2022",
                        document_title="Pomegranate Cultivation, Processing and Value Addition: A Training Manual",
                        section_or_pages="pp. 9–10",
                        supporting_statement="In deep soils (> 1 m depth), trench planting (0.75m x 0.75m) can be practiced.",
                        applicability_conditions="soil_depth_cm >= 100",
                        enforcement_level=EnforcementLevel.ADVISORY_ONLY,
                        can_trigger_disqualification=False
                    ))
            elif min_depth and ctx.soil_depth_cm < min_depth:
                res.warnings.append(
                    f"Soil depth ({ctx.soil_depth_cm} cm) is below recommended minimum depth ({min_depth} cm) for {profile.common_name}."
                )
        else:
            res.missing_parameters.append("soil_depth_cm")

        # -------------------------------------------------------------
        # 2. Soil Drainage & Waterlogging Constraint (Phase 5.1.2 Hardened)
        # -------------------------------------------------------------
        drainage_val = (ctx.drainage or "").lower()
        is_explicitly_waterlogged = ("waterlog" in drainage_val or "poor" in drainage_val or "ill-drained" in drainage_val)

        if is_explicitly_waterlogged:
            if crop_id in ("pomegranate", "chickpea"):
                res.is_disqualified = True
                reason = (
                    "Poor drainage / waterlogged soil violates mandatory root aeration requirement. "
                    "In pomegranate, waterlogging triggers devastating Phytophthora root rot and bacterial blight (ICAR-NRCP 2022, p. 3). "
                    "In chickpea, water stagnation causes collar rot and rapid Fusarium wilt (ICRISAT 2010, p. 8)."
                )
                res.limiting_factors.append(reason)
                res.applied_rules.append(AppliedRuleRecord(
                    rule_id=f"RULE_DRAINAGE_{crop_id.upper()}",
                    domain="Soil Intelligence",
                    parameter_checked="drainage",
                    rule_statement="Mandatory well-drained soil; highly intolerant of waterlogged or ill-drained conditions",
                    condition_met=False,
                    evidence_tier=tier,
                    citation=citation,
                    claim_verification_status="VERIFIED",
                    source_id="icar_nrcp_manage_2022" if crop_id == "pomegranate" else "icrisat_chickpea_2010",
                    document_title="Pomegranate Cultivation, Processing and Value Addition" if crop_id == "pomegranate" else "Chickpea Seed Production Manual",
                    section_or_pages="p. 3" if crop_id == "pomegranate" else "p. 8",
                    supporting_statement="Performs poorly in ill-drained heavy soils" if crop_id == "pomegranate" else "Saline soil and fields with high water table are not suitable; water stagnation causes collar rot",
                    applicability_conditions="drainage in ('poor', 'waterlogged', 'ill-drained')",
                    enforcement_level=EnforcementLevel.VERIFIED_HARD_CONSTRAINT,
                    can_trigger_disqualification=True
                ))
        elif ctx.standing_water_days and ctx.standing_water_days > 0:
            # Phase 5.1.2: Duration alone without verified poor drainage does NOT trigger hard disqualification
            if crop_id in ("pomegranate", "chickpea"):
                warn_msg = (
                    f"Standing surface water of {ctx.standing_water_days} days reported. "
                    "Primary literature (ICAR-NRCP 2022, ICRISAT 2010) establishes that water stagnation promotes root asphyxiation, "
                    "collar rot, and wilt, but does not define an empirical three-day numerical boundary. "
                    "Standing water represents an agronomic risk requiring clarification of field drainage furrows, subsoil percolation, "
                    "and water-table depth before conclusive suitability can be determined."
                )
                res.warnings.append(warn_msg)
                res.missing_parameters.extend(["drainage", "water_table_depth"])
                res.applied_rules.append(AppliedRuleRecord(
                    rule_id=f"RULE_DRAINAGE_RISK_{crop_id.upper()}",
                    domain="Soil Intelligence",
                    parameter_checked="standing_water_days",
                    rule_statement="Standing water duration represents an agronomic risk; duration alone does not trigger hard disqualification",
                    condition_met=True,
                    evidence_tier=tier,
                    citation=citation,
                    claim_verification_status="VERIFIED",
                    source_id="icar_nrcp_manage_2022" if crop_id == "pomegranate" else "icrisat_chickpea_2010",
                    document_title="Pomegranate Cultivation, Processing and Value Addition" if crop_id == "pomegranate" else "Chickpea Seed Production Manual",
                    section_or_pages="p. 3" if crop_id == "pomegranate" else "p. 8",
                    supporting_statement="Water stagnation and poor drainage are biological risks requiring field drainage assessment",
                    applicability_conditions="standing_water_days > 0 and drainage not confirmed poor",
                    enforcement_level=EnforcementLevel.CONDITIONAL_CONSTRAINT,
                    can_trigger_disqualification=False
                ))
        elif not ctx.drainage:
            res.missing_parameters.extend(["drainage", "water_table_depth"])

        # -------------------------------------------------------------
        # 3. Soil pH Interpretation & Hard Bounds (Phase 5.1.2 Hardened)
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
                        citation=citation,
                        claim_verification_status="VERIFIED",
                        source_id="icar_nrcp_manage_2022",
                        document_title="Pomegranate Cultivation, Processing and Value Addition: A Training Manual",
                        section_or_pages="p. 3",
                        supporting_statement="Light soil with pH 6.5–7.0 is most suitable for pomegranate cultivation.",
                        applicability_conditions="6.5 <= pH <= 7.0",
                        enforcement_level=EnforcementLevel.ADVISORY_ONLY,
                        can_trigger_disqualification=False
                    ))
                elif best_max < ph <= tol_max:
                    res.warnings.append(
                        f"Soil pH {ph} is above optimum (6.5–7.0) but within tolerable upper limit (8.5). "
                        "High organic manuring and micronutrient management required (ICAR-NRCP 2022, p. 3)."
                    )
                    res.applied_rules.append(AppliedRuleRecord(
                        rule_id="RULE_PH_POMEGRANATE_TOLERABLE",
                        domain="Soil Intelligence",
                        parameter_checked="soil_ph",
                        rule_statement="Soil pH 7.0–8.5 is tolerable with organic manures and micronutrient management (ICAR-NRCP 2022)",
                        condition_met=True,
                        evidence_tier=tier,
                        citation=citation,
                        claim_verification_status="VERIFIED",
                        source_id="icar_nrcp_manage_2022",
                        document_title="Pomegranate Cultivation, Processing and Value Addition: A Training Manual",
                        section_or_pages="p. 3",
                        supporting_statement="Tolerates pH up to 8.5 with high organic manures and micronutrients.",
                        applicability_conditions="7.0 < pH <= 8.5",
                        enforcement_level=EnforcementLevel.ADVISORY_ONLY,
                        can_trigger_disqualification=False
                    ))
                elif ph > tol_max:
                    # Phase 5.1.2: Do not interpret pH > 8.5 as universally verified hard disqualification.
                    # Label it outside documented tolerance range requiring local agronomic assessment.
                    res.warnings.append(
                        f"Soil pH {ph} is outside the documented tolerance range (6.5–8.5 per ICAR-NRCP & MANAGE 2022, p. 3). "
                        "Highly alkaline and calcareous conditions severely restrict micronutrient availability (Fe, Zn, Mn) "
                        "and induce lime-induced chlorosis. Detailed soil profiling, organic gypsum/sulfur application, "
                        "and local agronomic assessment are required before orchard establishment."
                    )
                    res.applied_rules.append(AppliedRuleRecord(
                        rule_id="RULE_PH_POMEGRANATE_EXTREME_ALKALINE",
                        domain="Soil Intelligence",
                        parameter_checked="soil_ph",
                        rule_statement="Soil pH > 8.5 is outside the documented tolerance range (6.5–8.5); requires local agronomic assessment (ICAR-NRCP 2022, p. 3)",
                        condition_met=True,
                        evidence_tier=tier,
                        citation=citation,
                        claim_verification_status="VERIFIED",
                        source_id="icar_nrcp_manage_2022",
                        document_title="Pomegranate Cultivation, Processing and Value Addition: A Training Manual",
                        section_or_pages="p. 3",
                        supporting_statement="Light soil with pH 6.5–7.0 is most suitable; tolerates up to 8.5 under well-managed conditions.",
                        applicability_conditions="pH > 8.5",
                        enforcement_level=EnforcementLevel.CONDITIONAL_CONSTRAINT,
                        can_trigger_disqualification=False
                    ))
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
                        citation=citation,
                        claim_verification_status="VERIFIED",
                        source_id="icrisat_chickpea_2010",
                        document_title="Chickpea Seed Production Manual",
                        section_or_pages="p. 8",
                        supporting_statement="Deep loams or silty clay loams with pH 6.0–8.0 are best suited.",
                        applicability_conditions="6.0 <= pH <= 8.0",
                        enforcement_level=EnforcementLevel.ADVISORY_ONLY,
                        can_trigger_disqualification=False
                    ))
                elif ph > 8.0:
                    res.warnings.append(
                        f"Soil pH {ph} exceeds the best-suited range of 6.0–8.0 (ICRISAT 2010, p. 8). "
                        "Alkaline and calcareous soils may induce iron chlorosis and reduce Rhizobium nodulation efficiency."
                    )
                    res.applied_rules.append(AppliedRuleRecord(
                        rule_id="RULE_PH_CHICKPEA_ALKALINE_ADVISORY",
                        domain="Soil Intelligence",
                        parameter_checked="soil_ph",
                        rule_statement="Soil pH > 8.0 exceeds best-suited range (6.0–8.0); may induce iron chlorosis (ICRISAT 2010, p. 8)",
                        condition_met=True,
                        evidence_tier=tier,
                        citation=citation,
                        claim_verification_status="VERIFIED",
                        source_id="icrisat_chickpea_2010",
                        document_title="Chickpea Seed Production Manual",
                        section_or_pages="p. 8",
                        supporting_statement="Deep loams or silty clay loams with pH 6.0–8.0 are best suited.",
                        applicability_conditions="pH > 8.0",
                        enforcement_level=EnforcementLevel.ADVISORY_ONLY,
                        can_trigger_disqualification=False
                    ))
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
                        citation=citation,
                        claim_verification_status="VERIFIED",
                        source_id="icar_nrcp_manage_2022",
                        document_title="Pomegranate Cultivation, Processing and Value Addition: A Training Manual",
                        section_or_pages="p. 3",
                        supporting_statement="Light soil is most suitable for pomegranate cultivation.",
                        applicability_conditions="texture in ('light', 'sandy loam', 'gravelly')",
                        enforcement_level=EnforcementLevel.ADVISORY_ONLY,
                        can_trigger_disqualification=False
                    ))
                elif "heavy clay" in tex or "deep black" in tex:
                    res.warnings.append(
                        "Heavy clay / deep black Vertisols require ridge-and-furrow planting, subsoil drainage, and strict water regulation for pomegranate."
                    )
        else:
            res.missing_parameters.append("soil_texture")

        # -------------------------------------------------------------
        # 5. Salinity (Electrical Conductivity) Diagnostic Risk
        # -------------------------------------------------------------
        q_lower = (ctx.user_query or "").lower()
        if ctx.electrical_conductivity_ds_m is not None:
            ec = ctx.electrical_conductivity_ds_m
            if crop_id == "chickpea":
                # ICRISAT 2010 (p. 8) establishes that saline soils and fields with a high water table
                # are not suitable for chickpea. Preserved as a diagnostic variable requiring interpretation.
                res.warnings.append(
                    f"Reported Soil Electrical Conductivity is {ec} dS/m. "
                    "ICRISAT 2010 (p. 8) states that saline soils and fields with a high water table are not suitable for chickpea. "
                    "Chickpea is salt-sensitive; soil salinity impairs germination, nodulation, and pod yield. "
                    "Detailed soil testing, water table depth verification, and drainage inspection are required before planting."
                )
                res.applied_rules.append(AppliedRuleRecord(
                    rule_id="RULE_CHICKPEA_SALINITY_RISK",
                    domain="Soil Intelligence",
                    parameter_checked="electrical_conductivity_ds_m",
                    rule_statement="Saline soils and high water table fields are unsuitable for chickpea (ICRISAT 2010, p. 8)",
                    condition_met=True,
                    evidence_tier=tier,
                    citation=citation,
                    claim_verification_status="VERIFIED",
                    source_id="icrisat_chickpea_2010",
                    document_title="Chickpea Seed Production Manual",
                    section_or_pages="p. 8",
                    supporting_statement="Saline soil and fields with a high water table are not suitable for chickpea.",
                    applicability_conditions="electrical_conductivity_ds_m is reported",
                    enforcement_level=EnforcementLevel.CONDITIONAL_CONSTRAINT,
                    can_trigger_disqualification=False
                ))
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
        # 6. Nutrient Status (Available N & SOC) — Phase 5.1.2 Audited
        # Claims from mpkv_pop_2023 are CONDITIONALLY_SUPPORTED / ADVISORY_ONLY
        # -------------------------------------------------------------
        if ctx.available_nitrogen_kg_ha is not None:
            avail_n = ctx.available_nitrogen_kg_ha
            if avail_n < 280.0:
                res.warnings.append(
                    f"Available Nitrogen is Low ({avail_n} kg/ha < 280 kg/ha standard in regional practice). Basal and split nitrogen fertilizer is advised."
                )
                res.applied_rules.append(AppliedRuleRecord(
                    rule_id="RULE_AVAILABLE_NITROGEN_DEFICIENCY",
                    domain="Soil Fertility Intelligence",
                    parameter_checked="available_nitrogen_kg_ha",
                    rule_statement="Available N < 280 kg/ha is Low; requires external nitrogen application (MPKV PoP)",
                    condition_met=True,
                    evidence_tier=EvidenceTier.CONDITIONALLY_SUPPORTED,
                    citation=citation,
                    claim_verification_status="CONDITIONALLY_SUPPORTED",
                    source_id="mpkv_pop_2023",
                    document_title="Package of Practices for Field Crops of Western Maharashtra",
                    section_or_pages="Compendium requires physical inspection",
                    supporting_statement="Available N < 280 kg/ha indicates low fertility status in regional soil testing standards.",
                    applicability_conditions="available_nitrogen_kg_ha < 280.0",
                    enforcement_level=EnforcementLevel.ADVISORY_ONLY,
                    can_trigger_disqualification=False
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
                    rule_statement="SOC < 0.50% indicates low soil organic carbon in Maharashtra soils (MPKV PoP)",
                    condition_met=True,
                    evidence_tier=EvidenceTier.CONDITIONALLY_SUPPORTED,
                    citation=citation,
                    claim_verification_status="CONDITIONALLY_SUPPORTED",
                    source_id="mpkv_pop_2023",
                    document_title="Package of Practices for Field Crops of Western Maharashtra",
                    section_or_pages="Compendium requires physical inspection",
                    supporting_statement="SOC < 0.50% represents low organic carbon in semi-arid Vertisols.",
                    applicability_conditions="soil_organic_carbon_pct < 0.50",
                    enforcement_level=EnforcementLevel.ADVISORY_ONLY,
                    can_trigger_disqualification=False
                ))

        return res
