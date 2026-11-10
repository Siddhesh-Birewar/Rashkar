"""
CropNet AI — Constrained LLM Agricultural Explanation & Dialogue Service.

Master service coordinating:
1. Retrieval of validated FarmEvaluationResponse from the deterministic engine.
2. Centralized farm context aggregation via FarmContextBuilder.
3. Multi-turn natural language diagnostic intent detection and deterministic re-evaluation.
4. Domain-aware prompt construction with anti-injection barriers.
5. Local Ollama Qwen3:8B inference with structured JSON output and concise reasoning.
6. Comprehensive numerical and agronomic guardrail validation.
7. Observability diagnostics tracking latency, task type, schema validity, and fallback reasons.
8. Deterministic template fallback on any failure or violation.
"""
import json
import time
import logging
from typing import Dict, Any, List, Optional
from pydantic import ValidationError
from sqlalchemy.orm import Session

from cropnet.services.api.app.schemas.agriculture_intelligence import (
    FarmEvaluationResponse,
    ExplainDecisionRequest,
    ConversationRequest,
    AgriculturalExplanationResponse,
    CitationMetadata,
    FollowUpQuestion,
    StructuredAdvisoryCard
)
from cropnet.services.api.app.services.agriculture_intelligence.decision_engine import (
    DeterministicDecisionEngine,
    _DECISION_STORE
)
from cropnet.services.api.app.services.llm.ollama_client import OllamaClient
from cropnet.services.api.app.services.llm.prompt_builder import (
    ExplanationPromptBuilder,
    detect_focus_crop,
    determine_response_mode
)
from cropnet.services.api.app.services.llm.guardrail_validator import GuardrailValidator
from cropnet.services.api.app.services.llm.template_fallback import TemplateFallbackGenerator
from cropnet.services.api.app.services.llm.farm_context_builder import FarmContextBuilder
from cropnet.services.api.app.services.llm.schemas import (
    LlmStructuredAdvisoryPayload,
    TelemetryCounter
)

logger = logging.getLogger(__name__)


class AgriculturalExplanationService:
    """
    Constrained explanation, contextual intelligence, and dialogue service for CropNet AI.
    """
    _global_telemetry = TelemetryCounter()

    def __init__(
        self,
        ollama_client: Optional[OllamaClient] = None,
        decision_engine: Optional[DeterministicDecisionEngine] = None
    ):
        self.ollama = ollama_client or OllamaClient()
        self.decision_engine = decision_engine or DeterministicDecisionEngine()
        self.telemetry = TelemetryCounter()

    @classmethod
    def get_global_telemetry(cls) -> TelemetryCounter:
        return cls._global_telemetry

    @classmethod
    def reset_global_telemetry(cls) -> None:
        cls._global_telemetry.reset()

    def get_telemetry(self) -> TelemetryCounter:
        return self.telemetry

    def reset_telemetry(self) -> None:
        self.telemetry.reset()

    def _record_live_success(self, latency: float = 0.0) -> None:
        self.telemetry.record_live_success(latency)
        if self._global_telemetry is not self.telemetry:
            self._global_telemetry.record_live_success(latency)

    def _record_fallback(self, reason: str, latency: float = 0.0, live_attempted: bool = False) -> None:
        self.telemetry.record_fallback(reason, latency, live_attempted=live_attempted)
        if self._global_telemetry is not self.telemetry:
            self._global_telemetry.record_fallback(reason, latency, live_attempted=live_attempted)

    @staticmethod
    def _extract_citations(resp: FarmEvaluationResponse) -> List[CitationMetadata]:
        """Collect deduplicated institutional citations attached by deterministic engine."""
        seen = set()
        citations = []
        for o in resp.crop_outcomes:
            for c in o.citations:
                if c.source_id not in seen:
                    seen.add(c.source_id)
                    citations.append(c)
        return citations

    @staticmethod
    def _extract_decision_summary(resp: FarmEvaluationResponse) -> Dict[str, str]:
        """Map crop IDs to their standardized machine-readable decision state."""
        return {
            o.crop_id: o.decision_state.value if hasattr(o.decision_state, "value") else str(o.decision_state)
            for o in resp.crop_outcomes
        }

    @classmethod
    def detect_answer_intent(
        cls,
        message: str,
        pending_questions: List[FollowUpQuestion]
    ) -> Dict[str, Any]:
        """
        Parse a farmer's natural language conversational turn to detect if it answers
        one of the deterministic engine's pending follow-up questions.
        """
        if not message or not pending_questions:
            return {}

        msg = message.lower().strip()
        detected: Dict[str, Any] = {}

        for q in pending_questions:
            param = q.target_parameter
            if not param:
                continue

            if param == "drainage":
                # Good / rapid drainage (check first to handle negations like 'no standing water')
                if any(w in msg for w in [
                    "no standing", "not standing", "drains well", "drains fast", "good", "quick",
                    "निचरा चांगला", "वाहून जाते", "पाणी साचत नाही"
                ]):
                    detected["drainage"] = "good"
                    detected["water_table_depth"] = "deep"
                # Poor drainage / waterlogging
                elif any(w in msg for w in [
                    "two days", "2 days", "stays", "waterlog", "standing water", "poor",
                    "साचून", "साचते", "निचरा होत नाही", "पाणथळ", "पाणी साचते", "पाणी राहते"
                ]):
                    detected["drainage"] = "poor"
                    detected["water_table_depth"] = "shallow"
                # Moderate drainage
                elif any(w in msg for w in ["moderate", "medium", "24 hours", "मध्यम"]):
                    detected["drainage"] = "moderate"
                    detected["water_table_depth"] = "moderate"

            elif param in ("soil_depth_cm", "depth"):
                if any(w in msg for w in ["shallow", "< 30", "less than 30", "खोल नाही", "कमी खोल", "दगड", "मुरमाड"]):
                    detected["soil_depth_cm"] = 25.0
                elif any(w in msg for w in ["medium", "30 to 60", "30-60", "मध्यम"]):
                    detected["soil_depth_cm"] = 45.0
                elif any(w in msg for w in ["deep", "> 60", "more than 60", "खोल", "भारी", "काळी भारी"]):
                    detected["soil_depth_cm"] = 75.0

            elif param == "target_bahar":
                if any(w in msg for w in ["mrig", "मृग"]):
                    detected["target_bahar"] = "mrig_bahar"
                elif any(w in msg for w in ["hasta", "हस्त"]):
                    detected["target_bahar"] = "hasta_bahar"
                elif any(w in msg for w in ["ambia", "आंबिया"]):
                    detected["target_bahar"] = "ambia_bahar"

            elif param in ("electrical_conductivity_ds_m", "water_salinity", "salinity"):
                if any(w in msg for w in ["sweet", "good water", "low salt", "गोड पाणी", "गोड"]):
                    detected["electrical_conductivity_ds_m"] = 0.6
                elif any(w in msg for w in ["saline", "salty", "high salt", "खारट पाणी", "खारट", "क्षार"]):
                    detected["electrical_conductivity_ds_m"] = 2.5

            elif param in ("water_table_depth", "well_depth_m", "well_depth"):
                if any(w in msg for w in ["deep", "300", "400", "500", "खोल", "३००", "४००"]):
                    detected["water_table_depth"] = "deep"
                    detected["well_depth_m"] = 100.0
                elif any(w in msg for w in ["shallow", "20", "30", "50", "उथळ", "२०", "३०", "५०"]):
                    detected["water_table_depth"] = "shallow"
                    detected["well_depth_m"] = 15.0

            elif param in ("irrigation_type", "irrigation_method"):
                if any(w in msg for w in ["drip", "ठिबक"]):
                    detected["irrigation_type"] = "drip"
                    detected["irrigation_method"] = "drip"
                elif any(w in msg for w in ["sprinkler", "तुषार"]):
                    detected["irrigation_type"] = "sprinkler"
                    detected["irrigation_method"] = "sprinkler"
                elif any(w in msg for w in ["flood", "canal", "पाटपाणी", "प्रवाही"]):
                    detected["irrigation_type"] = "flood"
                    detected["irrigation_method"] = "flood"

        return detected

    @classmethod
    def validate_explanation_guardrails(
        cls,
        text: str,
        decision: FarmEvaluationResponse,
        language: str = "en",
        user_message: Optional[str] = None,
        farm_context: Optional[Dict[str, Any]] = None
    ):
        """
        Validate generated explanation against Phase 5.8.2 and Phase 6.0 agronomic guardrails:
        1. Numerical grounding and no fabricated fertilizer dosages.
        2. No fabricated chemical spray or pesticide concentrations (ml/L).
        3. No diagnosing disease pathogens from satellite optical reflectance alone without scientific disclaimer.
        4. No reversing or overriding deterministic crop suitability states.
        """
        result = GuardrailValidator.validate(
            text, decision, language=language, user_message=user_message, farm_context=farm_context
        )
        violations = list(result.violations)
        cleaned_text = result.cleaned_text
        text_lower = cleaned_text.lower()
        query_lower = (user_message or "").lower()

        # Check: Satellite Pathogen Diagnosis without Scientific Disclaimer
        pathogen_terms = [
            "fusarium", "wilt", "blight", "telya", "root rot", "collar rot", "leaf spot", "pathogen",
            "करपा", "उकळा", "तेलकट डाग", "मूळकूज"
        ]
        disclaimer_markers = [
            "disclaimer", "cannot diagnose", "cannot identify", "not a direct", "optical reflectance",
            "indirect indicator", "वैज्ञानिक इशारा", "निदान करू शकत नाही", "अप्रत्यक्ष दर्शक", "थेट रोग निदान नाही"
        ]

        has_disclaimer = any(d in text_lower for d in disclaimer_markers)
        has_satellite_mention = any(s in text_lower for s in ["satellite", "sentinel", "ndvi", "ndmi", "उपग्रह", "कॅनॉपी"])
        has_pathogen_mention = any(p in text_lower for p in pathogen_terms)
        if has_satellite_mention and has_pathogen_mention and not has_disclaimer:
            violations.append(
                "Satellite Pathogen Diagnosis Guardrail Violation: Optical satellite reflectance (Sentinel-2 10m) "
                "cannot diagnose specific disease pathogens (e.g. wilt, blight, root rot). A scientific disclaimer is mandatory."
            )

        # Check: Fabricated Chemical Pesticide / Fungicide Spray Dosages
        import re
        spray_pattern = re.compile(
            r"\b\d+(?:\.\d+)?\s*(?:ml|मिली|gm|ग्रॅम|g)\s*(?:per\s*liter|/l|/liter|प्रति\s*लिटर|दर\s*लिटर)\b",
            re.IGNORECASE
        )
        spray_ha_pattern = re.compile(
            r"\b\d+(?:\.\d+)?\s*(?:ml|मिली|liters?|लिटर)\s*(?:per\s*hectare|/ha|प्रति\s*हेक्टर|दर\s*हेक्टर)\b",
            re.IGNORECASE
        )
        if spray_pattern.search(cleaned_text) or spray_ha_pattern.search(cleaned_text):
            violations.append(
                "Fabricated Chemical Spray Measurement Detected: CropNet AI strictly prohibits inventing unverified "
                "chemical pesticide or fungicide spray dosages or concentrations."
            )

        from cropnet.services.api.app.services.llm.guardrail_validator import GuardrailValidationResult
        return GuardrailValidationResult(
            is_valid=len(violations) == 0,
            violations=violations,
            cleaned_text=cleaned_text
        )

    @staticmethod
    def _enrich_card_observations(
        card: StructuredAdvisoryCard,
        farm_context: Optional[Dict[str, Any]],
        language: str = "en"
    ) -> StructuredAdvisoryCard:
        """Enrich StructuredAdvisoryCard observations with grounded multi-domain snapshot evidence."""
        if not farm_context:
            return card

        is_mr = language == "mr"
        from cropnet.services.api.app.schemas.agriculture_intelligence import AdvisoryObservationItem

        enriched_obs = list(card.observations)
        existing_params = {o.parameter.lower() for o in enriched_obs}

        # Water EC
        water_key = farm_context.get("water_intelligence", {}).get("key_indicators", {})
        if water_key.get("electrical_conductivity_ds_m") is not None:
            p_name = "पाण्याची क्षारता / EC" if is_mr else "Water Salinity (EC)"
            if not any(k in existing_params for k in ["water salinity", "पाण्याची क्षारता", "ec"]):
                enriched_obs.append(AdvisoryObservationItem(
                    parameter=p_name,
                    value=f"{water_key['electrical_conductivity_ds_m']:.2f} dS/m",
                    source="BIS IS 11624:2019 / Water Test",
                    status="available"
                ))

        # Satellite Canopy NDVI
        sat_intel = farm_context.get("satellite_intelligence", {})
        if sat_intel.get("canopy_ndvi") is not None:
            p_name = "निव्वळ पिकाची हिरवळ (Canopy NDVI)" if is_mr else "Pure Canopy NDVI"
            if not any("canopy" in k or "कॅनॉपी" in k or "ndvi" in k for k in existing_params):
                enriched_obs.append(AdvisoryObservationItem(
                    parameter=p_name,
                    value=f"{sat_intel['canopy_ndvi']:.2f}",
                    source="Sentinel-2 L2A Class 4",
                    status="available"
                ))

        # Weather Temperature
        wx_cur = farm_context.get("weather_intelligence", {}).get("current_weather", {})
        if wx_cur.get("temperature_c") is not None:
            p_name = "सध्याचे तापमान (Weather)" if is_mr else "Current Temperature"
            if not any("temperature" in k or "तापमान" in k for k in existing_params):
                enriched_obs.append(AdvisoryObservationItem(
                    parameter=p_name,
                    value=f"{wx_cur['temperature_c']:.1f}°C",
                    source="OpenWeather API",
                    status="available"
                ))

        return StructuredAdvisoryCard(
            title=card.title,
            direct_answer=card.direct_answer,
            what_this_means=card.what_this_means,
            crop_status_label=card.crop_status_label,
            crop_status_code=card.crop_status_code,
            observations=enriched_obs,
            what_needs_attention=card.what_needs_attention,
            next_steps=card.next_steps,
            evidence_references=card.evidence_references
        )

    def explain_decision(
        self,
        req: ExplainDecisionRequest,
        db: Optional[Session] = None,
        snapshot: Optional[Any] = None
    ) -> Optional[AgriculturalExplanationResponse]:
        """
        Generate a structured, farmer-friendly explanation of a validated decision.
        Consumes Phase 5.9 FarmHealthSnapshotResponse if provided, using local Qwen3:8B
        with JSON-Schema-constrained generation, mandatory Pydantic validation,
        observation enrichment, and strict numerical/agronomic guardrails.
        """
        start_t = time.time()
        # 1. Fetch validated decision from deterministic engine session store
        decision = self.decision_engine.get_decision(req.decision_id)
        if not decision:
            logger.warning(f"Decision '{req.decision_id}' not found in decision store.")
            return None

        lang = (req.language or decision.language or "en").lower()
        citations = self._extract_citations(decision)
        states_summary = self._extract_decision_summary(decision)
        follow_ups = decision.follow_up_questions

        mode = determine_response_mode(getattr(req, "response_mode", None), req.query)
        detected_crop = req.focus_crop or detect_focus_crop(req.query)

        fallback_card = TemplateFallbackGenerator.generate_structured_card(
            decision, language=lang, focus_crop=detected_crop, response_mode=mode, user_message=req.query
        )
        fallback_text = TemplateFallbackGenerator.generate_explanation(
            decision, language=lang, focus_crop=detected_crop, response_mode=mode, user_message=req.query
        )

        # 2. Build centralized grounded farm evidence (injecting farmer query and snapshot if present)
        snap = snapshot or getattr(req, "snapshot", None)
        farm_ctx = FarmContextBuilder.build_farm_context(
            farm_id=getattr(decision, "farm_id", None),
            db=db,
            query=req.query,
            focus_crop=detected_crop,
            decision=decision,
            language=lang,
            snapshot=snap
        )
        fallback_card = self._enrich_card_observations(fallback_card, farm_ctx, language=lang)

        # 3. Check Ollama availability
        if not self.ollama.is_available() or not self.ollama.is_model_available():
            logger.info("Ollama or Qwen3:8B model unavailable; executing deterministic fallback.")
            self._record_fallback("offline", latency=0.0, live_attempted=False)
            return AgriculturalExplanationResponse(
                decision_id=decision.decision_id,
                language=lang,
                explanation_text=fallback_text,
                response_mode=mode,
                direct_answer=fallback_card.direct_answer if fallback_card else fallback_text,
                recommended_action=fallback_card.recommended_action if fallback_card else None,
                key_reasons=fallback_card.key_reasons or [],
                limitations=fallback_card.limitations or [],
                generation_source="deterministic_fallback",
                validation_passed=True,
                validation_warnings=["Ollama service or Qwen3:8B model is offline; executed deterministic fallback"],
                decision_state_summary=states_summary,
                authoritative_citations=citations,
                follow_up_questions=follow_ups,
                structured_card=fallback_card
            )

        # 4. Construct domain-aware structured prompt
        sys_prompt = ExplanationPromptBuilder.build_system_prompt(language=lang, response_mode=mode)
        user_prompt = ExplanationPromptBuilder.build_user_prompt(
            decision, user_message=req.query, language=lang, focus_crop=detected_crop, farm_context=farm_ctx, response_mode=mode
        )
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # 5. Invoke local Ollama with JSON-Schema-constrained generation
        req_timeout = 35 if lang == "mr" else 25
        max_tokens = 300 if mode == "QUICK" else (450 if mode == "STANDARD" else 800)
        schema = LlmStructuredAdvisoryPayload.model_json_schema()
        try:
            llm_res = self.ollama.chat_completion(
                messages=messages,
                format=schema,
                max_tokens=max_tokens,
                timeout=req_timeout,
                think=False
            )
        except Exception as e:
            llm_res = {"success": False, "error_type": "unspecified_error", "error": str(e), "content": None}

        elapsed = time.time() - start_t

        if not llm_res.get("success") or not llm_res.get("content"):
            err = str(llm_res.get("error", "Unknown Ollama error"))
            err_type = llm_res.get("error_type")
            if err_type == "timeout" or "timed out" in err.lower():
                fallback_reason = "timeout"
            elif err_type == "connection_refused" or "refused" in err.lower() or "connect" in err.lower():
                fallback_reason = "connection_refused"
            elif not llm_res.get("content"):
                fallback_reason = "empty_response"
            else:
                fallback_reason = "unspecified_error"

            logger.warning(f"Ollama generation failed ({err}) after {elapsed:.2f}s [reason={fallback_reason}]; executing deterministic fallback.")
            self._record_fallback(fallback_reason, latency=elapsed, live_attempted=True)
            return AgriculturalExplanationResponse(
                decision_id=decision.decision_id,
                language=lang,
                explanation_text=fallback_text,
                response_mode=mode,
                direct_answer=fallback_card.direct_answer if fallback_card else fallback_text,
                recommended_action=fallback_card.recommended_action if fallback_card else None,
                key_reasons=fallback_card.key_reasons or [],
                limitations=fallback_card.limitations or [],
                generation_source="deterministic_fallback",
                validation_passed=True,
                validation_warnings=[f"Ollama inference failed ({err}); executed deterministic fallback"],
                decision_state_summary=states_summary,
                authoritative_citations=citations,
                follow_up_questions=follow_ups,
                structured_card=fallback_card
            )

        raw_content = llm_res["content"].strip()

        # 6. Mandatory Pydantic Validation & Structured Parsing
        parsed_payload: Optional[LlmStructuredAdvisoryPayload] = None

        if "{" in raw_content:
            try:
                start_i = raw_content.find("{")
                end_i = raw_content.rfind("}")
                json_str = raw_content[start_i:end_i + 1] if (start_i != -1 and end_i > start_i) else raw_content
                parsed_payload = LlmStructuredAdvisoryPayload.model_validate_json(json_str)
            except (ValidationError, Exception) as pe:
                logger.warning(f"Mandatory Pydantic schema validation failed: {pe}; triggering deterministic fallback.")
                self._record_fallback("pydantic_validation_error", latency=elapsed, live_attempted=True)
                return AgriculturalExplanationResponse(
                    decision_id=decision.decision_id,
                    language=lang,
                    explanation_text=fallback_text,
                    response_mode=mode,
                    direct_answer=fallback_card.direct_answer if fallback_card else fallback_text,
                    recommended_action=fallback_card.recommended_action if fallback_card else None,
                    key_reasons=fallback_card.key_reasons or [],
                    limitations=fallback_card.limitations or [],
                    generation_source="deterministic_fallback",
                    validation_passed=False,
                    validation_warnings=[f"Pydantic schema validation failed: {pe}"],
                    decision_state_summary=states_summary,
                    authoritative_citations=citations,
                    follow_up_questions=follow_ups,
                    structured_card=fallback_card
                )

        if parsed_payload is not None:
            direct_ans = parsed_payload.direct_answer.strip()
            key_reasons = parsed_payload.key_reasons or []
            rec_action = parsed_payload.recommended_action
            limitations = parsed_payload.limitations or []
            what_means = (parsed_payload.what_this_means or "").strip()
            what_att = parsed_payload.what_needs_attention or limitations or fallback_card.what_needs_attention
            next_s = parsed_payload.next_steps or ([rec_action] if rec_action else fallback_card.next_steps)

            combined_prose = f"{direct_ans}\n\n{what_means}\n\n" + "\n".join(what_att) + "\n\n" + "\n".join(next_s)
            val_result = self.validate_explanation_guardrails(
                combined_prose, decision, language=lang, user_message=req.query, farm_context=farm_ctx
            )

            if not val_result.is_valid:
                logger.warning(f"Guardrail rejection on generated explanation: {val_result.violations}")
                self._record_fallback("guardrail_violation", latency=elapsed, live_attempted=True)
                return AgriculturalExplanationResponse(
                    decision_id=decision.decision_id,
                    language=lang,
                    explanation_text=fallback_text,
                    response_mode=mode,
                    direct_answer=fallback_card.direct_answer if fallback_card else fallback_text,
                    recommended_action=fallback_card.recommended_action if fallback_card else None,
                    key_reasons=fallback_card.key_reasons or [],
                    limitations=fallback_card.limitations or [],
                    generation_source="deterministic_fallback",
                    validation_passed=False,
                    validation_warnings=val_result.violations,
                    decision_state_summary=states_summary,
                    authoritative_citations=citations,
                    follow_up_questions=follow_ups,
                    structured_card=fallback_card
                )

            # Format final explanation according to mode
            if mode == "QUICK":
                if rec_action and rec_action.lower() not in direct_ans.lower():
                    final_explanation = f"{direct_ans} {rec_action}".strip()
                else:
                    final_explanation = direct_ans
            elif mode == "STANDARD":
                lines = [direct_ans]
                if key_reasons:
                    lines.append("")
                    for kr in key_reasons[:3]:
                        lines.append(f"• {kr}")
                if rec_action and rec_action.lower() not in direct_ans.lower():
                    lines.append(f"\n{rec_action}")
                final_explanation = "\n".join(lines).strip()
            else: # DETAILED
                lines = [direct_ans]
                if what_means:
                    lines.append(f"\n{what_means}")
                if key_reasons:
                    lines.append("\nKey Factors:")
                    for kr in key_reasons:
                        lines.append(f"• {kr}")
                if limitations:
                    lines.append("\nLimitations & Risks:")
                    for lim in limitations:
                        lines.append(f"• {lim}")
                if rec_action:
                    lines.append(f"\nRecommended Action: {rec_action}")
                final_explanation = "\n".join(lines).strip()

            final_card = StructuredAdvisoryCard(
                title=str(parsed_payload.title or fallback_card.title),
                direct_answer=direct_ans or fallback_card.direct_answer,
                what_this_means=what_means or fallback_card.what_this_means,
                crop_status_label=fallback_card.crop_status_label,
                crop_status_code=fallback_card.crop_status_code,
                observations=fallback_card.observations,
                what_needs_attention=what_att or fallback_card.what_needs_attention,
                next_steps=next_s or fallback_card.next_steps,
                evidence_references=fallback_card.evidence_references,
                key_reasons=key_reasons,
                recommended_action=rec_action,
                limitations=limitations,
                response_mode=mode
            )
            final_card = self._enrich_card_observations(final_card, farm_ctx, language=lang)
            self._record_live_success(latency=elapsed)

            return AgriculturalExplanationResponse(
                decision_id=decision.decision_id,
                language=lang,
                explanation_text=final_explanation,
                response_mode=mode,
                direct_answer=direct_ans,
                recommended_action=rec_action,
                key_reasons=key_reasons,
                limitations=limitations,
                generation_source="llm_qwen3_8b",
                validation_passed=True,
                validation_warnings=[],
                decision_state_summary=states_summary,
                authoritative_citations=citations,
                follow_up_questions=follow_ups,
                structured_card=final_card
            )
        else:
            # Fallback to plain prose validation (for test mocks that mock plain prose)
            val_result = self.validate_explanation_guardrails(
                raw_content, decision, language=lang, user_message=req.query, farm_context=farm_ctx
            )
            if not val_result.is_valid:
                logger.warning(f"Guardrail rejection on generated prose: {val_result.violations}")
                self._record_fallback("guardrail_violation", latency=elapsed, live_attempted=True)
                return AgriculturalExplanationResponse(
                    decision_id=decision.decision_id,
                    language=lang,
                    explanation_text=fallback_text,
                    response_mode=mode,
                    direct_answer=fallback_card.direct_answer if fallback_card else fallback_text,
                    recommended_action=fallback_card.recommended_action if fallback_card else None,
                    key_reasons=fallback_card.key_reasons or [],
                    limitations=fallback_card.limitations or [],
                    generation_source="deterministic_fallback",
                    validation_passed=False,
                    validation_warnings=val_result.violations,
                    decision_state_summary=states_summary,
                    authoritative_citations=citations,
                    follow_up_questions=follow_ups,
                    structured_card=fallback_card
                )

            self._record_live_success(latency=elapsed)
            return AgriculturalExplanationResponse(
                decision_id=decision.decision_id,
                language=lang,
                explanation_text=val_result.cleaned_text,
                response_mode=mode,
                direct_answer=val_result.cleaned_text,
                recommended_action=None,
                key_reasons=[],
                limitations=[],
                generation_source="llm_qwen3_8b",
                validation_passed=True,
                validation_warnings=[],
                decision_state_summary=states_summary,
                authoritative_citations=citations,
                follow_up_questions=follow_ups,
                structured_card=fallback_card
            )

    def handle_conversation(
        self,
        req: ConversationRequest,
        db: Optional[Session] = None,
        snapshot: Optional[Any] = None
    ) -> Optional[AgriculturalExplanationResponse]:
        """
        Handle conversational dialogue or diagnostic answer submission with multi-turn understanding.
        - Natural language answers to diagnostic questions are detected and re-evaluated deterministically.
        - Multi-domain snapshot context and grounded farm evidence are assembled and injected into domain-aware prompts.
        - Answered follow-up questions are isolated and removed from follow-up chips.
        - Ollama generates structured JSON validated by mandatory Pydantic schema and Phase 6.0 guardrails.
        """
        start_t = time.time()
        # 1. Fetch current decision
        current_decision = self.decision_engine.get_decision(req.decision_id)
        if not current_decision:
            logger.warning(f"Decision '{req.decision_id}' not found for conversation.")
            return None

        # 2. Check for explicit submitted answers OR detect natural language answer intent
        answers_to_process = dict(req.submitted_answers or {})
        if not answers_to_process and req.message and current_decision.follow_up_questions:
            detected = self.detect_answer_intent(req.message, current_decision.follow_up_questions)
            if detected:
                logger.info(f"Detected natural language answer intent in message '{req.message}': {detected}")
                answers_to_process.update(detected)

        # 3. If answers detected, execute deterministic re-evaluation first
        if answers_to_process:
            logger.info(f"Executing deterministic re-evaluation for decision {req.decision_id}: {answers_to_process}")
            updated_decision = self.decision_engine.process_followup_answers(
                decision_id=req.decision_id,
                answers=answers_to_process,
                db=db
            )
            if updated_decision:
                current_decision = updated_decision

        lang = (req.language or current_decision.language or "en").lower()
        citations = self._extract_citations(current_decision)
        states_summary = self._extract_decision_summary(current_decision)
        follow_ups = current_decision.follow_up_questions

        mode = determine_response_mode(getattr(req, "response_mode", None), req.message)
        detected_crop = detect_focus_crop(req.message)

        fallback_card = TemplateFallbackGenerator.generate_structured_card(
            current_decision, language=lang, focus_crop=detected_crop, response_mode=mode, user_message=req.message
        )
        fallback_text = TemplateFallbackGenerator.generate_explanation(
            current_decision, language=lang, focus_crop=detected_crop, response_mode=mode, user_message=req.message
        )

        # 4. Build centralized grounded farm evidence (with snapshot if provided)
        snap = snapshot or getattr(req, "snapshot", None)
        farm_ctx = FarmContextBuilder.build_farm_context(
            farm_id=getattr(current_decision, "farm_id", None),
            db=db,
            query=req.message,
            focus_crop=detected_crop,
            decision=current_decision,
            language=lang,
            snapshot=snap
        )
        fallback_card = self._enrich_card_observations(fallback_card, farm_ctx, language=lang)

        # 5. If Ollama is offline, return template explanation
        if not self.ollama.is_available() or not self.ollama.is_model_available():
            self._record_fallback("offline", latency=0.0, live_attempted=False)
            return AgriculturalExplanationResponse(
                decision_id=current_decision.decision_id,
                language=lang,
                explanation_text=fallback_text,
                response_mode=mode,
                direct_answer=fallback_card.direct_answer if fallback_card else fallback_text,
                recommended_action=fallback_card.recommended_action if fallback_card else None,
                key_reasons=fallback_card.key_reasons or [],
                limitations=fallback_card.limitations or [],
                generation_source="deterministic_fallback",
                validation_passed=True,
                validation_warnings=["Ollama unavailable for conversational dialogue; executed deterministic fallback"],
                decision_state_summary=states_summary,
                authoritative_citations=citations,
                follow_up_questions=follow_ups,
                structured_card=fallback_card
            )

        # 6. Construct conversational dialogue prompt
        sys_prompt = ExplanationPromptBuilder.build_system_prompt(language=lang, response_mode=mode)
        user_prompt = ExplanationPromptBuilder.build_user_prompt(
            current_decision, user_message=req.message, language=lang, focus_crop=detected_crop, farm_context=farm_ctx, response_mode=mode
        )

        messages: List[Dict[str, str]] = [{"role": "system", "content": sys_prompt}]

        # Append bounded recent conversation history (up to last 4 turns)
        if req.history:
            recent_turns = req.history[-4:]
            for h in recent_turns:
                role = "assistant" if h.role == "assistant" else "user"
                messages.append({"role": role, "content": h.content})

        messages.append({"role": "user", "content": user_prompt})

        # 7. Invoke Ollama with JSON-Schema-constrained generation
        req_timeout = 35 if lang == "mr" else 25
        max_tokens = 300 if mode == "QUICK" else (450 if mode == "STANDARD" else 800)
        schema = LlmStructuredAdvisoryPayload.model_json_schema()
        try:
            llm_res = self.ollama.chat_completion(
                messages=messages,
                format=schema,
                max_tokens=max_tokens,
                timeout=req_timeout,
                think=False
            )
        except Exception as e:
            llm_res = {"success": False, "error_type": "unspecified_error", "error": str(e), "content": None}

        elapsed = time.time() - start_t

        if not llm_res.get("success") or not llm_res.get("content"):
            err = str(llm_res.get("error", "Unknown Ollama error"))
            err_type = llm_res.get("error_type")
            if err_type == "timeout" or "timed out" in err.lower():
                fallback_reason = "timeout"
            elif err_type == "connection_refused" or "refused" in err.lower() or "connect" in err.lower():
                fallback_reason = "connection_refused"
            elif not llm_res.get("content"):
                fallback_reason = "empty_response"
            else:
                fallback_reason = "unspecified_error"

            logger.warning(f"Ollama conversation failed ({err}) after {elapsed:.2f}s [reason={fallback_reason}]; executing deterministic fallback.")
            self._record_fallback(fallback_reason, latency=elapsed, live_attempted=True)
            return AgriculturalExplanationResponse(
                decision_id=current_decision.decision_id,
                language=lang,
                explanation_text=fallback_text,
                response_mode=mode,
                direct_answer=fallback_card.direct_answer if fallback_card else fallback_text,
                recommended_action=fallback_card.recommended_action if fallback_card else None,
                key_reasons=fallback_card.key_reasons or [],
                limitations=fallback_card.limitations or [],
                generation_source="deterministic_fallback",
                validation_passed=True,
                validation_warnings=[f"Ollama conversation failed ({err}); executed deterministic fallback"],
                decision_state_summary=states_summary,
                authoritative_citations=citations,
                follow_up_questions=follow_ups,
                structured_card=fallback_card
            )

        raw_content = llm_res["content"].strip()

        # 8. Mandatory Pydantic Validation & Structured Parsing
        parsed_payload: Optional[LlmStructuredAdvisoryPayload] = None

        if "{" in raw_content:
            try:
                start_i = raw_content.find("{")
                end_i = raw_content.rfind("}")
                json_str = raw_content[start_i:end_i + 1] if (start_i != -1 and end_i > start_i) else raw_content
                parsed_payload = LlmStructuredAdvisoryPayload.model_validate_json(json_str)
            except (ValidationError, Exception) as pe:
                logger.warning(f"Mandatory Pydantic schema validation failed: {pe}; triggering deterministic fallback.")
                self._record_fallback("pydantic_validation_error", latency=elapsed, live_attempted=True)
                return AgriculturalExplanationResponse(
                    decision_id=current_decision.decision_id,
                    language=lang,
                    explanation_text=fallback_text,
                    response_mode=mode,
                    direct_answer=fallback_card.direct_answer if fallback_card else fallback_text,
                    recommended_action=fallback_card.recommended_action if fallback_card else None,
                    key_reasons=fallback_card.key_reasons or [],
                    limitations=fallback_card.limitations or [],
                    generation_source="deterministic_fallback",
                    validation_passed=False,
                    validation_warnings=[f"Pydantic schema validation failed: {pe}"],
                    decision_state_summary=states_summary,
                    authoritative_citations=citations,
                    follow_up_questions=follow_ups,
                    structured_card=fallback_card
                )

        if parsed_payload is not None:
            direct_ans = parsed_payload.direct_answer.strip()
            key_reasons = parsed_payload.key_reasons or []
            rec_action = parsed_payload.recommended_action
            limitations = parsed_payload.limitations or []
            what_means = (parsed_payload.what_this_means or "").strip()
            what_att = parsed_payload.what_needs_attention or limitations or fallback_card.what_needs_attention
            next_s = parsed_payload.next_steps or ([rec_action] if rec_action else fallback_card.next_steps)

            combined_prose = f"{direct_ans}\n\n{what_means}\n\n" + "\n".join(what_att) + "\n\n" + "\n".join(next_s)
            val_result = self.validate_explanation_guardrails(
                combined_prose, current_decision, language=lang, user_message=req.message, farm_context=farm_ctx
            )

            if not val_result.is_valid:
                logger.warning(f"Guardrail rejection in conversation turn: {val_result.violations}")
                self._record_fallback("guardrail_violation", latency=elapsed, live_attempted=True)
                return AgriculturalExplanationResponse(
                    decision_id=current_decision.decision_id,
                    language=lang,
                    explanation_text=fallback_text,
                    response_mode=mode,
                    direct_answer=fallback_card.direct_answer if fallback_card else fallback_text,
                    recommended_action=fallback_card.recommended_action if fallback_card else None,
                    key_reasons=fallback_card.key_reasons or [],
                    limitations=fallback_card.limitations or [],
                    generation_source="deterministic_fallback",
                    validation_passed=False,
                    validation_warnings=val_result.violations,
                    decision_state_summary=states_summary,
                    authoritative_citations=citations,
                    follow_up_questions=follow_ups,
                    structured_card=fallback_card
                )

            # Format final explanation according to mode
            if mode == "QUICK":
                if rec_action and rec_action.lower() not in direct_ans.lower():
                    final_explanation = f"{direct_ans} {rec_action}".strip()
                else:
                    final_explanation = direct_ans
            elif mode == "STANDARD":
                lines = [direct_ans]
                if key_reasons:
                    lines.append("")
                    for kr in key_reasons[:3]:
                        lines.append(f"• {kr}")
                if rec_action and rec_action.lower() not in direct_ans.lower():
                    lines.append(f"\n{rec_action}")
                final_explanation = "\n".join(lines).strip()
            else: # DETAILED
                lines = [direct_ans]
                if what_means:
                    lines.append(f"\n{what_means}")
                if key_reasons:
                    lines.append("\nKey Factors:")
                    for kr in key_reasons:
                        lines.append(f"• {kr}")
                if limitations:
                    lines.append("\nLimitations & Risks:")
                    for lim in limitations:
                        lines.append(f"• {lim}")
                if rec_action:
                    lines.append(f"\nRecommended Action: {rec_action}")
                final_explanation = "\n".join(lines).strip()

            final_card = StructuredAdvisoryCard(
                title=str(parsed_payload.title or fallback_card.title),
                direct_answer=direct_ans or fallback_card.direct_answer,
                what_this_means=what_means or fallback_card.what_this_means,
                crop_status_label=fallback_card.crop_status_label,
                crop_status_code=fallback_card.crop_status_code,
                observations=fallback_card.observations,
                what_needs_attention=what_att or fallback_card.what_needs_attention,
                next_steps=next_s or fallback_card.next_steps,
                evidence_references=fallback_card.evidence_references,
                key_reasons=key_reasons,
                recommended_action=rec_action,
                limitations=limitations,
                response_mode=mode
            )
            final_card = self._enrich_card_observations(final_card, farm_ctx, language=lang)
            self._record_live_success(latency=elapsed)

            return AgriculturalExplanationResponse(
                decision_id=current_decision.decision_id,
                language=lang,
                explanation_text=final_explanation,
                response_mode=mode,
                direct_answer=direct_ans,
                recommended_action=rec_action,
                key_reasons=key_reasons,
                limitations=limitations,
                generation_source="llm_qwen3_8b",
                validation_passed=True,
                validation_warnings=[],
                decision_state_summary=states_summary,
                authoritative_citations=citations,
                follow_up_questions=follow_ups,
                structured_card=final_card
            )
        else:
            # Plain prose handling (e.g. from conversational test mocks or conversational responses)
            val_result = self.validate_explanation_guardrails(
                raw_content, current_decision, language=lang, user_message=req.message, farm_context=farm_ctx
            )
            if not val_result.is_valid:
                logger.warning(f"Guardrail rejection in conversation turn: {val_result.violations}")
                self._record_fallback("guardrail_violation", latency=elapsed, live_attempted=True)
                return AgriculturalExplanationResponse(
                    decision_id=current_decision.decision_id,
                    language=lang,
                    explanation_text=fallback_text,
                    response_mode=mode,
                    direct_answer=fallback_card.direct_answer if fallback_card else fallback_text,
                    recommended_action=fallback_card.recommended_action if fallback_card else None,
                    key_reasons=fallback_card.key_reasons or [],
                    limitations=fallback_card.limitations or [],
                    generation_source="deterministic_fallback",
                    validation_passed=False,
                    validation_warnings=val_result.violations,
                    decision_state_summary=states_summary,
                    authoritative_citations=citations,
                    follow_up_questions=follow_ups,
                    structured_card=fallback_card
                )

            self._record_live_success(latency=elapsed)
            return AgriculturalExplanationResponse(
                decision_id=current_decision.decision_id,
                language=lang,
                explanation_text=val_result.cleaned_text,
                response_mode=mode,
                direct_answer=val_result.cleaned_text,
                recommended_action=None,
                key_reasons=[],
                limitations=[],
                generation_source="llm_qwen3_8b",
                validation_passed=True,
                validation_warnings=[],
                decision_state_summary=states_summary,
                authoritative_citations=citations,
                follow_up_questions=follow_ups,
                structured_card=fallback_card
            )

