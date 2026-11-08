"""
CropNet AI — Constrained LLM Agricultural Explanation & Dialogue Service.

Master service coordinating:
1. Retrieval of validated FarmEvaluationResponse from the deterministic engine.
2. Restricted prompt construction with anti-injection barriers.
3. Local Ollama Qwen3:8B inference.
4. Comprehensive numerical and agronomic guardrail validation.
5. Deterministic template fallback on any failure or violation.
6. Natural conversational dialogue and diagnostic answer re-evaluation.
"""
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from cropnet.services.api.app.schemas.agriculture_intelligence import (
    FarmEvaluationResponse,
    ExplainDecisionRequest,
    ConversationRequest,
    AgriculturalExplanationResponse,
    CitationMetadata,
    FollowUpQuestion
)
from cropnet.services.api.app.services.agriculture_intelligence.decision_engine import (
    DeterministicDecisionEngine,
    _DECISION_STORE
)
from cropnet.services.api.app.services.llm.ollama_client import OllamaClient
from cropnet.services.api.app.services.llm.prompt_builder import ExplanationPromptBuilder
from cropnet.services.api.app.services.llm.guardrail_validator import GuardrailValidator
from cropnet.services.api.app.services.llm.template_fallback import TemplateFallbackGenerator

logger = logging.getLogger(__name__)


class AgriculturalExplanationService:
    """
    Constrained explanation and dialogue service for CropNet AI.
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

    def explain_decision(
        self,
        req: ExplainDecisionRequest,
        db: Optional[Session] = None
    ) -> Optional[AgriculturalExplanationResponse]:
        """
        Generate a natural, farmer-friendly explanation of a validated decision.
        Uses local Qwen3:8B with strict guardrails; falls back to deterministic
        templates if unavailable, timed out, or failing guardrail verification.
        """
        # 1. Fetch validated decision from deterministic engine session store
        decision = self.decision_engine.get_decision(req.decision_id)
        if not decision:
            logger.warning(f"Decision '{req.decision_id}' not found in decision store.")
            return None

        lang = (req.language or decision.language or "en").lower()
        citations = self._extract_citations(decision)
        states_summary = self._extract_decision_summary(decision)
        follow_ups = decision.follow_up_questions
        card = TemplateFallbackGenerator.generate_structured_card(decision, language=lang, focus_crop=req.focus_crop)

        # 2. Check Ollama availability
        if not self.ollama.is_available() or not self.ollama.is_model_available():
            logger.info("Ollama or Qwen3:8B model unavailable; using deterministic template fallback.")
            fallback_text = TemplateFallbackGenerator.generate_explanation(
                decision, language=lang, focus_crop=req.focus_crop
            )
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
                structured_card=card
            )

        # 3. Construct restricted prompt
        sys_prompt = ExplanationPromptBuilder.build_system_prompt(language=lang)
        user_prompt = ExplanationPromptBuilder.build_user_prompt(
            decision, language=lang, focus_crop=req.focus_crop
        )
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # 4. Invoke local Ollama
        try:
            llm_res = self.ollama.chat_completion(messages=messages)
        except Exception as e:
            llm_res = {"success": False, "error": str(e), "content": None}

        if not llm_res.get("success") or not llm_res.get("content"):
            err = llm_res.get("error", "Unknown Ollama error")
            logger.warning(f"Ollama generation failed ({err}); executing deterministic fallback.")
            fallback_text = TemplateFallbackGenerator.generate_explanation(
                decision, language=lang, focus_crop=req.focus_crop
            )
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
                structured_card=card
            )

        raw_content = llm_res["content"]

        # 5. Numerical and Agronomic Guardrail Validation
        val_result = GuardrailValidator.validate(raw_content, decision, language=lang)
        if not val_result.is_valid:
            logger.warning(f"Guardrail rejection on generated explanation: {val_result.violations}")
            fallback_text = TemplateFallbackGenerator.generate_explanation(
                decision, language=lang, focus_crop=req.focus_crop
            )
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
                structured_card=card
            )

        # 6. Success: return validated LLM explanation
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
            structured_card=card
        )

    def handle_conversation(
        self,
        req: ConversationRequest,
        db: Optional[Session] = None
    ) -> Optional[AgriculturalExplanationResponse]:
        """
        Handle conversational dialogue or diagnostic answer submission.
        - If answers are submitted, re-evaluates through the deterministic engine first.
        - Natural conversational questions are explained strictly grounded in the decision.
        """
        # 1. Fetch current decision
        current_decision = self.decision_engine.get_decision(req.decision_id)
        if not current_decision:
            logger.warning(f"Decision '{req.decision_id}' not found for conversation.")
            return None

        # 2. If farmer submitted diagnostic answers, execute deterministic re-evaluation
        if req.submitted_answers:
            logger.info(f"Processing follow-up answers for decision {req.decision_id}: {req.submitted_answers}")
            updated_decision = self.decision_engine.process_followup_answers(
                decision_id=req.decision_id,
                answers=req.submitted_answers,
                db=db
            )
            if updated_decision:
                current_decision = updated_decision

        lang = (req.language or current_decision.language or "en").lower()
        citations = self._extract_citations(current_decision)
        states_summary = self._extract_decision_summary(current_decision)
        follow_ups = current_decision.follow_up_questions
        card = TemplateFallbackGenerator.generate_structured_card(current_decision, language=lang)

        # 3. If Ollama is offline, return template explanation
        if not self.ollama.is_available() or not self.ollama.is_model_available():
            fallback_text = TemplateFallbackGenerator.generate_explanation(
                current_decision, language=lang
            )
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
                structured_card=card
            )

        # 4. Construct conversational dialogue prompt
        sys_prompt = ExplanationPromptBuilder.build_system_prompt(language=lang)
        user_prompt = ExplanationPromptBuilder.build_user_prompt(
            current_decision, user_message=req.message, language=lang
        )

        messages: List[Dict[str, str]] = [{"role": "system", "content": sys_prompt}]

        # Append bounded recent conversation history (up to last 3 turns)
        if req.history:
            recent_turns = req.history[-6:]
            for h in recent_turns:
                role = "assistant" if h.role == "assistant" else "user"
                messages.append({"role": role, "content": h.content})

        messages.append({"role": "user", "content": user_prompt})

        # 5. Invoke Ollama
        try:
            llm_res = self.ollama.chat_completion(messages=messages)
        except Exception as e:
            llm_res = {"success": False, "error": str(e), "content": None}

        if not llm_res.get("success") or not llm_res.get("content"):
            err = llm_res.get("error", "Unknown Ollama error")
            fallback_text = TemplateFallbackGenerator.generate_explanation(
                current_decision, language=lang
            )
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
                structured_card=card
            )

        # 6. Guardrail validation
        raw_content = llm_res["content"]
        val_result = GuardrailValidator.validate(
            raw_content, current_decision, language=lang, user_message=req.message
        )
        if not val_result.is_valid:
            logger.warning(f"Guardrail rejection in conversation turn: {val_result.violations}")
            fallback_text = TemplateFallbackGenerator.generate_explanation(
                current_decision, language=lang
            )
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
                structured_card=card
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
            structured_card=card
        )
