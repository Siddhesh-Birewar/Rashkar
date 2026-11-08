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
from cropnet.services.api.app.services.llm.prompt_builder import ExplanationPromptBuilder
from cropnet.services.api.app.services.llm.guardrail_validator import GuardrailValidator
from cropnet.services.api.app.services.llm.template_fallback import TemplateFallbackGenerator
from cropnet.services.api.app.services.llm.farm_context_builder import FarmContextBuilder

logger = logging.getLogger(__name__)


class AgriculturalExplanationService:
    """
    Constrained explanation, contextual intelligence, and dialogue service for CropNet AI.
    """

    def __init__(
        self,
        ollama_client: Optional[OllamaClient] = None,
        decision_engine: Optional[DeterministicDecisionEngine] = None
    ):
        self.ollama = ollama_client or OllamaClient()
        self.decision_engine = decision_engine or DeterministicDecisionEngine()

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
                # Poor drainage / waterlogging
                if any(w in msg for w in [
                    "two days", "2 days", "stays", "waterlog", "standing water", "poor",
                    "साचून", "साचते", "निचरा होत नाही", "पाणथळ", "पाणी साचते", "पाणी राहते"
                ]):
                    detected["drainage"] = "poor"
                    detected["water_table_depth"] = "shallow"
                # Good / rapid drainage
                elif any(w in msg for w in [
                    "no standing", "drains well", "drains fast", "good", "quick",
                    "निचरा चांगला", "वाहून जाते", "पाणी साचत नाही"
                ]):
                    detected["drainage"] = "good"
                    detected["water_table_depth"] = "deep"
                # Moderate drainage
                elif any(w in msg for w in ["moderate", "medium", "24 hours", "मध्यम"]):
                    detected["drainage"] = "moderate"
                    detected["water_table_depth"] = "moderate"

            elif param in ("soil_depth_cm", "depth"):
                if any(w in msg for w in ["shallow", "< 30", "less than 30", "खोल नाही", "कमी खोल", "दगड"]):
                    detected["soil_depth_cm"] = 25.0
                elif any(w in msg for w in ["medium", "30 to 60", "30-60", "मध्यम"]):
                    detected["soil_depth_cm"] = 45.0
                elif any(w in msg for w in ["deep", "> 60", "more than 60", "खोल", "भारी"]):
                    detected["soil_depth_cm"] = 75.0

            elif param == "target_bahar":
                if any(w in msg for w in ["mrig", "मृग"]):
                    detected["target_bahar"] = "mrig_bahar"
                elif any(w in msg for w in ["hasta", "हस्त"]):
                    detected["target_bahar"] = "hasta_bahar"
                elif any(w in msg for w in ["ambia", "आंबिया"]):
                    detected["target_bahar"] = "ambia_bahar"

            elif param == "electrical_conductivity_ds_m":
                if any(w in msg for w in ["sweet", "good water", "low salt", "गोड"]):
                    detected["electrical_conductivity_ds_m"] = 0.6
                elif any(w in msg for w in ["saline", "salty", "high salt", "खारट", "क्षार"]):
                    detected["electrical_conductivity_ds_m"] = 2.5

        return detected

    def explain_decision(
        self,
        req: ExplainDecisionRequest,
        db: Optional[Session] = None
    ) -> Optional[AgriculturalExplanationResponse]:
        """
        Generate a structured, farmer-friendly explanation of a validated decision.
        Uses local Qwen3:8B with structured JSON generation and strict guardrails.
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
        fallback_card = TemplateFallbackGenerator.generate_structured_card(decision, language=lang, focus_crop=req.focus_crop)
        fallback_text = TemplateFallbackGenerator.generate_explanation(decision, language=lang, focus_crop=req.focus_crop)

        # 2. Build centralized grounded farm evidence
        farm_ctx = FarmContextBuilder.build_farm_context(
            farm_id=getattr(decision, "farm_id", None),
            db=db,
            focus_crop=req.focus_crop,
            decision=decision,
            language=lang
        )

        # 3. Check Ollama availability
        if not self.ollama.is_available() or not self.ollama.is_model_available():
            logger.info("Ollama or Qwen3:8B model unavailable; executing deterministic fallback.")
            return AgriculturalExplanationResponse(
                decision_id=decision.decision_id,
                language=lang,
                explanation_text=fallback_text,
                generation_source="deterministic_fallback",
                validation_passed=True,
                validation_warnings=["Ollama service or Qwen3:8B model is offline; executed deterministic fallback"],
                decision_state_summary=states_summary,
                authoritative_citations=citations,
                follow_up_questions=follow_ups,
                structured_card=fallback_card
            )

        # 4. Construct domain-aware structured prompt
        sys_prompt = ExplanationPromptBuilder.build_system_prompt(language=lang)
        user_prompt = ExplanationPromptBuilder.build_user_prompt(
            decision, language=lang, focus_crop=req.focus_crop, farm_context=farm_ctx
        )
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # 5. Invoke local Ollama in structured JSON mode
        try:
            llm_res = self.ollama.chat_completion(messages=messages, format="json")
        except Exception as e:
            llm_res = {"success": False, "error": str(e), "content": None}

        elapsed = time.time() - start_t

        if not llm_res.get("success") or not llm_res.get("content"):
            err = llm_res.get("error", "Unknown Ollama error")
            logger.warning(f"Ollama generation failed ({err}) after {elapsed:.2f}s; executing deterministic fallback.")
            return AgriculturalExplanationResponse(
                decision_id=decision.decision_id,
                language=lang,
                explanation_text=fallback_text,
                generation_source="deterministic_fallback",
                validation_passed=True,
                validation_warnings=[f"Ollama inference failed ({err}); executed deterministic fallback"],
                decision_state_summary=states_summary,
                authoritative_citations=citations,
                follow_up_questions=follow_ups,
                structured_card=fallback_card
            )

        raw_content = llm_res["content"].strip()

        # 6. Parse structured JSON from model, or accept verified plain prose
        parsed_json: Optional[Dict[str, Any]] = None
        try:
            parsed_json = json.loads(raw_content)
        except Exception:
            parsed_json = None

        if isinstance(parsed_json, dict) and "direct_answer" in parsed_json:
            direct_ans = str(parsed_json.get("direct_answer", "")).strip()
            what_means = str(parsed_json.get("what_this_means", "")).strip()

            what_att_raw = parsed_json.get("what_needs_attention", [])
            if isinstance(what_att_raw, list):
                what_att = [str(x).strip() for x in what_att_raw if x]
            elif isinstance(what_att_raw, str) and what_att_raw.strip():
                what_att = [what_att_raw.strip()]
            else:
                what_att = fallback_card.what_needs_attention

            next_s_raw = parsed_json.get("next_steps", [])
            if isinstance(next_s_raw, list):
                next_s = [str(x).strip() for x in next_s_raw if x]
            elif isinstance(next_s_raw, str) and next_s_raw.strip():
                next_s = [next_s_raw.strip()]
            else:
                next_s = fallback_card.next_steps

            combined_prose = f"{direct_ans}\n\n{what_means}\n\n" + "\n".join(what_att) + "\n\n" + "\n".join(next_s)
            val_result = GuardrailValidator.validate(
                combined_prose, decision, language=lang, farm_context=farm_ctx
            )

            if not val_result.is_valid:
                logger.warning(f"Guardrail rejection on generated explanation: {val_result.violations}")
                return AgriculturalExplanationResponse(
                    decision_id=decision.decision_id,
                    language=lang,
                    explanation_text=fallback_text,
                    generation_source="deterministic_fallback",
                    validation_passed=False,
                    validation_warnings=val_result.violations,
                    decision_state_summary=states_summary,
                    authoritative_citations=citations,
                    follow_up_questions=follow_ups,
                    structured_card=fallback_card
                )

            final_card = StructuredAdvisoryCard(
                title=str(parsed_json.get("title") or fallback_card.title),
                direct_answer=direct_ans or fallback_card.direct_answer,
                what_this_means=what_means or fallback_card.what_this_means,
                crop_status_label=fallback_card.crop_status_label,
                crop_status_code=fallback_card.crop_status_code,
                observations=fallback_card.observations,
                what_needs_attention=what_att or fallback_card.what_needs_attention,
                next_steps=next_s or fallback_card.next_steps,
                evidence_references=fallback_card.evidence_references
            )

            final_explanation = f"{direct_ans}\n\n{what_means}"

            return AgriculturalExplanationResponse(
                decision_id=decision.decision_id,
                language=lang,
                explanation_text=final_explanation,
                generation_source="llm_qwen3_8b",
                validation_passed=True,
                validation_warnings=[],
                decision_state_summary=states_summary,
                authoritative_citations=citations,
                follow_up_questions=follow_ups,
                structured_card=final_card
            )
        else:
            # Fallback to plain prose validation (e.g. from mocked test responses or unstructured LLM output)
            val_result = GuardrailValidator.validate(
                raw_content, decision, language=lang, farm_context=farm_ctx
            )
            if not val_result.is_valid:
                logger.warning(f"Guardrail rejection on generated prose: {val_result.violations}")
                return AgriculturalExplanationResponse(
                    decision_id=decision.decision_id,
                    language=lang,
                    explanation_text=fallback_text,
                    generation_source="deterministic_fallback",
                    validation_passed=False,
                    validation_warnings=val_result.violations,
                    decision_state_summary=states_summary,
                    authoritative_citations=citations,
                    follow_up_questions=follow_ups,
                    structured_card=fallback_card
                )

            return AgriculturalExplanationResponse(
                decision_id=decision.decision_id,
                language=lang,
                explanation_text=val_result.cleaned_text,
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
        db: Optional[Session] = None
    ) -> Optional[AgriculturalExplanationResponse]:
        """
        Handle conversational dialogue or diagnostic answer submission with multi-turn understanding.
        - Natural language answers to diagnostic questions are detected and re-evaluated deterministically.
        - Grounded farm evidence is assembled and injected into domain-aware prompts.
        - Ollama generates structured JSON validated by guardrails.
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
        fallback_card = TemplateFallbackGenerator.generate_structured_card(current_decision, language=lang)
        fallback_text = TemplateFallbackGenerator.generate_explanation(current_decision, language=lang)

        # 4. Build centralized grounded farm evidence
        farm_ctx = FarmContextBuilder.build_farm_context(
            farm_id=getattr(current_decision, "farm_id", None),
            db=db,
            query=req.message,
            decision=current_decision,
            language=lang
        )

        # 5. If Ollama is offline, return template explanation
        if not self.ollama.is_available() or not self.ollama.is_model_available():
            return AgriculturalExplanationResponse(
                decision_id=current_decision.decision_id,
                language=lang,
                explanation_text=fallback_text,
                generation_source="deterministic_fallback",
                validation_passed=True,
                validation_warnings=["Ollama unavailable for conversational dialogue; executed deterministic fallback"],
                decision_state_summary=states_summary,
                authoritative_citations=citations,
                follow_up_questions=follow_ups,
                structured_card=fallback_card
            )

        # 6. Construct conversational dialogue prompt
        sys_prompt = ExplanationPromptBuilder.build_system_prompt(language=lang)
        user_prompt = ExplanationPromptBuilder.build_user_prompt(
            current_decision, user_message=req.message, language=lang, farm_context=farm_ctx
        )

        messages: List[Dict[str, str]] = [{"role": "system", "content": sys_prompt}]

        # Append bounded recent conversation history (up to last 4 turns)
        if req.history:
            recent_turns = req.history[-4:]
            for h in recent_turns:
                role = "assistant" if h.role == "assistant" else "user"
                messages.append({"role": role, "content": h.content})

        messages.append({"role": "user", "content": user_prompt})

        # 7. Invoke Ollama in structured JSON mode
        try:
            llm_res = self.ollama.chat_completion(messages=messages, format="json")
        except Exception as e:
            llm_res = {"success": False, "error": str(e), "content": None}

        elapsed = time.time() - start_t

        if not llm_res.get("success") or not llm_res.get("content"):
            err = llm_res.get("error", "Unknown Ollama error")
            logger.warning(f"Ollama conversation failed ({err}) after {elapsed:.2f}s; executing deterministic fallback.")
            return AgriculturalExplanationResponse(
                decision_id=current_decision.decision_id,
                language=lang,
                explanation_text=fallback_text,
                generation_source="deterministic_fallback",
                validation_passed=True,
                validation_warnings=[f"Ollama conversation failed ({err}); executed deterministic fallback"],
                decision_state_summary=states_summary,
                authoritative_citations=citations,
                follow_up_questions=follow_ups,
                structured_card=fallback_card
            )

        raw_content = llm_res["content"].strip()

        # 8. Parse structured JSON or validate plain prose
        parsed_json: Optional[Dict[str, Any]] = None
        try:
            parsed_json = json.loads(raw_content)
        except Exception:
            parsed_json = None

        if isinstance(parsed_json, dict) and "direct_answer" in parsed_json:
            direct_ans = str(parsed_json.get("direct_answer", "")).strip()
            what_means = str(parsed_json.get("what_this_means", "")).strip()

            what_att_raw = parsed_json.get("what_needs_attention", [])
            if isinstance(what_att_raw, list):
                what_att = [str(x).strip() for x in what_att_raw if x]
            elif isinstance(what_att_raw, str) and what_att_raw.strip():
                what_att = [what_att_raw.strip()]
            else:
                what_att = fallback_card.what_needs_attention

            next_s_raw = parsed_json.get("next_steps", [])
            if isinstance(next_s_raw, list):
                next_s = [str(x).strip() for x in next_s_raw if x]
            elif isinstance(next_s_raw, str) and next_s_raw.strip():
                next_s = [next_s_raw.strip()]
            else:
                next_s = fallback_card.next_steps

            combined_prose = f"{direct_ans}\n\n{what_means}\n\n" + "\n".join(what_att) + "\n\n" + "\n".join(next_s)
            val_result = GuardrailValidator.validate(
                combined_prose, current_decision, language=lang, user_message=req.message, farm_context=farm_ctx
            )

            if not val_result.is_valid:
                logger.warning(f"Guardrail rejection in conversation turn: {val_result.violations}")
                return AgriculturalExplanationResponse(
                    decision_id=current_decision.decision_id,
                    language=lang,
                    explanation_text=fallback_text,
                    generation_source="deterministic_fallback",
                    validation_passed=False,
                    validation_warnings=val_result.violations,
                    decision_state_summary=states_summary,
                    authoritative_citations=citations,
                    follow_up_questions=follow_ups,
                    structured_card=fallback_card
                )

            final_card = StructuredAdvisoryCard(
                title=str(parsed_json.get("title") or fallback_card.title),
                direct_answer=direct_ans or fallback_card.direct_answer,
                what_this_means=what_means or fallback_card.what_this_means,
                crop_status_label=fallback_card.crop_status_label,
                crop_status_code=fallback_card.crop_status_code,
                observations=fallback_card.observations,
                what_needs_attention=what_att or fallback_card.what_needs_attention,
                next_steps=next_s or fallback_card.next_steps,
                evidence_references=fallback_card.evidence_references
            )

            final_explanation = f"{direct_ans}\n\n{what_means}"

            return AgriculturalExplanationResponse(
                decision_id=current_decision.decision_id,
                language=lang,
                explanation_text=final_explanation,
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
            val_result = GuardrailValidator.validate(
                raw_content, current_decision, language=lang, user_message=req.message, farm_context=farm_ctx
            )
            if not val_result.is_valid:
                logger.warning(f"Guardrail rejection in conversation turn: {val_result.violations}")
                return AgriculturalExplanationResponse(
                    decision_id=current_decision.decision_id,
                    language=lang,
                    explanation_text=fallback_text,
                    generation_source="deterministic_fallback",
                    validation_passed=False,
                    validation_warnings=val_result.violations,
                    decision_state_summary=states_summary,
                    authoritative_citations=citations,
                    follow_up_questions=follow_ups,
                    structured_card=fallback_card
                )

            return AgriculturalExplanationResponse(
                decision_id=current_decision.decision_id,
                language=lang,
                explanation_text=val_result.cleaned_text,
                generation_source="llm_qwen3_8b",
                validation_passed=True,
                validation_warnings=[],
                decision_state_summary=states_summary,
                authoritative_citations=citations,
                follow_up_questions=follow_ups,
                structured_card=fallback_card
            )
