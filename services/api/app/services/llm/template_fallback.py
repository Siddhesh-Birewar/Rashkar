"""
CropNet AI — Deterministic Template Fallback & Response Formatting Service.

Provides high-quality, guaranteed hallucination-free deterministic explanations
in English and Marathi when the LLM is unavailable, timed out, or fails guardrails.
Enforces clean formatting: zero raw markdown headings (###, ####), zero raw Python
dictionaries, zero raw enum codes, and zero diagnostic question duplication.
"""
from typing import List, Dict, Any, Optional
from cropnet.services.api.app.schemas.agriculture_intelligence import (
    FarmEvaluationResponse,
    CropEvaluationOutcome,
    DecisionState,
    StructuredAdvisoryCard,
    AdvisoryObservationItem
)


class TemplateFallbackGenerator:
    """
    Generates deterministic, evidence-grounded template explanations and structured cards.
    """

    STATE_LABELS_EN = {
        DecisionState.VERIFIED_SUITABLE: "Verified suitable for your farm",
        DecisionState.CONDITIONALLY_SUITABLE_PENDING_DATA: "Conditionally suitable — pending farm measurements",
        DecisionState.REGIONAL_SCREENING_ONLY: "Regional assessment — field verification needed",
        DecisionState.REQUIRES_REGIONAL_VALIDATION: "Requires local agroecological validation",
        DecisionState.UNSUITABLE_VERIFIED_CONSTRAINT: "Not suitable — agronomic constraint identified",
        DecisionState.ABSTAIN_INSUFFICIENT_EVIDENCE: "Insufficient evidence — farm details required",
    }

    STATE_LABELS_MR = {
        DecisionState.VERIFIED_SUITABLE: "आपल्या शेतासाठी प्रमाणित अनुकूल",
        DecisionState.CONDITIONALLY_SUITABLE_PENDING_DATA: "सशर्त अनुकूल — शेतातील काही चाचण्या प्रलंबित",
        DecisionState.REGIONAL_SCREENING_ONLY: "प्रादेशिक छाननी — प्रत्यक्ष शेत पडताळणी आवश्यक",
        DecisionState.REQUIRES_REGIONAL_VALIDATION: "स्थानिक कृषी-हवामान पडताळणी आवश्यक",
        DecisionState.UNSUITABLE_VERIFIED_CONSTRAINT: "अयोग्य — कृषी मर्यादा आढळली",
        DecisionState.ABSTAIN_INSUFFICIENT_EVIDENCE: "माहिती अपुरी — शेताची सविस्तर माहिती आवश्यक",
    }

    @classmethod
    def format_irrigation_guidance(cls, guidance: Any, language: str = "en") -> str:
        """
        Convert structured irrigation guidance objects or dictionaries into fluent,
        safe human-readable prose. Never dumps raw Python dictionaries or braces.
        """
        if not guidance:
            return ""
        if isinstance(guidance, str):
            return guidance
        if isinstance(guidance, dict):
            is_mr = language == "mr"
            strategy = guidance.get("management_strategy")
            if strategy == "DECOUPLED_FRAMEWORKS":
                # Chickpea decoupled framework
                icrisat_rule = guidance.get("icrisat_2010_framework", {}).get("rule", "")
                mpkv_rule = guidance.get("mpkv_2023_framework", {}).get("rule", "")
                warning = guidance.get("anti_blending_warning", "")
                if is_mr:
                    parts = []
                    if icrisat_rule:
                        parts.append("ICRISAT पद्धत: १ ते २ हलकी पाणी देणे (फांद्या फुटताना आणि घाटे भरताना).")
                    if mpkv_rule:
                        parts.append("MPKV पद्धत: कालवा बागायतीसाठी पेरणीनंतर २०-२५ आणि ६०-६५ दिवसांनी पाणी देणे.")
                    if warning:
                        parts.append("महत्त्वाची सूचना: दोन्ही वेळापत्रके एकत्र करून ४ वेळा पाणी देऊ नका; अति पाण्यामुळे मूळकूज व उकळा रोगाचा धोका वाढतो.")
                    return " ".join(parts)
                else:
                    parts = []
                    if icrisat_rule:
                        parts.append(f"ICRISAT Framework: {icrisat_rule}")
                    if mpkv_rule:
                        parts.append(f"MPKV Framework: {mpkv_rule}")
                    if warning:
                        parts.append(f"Important: {warning}")
                    return " ".join(parts)
            elif "recommended_bahar" in guidance:
                rec = guidance.get("recommended_bahar", "")
                dis = guidance.get("disqualified_bahar", "")
                rat = guidance.get("rationale", "")
                if is_mr:
                    return f"शिफारस: {rec}. टाळावे: {dis}. कारण: {rat}"
                else:
                    return f"Recommended: {rec}. Avoid: {dis}. Rationale: {rat}"
            else:
                # Generic dictionary: stringify values cleanly without keys/braces
                items = []
                for k, v in guidance.items():
                    if isinstance(v, str):
                        items.append(v)
                    elif isinstance(v, dict):
                        sub = " - ".join([str(sv) for sk, sv in v.items() if isinstance(sv, (str, int, float))])
                        if sub:
                            items.append(sub)
                return ". ".join(items)
        return str(guidance)

    @classmethod
    def generate_explanation(
        cls,
        resp: FarmEvaluationResponse,
        language: str = "en",
        focus_crop: Optional[str] = None
    ) -> str:
        """
        Produce a comprehensive, farmer-friendly template explanation in English or Marathi.
        Uses clean readable formatting without raw markdown headers (###, ####).
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
        lines.append(f"CropNet Agricultural Advisory{taluka_str}{season_str}\n")

        # 2. Abstention cases
        if resp.input_validation_status == "ABSTAIN_ZERO_CONTEXT":
            lines.append(
                "No farm data or location was provided. CropNet strictly avoids making unverified guesses "
                "about crop suitability. To receive an accurate agricultural evaluation, please select your "
                "farm or answer the diagnostic questions below."
            )
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
            lines.append(f"{status_icon} {o.common_name} ({o.scientific_name}) — {state_label}")

            # Explanation sentence
            if o.explanation:
                lines.append(f"{o.explanation}\n")

            # Limiting Factors
            if o.limiting_factors:
                lines.append("Limiting Factors & Constraints:")
                for f in o.limiting_factors:
                    lines.append(f"• {f}")
                lines.append("")

            # Reproductive Heat / Weather Warnings
            if o.reproductive_risk_warnings:
                lines.append("Reproductive & Thermal Warnings:")
                for w in o.reproductive_risk_warnings:
                    lines.append(f"• {w}")
                lines.append("")

            # Irrigation guidance
            if o.irrigation_guidance:
                formatted_irr = cls.format_irrigation_guidance(o.irrigation_guidance, language="en")
                if formatted_irr:
                    lines.append(f"Irrigation Management: {formatted_irr}\n")

            # Uncertainty notes
            if o.uncertainty_notes:
                lines.append("Agronomic Notes & Diagnostic Caveats:")
                for u in o.uncertainty_notes:
                    lines.append(f"• {u}")
                lines.append("")

        # 4. Contextual Transition (Deduplicated - questions appear as chips below)
        if resp.follow_up_questions:
            lines.append("Next Steps: Please answer the diagnostic questions below so CropNet can re-evaluate your field's suitability.")

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
        lines.append(f"CropNet कृषी सल्ला अहवाल{taluka_str}{season_str}\n")

        # 2. Abstention cases
        if resp.input_validation_status == "ABSTAIN_ZERO_CONTEXT":
            lines.append(
                "आपल्या शेताची कोणतीही माहिती किंवा स्थान प्रविष्ट केलेले नाही. CropNet केवळ अंदाजे किंवा "
                "असमर्थित सल्ला देत नाही. अचूक पीक निवडीसाठी कृपया आपले शेत निवडा किंवा खालील प्रश्नांची माहिती द्यावी."
            )
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
            lines.append(f"{status_icon} {c_name} ({o.common_name}) — {state_label}")

            if o.explanation:
                lines.append(f"{o.explanation}\n")

            if o.limiting_factors:
                lines.append("मुख्य मर्यादा व त्रुटी (Limiting Factors):")
                for f in o.limiting_factors:
                    lines.append(f"• {f}")
                lines.append("")

            if o.reproductive_risk_warnings:
                lines.append("तापमान व फुलोरा धोक्याचा इशारा:")
                for w in o.reproductive_risk_warnings:
                    lines.append(f"• {w}")
                lines.append("")

            if o.irrigation_guidance:
                formatted_irr = cls.format_irrigation_guidance(o.irrigation_guidance, language="mr")
                if formatted_irr:
                    lines.append(f"पाणी व्यवस्थापन मार्गदर्शन: {formatted_irr}\n")

            if o.uncertainty_notes:
                lines.append("कृषी सल्ला व निरीक्षण नोंदी:")
                for u in o.uncertainty_notes:
                    lines.append(f"• {u}")
                lines.append("")

        if resp.follow_up_questions:
            lines.append("पुढील पावले: आपल्या शेतानुसार अचूक सल्ला मिळवण्यासाठी कृपया खाली विचारलेल्या प्रश्नांची उत्तरे द्यावीत.")

        return "\n".join(lines)

    @classmethod
    def generate_structured_card(
        cls,
        resp: FarmEvaluationResponse,
        language: str = "en",
        focus_crop: Optional[str] = None
    ) -> Optional[StructuredAdvisoryCard]:
        """
        Build the standardized 6-section StructuredAdvisoryCard from the validated decision.
        """
        is_mr = language == "mr"
        outcomes = resp.crop_outcomes
        if focus_crop:
            outcomes = [o for o in outcomes if o.crop_id.lower() == focus_crop.lower()]

        target_crop = outcomes[0] if outcomes else None
        crop_name = ""
        status_label = ""
        status_code = ""

        if target_crop:
            crop_name = (target_crop.marathi_name or target_crop.common_name) if is_mr else target_crop.common_name
            status_label = cls.STATE_LABELS_MR.get(target_crop.decision_state, str(target_crop.decision_state)) if is_mr else cls.STATE_LABELS_EN.get(target_crop.decision_state, str(target_crop.decision_state))
            status_code = target_crop.decision_state.value if hasattr(target_crop.decision_state, "value") else str(target_crop.decision_state)

        # 1. Title
        taluka = resp.taluka_resolved or "Maharashtra"
        if is_mr:
            title = f"{crop_name} कृषी मूल्यमापन सल्लागार ({taluka})" if crop_name else f"CropNet कृषी सल्लागार ({taluka})"
        else:
            title = f"{crop_name} Agronomic Feasibility Assessment ({taluka})" if crop_name else f"CropNet Agronomic Advisory ({taluka})"

        # 2. Direct Answer
        if target_crop:
            if target_crop.decision_state == DecisionState.VERIFIED_SUITABLE:
                direct_answer = (
                    f"{crop_name} आपल्या शेतासाठी सर्व आवश्यक माती व हवामान निकषांनुसार पूर्णपणे योग्य आहे."
                    if is_mr else
                    f"{crop_name} is verified suitable for your farm based on confirmed soil and agroclimatic conditions."
                )
            elif target_crop.decision_state == DecisionState.REGIONAL_SCREENING_ONLY:
                direct_answer = (
                    f"{crop_name} पिकाने {taluka} परिसरासाठी प्रादेशिक छाननी पूर्ण केली आहे. तथापि, आपल्या शेतातील विशिष्ट परिस्थितीनुसार हे पीक अनुकूल आहे की नाही, याची खात्री करण्यासाठी शेताची माहिती आवश्यक आहे."
                    if is_mr else
                    f"{crop_name} has passed regional-level screening for the {taluka} area. However, CropNet cannot yet confirm whether it is suitable for your specific field."
                )
            elif target_crop.decision_state == DecisionState.CONDITIONALLY_SUITABLE_PENDING_DATA:
                direct_answer = (
                    f"{crop_name} सशर्त अनुकूल आहे, परंतु अंतिम खात्रीसाठी शेतातील काही चाचण्यांची माहिती आवश्यक आहे."
                    if is_mr else
                    f"{crop_name} is conditionally suitable, but pending specific field diagnostic measurements."
                )
            elif target_crop.is_disqualified or target_crop.decision_state == DecisionState.UNSUITABLE_VERIFIED_CONSTRAINT:
                direct_answer = (
                    f"{crop_name} आपल्या शेतासाठी सध्याच्या माती/हवामान मर्यादांमुळे अयोग्य ठरले आहे."
                    if is_mr else
                    f"{crop_name} is not suitable for your farm due to identified agronomic constraints."
                )
            else:
                direct_answer = (
                    "अपुऱ्या शेत माहितीमुळे पीक मूल्यमापन प्रलंबित आहे."
                    if is_mr else
                    "Crop suitability assessment is pending due to insufficient farm details."
                )
        else:
            direct_answer = (
                "दिलेल्या शेत संदर्भानुसार प्रमाणित पीक मूल्यमापन खाली दिले आहे."
                if is_mr else
                "Deterministic crop evaluation summary for the selected farm context is presented below."
            )

        # 3. What this means
        if target_crop:
            if target_crop.decision_state == DecisionState.REGIONAL_SCREENING_ONLY:
                what_this_means = (
                    "प्रादेशिक छाननी हे हवामान व विभागाच्या माहितीवर आधारित प्राथमिक मूल्यमापन आहे. अंतिम अनुकूलतेची पुष्टी करण्यासाठी आपल्या शेतातील प्रत्यक्ष पाण्याचा निचरा, जमिनीची खोली आणि क्षारता तपासणे आवश्यक आहे."
                    if is_mr else
                    "Regional screening is an initial assessment based on agroecological zone data. Your field's actual drainage, soil depth and salinity still need verification before final suitability can be confirmed."
                )
            elif target_crop.is_disqualified:
                what_this_means = (
                    "शेतातील माती किंवा पाण्याची स्थिती या पिकाच्या वैज्ञानिक मर्यादेबाहेर आहे. त्यामुळे हे पीक घेतल्यास उत्पादनात मोठी घट किंवा झाडे सुकण्याचा धोका संभवतो."
                    if is_mr else
                    "One or more field conditions violate the physiological requirements for this crop, presenting significant agronomic or economic risk."
                )
            else:
                what_this_means = target_crop.explanation or (
                    "प्रणालीने प्रमाणित नियमांनुसार शेतातील परिस्थितीचे विश्लेषण केले आहे."
                    if is_mr else
                    "CropNet evaluated your farm parameters against institutional research recommendations."
                )
        else:
            what_this_means = (
                "CropNet च्या प्रमाणित निर्णय प्रणालीने आपल्या शेतासाठी पिकांची तपासणी केली आहे."
                if is_mr else
                "CropNet evaluated available crop options against ICAR and MPKV agroclimatic criteria."
            )

        # 4. Verified Observations (Actual values from farm context, never fabricated)
        observations: List[AdvisoryObservationItem] = []
        fc = getattr(resp, "farm_context", None)
        if fc:
            prov_str = "Soil Laboratory Report" if getattr(fc, "soil_data_provenance", "") == "laboratory_measured" else "SoilGrids Spatially Estimated"
            prov_str_mr = "प्रयोगशाळा माती अहवाल" if getattr(fc, "soil_data_provenance", "") == "laboratory_measured" else "SoilGrids भू-स्थानिक अंदाज"

            # Soil pH
            if fc.soil_ph is not None:
                observations.append(AdvisoryObservationItem(
                    parameter="जमिनीचा सामू (Soil pH)" if is_mr else "Soil pH",
                    value=f"{fc.soil_ph:.1f}",
                    source=prov_str_mr if is_mr else prov_str,
                    status="available"
                ))
            else:
                observations.append(AdvisoryObservationItem(
                    parameter="जमिनीचा सामू (Soil pH)" if is_mr else "Soil pH",
                    value="माहिती प्रलंबित (Untested)" if is_mr else "Untested / Pending",
                    source="Farm Profile",
                    status="untested"
                ))

            # Soil Organic Carbon
            if fc.soil_organic_carbon_pct is not None:
                observations.append(AdvisoryObservationItem(
                    parameter="सेंद्रिय कर्ब (SOC)" if is_mr else "Soil Organic Carbon",
                    value=f"{fc.soil_organic_carbon_pct:.2f}%",
                    source=prov_str_mr if is_mr else prov_str,
                    status="available"
                ))

            # Soil Texture
            if fc.soil_texture:
                observations.append(AdvisoryObservationItem(
                    parameter="जमिनीचा पोत (Texture)" if is_mr else "Soil Texture",
                    value=fc.soil_texture.capitalize(),
                    source=prov_str_mr if is_mr else prov_str,
                    status="available"
                ))

            # Electrical Conductivity
            if fc.electrical_conductivity_ds_m is not None:
                observations.append(AdvisoryObservationItem(
                    parameter="विद्युत वाहकता / क्षारता (EC)" if is_mr else "Salinity / EC",
                    value=f"{fc.electrical_conductivity_ds_m:.2f} dS/m",
                    source=prov_str_mr if is_mr else prov_str,
                    status="available"
                ))

            # Irrigation Source / Availability
            if fc.irrigation_source:
                observations.append(AdvisoryObservationItem(
                    parameter="सिंचन स्त्रोत (Irrigation)" if is_mr else "Irrigation Source",
                    value=fc.irrigation_source.capitalize(),
                    source="Farm Profile",
                    status="available"
                ))

        # 5. What needs attention (limiting factors + uncertainties)
        what_needs_attention: List[str] = []
        if target_crop:
            for lf in target_crop.limiting_factors:
                what_needs_attention.append(lf)
            for warn in target_crop.reproductive_risk_warnings:
                what_needs_attention.append(warn)
            for note in target_crop.uncertainty_notes:
                what_needs_attention.append(note)
        elif resp.follow_up_questions:
            for q in resp.follow_up_questions[:3]:
                txt = q.question_text_mr if is_mr else q.question_text_en
                what_needs_attention.append(f"{txt} ({q.agronomic_rationale})")

        # 6. Next steps (numbered action list)
        next_steps: List[str] = []
        if resp.follow_up_questions:
            next_steps.append(
                "खाली विचारलेल्या प्रश्नांची उत्तरे देऊन शेतातील परिस्थितीची खात्री करा."
                if is_mr else
                "Answer the diagnostic questions below to verify specific field drainage, depth, and salinity."
            )
        if target_crop and target_crop.irrigation_guidance:
            irr_text = cls.format_irrigation_guidance(target_crop.irrigation_guidance, language=language)
            if irr_text:
                next_steps.append(irr_text)
        next_steps.append(
            "अद्ययावत माहिती मिळताच CropNet पुन्हा मूल्यमापन करून अचूक सल्ला देईल."
            if is_mr else
            "CropNet will automatically re-run the deterministic evaluation once diagnostic details are submitted."
        )

        # 7. Evidence references (concise institutional citations)
        citations_seen = set()
        citations: List[str] = []
        if target_crop:
            for c in target_crop.citations:
                key = f"{c.organization} ({c.publication_year})"
                if key not in citations_seen:
                    citations_seen.add(key)
                    title_str = getattr(c, "publication_title", None) or getattr(c, "document_title", "Agronomic Research")
                    year_str = f" ({c.publication_year})" if getattr(c, "publication_year", None) else ""
                    pages_str = f", {c.section_or_pages}" if getattr(c, "section_or_pages", None) else ""
                    label = f"{c.organization} — {title_str}{year_str}{pages_str}"
                    citations.append(label)

        return StructuredAdvisoryCard(
            title=title,
            direct_answer=direct_answer,
            what_this_means=what_this_means,
            crop_status_label=status_label,
            crop_status_code=status_code,
            observations=observations,
            what_needs_attention=what_needs_attention,
            next_steps=next_steps,
            evidence_references=citations
        )
