"""
CropNet AI — Deterministic Climate & Weather Evaluator.

Evaluates ambient and forecast temperatures against growth-stage thresholds,
validates sowing moisture prerequisites, and qualifies thermal sensitivities.
Phase 5.1.2: Hardened evidence boundaries; unverified compendium thresholds
no longer enforce hard disqualification; all rules carry complete metadata.
"""
import logging
from typing import List, Optional, Dict, Any
from cropnet.services.api.app.schemas.agriculture_intelligence import (
    FarmContextInput,
    AppliedRuleRecord,
    EvidenceTier,
    EnforcementLevel,
    CitationMetadata
)
from cropnet.services.api.app.schemas.crop import CropFullProfileResponse
from cropnet.services.api.app.services.agriculture_intelligence.evidence_gate import EvidenceGate

logger = logging.getLogger(__name__)


class ClimateEvaluationResult:
    def __init__(self, crop_id: str):
        self.crop_id = crop_id
        self.is_disqualified: bool = False
        self.limiting_factors: List[str] = []
        self.reproductive_risk_warnings: List[str] = []
        self.warnings: List[str] = []
        self.missing_parameters: List[str] = []
        self.applied_rules: List[AppliedRuleRecord] = []


class ClimateSuitabilityEvaluator:
    """
    Evaluates meteorological constraints and thermal thresholds deterministically.
    """

    @staticmethod
    def evaluate(
        ctx: FarmContextInput,
        profile: CropFullProfileResponse,
        citation: Optional[CitationMetadata] = None
    ) -> ClimateEvaluationResult:
        res = ClimateEvaluationResult(crop_id=profile.id)
        clim_req = profile.climate
        if not clim_req:
            res.missing_parameters.append("crop_climate_requirements")
            return res

        crop_id = profile.id
        primary_src_id = profile.sources[0].id if (profile.sources and len(profile.sources) > 0) else None
        tier = EvidenceGate.get_tier(clim_req.source_id or primary_src_id)

        # -------------------------------------------------------------
        # 1. Chickpea Reproductive Thermal Stress Thresholds
        # -------------------------------------------------------------
        lang = (ctx.language or "en").lower()
        if crop_id == "chickpea":
            # High-temperature threshold (> 35°C daily max during reproductive stage)
            max_t = ctx.reproductive_temp_max_c if ctx.reproductive_temp_max_c is not None else ctx.forecast_max_temp_c
            if max_t is not None and max_t > 35.0:
                if lang == "mr":
                    warn_msg = (
                        f"कमाल तापमान ({max_t}°C) ३५°C च्या मर्यादेपेक्षा जास्त आहे. "
                        "ICRISAT (2010, पान ३) नुसार, पुनरुत्पादन अवस्थेत (reproductive stage) कमाल तापमान ३५°C पेक्षा जास्त राहिल्यास "
                        "फूल गळ (flower drop) होते आणि घाटे धारणेत (pod set) मोठी घट येते. "
                        "(टीप: ही पुनरुत्पादन संवेदनशीलतेची मर्यादा असून झाड मरण्याची मर्यादा नाही)."
                    )
                else:
                    warn_msg = (
                        f"Forecasted maximum daily temperature ({max_t}°C) exceeds the 35°C threshold. "
                        "According to ICRISAT (2010, p. 3), daily maximum temperature > 35°C during the "
                        "reproductive stage induces severe heat stress, causing flower drop and reduced pod set. "
                        "(Note: This is a reproductive-stage sensitivity threshold, not a universal plant mortality limit)."
                    )
                res.reproductive_risk_warnings.append(warn_msg)
                res.applied_rules.append(AppliedRuleRecord(
                    rule_id="RULE_CHICKPEA_HEAT_STRESS_35C",
                    domain="Weather and Climate Intelligence",
                    parameter_checked="forecast_max_temp_c",
                    rule_statement="Daily max temperature > 35°C during reproductive stage causes flower drop and reduced pod set (ICRISAT 2010, p. 3)",
                    condition_met=True,
                    evidence_tier=tier,
                    citation=citation,
                    claim_verification_status="VERIFIED",
                    source_id="icrisat_chickpea_2010",
                    document_title="Chickpea Seed Production Manual",
                    section_or_pages="p. 3",
                    supporting_statement="High temperatures (>35°C) during reproductive development cause flower drop and reduce pod set.",
                    applicability_conditions="reproductive_temp_max_c > 35.0",
                    enforcement_level=EnforcementLevel.ADVISORY_ONLY,
                    can_trigger_disqualification=False
                ))

            # Low-temperature threshold (mean of max and min < 15°C during reproductive stage)
            mean_t = ctx.reproductive_temp_mean_c
            if mean_t is None and ctx.forecast_max_temp_c is not None and ctx.forecast_min_temp_c is not None:
                mean_t = (ctx.forecast_max_temp_c + ctx.forecast_min_temp_c) / 2.0

            if mean_t is not None and mean_t < 15.0:
                if lang == "mr":
                    warn_msg = (
                        f"सरासरी तापमान ({mean_t:.1f}°C) १५°C च्या खाली आहे. "
                        "ICRISAT (2010, पान ३) नुसार, पुनरुत्पादन अवस्थेत कमाल आणि किमान तापमानाची सरासरी १५°C पेक्षा कमी राहिल्यास "
                        "फूल गळ (flower abortion) होते आणि घाटे धारणा (pod set) लांबणीवर पडते."
                    )
                else:
                    warn_msg = (
                        f"Mean daily temperature ({mean_t:.1f}°C) is below the 15°C threshold. "
                        "According to ICRISAT (2010, p. 3), mean daily temperature < 15°C during "
                        "the reproductive stage causes cold-induced flower abortion and delayed pod set."
                    )
                res.reproductive_risk_warnings.append(warn_msg)
                res.applied_rules.append(AppliedRuleRecord(
                    rule_id="RULE_CHICKPEA_COLD_STRESS_15C",
                    domain="Weather and Climate Intelligence",
                    parameter_checked="mean_daily_temp_c",
                    rule_statement="Mean of daily max and min temperatures < 15°C during reproductive stage causes flower drop and delayed pod set (ICRISAT 2010, p. 3)",
                    condition_met=True,
                    evidence_tier=tier,
                    citation=citation,
                    claim_verification_status="VERIFIED",
                    source_id="icrisat_chickpea_2010",
                    document_title="Chickpea Seed Production Manual",
                    section_or_pages="p. 3",
                    supporting_statement="Mean of maximum and minimum daily temperature < 15°C during reproductive development causes flower drop and delayed pod set.",
                    applicability_conditions="reproductive_temp_mean_c < 15.0",
                    enforcement_level=EnforcementLevel.ADVISORY_ONLY,
                    can_trigger_disqualification=False
                ))

        # -------------------------------------------------------------
        # 2. Climatology vs Real-Time Sowing Rain Prerequisite
        # Phase 5.1.2: Unverified MPKV thresholds cannot enforce hard disqualification
        # -------------------------------------------------------------
        rain_received = ctx.sowing_window_rain_mm if ctx.sowing_window_rain_mm is not None else ctx.actual_recorded_rain_mm
        if rain_received is not None and rain_received < 75.0:
            msg = (
                "Operational moisture advisory: Sowing into dry soil relying purely on 30-year historical climate averages "
                "without confirmed real-time monsoon onset will result in seed desiccation and germination failure. "
                "DO NOT SOW UNTIL MONSOON ARRIVES. Regional farm advisory recommends awaiting 75–100 mm actual soaking rainfall before Kharif sowing."
            )
            res.warnings.append(msg)
            res.limiting_factors.append(msg)
            res.applied_rules.append(AppliedRuleRecord(
                rule_id="RULE_KHARIF_SOWING_MOISTURE_GATE",
                domain="Weather and Climate Intelligence",
                parameter_checked="sowing_window_rain_mm",
                rule_statement="Awaiting 75–100 mm soaking rain before Kharif sowing is advised in regional practice; climatology != real-time forecast",
                condition_met=False,
                evidence_tier=EvidenceTier.CONDITIONALLY_SUPPORTED,
                citation=citation,
                claim_verification_status="CONDITIONALLY_SUPPORTED",
                source_id="mpkv_pop_2023",
                document_title="Package of Practices for Field Crops of Western Maharashtra",
                section_or_pages="Compendium requires physical inspection",
                supporting_statement="Sowing should be undertaken only after receiving 75–100 mm soaking rainfall.",
                applicability_conditions="sowing_window_rain_mm < 75.0",
                enforcement_level=EnforcementLevel.CONDITIONAL_CONSTRAINT,
                can_trigger_disqualification=False
            ))
        elif ctx.proposed_sowing_date and ctx.target_season == "kharif":
            if ctx.monsoon_arrived is False:
                msg = (
                    "Operational moisture advisory: Sowing into dry soil relying on 30-year historical climate averages "
                    "without real-time monsoon onset will result in seed desiccation and germination failure. "
                    "DO NOT SOW UNTIL MONSOON ARRIVES. A minimum of 75–100 mm actual soaking rainfall is advised before sowing."
                )
                res.warnings.append(msg)
                res.limiting_factors.append(msg)
                res.applied_rules.append(AppliedRuleRecord(
                    rule_id="RULE_KHARIF_SOWING_MOISTURE_GATE",
                    domain="Weather and Climate Intelligence",
                    parameter_checked="actual_recorded_rain_mm",
                    rule_statement="Awaiting 75–100 mm soaking rain before Kharif sowing is advised in regional practice; climatology != real-time forecast",
                    condition_met=False,
                    evidence_tier=EvidenceTier.CONDITIONALLY_SUPPORTED,
                    citation=citation,
                    claim_verification_status="CONDITIONALLY_SUPPORTED",
                    source_id="mpkv_pop_2023",
                    document_title="Package of Practices for Field Crops of Western Maharashtra",
                    section_or_pages="Compendium requires physical inspection",
                    supporting_statement="Sowing should be undertaken only after receiving 75–100 mm soaking rainfall.",
                    applicability_conditions="monsoon_arrived is False",
                    enforcement_level=EnforcementLevel.CONDITIONAL_CONSTRAINT,
                    can_trigger_disqualification=False
                ))

        # -------------------------------------------------------------
        # 3. Kharif Bajra Sowing Window
        # -------------------------------------------------------------
        if crop_id == "bajra" and ctx.target_season == "kharif" and ctx.proposed_sowing_date:
            try:
                dt = ctx.proposed_sowing_date
                if "-07-16" <= dt[-5:] or dt[-5:] < "06-15":
                    warn_b = (
                        "Kharif Bajra optimum sowing window in Maharashtra is June 15 to July 15. "
                        "Sowing later than July 15 significantly increases downy mildew susceptibility and shoot fly damage."
                    )
                    res.warnings.append(warn_b)
                    res.applied_rules.append(AppliedRuleRecord(
                        rule_id="RULE_BAJRA_KHARIF_SOWING_WINDOW",
                        domain="Weather and Climate Intelligence",
                        parameter_checked="proposed_sowing_date",
                        rule_statement="Kharif Bajra sowing window is June 15 to July 15 (MPKV / IIMR)",
                        condition_met=False,
                        evidence_tier=EvidenceTier.CONDITIONALLY_SUPPORTED,
                        citation=citation,
                        claim_verification_status="CONDITIONALLY_SUPPORTED",
                        source_id="mpkv_pop_2023",
                        document_title="Package of Practices for Field Crops of Western Maharashtra",
                        section_or_pages="Compendium requires physical inspection",
                        supporting_statement="Optimum sowing window for Kharif bajra is June 15 to July 15.",
                        applicability_conditions="kharif proposed_sowing_date outside 06-15 to 07-15",
                        enforcement_level=EnforcementLevel.ADVISORY_ONLY,
                        can_trigger_disqualification=False
                    ))
            except Exception as exc:
                logger.warning("Failed evaluating Kharif Bajra sowing window for date '%s': %s", ctx.proposed_sowing_date, exc)

        return res
