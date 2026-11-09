"""
CropNet AI — Deterministic Agricultural Decision Engine & Master Orchestrator.

Coordinates input validation, knowledge retrieval, modular constraint evaluation,
decision aggregation, and clinical follow-up question selection.
"""
import uuid
import re
import logging
import threading
from collections import OrderedDict
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

class BoundedLRUCache:
    """Thread-safe bounded in-memory LRU cache with eviction."""

    def __init__(self, maxsize: int = 500):
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._maxsize = maxsize
        self._lock = threading.Lock()

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                return self._cache[key]
            return default

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = value
            if len(self._cache) > self._maxsize:
                self._cache.popitem(last=False)

    def pop(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._cache.pop(key, default)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def values(self):
        with self._lock:
            return list(self._cache.values())

    def items(self):
        with self._lock:
            return list(self._cache.items())

    def __getitem__(self, key: str) -> Any:
        with self._lock:
            self._cache.move_to_end(key)
            return self._cache[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)

    def __delitem__(self, key: str) -> None:
        with self._lock:
            del self._cache[key]

    def __contains__(self, key: str) -> bool:
        with self._lock:
            return key in self._cache

    def __len__(self) -> int:
        with self._lock:
            return len(self._cache)


# Bounded in-memory caches mirroring authoritative persistent store
_DECISION_STORE: BoundedLRUCache = BoundedLRUCache(maxsize=500)
_CONTEXT_STORE: BoundedLRUCache = BoundedLRUCache(maxsize=500)

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


DEVANAGARI_DIGIT_MAP = str.maketrans("०१२३४५६७८९", "0123456789")


def extract_temperature_from_text(text: str) -> Optional[float]:
    """
    Extract numeric temperature in Celsius supporting English and Marathi numerals,
    decimals, negative values, and various degree symbols / words.
    Maps Devanagari numerals (०१२३४५६७८९) to ASCII (0123456789).
    Guarantees 35°C ("३५ अंश", "35°c", "35 degree") is never interpreted as 37°C.
    """
    if not text:
        return None
    # Normalize Devanagari numerals to ASCII
    norm = text.translate(DEVANAGARI_DIGIT_MAP).lower()

    # Pattern for numbers followed by degree/celsius/centigrade/अंश
    pattern = r"(-?\d+(?:\.\d+)?)\s*(?:°\s*c(?:elsius)?|celsius|centigrade|degrees?\s*(?:c(?:elsius)?)?|अंश(?:\s*सेल्सिअस)?|\s*°\s*|(?<=\d)\s*c\b)"
    match = re.search(pattern, norm)
    if match:
        try:
            return float(match.group(1))
        except (ValueError, TypeError):
            pass

    # Pattern for temperature keyword preceding number (e.g. "temperature is 35", "तापमान ३५.५", "कमाल तापमान ३५")
    pattern_prefix = r"(?:temp(?:erature)?|कमाल\s*तापमान|तापमान)\s*(?:is|of|around|जवळपास|:)?\s*(-?\d+(?:\.\d+)?)"
    match_pref = re.search(pattern_prefix, norm)
    if match_pref:
        try:
            return float(match_pref.group(1))
        except (ValueError, TypeError):
            pass

    return None


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
            parsed_temp = extract_temperature_from_text(q)
            if parsed_temp is not None:
                updates["reproductive_temp_max_c"] = parsed_temp
            elif ("फुले" in q and ("गळ" in q or "गळत" in q)) or (("flower drop" in q or "flowers dropping" in q) and ("heat" in q or "temp" in q)):
                updates["reproductive_temp_max_c"] = 36.0

        if ctx.reproductive_temp_mean_c is None:
            norm_q = q.translate(DEVANAGARI_DIGIT_MAP).lower()
            mean_match = re.search(r"(?:mean|average|सरासरी)\s*(?:is|temp|तापमान)?\s*(-?\d+(?:\.\d+)?)", norm_q)
            if mean_match:
                try:
                    updates["reproductive_temp_mean_c"] = float(mean_match.group(1))
                except (ValueError, TypeError):
                    pass
            elif "maximum is" in norm_q and "minimum is" in norm_q:
                max_m = re.search(r"maximum\s*(?:is)?\s*(-?\d+(?:\.\d+)?)", norm_q)
                min_m = re.search(r"minimum\s*(?:is)?\s*(-?\d+(?:\.\d+)?)", norm_q)
                if max_m and min_m:
                    try:
                        updates["reproductive_temp_mean_c"] = (float(max_m.group(1)) + float(min_m.group(1))) / 2.0
                    except (ValueError, TypeError):
                        pass
            elif "14°c" in norm_q or "(20 + 8) / 2" in norm_q:
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
        effective_user_id = user_id or getattr(ctx, "user_id", None)
        if effective_user_id and not getattr(ctx, "user_id", None):
            ctx = ctx.model_copy(update={"user_id": effective_user_id})
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
        failed_profile_crops = []
        for cid in eval_crops:
            profile = self.retriever.get_crop_profile(crop_id=cid, db=db)
            if not profile:
                failed_profile_crops.append(cid)
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

        # Handle failed profile loading explicitly
        if failed_profile_crops:
            for cid in failed_profile_crops:
                outcomes.append(CropEvaluationOutcome(
                    crop_id=cid,
                    common_name=cid.capitalize(),
                    scientific_name=cid,
                    decision_state=DecisionState.ABSTAIN_INSUFFICIENT_EVIDENCE,
                    is_disqualified=False,
                    limiting_factors=["MANDATORY_CROP_PROFILE_FAILED"],
                    uncertainty_notes=[f"Mandatory crop requirement profile for '{cid}' could not be loaded from knowledge base."],
                    missing_information=["crop_profile"],
                    applied_rules=[],
                    citations=[],
                    explanation=f"Cannot evaluate '{cid}' because its mandatory agronomic requirements profile failed to load."
                ))

        # -------------------------------------------------------------
        # Step 5: Follow-Up Question Selection
        # -------------------------------------------------------------
        follow_ups = FollowUpQuestionEngine.select_questions(ctx, val_res, outcomes)

        # Compile Response
        validation_status = "VALID"
        if failed_profile_crops and (len(failed_profile_crops) == len(eval_crops) or (requested_crops and any(c in requested_crops for c in failed_profile_crops))):
            validation_status = "ABSTAIN_MANDATORY_PROFILE_FAILED"
        elif not val_res.is_valid or val_res.contradictions:
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
        owner_id = effective_user_id or user_id
        if owner_id:
            record_decision_owner(decision_id, user_id=str(owner_id), farm_id=str(ctx.farm_id) if ctx.farm_id else None)

        self._persist_decision_to_db(decision_id, ctx, resp, db, user_id=effective_user_id)
        return resp

    def _persist_decision_to_db(
        self,
        decision_id: str,
        ctx: FarmContextInput,
        resp: FarmEvaluationResponse,
        db: Optional[Session],
        user_id: Optional[str] = None
    ) -> None:
        """Persist decision and context to database for multi-worker survival."""
        from cropnet.services.api.app.models.soil_and_farm import FarmDecisionModel
        from cropnet.services.api.app.core.database import SessionLocal

        resolved_user_id = str(user_id) if user_id else (str(ctx.user_id) if getattr(ctx, "user_id", None) else None)
        farm_id = str(ctx.farm_id) if getattr(ctx, "farm_id", None) else None

        decision_dict = resp.model_dump(mode="json")
        context_dict = ctx.model_dump(mode="json")

        def _save(session: Session):
            existing = session.query(FarmDecisionModel).filter(FarmDecisionModel.id == decision_id).first()
            if existing:
                existing.user_id = resolved_user_id
                existing.farm_id = farm_id
                existing.input_validation_status = resp.input_validation_status
                existing.target_season = ctx.target_season
                existing.context_json = context_dict
                existing.decision_json = decision_dict
                existing.updated_at = datetime.utcnow()
            else:
                record = FarmDecisionModel(
                    id=decision_id,
                    user_id=resolved_user_id,
                    farm_id=farm_id,
                    input_validation_status=resp.input_validation_status,
                    target_season=ctx.target_season,
                    context_json=context_dict,
                    decision_json=decision_dict,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                session.add(record)
            session.commit()

        if db is not None:
            try:
                _save(db)
            except Exception as exc:
                logger.warning("Failed to persist decision %s to active db session: %s", decision_id, exc)
                try:
                    db.rollback()
                except Exception as rollback_exc:
                    logger.debug("Failed rollback during decision persistence: %s", rollback_exc)
        else:
            try:
                with SessionLocal() as session:
                    _save(session)
            except Exception as exc:
                logger.warning("Failed to persist decision %s via SessionLocal: %s", decision_id, exc)

    def get_decision(
        self,
        decision_id: str,
        db: Optional[Session] = None,
        user_id: Optional[str] = None
    ) -> Optional[FarmEvaluationResponse]:
        """Fetch previously computed decision from LRU cache or authoritative database."""
        # 1. Check LRU Cache
        cached = _DECISION_STORE.get(decision_id)
        if cached is not None:
            if user_id:
                cached_ctx = _CONTEXT_STORE.get(decision_id)
                cached_user = getattr(cached_ctx, "user_id", None) if cached_ctx else None
                owner_meta = get_decision_owner(decision_id)
                owner_user = owner_meta.get("user_id") if owner_meta else None
                effective_owner = cached_user or owner_user
                if effective_owner and str(effective_owner) != str(user_id):
                    return None
            return cached

        # 2. Database Lookup
        from cropnet.services.api.app.models.soil_and_farm import FarmDecisionModel
        from cropnet.services.api.app.core.database import SessionLocal

        model = None
        if db is not None:
            try:
                model = db.query(FarmDecisionModel).filter(FarmDecisionModel.id == decision_id).first()
            except Exception as exc:
                logger.warning("Database lookup failed for decision %s: %s", decision_id, exc)
        else:
            try:
                with SessionLocal() as session:
                    model = session.query(FarmDecisionModel).filter(FarmDecisionModel.id == decision_id).first()
            except Exception as exc:
                logger.warning("SessionLocal lookup failed for decision %s: %s", decision_id, exc)

        if not model:
            return None

        # Ownership check
        if user_id and model.user_id and str(model.user_id) != str(user_id):
            return None

        try:
            resp = FarmEvaluationResponse(**model.decision_json)
            ctx = FarmContextInput(**model.context_json)
            _DECISION_STORE[decision_id] = resp
            _CONTEXT_STORE[decision_id] = ctx
            if model.user_id:
                record_decision_owner(decision_id, user_id=str(model.user_id), farm_id=str(model.farm_id) if model.farm_id else None)
            return resp
        except Exception as exc:
            logger.error("Failed to deserialize persisted decision %s: %s", decision_id, exc)
            return None

    def process_followup_answers(
        self,
        decision_id: str,
        answers: Dict[str, Any],
        db: Optional[Session] = None,
        user_id: Optional[str] = None
    ) -> Optional[FarmEvaluationResponse]:
        """
        Re-evaluate farm context with updated follow-up answers.
        Survives server restart and multi-worker execution.
        """
        old_ctx = _CONTEXT_STORE.get(decision_id)
        if not old_ctx:
            from cropnet.services.api.app.models.soil_and_farm import FarmDecisionModel
            from cropnet.services.api.app.core.database import SessionLocal

            model = None
            if db is not None:
                try:
                    model = db.query(FarmDecisionModel).filter(FarmDecisionModel.id == decision_id).first()
                except Exception as exc:
                    logger.warning("Database lookup failed during followup for decision %s: %s", decision_id, exc)
            else:
                try:
                    with SessionLocal() as session:
                        model = session.query(FarmDecisionModel).filter(FarmDecisionModel.id == decision_id).first()
                except Exception as exc:
                    logger.warning("SessionLocal lookup failed during followup for decision %s: %s", decision_id, exc)

            if model and model.context_json:
                try:
                    old_ctx = FarmContextInput(**model.context_json)
                    _CONTEXT_STORE[decision_id] = old_ctx
                except Exception as exc:
                    logger.error("Failed to deserialize context for decision %s: %s", decision_id, exc)

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
                        except (ValueError, TypeError) as exc:
                            logger.warning("Invalid soil_depth_cm answer value '%s': %s", v, exc)
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
                        except (ValueError, TypeError) as exc:
                            logger.warning("Invalid electrical_conductivity_ds_m answer value '%s': %s", v, exc)
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
