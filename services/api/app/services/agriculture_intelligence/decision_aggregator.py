"""
CropNet AI — Deterministic Decision Aggregator.

Aggregates dimensional evaluations across soil, climate, water, and regional suitability,
determines standardized machine-readable decision states, compiles limiting factors,
and formats transparent, evidence-backed explanations.
"""
from typing import List, Dict, Optional, Any
from cropnet.services.api.app.schemas.agriculture_intelligence import (
    FarmContextInput,
    DecisionState,
    CropEvaluationOutcome,
    AppliedRuleRecord,
    CitationMetadata
)
from cropnet.services.api.app.schemas.crop import CropFullProfileResponse
from cropnet.services.api.app.services.agriculture_intelligence.soil_evaluator import SoilEvaluationResult
from cropnet.services.api.app.services.agriculture_intelligence.climate_evaluator import ClimateEvaluationResult
from cropnet.services.api.app.services.agriculture_intelligence.water_evaluator import WaterEvaluationResult
from cropnet.services.api.app.services.agriculture_intelligence.regional_evaluator import RegionalEvaluationResult


class DecisionAggregator:
    """
    Aggregates modular evaluation results into a single CropEvaluationOutcome.
    """

    @staticmethod
    def aggregate(
        ctx: FarmContextInput,
        profile: CropFullProfileResponse,
        soil_res: SoilEvaluationResult,
        clim_res: ClimateEvaluationResult,
        water_res: WaterEvaluationResult,
        reg_res: RegionalEvaluationResult,
        citations: List[CitationMetadata]
    ) -> CropEvaluationOutcome:
        crop_id = profile.id
        limiting_factors: List[str] = []
        uncertainty_notes: List[str] = []
        missing_info: List[str] = []
        all_rules: List[AppliedRuleRecord] = []

        # Collect limiting factors
        limiting_factors.extend(soil_res.limiting_factors)
        limiting_factors.extend(clim_res.limiting_factors)
        limiting_factors.extend(water_res.limiting_factors)
        limiting_factors.extend(reg_res.limiting_factors)

        # Collect warnings into uncertainty notes
        uncertainty_notes.extend(soil_res.warnings)
        uncertainty_notes.extend(clim_res.warnings)
        uncertainty_notes.extend(water_res.warnings)
        uncertainty_notes.extend(reg_res.warnings)

        # Collect missing parameters
        missing_info.extend(soil_res.missing_parameters)
        missing_info.extend(clim_res.missing_parameters)
        missing_info.extend(water_res.missing_parameters)
        missing_info = list(set(missing_info))

        # Collect applied rules
        all_rules.extend(soil_res.applied_rules)
        all_rules.extend(clim_res.applied_rules)
        all_rules.extend(water_res.applied_rules)
        all_rules.extend(reg_res.applied_rules)

        # Determine Decision State
        is_disqualified = soil_res.is_disqualified or clim_res.is_disqualified or water_res.is_disqualified

        if is_disqualified:
            decision_state = DecisionState.UNSUITABLE_VERIFIED_CONSTRAINT
        elif reg_res.regional_decision_state == DecisionState.REQUIRES_REGIONAL_VALIDATION:
            decision_state = DecisionState.REQUIRES_REGIONAL_VALIDATION
        elif reg_res.regional_decision_state == DecisionState.REGIONAL_SCREENING_ONLY:
            decision_state = DecisionState.REGIONAL_SCREENING_ONLY
        elif len(missing_info) > 0 and any(m in ("electrical_conductivity_ds_m", "irrigation_water_ec_ds_m", "soil_depth_cm") for m in missing_info):
            decision_state = DecisionState.CONDITIONALLY_SUITABLE_PENDING_DATA
        else:
            decision_state = DecisionState.VERIFIED_SUITABLE

        # Synthesize Explanation
        explanation = DecisionAggregator._synthesize_explanation(
            ctx=ctx,
            profile=profile,
            decision_state=decision_state,
            limiting_factors=limiting_factors,
            uncertainty_notes=uncertainty_notes,
            reproductive_warnings=clim_res.reproductive_risk_warnings
        )

        return CropEvaluationOutcome(
            crop_id=crop_id,
            common_name=profile.common_name,
            scientific_name=profile.scientific_name,
            marathi_name=profile.marathi_name,
            decision_state=decision_state,
            is_disqualified=is_disqualified,
            limiting_factors=limiting_factors,
            reproductive_risk_warnings=clim_res.reproductive_risk_warnings,
            irrigation_guidance=water_res.irrigation_guidance,
            pomegranate_daily_water=water_res.pomegranate_daily_water,
            missing_information=missing_info,
            uncertainty_notes=uncertainty_notes,
            applied_rules=all_rules,
            citations=citations,
            explanation=explanation
        )

    @staticmethod
    def _synthesize_explanation(
        ctx: FarmContextInput,
        profile: CropFullProfileResponse,
        decision_state: DecisionState,
        limiting_factors: List[str],
        uncertainty_notes: List[str],
        reproductive_warnings: List[str]
    ) -> str:
        lang = (ctx.language or "en").lower()
        crop_name = profile.marathi_name if (lang == "mr" and profile.marathi_name) else profile.common_name
        taluka = (ctx.taluka or "Maharashtra").capitalize()

        if lang == "mr":
            if decision_state == DecisionState.UNSUITABLE_VERIFIED_CONSTRAINT:
                reasons = " ".join(limiting_factors)
                return f"{crop_name} हे पीक आपल्या शेतातील परिस्थितीनुसार अयोग्य ठरते. कारणे: {reasons}"
            elif decision_state == DecisionState.REQUIRES_REGIONAL_VALIDATION:
                return (
                    f"{taluka} तालुक्यात {crop_name} पिकासाठी प्रादेशिक क्षेत्रीय पडताळणी आवश्यक आहे. "
                    "पश्चिम घाट परिसरातील जास्त पाऊस आणि आर्द्रतेमुळे स्थानिक शेतपातळीवर रोगांचा धोका तपासणे गरजेचे आहे."
                )
            elif decision_state == DecisionState.CONDITIONALLY_SUITABLE_PENDING_DATA:
                return (
                    f"{crop_name} पीक प्राथमिक निकषांनुसार योग्य वाटत असले, तरी काही महत्त्वाची माहिती प्रलंबित आहे. "
                    "कृपया जमिनीची खोली, निचरा किंवा क्षारता (EC) तपासून खात्री करावी."
                )
            elif decision_state == DecisionState.REGIONAL_SCREENING_ONLY:
                return (
                    f"{taluka} तालुक्यासाठी {crop_name} पिकाची शिफारस प्रादेशिक छाननीवर आधारित आहे. "
                    "मध्यम ते भारी काळ्या जमिनीसाठी ही सर्वसाधारण शिफारस असून, स्वतःच्या शेताची माती व पाणी तपासणी करूनच लागवड करावी."
                )
            else:
                return f"{crop_name} पीक आपल्या शेतासाठी पूर्णतः अनुकूल व प्रमाणित आढळले आहे."
        else:
            if decision_state == DecisionState.UNSUITABLE_VERIFIED_CONSTRAINT:
                reasons = " ".join(limiting_factors)
                return f"{crop_name} is disqualified as unsuitable under your farm conditions. Limiting factors: {reasons}"
            elif decision_state == DecisionState.REQUIRES_REGIONAL_VALIDATION:
                return (
                    f"{crop_name} in {taluka} requires regional validation. "
                    "Western Ghat transition agroecology requires localized field verification due to humidity and disease risks."
                )
            elif decision_state == DecisionState.CONDITIONALLY_SUITABLE_PENDING_DATA:
                return (
                    f"{crop_name} is conditionally suitable pending diagnostic verification. "
                    "Critical diagnostic variables (such as EC, water table, or subsoil depth) must be confirmed."
                )
            elif decision_state == DecisionState.REGIONAL_SCREENING_ONLY:
                return (
                    f"{crop_name} in {taluka} meets regional suitability criteria based on macro agroecological recommendations (MPKV 2023). "
                    "This is an eligibility baseline, not a farm-level verification. Field-level soil and irrigation testing is required."
                )
            else:
                return f"{crop_name} is evaluated as verified suitable across verified soil, climate, and water requirements."
