"""
CropNet AI — Explanation Guardrail & Numerical Validation Service.

Validates that LLM-generated explanations strictly adhere to the original
deterministic decision payload. Enforces:
1. Decision state consistency (no reversing suitability verdicts).
2. Numerical grounding (rejection of hallucinated numbers and dosages).
3. Fertilizer dosage protection (rejection of fabricated fertilizer amounts).
4. Crop scope protection (no recommending unregistered crops).
5. Automatic fallback trigger when violations occur.
"""
import re
import logging
from typing import List, Set, Dict, Any, Tuple, Optional
from cropnet.services.api.app.schemas.agriculture_intelligence import (
    FarmEvaluationResponse,
    DecisionState
)

logger = logging.getLogger(__name__)


class GuardrailValidationResult:
    """Outcome of the guardrail validation check."""
    def __init__(self, is_valid: bool, violations: List[str], cleaned_text: str):
        self.is_valid = is_valid
        self.violations = violations
        self.cleaned_text = cleaned_text


class GuardrailValidator:
    """
    Validates LLM-generated explanation text against the original FarmEvaluationResponse.
    """

    # Numbers naturally allowed in prose, ordinals, bullet points, or dates
    BENIGN_NUMBERS = {
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
        24, 48, 72, # Hours
        2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027 # Years
    }

    @classmethod
    def _extract_all_numbers_from_text(cls, text: str) -> List[float]:
        """Extract all integer and floating point numbers from a text string."""
        # Replace Marathi numerals with Arabic numerals first
        marathi_digits = str.maketrans("०१२३४५६७८९", "0123456789")
        normalized = text.translate(marathi_digits)

        # Regex for numbers including decimals, ranges (e.g. 6.5-7.0 -> 6.5, 7.0)
        found = re.findall(r"\b\d+(?:\.\d+)?\b", normalized)
        results = []
        for s in found:
            try:
                val = float(s)
                results.append(val)
            except ValueError:
                continue
        return results

    @classmethod
    def _collect_authorized_numbers(
        cls,
        resp: FarmEvaluationResponse,
        user_message: Optional[str] = None
    ) -> Set[float]:
        """
        Collect all valid numbers present in the decision payload and user message:
        outcomes, limiting factors, uncertainty notes, applied rules, and follow-ups.
        """
        text_corpus = []

        # Add taluka and status strings
        def add_item(item: Any):
            if item is None:
                return
            if isinstance(item, (list, tuple, set)):
                for sub in item:
                    add_item(sub)
            elif isinstance(item, dict):
                for k, v in item.items():
                    add_item(k)
                    add_item(v)
            else:
                text_corpus.append(str(item))

        add_item(resp.input_validation_status)
        add_item(resp.taluka_resolved)
        if getattr(resp, "farm_context", None):
            add_item(resp.farm_context.model_dump())
        if user_message:
            add_item(user_message)

        for o in resp.crop_outcomes:
            add_item(o.common_name)
            add_item(o.limiting_factors)
            add_item(o.uncertainty_notes)
            add_item(o.reproductive_risk_warnings)
            add_item(o.irrigation_guidance)
            add_item(o.pomegranate_daily_water)
            add_item(o.explanation)
            for r in o.applied_rules:
                add_item(r.rule_statement)
                add_item(r.supporting_statement)
                add_item(r.applicability_conditions)
                add_item(r.section_or_pages)

        for q in resp.follow_up_questions:
            add_item(q.question_text_en)
            add_item(q.question_text_mr)
            add_item(q.agronomic_rationale)
            add_item(q.options)

        combined = " ".join(text_corpus)
        extracted = cls._extract_all_numbers_from_text(combined)
        authorized: Set[float] = set(extracted)

        # Also add benign integers
        for b in cls.BENIGN_NUMBERS:
            authorized.add(float(b))

        return authorized

    @classmethod
    def validate(
        cls,
        generated_text: str,
        resp: FarmEvaluationResponse,
        language: str = "en",
        user_message: Optional[str] = None
    ) -> GuardrailValidationResult:
        """
        Validate generated explanation against original decision payload.
        Returns GuardrailValidationResult.
        """
        violations: List[str] = []
        cleaned_text = generated_text.strip()

        # 1. Strip fake bibliographies/references if Qwen attempted to generate them
        cleaned_text = re.sub(r"(?i)\n*(references|citations|संदर्भ|ग्रंथसूची):\s*\n.*", "", cleaned_text, flags=re.DOTALL).strip()
        # Clean raw Markdown heading tokens (###, ####) so text flows naturally
        cleaned_text = re.sub(r"^\s*#{1,6}\s*", "", cleaned_text, flags=re.MULTILINE).strip()

        # 2. Check for Leaked Python Dictionaries or JSON syntax
        dict_pattern = re.compile(r"\{['\"].*?['\"]\s*:\s*.*?\}", re.DOTALL)
        if dict_pattern.search(cleaned_text):
            violations.append("Raw Python Dictionary or JSON detected in explanation output.")

        # 3. Check for Leaked Internal Machine Enums
        for raw_enum in ["REGIONAL_SCREENING_ONLY", "CONDITIONALLY_SUITABLE_PENDING_DATA", "UNSUITABLE_VERIFIED_CONSTRAINT", "DECOUPLED_FRAMEWORKS"]:
            if raw_enum in cleaned_text:
                violations.append(f"Raw internal enum constant '{raw_enum}' leaked into explanation text.")

        # 4. Check Decision State & Suitability Integrity
        for o in resp.crop_outcomes:
            c_names = {o.crop_id.lower(), o.common_name.lower(), o.common_name.split("(")[0].strip().lower()}
            m_names = {o.marathi_name.lower()} if o.marathi_name else set()
            text_lower = cleaned_text.lower()

            if o.is_disqualified:
                # Disqualified crop must NOT be stated as suitable or recommended
                en_violation = any(
                    (f"{name} is suitable" in text_lower
                     or f"{name} is highly suitable" in text_lower
                     or f"{name} is recommended" in text_lower
                     or f"recommend {name}" in text_lower
                     or f"plant {name}" in text_lower)
                    for name in c_names
                )
                mr_violation = any(
                    (name in text_lower)
                    and ("लागवड करण्यास हरकत नाही" in text_lower or "उत्कृष्ट पीक आहे" in text_lower or "अत्यंत योग्य आहे" in text_lower)
                    for name in (c_names | m_names)
                )
                if en_violation or mr_violation:
                    violations.append(
                        f"Decision State Contradiction / Inversion: Crop '{o.common_name}' is disqualified in deterministic engine, but explanation claims it is suitable."
                    )

            elif o.decision_state == DecisionState.VERIFIED_SUITABLE:
                # Verified suitable crop must not be claimed as unsuitable/disqualified
                if any(
                    (f"{name} is not suitable" in text_lower or f"{name} is unsuitable" in text_lower)
                    for name in c_names
                ):
                    violations.append(
                        f"Decision State Contradiction / Inversion: Crop '{o.common_name}' is verified suitable, but explanation claims it is unsuitable."
                    )

        # 3. Check for Out-of-Catalogue Crop Recommendation
        if resp.input_validation_status == "ABSTAIN_UNREGISTERED_CROP":
            # Must contain clear abstention indication
            if language == "mr":
                if "नोंदणीकृत" not in cleaned_text and "अपात्र" not in cleaned_text and "माहिती उपलब्ध नाही" not in cleaned_text and "कव्हर" not in cleaned_text:
                    violations.append("Abstention Failure: Out-of-catalogue crop query did not clearly explain CropNet's abstention policy.")
            else:
                if "abstain" not in cleaned_text.lower() and "unregistered" not in cleaned_text.lower() and "only covers" not in cleaned_text.lower() and "not in cropnet" not in cleaned_text.lower():
                    violations.append("Abstention Failure: Out-of-catalogue crop query did not clearly explain CropNet's abstention policy.")

        # 4. Numerical Grounding Check
        authorized_numbers = cls._collect_authorized_numbers(resp, user_message=user_message)
        generated_numbers = cls._extract_all_numbers_from_text(cleaned_text)

        unauthorized_numbers = []
        for num in generated_numbers:
            # Check exact match or close float match (within 0.05 for minor rounding)
            matched = any(abs(num - auth) < 0.05 for auth in authorized_numbers)
            if not matched:
                unauthorized_numbers.append(num)

        if unauthorized_numbers:
            violations.append(
                f"Numerical Hallucination Detected: Text contains unauthorized numerical values not found in source decision payload: {unauthorized_numbers[:5]}"
            )

        # 5. Fabricated Fertilizer Dosage Check
        # Patterns like: "120 kg urea", "50 kg DAP", "100 किलो युरिया"
        fert_pattern = re.compile(r"\b\d+\s*(?:kg|किलो|पोती|bags)\s*(?:urea|dap|mop|npk|युरिया|डीएपी|पोटॅश)\b", re.IGNORECASE)
        fert_matches = fert_pattern.findall(cleaned_text)
        if fert_matches:
            violations.append(
                f"Fabricated Fertilizer Dosage Detected: Model generated unverified fertilizer dosage recommendations: {fert_matches}"
            )

        is_valid = len(violations) == 0
        if not is_valid:
            logger.warning(f"Guardrail validation FAILED with {len(violations)} violations: {violations}")

        return GuardrailValidationResult(
            is_valid=is_valid,
            violations=violations,
            cleaned_text=cleaned_text
        )
