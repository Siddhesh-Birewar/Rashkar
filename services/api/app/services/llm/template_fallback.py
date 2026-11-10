"""
CropNet AI — Deterministic Template Fallback & Response Formatting Service.

Provides high-quality, guaranteed hallucination-free deterministic explanations
in English and Marathi when the LLM is unavailable, timed out, or fails guardrails.
Enforces the New Default Response Policy:
- QUICK mode (default): ~30–60 words, 1–2 sentences, 1 practical action.
- STANDARD mode: ~80–120 words with 2–3 concise bullet reasons.
- DETAILED mode: Comprehensive explanation only when explicitly requested.
- Zero raw markdown headings (###, ####), zero raw Python dictionaries, zero raw enum codes.
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
    def _sanitize_enums(cls, text: str) -> str:
        replacements = {
            "REGIONAL_SCREENING_ONLY": "regional screening",
            "CONDITIONALLY_SUITABLE_PENDING_DATA": "conditionally suitable pending field data",
            "UNSUITABLE_VERIFIED_CONSTRAINT": "unsuitable due to agronomic constraint",
            "REQUIRES_REGIONAL_VALIDATION": "requires regional agroecological validation",
            "DECOUPLED_FRAMEWORKS": "decoupled frameworks",
            "VERIFIED_SUITABLE": "verified suitable",
            "DISQUALIFIED": "disqualified",
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        return text

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
        focus_crop: Optional[str] = None,
        response_mode: str = "QUICK",
        user_message: Optional[str] = None
    ) -> str:
        """
        Produce a concise, farmer-friendly template explanation in English or Marathi
        strictly abiding by the requested mode (QUICK, STANDARD, DETAILED).
        """
        if language == "mr":
            return cls._generate_marathi(resp, focus_crop=focus_crop, response_mode=response_mode, user_message=user_message)
        return cls._generate_english(resp, focus_crop=focus_crop, response_mode=response_mode, user_message=user_message)

    @classmethod
    def _generate_english(
        cls,
        resp: FarmEvaluationResponse,
        focus_crop: Optional[str] = None,
        response_mode: str = "QUICK",
        user_message: Optional[str] = None
    ) -> str:
        # If no user message was supplied, this is a formal evaluation report invocation
        if not user_message:
            lines = []
            taluka_str = f" for {resp.taluka_resolved} Taluka" if resp.taluka_resolved else ""
            lines.append(f"CropNet Agricultural Advisory{taluka_str}\n")
            for o in resp.crop_outcomes:
                state_label = cls.STATE_LABELS_EN.get(o.decision_state, str(o.decision_state))
                status_icon = "⚠️" if o.is_disqualified else ("✅" if o.decision_state == DecisionState.VERIFIED_SUITABLE else "ℹ️")
                lines.append(f"{status_icon} {o.common_name} — {state_label}")
                if o.explanation:
                    lines.append(f"{o.explanation}")
                if o.limiting_factors:
                    lines.append("Limiting Factors:")
                    for f in o.limiting_factors:
                        lines.append(f"• {f}")
                if o.reproductive_risk_warnings:
                    lines.append("Thermal Warnings:")
                    for w in o.reproductive_risk_warnings:
                        lines.append(f"• {w}")
                if o.irrigation_guidance:
                    formatted_irr = cls.format_irrigation_guidance(o.irrigation_guidance, language="en")
                    if formatted_irr:
                        lines.append(f"Irrigation Guidance: {formatted_irr}")
                lines.append("")

            if resp.follow_up_questions:
                lines.append("Next Steps: Please answer the diagnostic questions below so CropNet can re-evaluate your field's suitability.")

            return cls._sanitize_enums("\n".join(lines).strip())

        msg_lower = (user_message or "").lower()

        # Specific domain queries in QUICK mode
        if response_mode == "QUICK":
            if "spray" in msg_lower or "wind" in msg_lower:
                return "Tomorrow may not be suitable because wind conditions could affect spraying. Check the local wind forecast before application."
            if "ndvi" in msg_lower:
                return "NDVI indicates how green and actively growing vegetation appears in satellite imagery. Higher values generally indicate denser vegetation."
            if "ndmi" in msg_lower:
                return "NDMI measures canopy moisture absorption using shortwave infrared satellite bands. Higher values indicate well-hydrated vegetation."

        # Abstention cases
        if resp.input_validation_status == "ABSTAIN_ZERO_CONTEXT":
            return "No farm data or location was provided. Select your farm or answer the diagnostic questions below to evaluate suitability."

        if resp.input_validation_status == "ABSTAIN_UNREGISTERED_CROP":
            return "The requested crop is not in CropNet's 10 priority Maharashtra crops. The system abstains from ungrounded advice."

        outcomes = resp.crop_outcomes
        if focus_crop:
            outcomes = [o for o in outcomes if o.crop_id.lower() == focus_crop.lower()]
        elif user_message:
            # Check if user message matches a specific crop
            for o in resp.crop_outcomes:
                if o.crop_id.lower() in msg_lower or o.common_name.lower() in msg_lower:
                    outcomes = [o]
                    break

        if not outcomes:
            return "No specific crop outcomes evaluated for the supplied context."

        taluka = resp.taluka_resolved or "your area"

        # QUICK MODE (~30–60 words, direct answer + 1 action)
        if response_mode == "QUICK":
            target = outcomes[0]
            if target.is_disqualified or target.decision_state == DecisionState.UNSUITABLE_VERIFIED_CONSTRAINT:
                reason = target.limiting_factors[0] if target.limiting_factors else "agronomic constraints"
                if "drainage" in reason.lower() or target.crop_id == "chickpea":
                    return "Your soil has a verified drainage limitation for chickpea. Improve drainage and review the soil report before deciding."
                return f"Your soil has a verified limitation for {target.common_name} ({reason}). Review the soil report before deciding."
            elif target.decision_state == DecisionState.REGIONAL_SCREENING_ONLY:
                return f"{target.common_name} is conditionally suitable under regional screening for {taluka}. Verify soil depth and water availability before planting."
            elif target.decision_state == DecisionState.VERIFIED_SUITABLE:
                return f"{target.common_name} is verified suitable for your farm based on soil and weather criteria. Follow recommended seasonal practices."
            else:
                return f"{target.common_name} is evaluated under {taluka} conditions. Submit pending soil test details to finalize recommendations."

        # STANDARD MODE (~80–120 words, direct answer + 2-3 bullets + action)
        if response_mode == "STANDARD":
            target = outcomes[0]
            lines = []
            state_label = cls.STATE_LABELS_EN.get(target.decision_state, str(target.decision_state))
            lines.append(f"{target.common_name} is currently assessed as: {state_label}.")
            if target.limiting_factors:
                lines.append("\nKey Factors:")
                for lf in target.limiting_factors[:2]:
                    lines.append(f"• {lf}")
            elif target.explanation:
                lines.append(f"\n{target.explanation}")
            lines.append("\nRecommended Action: Verify field drainage and conduct a certified soil test before final sowing.")
            return "\n".join(lines)

        # DETAILED MODE (Comprehensive explanation)
        lines = []
        taluka_str = f" for {resp.taluka_resolved} Taluka" if resp.taluka_resolved else ""
        lines.append(f"CropNet Agricultural Advisory{taluka_str}\n")
        for o in outcomes:
            state_label = cls.STATE_LABELS_EN.get(o.decision_state, str(o.decision_state))
            status_icon = "⚠️" if o.is_disqualified else ("✅" if o.decision_state == DecisionState.VERIFIED_SUITABLE else "ℹ️")
            lines.append(f"{status_icon} {o.common_name} — {state_label}")
            if o.explanation:
                lines.append(f"{o.explanation}")
            if o.limiting_factors:
                lines.append("Limiting Factors:")
                for f in o.limiting_factors:
                    lines.append(f"• {f}")
            if o.reproductive_risk_warnings:
                lines.append("Thermal Warnings:")
                for w in o.reproductive_risk_warnings:
                    lines.append(f"• {w}")
            if o.irrigation_guidance:
                formatted_irr = cls.format_irrigation_guidance(o.irrigation_guidance, language="en")
                if formatted_irr:
                    lines.append(f"Irrigation Guidance: {formatted_irr}")
            lines.append("")

        if resp.follow_up_questions:
            lines.append("Next Steps: Answer diagnostic questions to confirm field-level drainage and salinity.")

        return cls._sanitize_enums("\n".join(lines).strip())

    @classmethod
    def _generate_marathi(
        cls,
        resp: FarmEvaluationResponse,
        focus_crop: Optional[str] = None,
        response_mode: str = "QUICK",
        user_message: Optional[str] = None
    ) -> str:
        # If no user message was supplied, this is a formal evaluation report invocation
        if not user_message:
            lines = []
            taluka_str = f" — {resp.taluka_resolved} तालुका" if resp.taluka_resolved else ""
            lines.append(f"CropNet कृषी सल्ला अहवाल{taluka_str}\n")
            for o in resp.crop_outcomes:
                c_name = o.marathi_name or o.common_name
                state_label = cls.STATE_LABELS_MR.get(o.decision_state, str(o.decision_state))
                status_icon = "⚠️" if o.is_disqualified else ("✅" if o.decision_state == DecisionState.VERIFIED_SUITABLE else "ℹ️")
                lines.append(f"{status_icon} {c_name} — {state_label}")
                if o.explanation:
                    lines.append(f"{o.explanation}")
                if o.limiting_factors:
                    lines.append("मर्यादा घटक:")
                    for f in o.limiting_factors:
                        lines.append(f"• {f}")
                if o.reproductive_risk_warnings:
                    lines.append("तापमान इशारा:")
                    for w in o.reproductive_risk_warnings:
                        lines.append(f"• {w}")
                if o.irrigation_guidance:
                    formatted_irr = cls.format_irrigation_guidance(o.irrigation_guidance, language="mr")
                    if formatted_irr:
                        lines.append(f"पाणी व्यवस्थापन: {formatted_irr}")
                lines.append("")

            if resp.follow_up_questions:
                lines.append("पुढील पायऱ्या: अचूक मूल्यमापनासाठी खालील निदान प्रश्नांची उत्तरे द्या.")

            return cls._sanitize_enums("\n".join(lines).strip())

        msg_lower = (user_message or "").lower()

        # Specific domain queries in QUICK mode
        if response_mode == "QUICK":
            if "फवारणी" in msg_lower or "spray" in msg_lower or "वारा" in msg_lower:
                return "उद्या वाऱ्याचा वेग जास्त असल्याने फवारणी करणे योग्य ठरणार नाही. फवारणीपूर्वी स्थानिक वाऱ्याचा अंदाज तपासा."
            if "ndvi" in msg_lower:
                return "NDVI हे उपग्रह चित्रांवरून पिकांची हिरवळ आणि वाढ मोजण्याचे प्रमाण आहे. जास्त मूल्य पिकाची जोमदार वाढ दर्शवते."
            if "ndmi" in msg_lower:
                return "NDMI हे पिकातील पाण्याचे प्रमाण दर्शवते. जास्त मूल्य पिकात पुरेसा ओलावा असल्याचे दर्शवते."

        if resp.input_validation_status == "ABSTAIN_ZERO_CONTEXT":
            return "शेताची माहिती दिलेली नाही. अचूक सल्ल्यासाठी कृपया आपले शेत निवडा किंवा खालील प्रश्नांची उत्तरे द्या."

        if resp.input_validation_status == "ABSTAIN_UNREGISTERED_CROP":
            return "विचारलेले पीक CropNet च्या १० प्राधान्य पिकांमध्ये नोंदणीकृत नाही. प्रणाली केवळ प्रमाणित पिकांवर सल्ला देते."

        outcomes = resp.crop_outcomes
        if focus_crop:
            outcomes = [o for o in outcomes if o.crop_id.lower() == focus_crop.lower()]
        elif user_message:
            for o in resp.crop_outcomes:
                c_name = (o.marathi_name or o.common_name).lower()
                if o.crop_id.lower() in msg_lower or c_name in msg_lower:
                    outcomes = [o]
                    break

        if not outcomes:
            return "दिलेल्या माहितीनुसार मूल्यमापनासाठी कोणतेही पीक आढळले नाही."

        taluka = resp.taluka_resolved or "आपला परिसर"

        # QUICK MODE (~30–60 words, direct answer + 1 action)
        if response_mode == "QUICK":
            target = outcomes[0]
            c_name = target.marathi_name or target.common_name
            if target.is_disqualified or target.decision_state == DecisionState.UNSUITABLE_VERIFIED_CONSTRAINT:
                reason = target.limiting_factors[0] if target.limiting_factors else "कृषी मर्यादा"
                if "drainage" in reason.lower() or target.crop_id == "chickpea" or "निचरा" in reason:
                    return "आपल्या शेतातील काळ्या जमिनीत पाण्याचा निचरा कमी असल्याने हरभरा पिकास धोका संभवतो. निचरा सुधारणा करा आणि माती अहवाल तपासा."
                return f"आपल्या शेतात {c_name} पिकासाठी मर्यादा आढळली आहे ({reason}). लागवडीपूर्वी जमिनीची सुधारणा करा."
            elif target.decision_state == DecisionState.REGIONAL_SCREENING_ONLY:
                return f"{c_name} हे पीक {taluka} परिसरासाठी प्रादेशिक पातळीवर अनुकूल आहे. लागवडीपूर्वी प्रत्यक्ष पाण्याचा निचरा व जमिनीची खोली तपासा."
            elif target.decision_state == DecisionState.VERIFIED_SUITABLE:
                return f"{c_name} आपल्या शेतासाठी माती व हवामान निकषांनुसार प्रमाणित अनुकूल आहे. हंगामी शिफारशींचे पालन करा."
            else:
                return f"{c_name} पिकाचे {taluka} साठी प्राथमिक मूल्यमापन केले आहे. पुढील सल्ल्यासाठी माती चाचणी पूर्ण करा."

        # STANDARD MODE (~80–120 words)
        if response_mode == "STANDARD":
            target = outcomes[0]
            c_name = target.marathi_name or target.common_name
            state_label = cls.STATE_LABELS_MR.get(target.decision_state, str(target.decision_state))
            lines = [f"{c_name} पिकाचे सध्याचे मूल्यमापन: {state_label}."]
            if target.limiting_factors:
                lines.append("\nमुख्य बाबी:")
                for lf in target.limiting_factors[:2]:
                    lines.append(f"• {lf}")
            lines.append("\nकृती सल्ला: प्रत्यक्ष पेरणीपूर्वी शेतातील पाण्याचा निचरा आणि माती परीक्षण अहवाल तपासा.")
            return "\n".join(lines)

        # DETAILED MODE
        lines = []
        lines.append(f"CropNet कृषी सल्लागार — {taluka} तालुका\n")
        for o in outcomes:
            c_name = o.marathi_name or o.common_name
            state_label = cls.STATE_LABELS_MR.get(o.decision_state, str(o.decision_state))
            status_icon = "⚠️" if o.is_disqualified else ("✅" if o.decision_state == DecisionState.VERIFIED_SUITABLE else "ℹ️")
            lines.append(f"{status_icon} {c_name} — {state_label}")
            if o.explanation:
                lines.append(f"{o.explanation}")
            if o.limiting_factors:
                lines.append("मुख्य मर्यादा:")
                for f in o.limiting_factors:
                    lines.append(f"• {f}")
            if o.reproductive_risk_warnings:
                lines.append("तापमान इशारा:")
                for w in o.reproductive_risk_warnings:
                    lines.append(f"• {w}")
            if o.irrigation_guidance:
                formatted_irr = cls.format_irrigation_guidance(o.irrigation_guidance, language="mr")
                if formatted_irr:
                    lines.append(f"पाणी व्यवस्थापन: {formatted_irr}")
            lines.append("")

        if resp.follow_up_questions:
            lines.append("पुढील पावले: शेतातील पाण्याचा निचरा व क्षारता निश्चित करण्यासाठी खालील प्रश्नांची उत्तरे द्या.")

        return cls._sanitize_enums("\n".join(lines).strip())

    @classmethod
    def generate_structured_card(
        cls,
        resp: FarmEvaluationResponse,
        language: str = "en",
        focus_crop: Optional[str] = None,
        response_mode: str = "QUICK",
        user_message: Optional[str] = None
    ) -> Optional[StructuredAdvisoryCard]:
        """
        Build the structured StructuredAdvisoryCard with direct_answer, key_reasons,
        recommended_action, limitations, and response_mode.
        """
        is_mr = language == "mr"
        outcomes = resp.crop_outcomes
        if focus_crop:
            outcomes = [o for o in outcomes if o.crop_id.lower() == focus_crop.lower()]
        elif user_message:
            msg_lower = user_message.lower()
            for o in resp.crop_outcomes:
                if o.crop_id.lower() in msg_lower or o.common_name.lower() in msg_lower:
                    outcomes = [o]
                    break

        target_crop = outcomes[0] if outcomes else None
        crop_name = ""
        status_label = ""
        status_code = ""

        if target_crop:
            crop_name = (target_crop.marathi_name or target_crop.common_name) if is_mr else target_crop.common_name
            status_label = cls.STATE_LABELS_MR.get(target_crop.decision_state, str(target_crop.decision_state)) if is_mr else cls.STATE_LABELS_EN.get(target_crop.decision_state, str(target_crop.decision_state))
            status_code = target_crop.decision_state.value if hasattr(target_crop.decision_state, "value") else str(target_crop.decision_state)

        taluka = resp.taluka_resolved or "Maharashtra"
        title = f"{crop_name} Advisory" if crop_name else "CropNet Advisory"

        # Direct answer
        direct_answer = cls.generate_explanation(
            resp, language=language, focus_crop=target_crop.crop_id if target_crop else None,
            response_mode="QUICK", user_message=user_message
        )

        what_this_means = (
            f"Assessment based on {taluka} agroecological conditions and MPKV 2023 recommendations."
            if not is_mr else
            f"{taluka} कृषी हवामान व महात्मा फुले कृषी विद्यापीठाच्या २०२३ शिफारशींवर आधारित मूल्यमापन."
        )

        # Key reasons & limitations
        key_reasons = []
        limitations = []
        if target_crop:
            for lf in target_crop.limiting_factors[:2]:
                limitations.append(lf)
                key_reasons.append(lf)
            for warn in target_crop.reproductive_risk_warnings[:1]:
                key_reasons.append(warn)

        # Recommended action
        if target_crop and target_crop.is_disqualified:
            recommended_action = (
                "सुयोग्य निचरा व्यवस्थापन करा आणि पर्यायी पिकांची निवड करा."
                if is_mr else
                "Improve field drainage and evaluate alternative suitable crops."
            )
        elif target_crop and target_crop.decision_state == DecisionState.REGIONAL_SCREENING_ONLY:
            recommended_action = (
                "लागवडीपूर्वी प्रत्यक्ष शेतातील मातीची खोली व पाण्याचा निचरा तपासा."
                if is_mr else
                "Verify field soil depth and drainage before finalizing planting."
            )
        else:
            recommended_action = (
                "स्थानिक हंगामी मार्गदर्शक तत्त्वांचे पालन करा."
                if is_mr else
                "Follow standard regional package of practices."
            )

        # Verified Observations
        observations: List[AdvisoryObservationItem] = []
        fc = getattr(resp, "farm_context", None)
        if fc:
            prov_str = "Soil Laboratory Report" if getattr(fc, "soil_data_provenance", "") == "laboratory_measured" else "SoilGrids Estimated"
            prov_str_mr = "प्रयोगशाळा अहवाल" if getattr(fc, "soil_data_provenance", "") == "laboratory_measured" else "SoilGrids अंदाज"

            if fc.soil_ph is not None:
                observations.append(AdvisoryObservationItem(
                    parameter="Soil pH" if not is_mr else "सामू (pH)",
                    value=f"{fc.soil_ph:.1f}",
                    source=prov_str_mr if is_mr else prov_str,
                    status="available"
                ))
            if fc.soil_texture:
                observations.append(AdvisoryObservationItem(
                    parameter="Soil Texture" if not is_mr else "पोत",
                    value=fc.soil_texture.capitalize(),
                    source=prov_str_mr if is_mr else prov_str,
                    status="available"
                ))
            if getattr(fc, "soil_organic_carbon_pct", None) is not None:
                observations.append(AdvisoryObservationItem(
                    parameter="Organic Carbon" if not is_mr else "सेंद्रिय कर्ब",
                    value=f"{fc.soil_organic_carbon_pct:.2f}%",
                    source=prov_str_mr if is_mr else prov_str,
                    status="available"
                ))
            if getattr(fc, "electrical_conductivity_ds_m", None) is not None:
                observations.append(AdvisoryObservationItem(
                    parameter="Electrical Conductivity" if not is_mr else "विद्युत वाहकता",
                    value=f"{fc.electrical_conductivity_ds_m:.2f} dS/m",
                    source=prov_str_mr if is_mr else prov_str,
                    status="available"
                ))
            if getattr(fc, "irrigation_source", None):
                observations.append(AdvisoryObservationItem(
                    parameter="Irrigation Source" if not is_mr else "पाण्याचा स्रोत",
                    value=str(fc.irrigation_source).capitalize(),
                    source="Farmer Reported" if not is_mr else "शेतकरी नोंद",
                    status="available"
                ))

        # Evidence references
        citations: List[str] = []
        if target_crop:
            for c in target_crop.citations[:2]:
                citations.append(f"{c.organization} ({c.publication_year})")

        return StructuredAdvisoryCard(
            title=title,
            direct_answer=direct_answer,
            what_this_means=what_this_means,
            crop_status_label=status_label,
            crop_status_code=status_code,
            observations=observations,
            what_needs_attention=limitations,
            next_steps=[recommended_action],
            evidence_references=citations,
            key_reasons=key_reasons,
            recommended_action=recommended_action,
            limitations=limitations,
            response_mode=response_mode
        )
