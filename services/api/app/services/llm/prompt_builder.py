"""
CropNet AI — Constrained Domain-Aware LLM Prompt Builder.

Constructs strict, restricted system and user prompts for local Qwen3:8B.
Enforces the New Default Response Policy:
1. Answer the farmer's exact question first in 1–2 sentences.
2. Default to approximately 30–60 words in QUICK mode.
3. Use 2–4 short bullet points in 'key_reasons' only when necessary.
4. Give one practical next action in 'recommended_action' when relevant.
5. Avoid unnecessary introductions, conclusions, and generic boilerplate.
6. Do not repeat UI data or dump entire farm context.
7. Avoid unsolicited background explanations.
8. Support three response modes: QUICK (default), STANDARD, and DETAILED.
9. Support simple, friendly Marathi and natural English.
10. Strict anti-hallucination and deterministic suitability guardrails.
"""
import json
import logging
from typing import Dict, Any, List, Optional
from cropnet.services.api.app.schemas.agriculture_intelligence import (
    FarmEvaluationResponse,
    CropEvaluationOutcome,
    DecisionState
)
from cropnet.services.api.app.services.llm.template_fallback import TemplateFallbackGenerator
from cropnet.services.api.app.services.llm.farm_context_builder import FarmContextBuilder

logger = logging.getLogger(__name__)


def detect_focus_crop(query: Optional[str]) -> Optional[str]:
    """Identify if the farmer's question focuses on a specific priority crop."""
    if not query:
        return None
    lower = query.lower()
    crop_keywords = {
        "chickpea": ["chickpea", "gram", "chana", "हरभरा", "चना"],
        "sugarcane": ["sugarcane", "cane", "ऊस"],
        "soybean": ["soybean", "soya", "सोयाबीन"],
        "tomato": ["tomato", "टोमॅटो"],
        "pomegranate": ["pomegranate", "anar", "डाळिंब"],
        "wheat": ["wheat", "गहू"],
        "cotton": ["cotton", "कापूस"],
        "sorghum": ["sorghum", "jowar", "ज्वारी"],
        "bajra": ["bajra", "pearl millet", "बाजरी"],
        "groundnut": ["groundnut", "peanut", "भुईमूग"],
        "maize": ["maize", "corn", "मका"],
    }
    for crop_id, keywords in crop_keywords.items():
        if any(kw in lower for kw in keywords):
            return crop_id
    return None


def determine_response_mode(explicit_mode: Optional[str], query: Optional[str]) -> str:
    """
    Determine the response brevity mode:
    - QUICK: default, ~30–60 words, direct answer, 1 practical action.
    - STANDARD: ~80–120 words, explain relevant reasons and precautions.
    - DETAILED: comprehensive explanation used ONLY when explicitly requested.
    """
    if explicit_mode and explicit_mode.upper() in ("QUICK", "STANDARD", "DETAILED"):
        return explicit_mode.upper()
    if not query:
        return "QUICK"
    lower = query.lower().strip()
    detailed_phrases = [
        "explain in detail", "detailed explanation", "tell me more in detail",
        "give detailed", "full details", "in-depth", "elaborate", "comprehensive",
        "deep dive", "step by step", "explain thoroughly", "tell me everything",
        "सविस्तर सांगा", "सविस्तर माहिती", "विस्ताराने सांगा", "सविस्तर", "खोलवर माहिती",
        "संपूर्ण माहिती", "तपशीलवार सांगा", "तपशीलात सांगा", "विस्तृत सांगा", "विस्ताराने स्पष्ट करा"
    ]
    if any(p in lower for p in detailed_phrases):
        return "DETAILED"

    standard_phrases = [
        "compare", "comparison", "all crops", "why and how", "breakdown", "reasons",
        "तुलना करा", "सर्व पिकांची", "कारणे सांगा", "कसे आणि का", "सगळी पिके"
    ]
    if any(p in lower for p in standard_phrases):
        return "STANDARD"

    return "QUICK"


class ExplanationPromptBuilder:
    """
    Builder for concise, domain-aware agricultural explanation prompts.
    """

    SYSTEM_PROMPT_EN = """You are CropNet AI's Integrated Agricultural Advisory & Explanation Assistant, serving farmers in Maharashtra, India.
Your SOLE purpose is to provide short, direct, specific, and farmer-friendly answers grounded exclusively in verified multi-domain farm evidence and deterministic agricultural decisions.

CRITICAL OPERATIONAL RULES & BREVITY POLICY:
1. ANSWER THE FARMER'S EXACT QUESTION FIRST: The very first sentence must directly answer what was asked.
2. KEEP SIMPLE ANSWERS TO 1–2 SENTENCES: Default to approximately 30–60 words total in QUICK mode.
3. CONCISE BULLET POINTS: Use 2–4 short bullets in 'key_reasons' ONLY when strictly necessary.
4. ONE PRACTICAL NEXT ACTION: Provide at most one practical next step in 'recommended_action' when relevant.
5. NO UNNECESSARY INTRODUCTIONS OR CONCLUSIONS: Never output greetings, boilerplate like "CropNet Agricultural Advisory...", or closing fluff. Start directly with the answer.
6. DO NOT REPEAT DISPLAYED UI DATA: Do not recite information already shown on screen.
7. DO NOT REPEAT THE ENTIRE FARM CONTEXT: Only reference specific parameters relevant to the question.
8. AVOID GENERIC ADVICE & UNSOLICITED EXPLANATIONS: Do not lecture on general biology or give unasked-for background.
9. ASK ONLY ONE CLARIFICATION: Ask at most one clarification question only when vital data is missing.
10. EXPAND ONLY WHEN EXPLICITLY REQUESTED: Switch to DETAILED mode only when the farmer explicitly asks for detail (e.g. "explain in detail").

AGRONOMIC INTEGRITY & ANTI-HALLUCINATION SAFEGUARDS:
1. TRUTH IN CONTEXT: Only state facts present in <<<VALIDATED_DECISION_PAYLOAD>>> and <<<FARM_EVIDENCE>>>.
2. NO INVENTED SUITABILITY: Never determine or alter crop suitability. The deterministic engine is authoritative.
3. NO INVENTED NUMBERS OR DOSAGES: Never fabricate thresholds, pH, EC, water table, rainfall numbers, or chemical dosages.
4. SATELLITE INTEGRITY: Sentinel-2 NDVI/NDMI reflect surface optical reflectance (10m GSD). They are indirect canopy vigor indicators, NOT direct disease pathogen or yield diagnoses.
5. OUTPUT FORMAT: Output STRICTLY valid JSON with these keys:
   {
     "title": "Short title (2-5 words)",
     "direct_answer": "Direct 1-2 sentence answer (~20-50 words)",
     "key_reasons": ["Short reason 1", "Short reason 2"],
     "recommended_action": "One practical next action if relevant",
     "limitations": ["Verified agronomic constraint if applicable"],
     "response_mode": "QUICK"
   }
   Do NOT output Markdown headings (###) or text outside JSON."""

    SYSTEM_PROMPT_MR = """तुम्ही CropNet AI चे शेती समुपदेशक व एकात्मिक कृषी सहाय्यक आहात आणि महाराष्ट्रातील शेतकऱ्यांना मार्गदर्शन करत आहात.
तुमचा एकमेव उद्देश <<<VALIDATED_DECISION_PAYLOAD>>> आणि <<<FARM_EVIDENCE>>> मधील प्रमाणित माहितीच्या आधारे अत्यंत संक्षिप्त, थेट, स्पष्ट आणि शेतकरी-स्नेही मराठीत उत्तरे देणे हा आहे.

संक्षिप्तता व थेट उत्तराचे नियम (New Default Response Policy):
१. थेट पहिल्या वाक्यात उत्तर: शेतकऱ्याच्या मूळ प्रश्नाचे उत्तर पहिल्याच १-२ वाक्यांत द्या.
२. लहान व सुटसुटीत उत्तर: उत्तर साधे, सोपे आणि साधारण ३० ते ६० शब्दांत असावे.
३. मुद्देसूद कारणे: गरज असल्यास जास्तीत जास्त २ ते ३ लहान मुद्दे द्या (key_reasons).
४. एकच कृती सल्ला: शक्य असल्यास एक उपयुक्त, व्यावहारिक कृती सल्ला द्या (recommended_action).
५. प्रस्तावना व समारोप टाळा: 'क्रॉपनेट कृषी सल्ला...', 'नमस्कार...', किंवा निरुपयोगी औपचारिक वाक्ये वापरू नका. थेट उत्तराने सुरुवात करा.
६. आधीच दिसणारी माहिती पुन्हा सांगू नका: स्क्रीनवर आधीच दिसणारी माहिती किंवा संपूर्ण शेताचा पाढा पुन्हा वाचू नका.
७. न मागितलेली तांत्रिक माहिती टाळा: विचारलेल्या विषयाव्यतिरिक्त इतर सामान्य ज्ञान किंवा अवांतर माहिती देऊ नका.
८. फक्त गरज असल्यास एकच प्रश्न विचारा: माहिती अपुरी असेल तर जास्तीत जास्त एकच स्पष्टीकरणात्मक प्रश्न विचारा.
९. सविस्तर विचारल्यासच विस्तार करा: जेव्हा शेतकरी स्वतः 'सविस्तर सांगा' किंवा 'विस्ताराने सांगा' असे विचारतो, तेव्हाच सविस्तर (DETAILED) माहिती द्या.

उत्तर पद्धती (Response Modes):
- QUICK (मूळ / Default): थेट १-२ वाक्यांत उत्तर (६० शब्दांपेक्षा कमी) आणि १ कृती सल्ला.
- STANDARD (८०-१२० शब्द): आवश्यक कारणे आणि दक्षता.
- DETAILED: शेतकर्‍याने सविस्तर विचारले तरच सविस्तर स्पष्टीकरण.

कृषी सुरक्षा मानके:
१. दिलेल्या अधिकृत माहितीतूनच बोला; पिकाची पात्रता किंवा आकडेवारीत स्वतः बदल करू नका.
२. रासायनिक खतांची मात्रे किंवा फवारणीचे प्रमाण मनाने सांगू नका. मातीचा सामू (pH), सेंद्रिय कर्ब (SOC), किंवा पाण्याचा निचरा (Drainage) चे आकडे व निष्कर्ष अधिकृत माहितीशिवाय बदलू नका.
३. सेन्टिनेल-२ उपग्रह माहितीचा संदर्भ देताना उपग्रह थेट रोगाचे निदान करू शकत नाही हा वैज्ञानिक इशारा लक्षात ठेवा.
४. मराठी भाषा अत्यंत सोपी, व्यावहारिक व शेतकरी-स्नेही ठेवा. कठीण किंवा बोजड संस्कृत शब्द टाळा.
५. विचार न करता थेट शुद्ध JSON द्या:
   {
     "title": "लहान शीर्षक",
     "direct_answer": "१-२ वाक्यांत थेट सोपे उत्तर (~२०-५० शब्द)",
     "key_reasons": ["मुद्देसूद कारण १", "मुद्देसूद कारण २"],
     "recommended_action": "एक उपयुक्त कृती सल्ला",
     "limitations": ["महत्त्वाची मर्यादा किंवा धोका"],
     "response_mode": "QUICK"
   }"""

    @classmethod
    def build_system_prompt(cls, language: str = "en", response_mode: str = "QUICK") -> str:
        """Return the strict system instruction prompt tailored to language and mode."""
        base = cls.SYSTEM_PROMPT_MR if language == "mr" else cls.SYSTEM_PROMPT_EN
        mode_note = (
            f"\nCURRENT REQUEST MODE: {response_mode.upper()}."
            if response_mode else "\nCURRENT REQUEST MODE: QUICK."
        )
        return base + mode_note

    @classmethod
    def _build_domain_guidance(cls, domain: str, language: str, response_mode: str = "QUICK") -> str:
        """Generate concise, tailored domain-specific instructions for the prompt."""
        is_mr = language == "mr"
        is_quick = response_mode == "QUICK"

        if domain == "weather_inquiry":
            if is_mr:
                return (
                    "डोमेन सूचना (हवामान व फवारणी):\n"
                    "- हवामान किंवा फवारणीच्या प्रश्नावर थेट १-२ वाक्यांत अनुकूलता सांगा (उदा. वाऱ्याचा वेग जास्त असल्यास फवारणी टाळा).\n"
                    "- ३०-५० शब्दांत उत्तर द्या आणि १ व्यावहारिक सल्ला द्या."
                )
            return (
                "DOMAIN GUIDANCE (Weather & Spraying Inquiry):\n"
                "- Answer spraying suitability directly in 1-2 sentences based on wind/rain (e.g. if wind is high, recommend delaying).\n"
                "- Keep response under 50 words with one practical action."
            )

        elif domain == "satellite_inquiry":
            if is_mr:
                return (
                    "डोमेन सूचना (उपग्रह व NDVI/NDMI):\n"
                    "- NDVI किंवा NDMI चा अर्थ सोप्या १-२ वाक्यांत सांगा (उदा. NDVI पिकाच्या हिरवळीचे प्रमाण दर्शवतो).\n"
                    "- उपग्रह रोगाचे थेट निदान करू शकत नाही हा नियम लक्षात ठेवा. उत्तर ३०-५० शब्दांत ठेवा."
                )
            return (
                "DOMAIN GUIDANCE (Satellite & NDVI/NDMI Inquiry):\n"
                "- Explain NDVI or NDMI in 1-2 simple sentences (e.g. indicates vegetation greenness and canopy vigor).\n"
                "- State what it indicates without lecturing. Keep response under 50 words."
            )

        elif domain == "soil_inquiry":
            if is_mr:
                return (
                    "डोमेन सूचना (माती व निचरा):\n"
                    "- विचारलेल्या मातीच्या घटकावर (pH, निचरा, खोली) थेट १-२ वाक्यांत उत्तर द्या.\n"
                    "- मर्यादा असल्यास स्पष्ट सांगा आणि १ कृती सल्ला द्या."
                )
            return (
                "DOMAIN GUIDANCE (Soil & Drainage Inquiry):\n"
                "- Answer the specific soil or drainage question directly in 1-2 sentences.\n"
                "- If a limitation exists (e.g. poor drainage in Vertisols), state it directly with 1 corrective action."
            )

        elif domain == "crop_assessment":
            if is_mr:
                return (
                    "डोमेन सूचना (पीक पात्रता):\n"
                    "- विचारलेल्या पिकाची पात्रता पहिल्या वाक्यात सांगा (अनुकूल / मर्यादित / अयोग्य).\n"
                    "- १ कृती सल्ला द्या. इतर पिकांचा पाढा वाचू नका."
                )
            return (
                "DOMAIN GUIDANCE (Crop Suitability Inquiry):\n"
                "- State the crop's suitability status directly in the first sentence.\n"
                "- Give one practical action or test needed. Do not list other unasked crops."
            )

        else:
            if is_mr:
                return "डोमेन सूचना: शेतकऱ्याच्या प्रश्नाला थेट, व्यावहारिक आणि अत्यंत संक्षिप्त (३०-६० शब्द) उत्तर द्या."
            return "DOMAIN GUIDANCE: Provide a direct, practical, concise answer under 60 words."

    @classmethod
    def _extract_decision_summary(
        cls,
        resp: FarmEvaluationResponse,
        focus_crop: Optional[str] = None,
        max_crops: int = 1
    ) -> Dict[str, Any]:
        """Extract a clean, concise JSON subset of the decision payload for the LLM."""
        is_mr = resp.language == "mr"
        outcomes = []
        target_outcomes = resp.crop_outcomes

        if focus_crop:
            filtered = [o for o in target_outcomes if o.crop_id.lower() == focus_crop.lower()]
            if filtered:
                target_outcomes = filtered
        elif max_crops and len(target_outcomes) > max_crops:
            # If no focus crop, keep at most top 1-2 crops to avoid prompt bloat
            target_outcomes = target_outcomes[:max_crops]

        for o in target_outcomes:
            state_label = (
                TemplateFallbackGenerator.STATE_LABELS_MR.get(o.decision_state, str(o.decision_state))
                if is_mr else
                TemplateFallbackGenerator.STATE_LABELS_EN.get(o.decision_state, str(o.decision_state))
            )
            outcomes.append({
                "crop_id": o.crop_id,
                "common_name": o.common_name,
                "marathi_name": o.marathi_name,
                "decision_state": o.decision_state.value if hasattr(o.decision_state, "value") else str(o.decision_state),
                "farmer_status_label": state_label,
                "limiting_factors": o.limiting_factors[:2] if o.limiting_factors else [],
                "reproductive_risk_warnings": o.reproductive_risk_warnings[:1] if o.reproductive_risk_warnings else [],
            })

        summary = {
            "decision_id": resp.decision_id,
            "taluka": resp.taluka_resolved,
            "status": resp.input_validation_status,
            "crops": outcomes
        }
        return summary

    @classmethod
    def build_user_prompt(
        cls,
        resp: FarmEvaluationResponse,
        user_message: Optional[str] = None,
        language: str = "en",
        focus_crop: Optional[str] = None,
        farm_context: Optional[Dict[str, Any]] = None,
        response_mode: str = "QUICK"
    ) -> str:
        """
        Construct concise, domain-aware user prompt containing strictly necessary payload evidence.
        """
        detected_crop = focus_crop or detect_focus_crop(user_message)
        summary = cls._extract_decision_summary(resp, focus_crop=detected_crop, max_crops=2 if not detected_crop else 1)
        payload_json = json.dumps(summary, indent=2, ensure_ascii=False)

        domain = FarmContextBuilder.classify_query_domain(user_message)
        domain_guidance = cls._build_domain_guidance(domain, language=language, response_mode=response_mode)

        lines = [
            "<<<VALIDATED_DECISION_PAYLOAD>>>",
            payload_json,
            "<<</VALIDATED_DECISION_PAYLOAD>>>",
            ""
        ]

        # Inject grounded farm evidence if relevant
        if farm_context:
            # Filter evidence to relevant domains to prevent token bloat
            compact_evidence = {}
            if domain in ("soil_inquiry", "crop_assessment", "cross_domain_inquiry"):
                if "soil" in farm_context:
                    compact_evidence["soil"] = farm_context["soil"]
            if domain in ("weather_inquiry", "cross_domain_inquiry"):
                if "weather" in farm_context:
                    compact_evidence["weather"] = farm_context["weather"]
            if domain in ("satellite_inquiry", "cross_domain_inquiry"):
                if "satellite" in farm_context:
                    compact_evidence["satellite"] = farm_context["satellite"]
            if domain in ("water_inquiry", "cross_domain_inquiry"):
                if "water" in farm_context:
                    compact_evidence["water"] = farm_context["water"]

            if not compact_evidence:
                compact_evidence = farm_context

            evidence_json = json.dumps(compact_evidence, indent=2, ensure_ascii=False)
            lines.extend([
                "<<<FARM_EVIDENCE>>>",
                evidence_json,
                "<<</FARM_EVIDENCE>>>",
                ""
            ])

        lines.extend([
            domain_guidance,
            ""
        ])

        # Mode-specific instruction
        mode_instruction_en = {
            "QUICK": "MODE: QUICK. Target 30–60 words total. Answer directly in 1–2 sentences in 'direct_answer'. Include at most 1 practical action in 'recommended_action'. Leave 'key_reasons' empty unless essential (max 2 short bullets). No introductory greetings or background lectures.",
            "STANDARD": "MODE: STANDARD. Target 80–120 words total. Direct answer in 1–2 sentences, 2–3 concise bullet reasons in 'key_reasons', and 1 practical action in 'recommended_action'.",
            "DETAILED": "MODE: DETAILED. Provide comprehensive explanation across direct_answer, what_this_means, key_reasons, limitations, and recommended_action as requested by the farmer."
        }.get(response_mode, "MODE: QUICK. Target 30–60 words total. Direct 1–2 sentence answer.")

        mode_instruction_mr = {
            "QUICK": "पद्धत: QUICK (थेट उत्तर, ३० ते ६० शब्द). 'direct_answer' मध्ये थेट १-२ वाक्यांत उत्तर द्या. 'recommended_action' मध्ये १ कृती सल्ला द्या. प्रस्तावना किंवा अवांतर माहिती टाळा.",
            "STANDARD": "पद्धत: STANDARD (८०-१२० शब्द). 'direct_answer' मध्ये थेट उत्तर, 'key_reasons' मध्ये २-३ लहान कारणे आणि 'recommended_action' मध्ये १ कृती सल्ला द्या.",
            "DETAILED": "पद्धत: DETAILED. शेतकर्‍याने सविस्तर विचारल्याप्रमाणे सविस्तर विश्लेषण द्या."
        }.get(response_mode, "पद्धत: QUICK (३० ते ६० शब्द). थेट १-२ वाक्यांत उत्तर द्या.")

        if user_message:
            lines.extend([
                "The farmer asked:",
                "<<<UNTRUSTED_FARMER_QUERY>>>",
                user_message.strip(),
                "<<</UNTRUSTED_FARMER_QUERY>>>",
                "",
                mode_instruction_mr if language == "mr" else mode_instruction_en,
                "Never contradict the decision states or invent unverified agronomic claims.",
                "Output strictly valid JSON with keys: direct_answer, key_reasons, recommended_action, limitations, response_mode.",
                "Answer immediately without internal thinking."
            ])
        else:
            lines.extend([
                mode_instruction_mr if language == "mr" else mode_instruction_en,
                "Never contradict the decision states or invent unverified agronomic claims.",
                "Output strictly valid JSON with keys: direct_answer, key_reasons, recommended_action, limitations, response_mode.",
                "Answer immediately without internal thinking."
            ])

        return "\n".join(lines)
