"""
CropNet AI — Deterministic Water Availability & Irrigation Evaluator.

Evaluates crop hydrological feasibility, provides pomegranate Bahar daily tree
schedules (liters/tree/day), enforces decoupled chickpea irrigation statements,
and provides weather-aware conditional advisories.
Phase 5.1.2: Hardened evidence boundaries, month-only water assumptions no longer
trigger automatic hard disqualification; rainfall advisory is conditional and probabilistic.
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


class WaterEvaluationResult:
    def __init__(self, crop_id: str):
        self.crop_id = crop_id
        self.is_disqualified: bool = False
        self.limiting_factors: List[str] = []
        self.warnings: List[str] = []
        self.missing_parameters: List[str] = []
        self.irrigation_guidance: Optional[Dict[str, Any]] = None
        self.pomegranate_daily_water: Optional[Dict[str, Any]] = None
        self.applied_rules: List[AppliedRuleRecord] = []


class WaterAvailabilityEvaluator:
    """
    Evaluates irrigation requirements and Bahar water schedules deterministically.
    """

    @staticmethod
    def evaluate(
        ctx: FarmContextInput,
        profile: CropFullProfileResponse,
        citation: Optional[CitationMetadata] = None
    ) -> WaterEvaluationResult:
        res = WaterEvaluationResult(crop_id=profile.id)
        crop_id = profile.id
        primary_src_id = profile.sources[0].id if (profile.sources and len(profile.sources) > 0) else None
        tier = EvidenceGate.get_tier(profile.water.source_id if profile.water else primary_src_id)

        # -------------------------------------------------------------
        # 1. Sugarcane Hydrological & Seasonal Water Constraint
        # -------------------------------------------------------------
        if crop_id == "sugarcane":
            capacity = (ctx.irrigation_capacity or "").lower()
            source = (ctx.irrigation_source or "").lower()
            query_lower = (ctx.user_query or "").lower()

            if ctx.irrigation_available is False:
                # Verified hard constraint: sugarcane cannot be grown rainfed in semi-arid Maharashtra
                res.is_disqualified = True
                msg = (
                    "Hydrological disqualification: Sugarcane requires assured perennial water throughout its 12–18 month duration. "
                    "Annual rainfall in semi-arid Maharashtra is insufficient to sustain commercial sugarcane without irrigation. "
                    "Rainfed sugarcane without irrigation is completely unfeasible."
                )
                res.limiting_factors.append(msg)
                res.applied_rules.append(AppliedRuleRecord(
                    rule_id="RULE_SUGARCANE_RAINFED_DISQUALIFICATION",
                    domain="Irrigation Intelligence",
                    parameter_checked="irrigation_available",
                    rule_statement="Sugarcane cannot be cultivated rainfed without irrigation in semi-arid Maharashtra",
                    condition_met=False,
                    evidence_tier=EvidenceTier.VERIFIED,
                    citation=citation,
                    claim_verification_status="VERIFIED",
                    source_id="mpkv_research_2023",
                    document_title="MPKV Research Recommendations 2023",
                    section_or_pages="Rec. 3",
                    supporting_statement="Sugarcane requires assured perennial micro-irrigation or canal irrigation; cannot be grown rainfed.",
                    applicability_conditions="irrigation_available is False",
                    enforcement_level=EnforcementLevel.VERIFIED_HARD_CONSTRAINT,
                    can_trigger_disqualification=True
                ))
            elif ("dry_by_february" in capacity or "seasonal" in capacity or "february" in source) and (
                "only one" in query_lower or "फक्त एक" in query_lower or "runs dry" in query_lower or "आटते" in query_lower or "no alternative" in query_lower or capacity == "seasonal_dry_by_february"
            ):
                # When actual farm water capacity is verified exhausted before summer tillering (March–May) with no alternative
                res.is_disqualified = True
                msg = (
                    "Hydrological disqualification: Sugarcane requires assured perennial irrigation throughout its 12–18 month duration "
                    "(2000–3000 mm under furrow, or 1000–1500 mm under drip per MPKV PoP 2023 & MPKV Research 2023 Rec. 3). "
                    "A seasonal water source exhausted by February coincides with the critical summer tillering "
                    "and stem elongation phase (March–May), causing acute moisture stress, desiccation, and complete crop loss (MPKV PoP 2023). "
                    "Sugarcane cannot be sustained without perennial irrigation."
                )
                res.warnings.append(msg)
                res.limiting_factors.append(msg)
                res.applied_rules.append(AppliedRuleRecord(
                    rule_id="RULE_SUGARCANE_SUMMER_WATER_DEPLETION",
                    domain="Irrigation Intelligence",
                    parameter_checked="irrigation_capacity",
                    rule_statement="Sugarcane requires perennial water; summer tillering (March–May) is the critical moisture stress period (MPKV PoP 2023)",
                    condition_met=False,
                    evidence_tier=EvidenceTier.VERIFIED,
                    citation=citation,
                    claim_verification_status="VERIFIED",
                    source_id="mpkv_research_2023",
                    document_title="MPKV Research Recommendations 2023",
                    section_or_pages="Rec. 3",
                    supporting_statement="Moisture stress during summer formative stage severely reduces tillering and cane yield.",
                    applicability_conditions="actual water capacity exhausted before summer formative stage",
                    enforcement_level=EnforcementLevel.VERIFIED_HARD_CONSTRAINT,
                    can_trigger_disqualification=True
                ))
            elif "seasonal" in capacity or "february" in source or (ctx.proposed_sowing_date and "-02-" in ctx.proposed_sowing_date):
                # Month-only or unconfirmed seasonal constraint: Do NOT automatically disqualify based only on calendar month!
                # Return conditional water-risk outcome assessing alternative irrigation.
                res.is_disqualified = False
                msg = (
                    "Hydrological risk / Conditional constraint: Sugarcane requires 12–18 months of assured water. "
                    "A seasonal water source that depletes during summer leaves the crop vulnerable during the critical "
                    "formative stage (March–May) unless supplemental alternative irrigation (tanker, farm pond, canal rotation) is available. "
                    "Inquire whether alternative summer irrigation is available."
                )
                res.warnings.append(msg)
                res.missing_parameters.append("alternative_summer_irrigation")
                res.applied_rules.append(AppliedRuleRecord(
                    rule_id="RULE_SUGARCANE_SUMMER_WATER_DEPLETION",
                    domain="Irrigation Intelligence",
                    parameter_checked="irrigation_capacity",
                    rule_statement="Sugarcane requires perennial water; assess alternative summer irrigation during March–May tillering",
                    condition_met=False,
                    evidence_tier=EvidenceTier.CONDITIONALLY_SUPPORTED,
                    citation=citation,
                    claim_verification_status="CONDITIONALLY_SUPPORTED",
                    source_id="mpkv_pop_2023",
                    document_title="Package of Practices for Field Crops of Western Maharashtra",
                    section_or_pages="Compendium requires physical inspection",
                    supporting_statement="Summer moisture stress severely restricts tillering unless supplemental water is provided.",
                    applicability_conditions="seasonal irrigation with potential alternative water",
                    enforcement_level=EnforcementLevel.CONDITIONAL_CONSTRAINT,
                    can_trigger_disqualification=False
                ))

        # -------------------------------------------------------------
        # 2. Pomegranate Bahar-Specific Daily Water Schedules
        # -------------------------------------------------------------
        elif crop_id == "pomegranate":
            # If farmer faces summer water scarcity after February
            if ctx.water_scarcity_period and "february" in ctx.water_scarcity_period.lower():
                res.applied_rules.append(AppliedRuleRecord(
                    rule_id="RULE_POMEGRANATE_BAHAR_SELECTION_WATER_SCARCITY",
                    domain="Irrigation Intelligence",
                    parameter_checked="water_scarcity_period",
                    rule_statement="Hasta Bahar is recommended under summer water scarcity; Ambia Bahar requires peak summer water",
                    condition_met=True,
                    evidence_tier=EvidenceTier.VERIFIED,
                    citation=citation,
                    claim_verification_status="VERIFIED",
                    source_id="icar_nrcp_manage_2022",
                    document_title="Pomegranate Cultivation, Processing and Value Addition",
                    section_or_pages="pp. 45–46",
                    supporting_statement="Hasta Bahar is recommended where summer water is scarce; Ambia Bahar requires peak summer water.",
                    applicability_conditions="water_scarcity_period post_february",
                    enforcement_level=EnforcementLevel.ADVISORY_ONLY,
                    can_trigger_disqualification=False
                ))
                res.irrigation_guidance = {
                    "recommended_bahar": "Hasta Bahar (हस्त बहार)",
                    "disqualified_bahar": "Ambia Bahar (आंबिया बहार)",
                    "rationale": (
                        "Hasta Bahar flowers in Sept–Oct and harvests in Feb–March before acute summer drought. "
                        "Ambia Bahar flowers in Jan–Feb and requires intensive drip irrigation (up to 54–70 L/tree/day) "
                        "during peak summer heat (March–May)."
                    )
                }

            # Retrieve exact daily schedule if Bahar and age are known
            dwt = profile.water.daily_water_table if profile.water else None
            if dwt and ctx.target_bahar:
                bahar_key = ctx.target_bahar.lower()
                age = ctx.tree_age_years or 4
                if bahar_key in dwt:
                    bahar_data = dwt[bahar_key]
                    schedule = bahar_data.get("schedule", []) if isinstance(bahar_data, dict) else []
                    res.pomegranate_daily_water = {
                        "unit": "liters_per_tree_per_day",
                        "bahar": bahar_key,
                        "tree_age_years": age,
                        "weekly_schedule": schedule,
                        "october_range_liters_day": "28.3 to 34.2 L/tree/day (Met Weeks 40–44 in Mrig Bahar)" if bahar_key == "mrig_bahar" else None,
                        "annual_water_mm": None,
                        "provenance_note": "ICAR-NRCP & MANAGE (2022) Table 1–3, pp. 45–46. Annual millimeter requirement is unverified (NULL)."
                    }
                    res.applied_rules.append(AppliedRuleRecord(
                        rule_id="RULE_POMEGRANATE_DAILY_WATER_SCHEDULE",
                        domain="Irrigation Intelligence",
                        parameter_checked="target_bahar",
                        rule_statement="Table 1–3: Daily water schedule in liters/tree/day indexed by age and Bahar (ICAR-NRCP 2022)",
                        condition_met=True,
                        evidence_tier=EvidenceTier.VERIFIED,
                        citation=citation,
                        claim_verification_status="VERIFIED",
                        source_id="icar_nrcp_manage_2022",
                        document_title="Pomegranate Cultivation, Processing and Value Addition",
                        section_or_pages="Table 1–3, pp. 45–46",
                        supporting_statement="Daily water requirement of pomegranate tree for Mrig, Hasta and Ambia Bahar in L/tree/day.",
                        applicability_conditions="target_bahar is specified",
                        enforcement_level=EnforcementLevel.ADVISORY_ONLY,
                        can_trigger_disqualification=False
                    ))

        # -------------------------------------------------------------
        # 3. Chickpea Decoupled Irrigation & Weather-Aware Advisory (Phase 5.1.2)
        # -------------------------------------------------------------
        elif crop_id == "chickpea":
            # Decoupled schedule presentation
            res.irrigation_guidance = {
                "management_strategy": "DECOUPLED_FRAMEWORKS",
                "icrisat_2010_framework": {
                    "source": "ICRISAT Chickpea Seed Production Manual (2010, p. 11)",
                    "rule": "1 to 2 light irrigations total at critical physiological stages: Branching and Pod-filling."
                },
                "mpkv_2023_framework": {
                    "source": "MPKV Research Recommendations (2023, Rec. 8, pp. 2–3)",
                    "rule": "Canal-irrigated scheduling in Plain Zone Vertisols at 20–25 DAS and 60–65 DAS."
                },
                "anti_blending_warning": (
                    "Do NOT combine both into 4 irrigations. Applying 4 irrigations in heavy Vertisols causes "
                    "excessive vegetative growth, soil saturation, and destructive Fusarium wilt / collar rot."
                )
            }
            res.applied_rules.append(AppliedRuleRecord(
                rule_id="RULE_CHICKPEA_DECOUPLED_IRRIGATION_SCHEDULE",
                domain="Irrigation Intelligence",
                parameter_checked="irrigation_guidance",
                rule_statement="Decoupled presentation of ICRISAT (physiological) and MPKV (calendar) frameworks with anti-blending warning",
                condition_met=True,
                evidence_tier=EvidenceTier.VERIFIED,
                citation=citation,
                claim_verification_status="VERIFIED",
                source_id="icrisat_chickpea_2010",
                document_title="Chickpea Seed Production Manual",
                section_or_pages="p. 11",
                supporting_statement="1 to 2 light irrigations at branching and pod-filling. Higher number of irrigations leads to excessive vegetative growth.",
                applicability_conditions="chickpea irrigation planning",
                enforcement_level=EnforcementLevel.ADVISORY_ONLY,
                can_trigger_disqualification=False
            ))

            # Phase 5.1.2: Weather-aware irrigation conditional advisory (not automatic instruction)
            if ctx.forecast_rain_mm_48h is not None and ctx.forecast_rain_mm_48h > 0:
                rain_amt = ctx.forecast_rain_mm_48h
                advisory_msg = (
                    f"Weather-Aware Irrigation Advisory: Meteorological forecast indicates {rain_amt} mm precipitation within the next 48 hours. "
                    "Forecast information carries probabilistic uncertainty and must be distinguished from recorded rainfall. "
                    "ICRISAT 2010 (pp. 8, 11) establishes that chickpea is acutely sensitive to soil water stagnation and collar rot. "
                    f"Field drainage is currently '{ctx.drainage or 'unverified'}'. "
                    "Guidance: Do not automatically suspend irrigation if the forecast is light and root-zone soil is dry. "
                    "However, if forecast rain is substantial, soil moisture is adequate, or drainage is poor, "
                    "postpone scheduled irrigation until the weather event concludes and ensure drainage furrows are clear to prevent water stagnation."
                )
                res.warnings.append(advisory_msg)
                res.applied_rules.append(AppliedRuleRecord(
                    rule_id="RULE_CHICKPEA_IRRIGATION_SUSPENSION_RAIN_FORECAST",
                    domain="Irrigation Intelligence",
                    parameter_checked="forecast_rain_mm_48h",
                    rule_statement="Conditional advisory considering forecast precipitation magnitude, probability, soil drainage, and moisture rather than automatic suspension",
                    condition_met=True,
                    evidence_tier=EvidenceTier.VERIFIED,
                    citation=citation,
                    claim_verification_status="VERIFIED",
                    source_id="icrisat_chickpea_2010",
                    document_title="Chickpea Seed Production Manual",
                    section_or_pages="pp. 8, 11",
                    supporting_statement="Water stagnation and excessive irrigations cause collar rot and wilt.",
                    applicability_conditions="forecast_rain_mm_48h is reported",
                    enforcement_level=EnforcementLevel.ADVISORY_ONLY,
                    can_trigger_disqualification=False
                ))
                if not ctx.drainage:
                    res.missing_parameters.append("drainage")
                if not ctx.days_after_sowing and not ctx.growth_stage:
                    res.missing_parameters.append("growth_stage")

        return res
