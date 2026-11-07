"""
CropNet AI — Deterministic Template Fallback Generator.

Provides high-quality, guaranteed hallucination-free deterministic explanations
in English and Marathi when the LLM is unavailable, timed out, or fails guardrails.
"""
from typing import List, Dict, Any, Optional
from cropnet.services.api.app.schemas.agriculture_intelligence import (
    FarmEvaluationResponse,
    CropEvaluationOutcome,
    DecisionState
)


class TemplateFallbackGenerator:
    """
    Generates deterministic, evidence-grounded template explanations.
    """

    STATE_LABELS_EN = {
        DecisionState.VERIFIED_SUITABLE: "Verified Suitable",
        DecisionState.CONDITIONALLY_SUITABLE_PENDING_DATA: "Conditionally Suitable (Pending Diagnostic Data)",
        DecisionState.REGIONAL_SCREENING_ONLY: "Regional Screening Only (Requires Farm Validation)",
        DecisionState.REQUIRES_REGIONAL_VALIDATION: "Requires Local Agroecological Validation",
        DecisionState.UNSUITABLE_VERIFIED_CONSTRAINT: "Unsuitable (Agronomic Constraint Violated)",
        DecisionState.ABSTAIN_INSUFFICIENT_EVIDENCE: "Abstain (Insufficient Evidence)",
    }

    STATE_LABELS_MR = {
        DecisionState.VERIFIED_SUITABLE: "प्रमाणित अनुकूल (Verified Suitable)",
        DecisionState.CONDITIONALLY_SUITABLE_PENDING_DATA: "सशर्त अनुकूल (काही चाचण्या प्रलंबित)",
        DecisionState.REGIONAL_SCREENING_ONLY: "प्रादेशिक छाननी (शेताची माती तपासणी आवश्यक)",
        DecisionState.REQUIRES_REGIONAL_VALIDATION: "स्थानिक कृषी-हवामान पडताळणी आवश्यक",
        DecisionState.UNSUITABLE_VERIFIED_CONSTRAINT: "अयोग्य (मर्यादा उल्लंघन / Unsuitable)",
        DecisionState.ABSTAIN_INSUFFICIENT_EVIDENCE: "अपूर्ण पुराव्यामुळे मार्गदर्शन स्थगित",
    }

    @classmethod
    def generate_explanation(
        cls,
        resp: FarmEvaluationResponse,
        language: str = "en",
        focus_crop: Optional[str] = None
    ) -> str:
        """
        Produce a comprehensive, farmer-friendly template explanation in English or Marathi.
        """
        if language == "mr":
            return cls._generate_marathi(resp, focus_crop=focus_crop)
        return cls._generate_english(resp, focus_crop=focus_crop)

    @classmethod
    def _generate_english(
        cls,
        resp: FarmEvaluationResponse,
        focus_crop: Optional[str] = None
    ) -> str:
        lines = []

        # 1. Header / Context
        taluka_str = f" for {resp.taluka_resolved} Taluka" if resp.taluka_resolved else ""
        season_str = f" ({resp.target_season.capitalize()} season)" if resp.target_season else ""
        lines.append(f"### CropNet Agricultural Advisory{taluka_str}{season_str}\n")

        # 2. Abstention cases
        if resp.input_validation_status == "ABSTAIN_ZERO_CONTEXT":
            lines.append(
                "No farm data or location was provided. CropNet strictly avoids making unverified guesses "
                "about crop suitability. To receive an accurate agricultural evaluation, please provide your "
                "location and farm context using the questions below."
            )
            cls._append_followups_en(lines, resp)
            return "\n".join(lines)

        if resp.input_validation_status == "ABSTAIN_UNREGISTERED_CROP":
            lines.append(
                "The requested crop is not currently registered in CropNet's 10 priority Maharashtra crops "
                "(Chickpea, Sorghum, Soybean, Cotton, Sugarcane, Wheat, Bajra, Groundnut, Maize, Pomegranate). "
                "To protect farmer investments, the system strictly abstains from synthesizing ungrounded agronomic advice."
            )
            return "\n".join(lines)

        # 3. Evaluated Crop Outcomes
        outcomes = resp.crop_outcomes
        if focus_crop:
            outcomes = [o for o in outcomes if o.crop_id.lower() == focus_crop.lower()]

        if not outcomes:
            lines.append("No specific crop outcomes evaluated for the supplied context.")
            return "\n".join(lines)

        for o in outcomes:
            state_label = cls.STATE_LABELS_EN.get(o.decision_state, str(o.decision_state))
            status_icon = "⚠️" if o.is_disqualified else ("✅" if o.decision_state == DecisionState.VERIFIED_SUITABLE else "ℹ️")
            lines.append(f"#### {status_icon} {o.common_name} (*{o.scientific_name}*) — **{state_label}**")

            # Explanation sentence
            if o.explanation:
                lines.append(f"{o.explanation}\n")

            # Limiting Factors
            if o.limiting_factors:
                lines.append("**Limiting Factors & Constraints:**")
                for f in o.limiting_factors:
                    lines.append(f"- {f}")
                lines.append("")

            # Reproductive Heat / Weather Warnings
            if o.reproductive_risk_warnings:
                lines.append("**Reproductive & Thermal Warnings:**")
                for w in o.reproductive_risk_warnings:
                    lines.append(f"- {w}")
                lines.append("")

            # Irrigation guidance
            if o.irrigation_guidance:
                lines.append(f"**Irrigation Management**: {o.irrigation_guidance}\n")

            # Uncertainty notes
            if o.uncertainty_notes:
                lines.append("**Agronomic Notes & Diagnostic Caveats:**")
                for u in o.uncertainty_notes:
                    lines.append(f"- {u}")
                lines.append("")

        # 4. Follow-up Questions
        cls._append_followups_en(lines, resp)

        return "\n".join(lines)

    @classmethod
    def _generate_marathi(
        cls,
        resp: FarmEvaluationResponse,
        focus_crop: Optional[str] = None
    ) -> str:
        lines = []

        # 1. Header
        taluka_str = f" — {resp.taluka_resolved} तालुका" if resp.taluka_resolved else ""
        season_str = f" ({resp.target_season} हंगाम)" if resp.target_season else ""
        lines.append(f"### CropNet कृषी सल्ला अहवाल{taluka_str}{season_str}\n")

        # 2. Abstention cases
        if resp.input_validation_status == "ABSTAIN_ZERO_CONTEXT":
            lines.append(
                "आपल्या शेताची कोणतीही माहिती किंवा स्थान प्रविष्ट केलेले नाही. CropNet केवळ अंदाजे किंवा "
                "असमर्थित सल्ला देत नाही. अचूक पीक निवडीसाठी कृपया खालील प्राथमिक प्रश्नांची माहिती द्यावी."
            )
            cls._append_followups_mr(lines, resp)
            return "\n".join(lines)

        if resp.input_validation_status == "ABSTAIN_UNREGISTERED_CROP":
            lines.append(
                "विचारलेले पीक CropNet च्या महाराष्ट्रातील १० प्राधान्य पिकांमध्ये नोंदणीकृत नाही "
                "(हरभरा, रब्बी ज्वारी, सोयाबीन, कापूस, ऊस, गहू, बाजरी, भुईमूग, मका, डाळिंब). "
                "शेतकऱ्यांचे आर्थिक नुकसान टाळण्यासाठी, वैज्ञानिक पुराव्याशिवाय अनधिकृत पिकांवर मार्गदर्शन देणे प्रणाली टाळते."
            )
            return "\n".join(lines)

        # 3. Evaluated Crop Outcomes
        outcomes = resp.crop_outcomes
        if focus_crop:
            outcomes = [o for o in outcomes if o.crop_id.lower() == focus_crop.lower()]

        if not outcomes:
            lines.append("दिलेल्या माहितीनुसार मूल्यमापनासाठी कोणतेही पीक आढळले नाही.")
            return "\n".join(lines)

        for o in outcomes:
            c_name = o.marathi_name or o.common_name
            state_label = cls.STATE_LABELS_MR.get(o.decision_state, str(o.decision_state))
            status_icon = "⚠️" if o.is_disqualified else ("✅" if o.decision_state == DecisionState.VERIFIED_SUITABLE else "ℹ️")
            lines.append(f"#### {status_icon} {c_name} ({o.common_name}) — **{state_label}**")

            if o.explanation:
                lines.append(f"{o.explanation}\n")

            if o.limiting_factors:
                lines.append("**मुख्य मर्यादा व त्रुटी (Limiting Factors):**")
                for f in o.limiting_factors:
                    lines.append(f"- {f}")
                lines.append("")

            if o.reproductive_risk_warnings:
                lines.append("**तापमान व फुलोरा धोक्याचा इशारा:**")
                for w in o.reproductive_risk_warnings:
                    lines.append(f"- {w}")
                lines.append("")

            if o.irrigation_guidance:
                lines.append(f"**पाणी व्यवस्थापन मार्गदर्शन**: {o.irrigation_guidance}\n")

            if o.uncertainty_notes:
                lines.append("**कृषी सल्ला व निरीक्षण नोंदी:**")
                for u in o.uncertainty_notes:
                    lines.append(f"- {u}")
                lines.append("")

        cls._append_followups_mr(lines, resp)

        return "\n".join(lines)

    @classmethod
    def _append_followups_en(cls, lines: List[str], resp: FarmEvaluationResponse):
        if resp.follow_up_questions:
            lines.append("### Recommended Follow-Up Diagnostic Questions:")
            lines.append("To refine this recommendation and eliminate remaining uncertainties, please clarify:")
            for idx, q in enumerate(resp.follow_up_questions, 1):
                opts = f" (Options: {', '.join(q.options)})" if q.options else ""
                lines.append(f"{idx}. **{q.question_text_en}**{opts}")
                lines.append(f"   *Agronomic purpose: {q.agronomic_rationale}*")
            lines.append("")

    @classmethod
    def _append_followups_mr(cls, lines: List[str], resp: FarmEvaluationResponse):
        if resp.follow_up_questions:
            lines.append("### शिफारस अधिक अचूक करण्यासाठी आवश्यक प्रश्न:")
            lines.append("उरलेल्या त्रुटी दूर करून आपल्या शेतानुसार अचूक सल्ला मिळवण्यासाठी खालील बाबींची खात्री करा:")
            for idx, q in enumerate(resp.follow_up_questions, 1):
                opts = f" (पर्याय: {', '.join(q.options)})" if q.options else ""
                lines.append(f"{idx}. **{q.question_text_mr}**{opts}")
                lines.append(f"   *कृषी उद्देश: {q.agronomic_rationale}*")
            lines.append("")
