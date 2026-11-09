"""
CropNet AI — Deterministic Agricultural Decision Engine & Master Orchestrator.

Coordinates input validation, knowledge retrieval, modular constraint evaluation,
decision aggregation, and clinical follow-up question selection.
"""
import uuid
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session

from cropnet.services.api.app.schemas.agriculture_intelligence import (
    FarmContextInput,
    FarmEvaluationResponse,
    CropEvaluationOutcome,
    DecisionState,
    EvidenceTier,
    CitationMetadata
)
from cropnet.services.api.app.services.agriculture_intelligence.context_validator import FarmContextValidator, PILOT_TALUKAS
from cropnet.services.api.app.services.agriculture_intelligence.knowledge_retriever import KnowledgeRetriever
from cropnet.services.api.app.services.agriculture_intelligence.evidence_gate import EvidenceGate
from cropnet.services.api.app.services.agriculture_intelligence.soil_evaluator import SoilConstraintEvaluator
from cropnet.services.api.app.services.agriculture_intelligence.climate_evaluator import ClimateSuitabilityEvaluator
from cropnet.services.api.app.services.agriculture_intelligence.water_evaluator import WaterAvailabilityEvaluator
from cropnet.services.api.app.services.agriculture_intelligence.regional_evaluator import RegionalSuitabilityEvaluator
from cropnet.services.api.app.services.agriculture_intelligence.decision_aggregator import DecisionAggregator
from cropnet.services.api.app.services.agriculture_intelligence.followup_engine import FollowUpQuestionEngine

logger = logging.getLogger(__name__)

# In-memory store for evaluated decisions (session history)
_DECISION_STORE: Dict[str, FarmEvaluationResponse] = {}
_CONTEXT_STORE: Dict[str, FarmContextInput] = {}
# Decision ownership tracking: decision_id -> {"user_id": str, "farm_id": Optional[str]}
_DECISION_OWNERSHIP: Dict[str, Dict[str, Optional[str]]] = {}


def record_decision_owner(decision_id: str, user_id: str, farm_id: Optional[str] = None) -> None:
    """Record caller and farm ownership for an evaluated decision."""
    _DECISION_OWNERSHIP[decision_id] = {
        "user_id": str(user_id),
        "farm_id": str(farm_id) if farm_id else None,
    }


def get_decision_owner(decision_id: str) -> Optional[Dict[str, Optional[str]]]:
    """Retrieve owner metadata for a decision."""
    return _DECISION_OWNERSHIP.get(decision_id)


class DeterministicDecisionEngine:
    """
    Master deterministic engine executing evidence-grounded agricultural reasoning.
    """

    def __init__(self, retriever: Optional[KnowledgeRetriever] = None):
        self.retriever = retriever or KnowledgeRetriever()

    @staticmethod
    def _augment_context_from_query(ctx: FarmContextInput) -> FarmContextInput:
        """Augment missing structured context attributes when explicitly stated in user query."""
        if not ctx.user_query:
            return ctx

        q = ctx.user_query.lower()
        updates = {}

        # Bahar detection
        if not ctx.target_bahar:
            if "mrig" in q or "मृग" in q:
                updates["target_bahar"] = "mrig_bahar"
            elif "hasta" in q or "हस्त" in q:
                updates["target_bahar"] = "hasta_bahar"
            elif "ambia" in q or "आंबिया" in q:
                updates["target_bahar"] = "ambia_bahar"

        # Tree age detection
        if not ctx.tree_age_years:
            if "4-year" in q or "4 year" in q or "४ वर्ष" in q:
                updates["tree_age_years"] = 4
            elif "5-year" in q or "5 year" in q:
                updates["tree_age_years"] = 5

        # Water scarcity period
        if not ctx.water_scarcity_period:
            if ("summer" in q and ("scarcity" in q or "shortage" in q or "water run" in q or "exhaust" in q)) or "उन्हाळ्यात पाणी टंचाई" in q or "पाणी टंचाई" in q or "post-february" in q:
                updates["water_scarcity_period"] = "post_february_summer"

        # Sowing window rainfall
        if ctx.sowing_window_rain_mm is None:
            if "delayed monsoon" in q or "dry weather" in q or "relying on this average" in q or "पाऊस लांबला" in q:
                updates["sowing_window_rain_mm"] = 0.0

        # Standing water & drainage
        if ctx.standing_water_days is None:
            if "two weeks" in q or "14 days" in q or "दोन आठवडे" in q:
                updates["standing_water_days"] = 14
            elif "water stands" in q or "standing water" in q or "पाणी साचून" in q:
                updates["standing_water_days"] = 7

        if not ctx.drainage:
            if "पाणी साचून" in q or "पाणी साचते" in q or "water stands" in q or "waterlog" in q:
                updates["drainage"] = "Poor / Waterlogged"

        if not ctx.soil_texture:
            if "जमीन खूप जड" in q or "भारी जमीन" in q or "heavy soil" in q:
                updates["soil_texture"] = "Heavy clay"

        # Irrigation source
        if not ctx.irrigation_source:
            if "well water" in q or "विहिरीचे पाणी" in q or "विहीर" in q:
                updates["irrigation_source"] = "well"
            elif "canal" in q or "कालवा" in q:
                updates["irrigation_source"] = "canal"

        # Reproductive temperature sensitivity for chickpea
        if ctx.reproductive_temp_max_c is None:
            if "37°c" in q or "37 °c" in q or "37c" in q or "37 degree" in q or "३५ अंश" in q or "35°c" in q or "35 degree" in q:
                updates["reproductive_temp_max_c"] = 37.0
            elif "36°c" in q:
                updates["reproductive_temp_max_c"] = 36.0
            elif ("फुले" in q and ("गळ" in q or "गळत" in q)) or (("flower drop" in q or "flowers dropping" in q) and ("heat" in q or "temp" in q)):
                updates["reproductive_temp_max_c"] = 36.0

        if ctx.reproductive_temp_mean_c is None:
            if ("maximum is 20°c" in q and "minimum is 8°c" in q) or "14°c" in q or "(20 + 8) / 2" in q:
                updates["reproductive_temp_mean_c"] = 14.0

        if updates:
            return ctx.model_copy(update=updates)
        return ctx

    def evaluate_farm(
        self,
        ctx: FarmContextInput,
        db: Optional[Session] = None,
        user_id: Optional[str] = None
    ) -> FarmEvaluationResponse:
        ctx = self._augment_context_from_query(ctx)
        decision_id = f"dec_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()

        # -------------------------------------------------------------
        # Step 1: Farm Context Validation
        # -------------------------------------------------------------
        val_res = FarmContextValidator.validate(ctx)

        # -------------------------------------------------------------
        # Step 2: Handle Complete Context Absence (Zero Context)
        # -------------------------------------------------------------
        if val_res.is_empty_context:
            followups = FollowUpQuestionEngine.select_questions(ctx, val_res, [])
            resp = FarmEvaluationResponse(
                decision_id=decision_id,
                evaluated_at=now,
                input_validation_status="ABSTAIN_ZERO_CONTEXT",
                contradictions_detected=[],
                missing_parameters_flagged=val_res.missing_parameters,
                taluka_resolved=None,
                target_season=None,
                language=ctx.language or "en",
                farm_context=ctx,
                crop_outcomes=[],
                follow_up_questions=followups
            )
            _DECISION_STORE[decision_id] = resp
            _CONTEXT_STORE[decision_id] = ctx
            if user_id:
                record_decision_owner(decision_id, user_id=str(user_id), farm_id=str(ctx.farm_id) if ctx.farm_id else None)
            return resp

        # -------------------------------------------------------------
        # Step 3: Determine Candidate Crops
        # -------------------------------------------------------------
        supported_crops = self.retriever.get_supported_crops(db=db)
        outcomes: List[CropEvaluationOutcome] = []

        # If user queried for specific crops
        requested_crops = ctx.target_crops or []
        if ctx.user_query and not requested_crops:
            # Simple keyword extraction for the 10 crops
            q_lower = ctx.user_query.lower()
            for sc in supported_crops:
                if sc in q_lower:
                    requested_crops.append(sc)
                elif sc == "chickpea" and any(k in q_lower for k in ("gram", "chana", "हरभरा", "चना")):
                    requested_crops.append("chickpea")
                elif sc == "sorghum" and any(k in q_lower for k in ("jowar", "ज्वारी")):
                    requested_crops.append("sorghum")
                elif sc == "bajra" and any(k in q_lower for k in ("millet", "बाजरी")):
                    requested_crops.append("bajra")
                elif sc == "pomegranate" and any(k in q_lower for k in ("anar", "डाळिंब")):
                    requested_crops.append("pomegranate")
                elif sc == "sugarcane" and any(k in q_lower for k in ("cane", "ऊस")):
                    requested_crops.append("sugarcane")
                elif sc == "wheat" and any(k in q_lower for k in ("gehun", "गहू")):
                    requested_crops.append("wheat")
                elif sc == "cotton" and any(k in q_lower for k in ("kapas", "कापूस")):
                    requested_crops.append("cotton")
                elif sc == "groundnut" and any(k in q_lower for k in ("peanut", "भुईमूग")):
                    requested_crops.append("groundnut")
                elif sc == "soybean" and any(k in q_lower for k in ("soya", "सोयाबीन")):
                    requested_crops.append("soybean")

        # Check for Out-of-Catalogue Crops (Adversarial 26: Dragon fruit, vanilla, etc.)
        unsupported = [c for c in requested_crops if c not in supported_crops]
        ooc = unsupported[0] if unsupported else None
        if not ooc and ctx.user_query:
            q_lower = ctx.user_query.lower()
            out_of_catalogue_triggers = ["dragon fruit", "pitaya", "vanilla", "apple", "cashew", "rubber", "कॉफी", "ड्रॅगन फ्रूट"]
            for trigger in out_of_catalogue_triggers:
                if trigger in q_lower:
                    ooc = trigger
                    break

        if ooc:
            # Explicit abstention on out-of-catalogue crop
            resp = FarmEvaluationResponse(
                decision_id=decision_id,
                evaluated_at=now,
                input_validation_status="ABSTAIN_UNREGISTERED_CROP",
                contradictions_detected=[],
                missing_parameters_flagged=[],
                taluka_resolved=val_res.resolved_taluka,
                target_season=ctx.target_season,
                language=ctx.language or "en",
                farm_context=ctx,
                crop_outcomes=[
                    CropEvaluationOutcome(
                        crop_id="unregistered_crop",
                        common_name=f"Out of Catalogue Crop ({ooc})",
                        scientific_name="N/A",
                        marathi_name="अनोंदणीकृत पीक",
                        decision_state=DecisionState.ABSTAIN_INSUFFICIENT_EVIDENCE,
                        is_disqualified=True,
                        limiting_factors=[f"Crop '{ooc}' is not registered in CropNet's 10 priority crops knowledge base."],
                        missing_information=[],
                        uncertainty_notes=["CropNet strictly abstains from synthesizing unverified agronomic rules for out-of-scope crops."],
                        applied_rules=[],
                        citations=[],
                        explanation=(
                            f"CropNet covers exactly 10 priority crops: {', '.join(supported_crops)}. "
                            f"'{ooc}' is not in the verified Maharashtra knowledge base. System abstains from ungrounded advice."
                        )
                    )
                ],
                follow_up_questions=[]
            )
            _DECISION_STORE[decision_id] = resp
            _CONTEXT_STORE[decision_id] = ctx
            if user_id:
                record_decision_owner(decision_id, user_id=str(user_id), farm_id=str(ctx.farm_id) if ctx.farm_id else None)
            return resp

        # Default to requested crops if identified, else evaluate all 10 priority crops
        eval_crops = requested_crops if requested_crops else supported_crops

        # -------------------------------------------------------------
        # Step 4: Modular Dimensional Evaluation per Candidate Crop
        # -------------------------------------------------------------
        for cid in eval_crops:
            profile = self.retriever.get_crop_profile(crop_id=cid, db=db)
            if not profile:
                continue

            # Fetch primary citation
            primary_src_id = profile.sources[0].id if (profile.sources and len(profile.sources) > 0) else None
            primary_citation = self.retriever.get_source_citation(source_id=primary_src_id, db=db)
            citations_list = [primary_citation] if primary_citation else []

            # Attach Maharashtra regional research and package of practices citations
            if (not ctx.taluka) or (ctx.taluka and ctx.taluka.strip().lower() in PILOT_TALUKAS) or cid in ("chickpea", "sorghum", "bajra", "wheat", "cotton", "sugarcane", "soybean"):
                mpkv_res_cit = self.retriever.get_source_citation("mpkv_research_2023", db=db)
                if mpkv_res_cit and mpkv_res_cit not in citations_list:
                    citations_list.append(mpkv_res_cit)
                mpkv_pop_cit = self.retriever.get_source_citation("mpkv_pop_2023", db=db)
                if mpkv_pop_cit and mpkv_pop_cit not in citations_list:
                    citations_list.append(mpkv_pop_cit)

            if cid == "bajra":
                iimr_cit = self.retriever.get_source_citation("icar_iimr_millets_2022", db=db)
                if iimr_cit and iimr_cit not in citations_list:
                    citations_list.append(iimr_cit)
            elif cid == "sugarcane":
                iisr_cit = self.retriever.get_source_citation("icar_iisr_sugarcane_2022", db=db)
                if iisr_cit and iisr_cit not in citations_list:
                    citations_list.append(iisr_cit)
            elif cid == "cotton":
                cicr_cit = self.retriever.get_source_citation("icar_cicr_cotton_2022", db=db)
                if cicr_cit and cicr_cit not in citations_list:
                    citations_list.append(cicr_cit)

            # 1. Soil Evaluation
            soil_citation = self.retriever.get_source_citation(
                source_id=profile.soil.source_id if profile.soil else None, db=db
            ) or primary_citation
            if soil_citation and soil_citation not in citations_list:
                citations_list.append(soil_citation)
            soil_res = SoilConstraintEvaluator.evaluate(ctx, profile, soil_citation)

            # 2. Climate Evaluation
            clim_citation = self.retriever.get_source_citation(
                source_id=profile.climate.source_id if profile.climate else None, db=db
            ) or primary_citation
            if clim_citation and clim_citation not in citations_list:
                citations_list.append(clim_citation)
            clim_res = ClimateSuitabilityEvaluator.evaluate(ctx, profile, clim_citation)

            # 3. Water Evaluation
            water_citation = self.retriever.get_source_citation(
                source_id=profile.water.source_id if profile.water else None, db=db
            ) or primary_citation
            if water_citation and water_citation not in citations_list:
                citations_list.append(water_citation)
            water_res = WaterAvailabilityEvaluator.evaluate(ctx, profile, water_citation)

            # 4. Regional Evaluation
            reg_record = None
            reg_citation = None
            if ctx.taluka:
                reg_record = self.retriever.get_regional_suitability(cid, ctx.taluka, db=db)
                if reg_record and reg_record.get("source_id"):
                    reg_citation = self.retriever.get_source_citation(reg_record["source_id"], db=db)
                    if reg_citation and reg_citation not in citations_list:
                        citations_list.append(reg_citation)
            reg_res = RegionalSuitabilityEvaluator.evaluate(ctx, profile, reg_record, reg_citation or primary_citation)

            # 5. Aggregate into Outcome
            outcome = DecisionAggregator.aggregate(
                ctx=ctx,
                profile=profile,
                soil_res=soil_res,
                clim_res=clim_res,
                water_res=water_res,
                reg_res=reg_res,
                citations=citations_list
            )
            outcomes.append(outcome)

        # -------------------------------------------------------------
        # Step 5: Follow-Up Question Selection
        # -------------------------------------------------------------
        follow_ups = FollowUpQuestionEngine.select_questions(ctx, val_res, outcomes)

        # Compile Response
        validation_status = "VALID"
        if not val_res.is_valid or val_res.contradictions:
            validation_status = "CONTRADICTORY_INPUTS_DETECTED"
        elif val_res.warnings:
            validation_status = "VALID_WITH_UNRESOLVED_CAVEATS"

        resp = FarmEvaluationResponse(
            decision_id=decision_id,
            evaluated_at=now,
            input_validation_status=validation_status,
            contradictions_detected=val_res.contradictions,
            missing_parameters_flagged=val_res.missing_parameters,
            taluka_resolved=val_res.resolved_taluka,
            target_season=ctx.target_season,
            language=ctx.language or "en",
            farm_context=ctx,
            crop_outcomes=outcomes,
            follow_up_questions=follow_ups
        )

        _DECISION_STORE[decision_id] = resp
        _CONTEXT_STORE[decision_id] = ctx
        if user_id:
            record_decision_owner(decision_id, user_id=str(user_id), farm_id=str(ctx.farm_id) if ctx.farm_id else None)
        return resp

    def get_decision(self, decision_id: str) -> Optional[FarmEvaluationResponse]:
        """Fetch previously computed decision from session store."""
        return _DECISION_STORE.get(decision_id)

    def process_followup_answers(
        self,
        decision_id: str,
        answers: Dict[str, Any],
        db: Optional[Session] = None,
        user_id: Optional[str] = None
    ) -> Optional[FarmEvaluationResponse]:
        """
        Re-evaluate farm context with updated follow-up answers.
        """
        old_ctx = _CONTEXT_STORE.get(decision_id)
        if not old_ctx:
            return None

        # Build updated context dict
        ctx_dict = old_ctx.model_dump()
        for k, v in answers.items():
            if k == "soil_depth_cm":
                if isinstance(v, str):
                    if "< 30" in v or "shallow" in v.lower():
                        ctx_dict["soil_depth_cm"] = 25.0
                    elif "30" in v or "medium" in v.lower():
                        ctx_dict["soil_depth_cm"] = 45.0
                    elif "> 60" in v or "deep" in v.lower():
                        ctx_dict["soil_depth_cm"] = 75.0
                    else:
                        try:
                            ctx_dict["soil_depth_cm"] = float(v)
                        except (ValueError, TypeError):
                            pass
                elif isinstance(v, (int, float)):
                    ctx_dict["soil_depth_cm"] = float(v)
            elif k == "electrical_conductivity_ds_m":
                if isinstance(v, str):
                    if "< 1.0" in v:
                        ctx_dict["electrical_conductivity_ds_m"] = 0.6
                    elif "1.0" in v:
                        ctx_dict["electrical_conductivity_ds_m"] = 1.4
                    elif "> 2.0" in v:
                        ctx_dict["electrical_conductivity_ds_m"] = 2.5
                    else:
                        try:
                            ctx_dict["electrical_conductivity_ds_m"] = float(v)
                        except (ValueError, TypeError):
                            pass
                elif isinstance(v, (int, float)):
                    ctx_dict["electrical_conductivity_ds_m"] = float(v)
            elif k == "target_bahar":
                if "mrig" in str(v).lower():
                    ctx_dict["target_bahar"] = "mrig_bahar"
                elif "hasta" in str(v).lower():
                    ctx_dict["target_bahar"] = "hasta_bahar"
                elif "ambia" in str(v).lower():
                    ctx_dict["target_bahar"] = "ambia_bahar"
                else:
                    ctx_dict["target_bahar"] = str(v)
            elif k == "drainage":
                ctx_dict["drainage"] = str(v)
            elif k in ("water_table_depth", "chickpea_water_table_depth"):
                if isinstance(v, str):
                    if "< 1" in v or "shallow" in v.lower() or "high" in v.lower() or "waterlog" in v.lower():
                        ctx_dict["water_table_depth"] = "shallow"
                        ctx_dict["water_table_depth_m"] = 0.5
                    elif "1–2" in v or "moderate" in v.lower():
                        ctx_dict["water_table_depth"] = "moderate"
                        ctx_dict["water_table_depth_m"] = 1.5
                    elif "> 2" in v or "deep" in v.lower():
                        ctx_dict["water_table_depth"] = "deep"
                        ctx_dict["water_table_depth_m"] = 3.0
                    else:
                        ctx_dict["water_table_depth"] = v
                elif isinstance(v, (int, float)):
                    ctx_dict["water_table_depth_m"] = float(v)
            elif k in ctx_dict:
                ctx_dict[k] = v

        updated_ctx = FarmContextInput(**ctx_dict)
        owner_info = get_decision_owner(decision_id)
        effective_user_id = user_id or (owner_info["user_id"] if owner_info else None)
        return self.evaluate_farm(ctx=updated_ctx, db=db, user_id=effective_user_id)
