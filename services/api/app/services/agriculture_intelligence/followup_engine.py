"""
CropNet AI — Deterministic Follow-Up Question Engine.

Selects targeted, non-leading diagnostic questions prioritized by decision
relevance to resolve missing parameters and eliminate decision uncertainty.
"""
from typing import List, Dict, Set, Optional, Any
from cropnet.services.api.app.schemas.agriculture_intelligence import (
    FarmContextInput,
    FollowUpQuestion,
    CropEvaluationOutcome,
    DecisionState
)
from cropnet.services.api.app.services.agriculture_intelligence.context_validator import ValidationResult


class FollowUpQuestionEngine:
    """
    Selects clinical follow-up questions prioritized by agronomic impact.
    """

    @staticmethod
    def select_questions(
        ctx: FarmContextInput,
        val_res: ValidationResult,
        outcomes: List[CropEvaluationOutcome]
    ) -> List[FollowUpQuestion]:
        questions: List[FollowUpQuestion] = []
        asked_params: Set[str] = set()

        # -------------------------------------------------------------
        # Priority 1: Complete Context Absence (Empty Context)
        # -------------------------------------------------------------
        if val_res.is_empty_context:
            questions.append(FollowUpQuestion(
                question_id="Q_LOCATION_TALUKA",
                target_parameter="taluka",
                priority=1,
                question_text_en="Which taluka or village is your farm located in?",
                question_text_mr="आपले शेत कोणत्या तालुक्यात किंवा गावात आहे?",
                question_type="choice",
                options=["Baramati", "Indapur", "Maval", "Mulshi", "Other"],
                agronomic_rationale="Regional agroecological screening requires geographic taluka location."
            ))
            questions.append(FollowUpQuestion(
                question_id="Q_TARGET_SEASON",
                target_parameter="target_season",
                priority=1,
                question_text_en="Which cropping season are you planning for?",
                question_text_mr="आपण कोणत्या हंगामासाठी नियोजन करत आहात?",
                question_type="choice",
                options=["Kharif (Monsoon)", "Rabi (Winter)", "Summer (Zaid)", "Annual (Horticulture)"],
                agronomic_rationale="Crop feasibility depends on seasonal temperature and monsoon windows."
            ))
            questions.append(FollowUpQuestion(
                question_id="Q_SOIL_TYPE_DRAINAGE",
                target_parameter="soil_texture",
                priority=1,
                question_text_en="What is your soil texture and drainage condition?",
                question_text_mr="आपल्या जमिनीचा पोत आणि पाण्याचा निचरा कसा आहे?",
                question_type="choice",
                options=["Light well-drained", "Medium black loam", "Deep heavy clay", "Shallow gravelly"],
                agronomic_rationale="Soil texture and aeration determine root suitability and wilt risks."
            ))
            return questions

        # -------------------------------------------------------------
        # Priority 1: Physical Contradiction Resolutions
        # -------------------------------------------------------------
        if val_res.contradictions:
            for c in val_res.contradictions:
                if "coarse sandy soil reported with" in c.lower() or "standing water" in c.lower():
                    if "subsoil_hardpan" not in asked_params:
                        questions.append(FollowUpQuestion(
                            question_id="Q_SUBSOIL_HARDPAN",
                            target_parameter="subsoil_hardpan",
                            priority=1,
                            question_text_en="Is there an impermeable hardpan, clay lens, or rock layer right beneath the sandy topsoil?",
                            question_text_mr="वालुकामय वरच्या थराखाली घट्ट मुरूम, चुनखडीचा थर किंवा खडकाचा थर आहे का?",
                            question_type="boolean",
                            options=["Yes", "No", "Uncertain"],
                            agronomic_rationale="Coarse sand cannot waterlog without an impermeable subsurface layer."
                        ))
                        asked_params.add("subsoil_hardpan")

        # -------------------------------------------------------------
        # Priority 1: Critical Missing Limiting Factors
        # -------------------------------------------------------------
        # Soil Depth
        if ctx.soil_depth_cm is None and "soil_depth_cm" not in asked_params:
            questions.append(FollowUpQuestion(
                question_id="Q_SOIL_DEPTH",
                target_parameter="soil_depth_cm",
                priority=1,
                question_text_en="What is the effective depth of your soil before hitting hard rock or murum?",
                question_text_mr="खडक किंवा कठीण मुरूम लागण्यापूर्वी जमिनीची प्रभावी खोली किती आहे?",
                question_type="choice",
                options=["Shallow (< 30 cm)", "Medium (30–60 cm)", "Deep (> 60 cm)"],
                agronomic_rationale="Soil depth determines root volume and disqualifies deep-rooted crops (Pomegranate, Cotton)."
            ))
            asked_params.add("soil_depth_cm")

        # Soil Drainage
        if ctx.drainage is None and "drainage" not in asked_params:
            questions.append(FollowUpQuestion(
                question_id="Q_DRAINAGE_CONDITION",
                target_parameter="drainage",
                priority=1,
                question_text_en="How would you describe your field's drainage after heavy rains?",
                question_text_mr="मुसळधार पावसानंतर शेतातील पाण्याचा निचरा कसा होतो?",
                question_type="choice",
                options=["Well-drained (water clears within 24h)", "Moderate (water clears in 1–2 days)", "Poor (water accumulates / waterlogged)"],
                agronomic_rationale="Aeration is critical for root health; chickpea and pomegranate die under standing water."
            ))
            asked_params.add("drainage")

        # Salinity (EC) in Canal Command or Unchecked Groundwater
        if "electrical_conductivity_ds_m" in val_res.missing_parameters and "electrical_conductivity_ds_m" not in asked_params:
            questions.append(FollowUpQuestion(
                question_id="Q_SOIL_SALINITY_EC",
                target_parameter="electrical_conductivity_ds_m",
                priority=1,
                question_text_en="What is the Electrical Conductivity (EC / क्षारता) of your soil from a recent soil test?",
                question_text_mr="नुकत्याच केलेल्या माती परीक्षणात जमिनीची विद्युत वाहकता (क्षारता / EC) किती आहे?",
                question_type="choice",
                options=["Normal (< 1.0 dS/m)", "Slightly saline (1.0–2.0 dS/m)", "Saline (> 2.0 dS/m)", "Not tested"],
                agronomic_rationale="Canal command areas risk seepage salinity; chickpea is highly sensitive to EC > 1.5 dS/m."
            ))
            asked_params.add("electrical_conductivity_ds_m")

        # Pomegranate Bahar Selection
        target_crops = [o.crop_id for o in outcomes]
        outcome_missing = {m for o in outcomes for m in o.missing_information}

        # Water Table Depth (Chickpea / Pomegranate Drainage Diagnostic)
        if "water_table_depth" in outcome_missing and "water_table_depth" not in asked_params:
            questions.append(FollowUpQuestion(
                question_id="Q_WATER_TABLE_DEPTH",
                target_parameter="water_table_depth",
                priority=1,
                question_text_en="What is the seasonal water table depth in your field, or does the field experience prolonged subsoil water stagnation?",
                question_text_mr="आपल्या शेतातील भूजल पातळी किती खोल आहे किंवा जमिनीत पाणी जास्त काळ साचून राहते का?",
                question_type="choice",
                options=["Deep (> 2 meters)", "Moderate (1–2 meters)", "High / shallow (< 1 meter)", "Waterlogging / saline seepage"],
                agronomic_rationale="ICRISAT (2010, p. 8) establishes that chickpea is not suitable for fields with a high water table or salinity."
            ))
            asked_params.add("water_table_depth")

        # Alternative Summer Irrigation (Sugarcane Seasonal Water Risk)
        if "alternative_summer_irrigation" in outcome_missing and "alternative_summer_irrigation" not in asked_params:
            questions.append(FollowUpQuestion(
                question_id="Q_SUGARCANE_ALTERNATIVE_IRRIGATION",
                target_parameter="alternative_summer_irrigation",
                priority=1,
                question_text_en="Do you have access to alternative summer irrigation (e.g. farm pond, canal turns, or tankers) during March–May tillering?",
                question_text_mr="मार्च ते मे दरम्यान उसाच्या फुटव्यांच्या काळात आपल्याकडे पर्यायी पाण्याची सोय (उदा. शेततळे, कालव्याचे आवर्तन किंवा टँकर) उपलब्ध आहे का?",
                question_type="choice",
                options=["Yes, farm pond available", "Yes, canal rotation turns available", "Yes, water tanker available", "No alternative water available"],
                agronomic_rationale="Sugarcane water requirement is critical during summer tillering; without supplemental water, severe yield loss occurs."
            ))
            asked_params.add("alternative_summer_irrigation")

        if "pomegranate" in target_crops and ctx.target_bahar is None and "target_bahar" not in asked_params:
            questions.append(FollowUpQuestion(
                question_id="Q_POMEGRANATE_BAHAR",
                target_parameter="target_bahar",
                priority=1,
                question_text_en="Which Bahar are you regulating for your pomegranate orchard?",
                question_text_mr="आपण डाळिंब बागेसाठी कोणता बहार धरणार आहात?",
                question_type="choice",
                options=["Mrig Bahar (June flowering)", "Hasta Bahar (Sept–Oct flowering)", "Ambia Bahar (Jan–Feb flowering)"],
                agronomic_rationale="Bahar choice dictates irrigation schedules, disease exposure, and summer water risk."
            ))
            asked_params.add("target_bahar")

        # -------------------------------------------------------------
        # Priority 2: Diagnostic & Soil Fertility Clarifications
        # -------------------------------------------------------------
        # Total N without Available N
        if ctx.total_nitrogen_pct is not None and ctx.available_nitrogen_kg_ha is None:
            if "available_nitrogen_kg_ha" not in asked_params:
                questions.append(FollowUpQuestion(
                    question_id="Q_AVAILABLE_NITROGEN_LAB",
                    target_parameter="available_nitrogen_kg_ha",
                    priority=2,
                    question_text_en="Do you have an Available Nitrogen value (in kg/ha or rating Low/Med/High) from a laboratory test?",
                    question_text_mr="आपल्याकडे माती परीक्षण प्रयोगशाळेतील उपलब्ध नत्र (kg/ha किंवा कमी/मध्यम/जास्त) अहवाल आहे का?",
                    question_type="choice",
                    options=["Low (< 280 kg/ha)", "Medium (280–560 kg/ha)", "High (> 560 kg/ha)", "Not available"],
                    agronomic_rationale="Total N is organically bound; Available N is required to calculate fertilizer dosages."
                ))
                asked_params.add("available_nitrogen_kg_ha")

        return sorted(questions, key=lambda q: q.priority)
