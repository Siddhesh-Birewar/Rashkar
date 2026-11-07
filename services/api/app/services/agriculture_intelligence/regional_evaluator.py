"""
CropNet AI — Deterministic Regional Suitability Evaluator.

Evaluates pilot taluka agroecological conditions, distinguishes regional
screening from farm verification, and enforces strict governance boundaries.
Phase 5.1.2: Separated governance classifications from scientific claims;
removed unsupported numerical thresholds (>2000 mm, >50% RH).
"""
from typing import List, Dict, Optional, Any
from cropnet.services.api.app.schemas.agriculture_intelligence import (
    FarmContextInput,
    DecisionState,
    AppliedRuleRecord,
    EvidenceTier,
    EnforcementLevel,
    CitationMetadata
)
from cropnet.services.api.app.schemas.crop import CropFullProfileResponse
from cropnet.services.api.app.services.agriculture_intelligence.evidence_gate import EvidenceGate


class RegionalEvaluationResult:
    def __init__(self, crop_id: str):
        self.crop_id = crop_id
        self.regional_decision_state: DecisionState = DecisionState.REGIONAL_SCREENING_ONLY
        self.limiting_factors: List[str] = []
        self.warnings: List[str] = []
        self.applied_rules: List[AppliedRuleRecord] = []
        self.citation: Optional[CitationMetadata] = None


class RegionalSuitabilityEvaluator:
    """
    Evaluates taluka suitability classifications deterministically.
    """

    @staticmethod
    def evaluate(
        ctx: FarmContextInput,
        profile: CropFullProfileResponse,
        regional_record: Optional[Dict[str, Any]] = None,
        citation: Optional[CitationMetadata] = None
    ) -> RegionalEvaluationResult:
        res = RegionalEvaluationResult(crop_id=profile.id)
        crop_id = profile.id
        taluka = (ctx.taluka or "").strip().lower()

        # -------------------------------------------------------------
        # 1. Pilot Taluka Screening vs Validation Classification
        # -------------------------------------------------------------
        if taluka in ("maval", "mulshi"):
            # Western Ghats Transition Zone — Governance Policy
            res.regional_decision_state = DecisionState.REQUIRES_REGIONAL_VALIDATION
            
            if crop_id == "chickpea":
                msg = (
                    "Maval/Mulshi Western Ghats transition zone features high atmospheric humidity and hilly lateritic soils. "
                    "Chickpea is vulnerable to Ascochyta blight, Botrytis grey mould, and excessive vegetative growth. "
                    "Classified as 'requires_regional_validation' under CropNet governance pending local field trials."
                )
                res.warnings.append(msg)
            elif crop_id == "soybean":
                msg = (
                    "Mulshi is located in the Western Ghats high-rainfall tract. "
                    "Prolonged heavy monsoon rain during flowering induces flower drop, poor pod setting, and fungal collar rot. "
                    "Classified as 'requires_regional_validation' under CropNet governance."
                )
                res.warnings.append(msg)
            elif crop_id == "pomegranate":
                msg = (
                    "Persistent atmospheric humidity and monsoon rainfall in the Western Ghats drastically elevate Bacterial Blight "
                    "(*Xanthomonas axonopodis pv. punicae*) and Phytophthora root rot risks. Classified as 'requires_regional_validation'."
                )
                res.warnings.append(msg)
            else:
                res.warnings.append(
                    f"CropNet classifies {crop_id.capitalize()} in {taluka.capitalize()} as 'requires_regional_validation' "
                    "due to lack of published university agronomic trials for Western Ghats transition microclimates."
                )

            res.applied_rules.append(AppliedRuleRecord(
                rule_id=f"RULE_REGIONAL_VALIDATION_{taluka.upper()}",
                domain="Crop Suitability",
                parameter_checked="taluka",
                rule_statement=f"{taluka.capitalize()} Western Ghats transition zone requires localized field validation (CropNet Regional Governance Policy)",
                condition_met=True,
                evidence_tier=EvidenceTier.VERIFIED,
                citation=citation,
                claim_verification_status="GOVERNANCE_POLICY",
                source_id="cropnet_governance",
                document_title="CropNet Regional Governance & Agroecological Zonation Policy",
                section_or_pages="Pilot Taluka Protocol",
                supporting_statement="Ghat transition zones require localized trial validation before commercial recommendation.",
                applicability_conditions=f"taluka == '{taluka}'",
                enforcement_level=EnforcementLevel.CONDITIONAL_CONSTRAINT,
                can_trigger_disqualification=False
            ))

        elif taluka in ("baramati", "indapur"):
            # Plain Zone / Scarcity Zone Vertisols
            res.regional_decision_state = DecisionState.REGIONAL_SCREENING_ONLY
            res.applied_rules.append(AppliedRuleRecord(
                rule_id="RULE_REGIONAL_SCREENING_SCARCITY_ZONE",
                domain="Crop Suitability",
                parameter_checked="taluka",
                rule_statement="Baramati/Indapur supported under regional screening for Plain Zone Vertisols (MPKV regional baseline)",
                condition_met=True,
                evidence_tier=EvidenceTier.VERIFIED,
                citation=citation,
                claim_verification_status="VERIFIED",
                source_id="mpkv_research_2023",
                document_title="MPKV Research Recommendations 2023",
                section_or_pages="Zonal Recommendations",
                supporting_statement="Macro agroecological recommendations apply to Plain Zone Vertisols.",
                applicability_conditions="taluka in ('baramati', 'indapur')",
                enforcement_level=EnforcementLevel.ADVISORY_ONLY,
                can_trigger_disqualification=False
            ))
            res.warnings.append(
                f"Regional screening for {taluka.capitalize()} represents a macro-zonal agroecological baseline for "
                "Plain Zone Vertisols. It does NOT constitute individual farm verification. "
                "Local soil depth, salinity, and water drainage must be tested."
            )

        # -------------------------------------------------------------
        # 2. Contextual Inapplicability Guard
        # -------------------------------------------------------------
        if taluka in ("maval", "mulshi") and ctx.soil_texture:
            tex_lower = ctx.soil_texture.lower()
            if ("gravel" in tex_lower or "shallow" in tex_lower or "laterite" in tex_lower) and crop_id == "chickpea":
                res.limiting_factors.append(
                    "Contextual inapplicability: High-yield gram recommendations developed for "
                    "medium-to-deep black Vertisols in the Plain Zone cannot be extrapolated "
                    "to shallow gravelly or lateritic soils in Western Ghats transition tracts."
                )

        return res
