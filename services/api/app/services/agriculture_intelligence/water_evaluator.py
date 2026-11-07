"""
CropNet AI — Deterministic Water Availability & Irrigation Evaluator.

Evaluates crop hydrological feasibility, provides pomegranate Bahar daily tree
schedules (liters/tree/day), enforces decoupled chickpea irrigation statements,
and advises weather-aware irrigation suspension.
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
        # 1. Sugarcane Summer Water Exhaustion Disqualification
        # -------------------------------------------------------------
        if crop_id == "sugarcane":
            capacity = (ctx.irrigation_capacity or "").lower()
            source = (ctx.irrigation_source or "").lower()
            if "seasonal" in capacity or "dry_by_february" in capacity or "february" in source:
                res.is_disqualified = True
                msg = (
                    "Hydrological disqualification: Sugarcane requires 1500–2500 mm over 12–18 months. "
                    "A seasonal water source exhausted by February coincides with the critical summer tillering "
                    "and stem elongation phase (March–May), causing desiccation and complete crop loss (IISR 2022 / MPKV 2023)."
                )
                res.limiting_factors.append(msg)
                res.applied_rules.append(AppliedRuleRecord(
                    rule_id="RULE_SUGARCANE_SUMMER_WATER_DEPLETION",
                    domain="Irrigation Intelligence",
                    parameter_checked="irrigation_capacity",
                    rule_statement="Sugarcane requires perennial water through summer tillering (March–May)",
                    condition_met=False,
                    evidence_tier=tier,
                    citation=citation
                ))
            elif ctx.irrigation_available is False:
                res.is_disqualified = True
                res.limiting_factors.append("Sugarcane cannot be grown rainfed in semi-arid Maharashtra.")

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
                    citation=citation
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

        # -------------------------------------------------------------
        # 3. Chickpea Decoupled Irrigation & Rainfall-Aware Suspension
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

            # Weather-aware irrigation suspension check
            # If irrigation is planned (e.g. around 20-25 DAS) but 48h forecast shows >= 40 mm rain
            if ctx.forecast_rain_mm_48h and ctx.forecast_rain_mm_48h >= 40.0:
                res.warnings.append(
                    f"CRITICAL: Weather forecast indicates {ctx.forecast_rain_mm_48h} mm heavy rainfall within 48 hours. "
                    "SUSPEND any planned irrigation immediately. Open field drainage furrows to discharge surface water. "
                    "Chickpea is acutely vulnerable to soil saturation and collar rot."
                )
                res.applied_rules.append(AppliedRuleRecord(
                    rule_id="RULE_CHICKPEA_IRRIGATION_SUSPENSION_RAIN_FORECAST",
                    domain="Irrigation Intelligence",
                    parameter_checked="forecast_rain_mm_48h",
                    rule_statement="Suspend chickpea irrigation when heavy rainfall (>= 40 mm) is forecast to prevent root rot",
                    condition_met=True,
                    evidence_tier=EvidenceTier.VERIFIED,
                    citation=citation
                ))

        return res
