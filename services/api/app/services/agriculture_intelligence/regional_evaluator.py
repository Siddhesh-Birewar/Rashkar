"""
CropNet AI — Deterministic Regional Suitability Evaluator.

Evaluates pilot taluka agroecological conditions, distinguishes regional
screening from farm verification, and prevents inapplicable document extrapolation.
"""
from typing import List, Dict, Optional, Any
from cropnet.services.api.app.schemas.agriculture_intelligence import (
    FarmContextInput,
    DecisionState,
    AppliedRuleRecord,
    EvidenceTier,
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
            # High rainfall Western Ghats Transition Zone
            res.regional_decision_state = DecisionState.REQUIRES_REGIONAL_VALIDATION
            
            if crop_id == "chickpea":
                msg = (
                    f"Maval/Mulshi Western Ghats transition zone has high atmospheric humidity and lateritic/acidic soils. "
                    "Chickpea is vulnerable to Ascochyta blight, Botrytis grey mould, and excessive vegetative overgrowth. "
                    "Classified as 'requires_regional_validation'; requires local field verification."
                )
                res.warnings.append(msg)
            elif crop_id == "soybean":
                msg = (
                    f"Mulshi receives excessive monsoon rainfall (>2000 mm) during Kharif. "
                    "Continuous rain during flowering induces flower abortion, poor pod setting, and fungal collar rot. "
                    "Classified as 'requires_regional_validation'."
                )
                res.warnings.append(msg)
            elif crop_id == "pomegranate":
                msg = (
                    "High humidity (>50% RH) and persistent rain in Western Ghats drastically elevate Bacterial Blight "
                    "(*Xanthomonas*) and Phytophthora root rot risks. Classified as 'requires_regional_validation'."
                )
                res.warnings.append(msg)
            else:
                res.warnings.append(
                    f"CropNet classifies {crop_id.capitalize()} in {taluka.capitalize()} as 'requires_regional_validation' "
                    "due to lack of published MPKV university trial data for Ghat transition microclimates."
                )

            res.applied_rules.append(AppliedRuleRecord(
                rule_id=f"RULE_REGIONAL_VALIDATION_{taluka.upper()}",
                domain="Crop Suitability",
                parameter_checked="taluka",
                rule_statement=f"Maval/Mulshi requires localized field validation (CropNet Regional Governance)",
                condition_met=True,
                evidence_tier=EvidenceTier.VERIFIED,
                citation=citation
            ))

        elif taluka in ("baramati", "indapur"):
            # Plain Zone / Scarcity Zone Vertisols
            res.regional_decision_state = DecisionState.REGIONAL_SCREENING_ONLY
            res.applied_rules.append(AppliedRuleRecord(
                rule_id="RULE_REGIONAL_SCREENING_SCARCITY_ZONE",
                domain="Crop Suitability",
                parameter_checked="taluka",
                rule_statement="Baramati/Indapur supported under regional screening for Plain Zone Vertisols",
                condition_met=True,
                evidence_tier=EvidenceTier.VERIFIED,
                citation=citation
            ))
            res.warnings.append(
                f"Regional screening for {taluka.capitalize()} represents a macro-zonal agroecological baseline for "
                "Plain Zone Vertisols (MPKV 2023). It does NOT constitute individual farm verification. "
                "Local soil depth, salinity, and water drainage must be tested."
            )

        # -------------------------------------------------------------
        # 2. Contextual Inapplicability Guard (Adversarial 9)
        # -------------------------------------------------------------
        if taluka in ("maval", "mulshi") and ctx.soil_texture:
            tex_lower = ctx.soil_texture.lower()
            if ("gravel" in tex_lower or "shallow" in tex_lower or "laterite" in tex_lower) and crop_id == "chickpea":
                res.limiting_factors.append(
                    "Contextual inapplicability: MPKV 2023 high-yield gram recommendations apply strictly to "
                    "medium-to-deep black Vertisols under canal irrigation in the Scarcity Zone (Rahuri). "
                    "They cannot be extrapolated to shallow gravelly soils in Maval."
                )

        return res
