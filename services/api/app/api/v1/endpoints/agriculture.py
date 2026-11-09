"""
CropNet AI — Agriculture Intelligence API Endpoints.

Provides REST interfaces for:
1. Agro-climatic cropping season calendar (Kharif, Rabi, Summer).
2. Deterministic farm crop evaluation with hard biological constraints (Phase 5.1).
3. Evaluation decision inspection by decision ID.
4. Interactive diagnostic follow-up re-evaluation.
5. Grounded, farmer-friendly natural language explanations (Phase 5.2).
6. Grounded conversational dialogue and follow-up consultation.
"""
import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from cropnet.services.api.app.core.database import get_db
from cropnet.services.api.app.core.security import get_current_user, CurrentUser
from cropnet.services.api.app.schemas.crop import MaharashtraSeasonCalendarResponse
from cropnet.services.api.app.schemas.agriculture_intelligence import (
    FarmContextInput,
    FarmEvaluationResponse,
    FollowUpAnswerRequest,
    AgriculturalExplanationResponse,
    ExplainDecisionRequest,
    ConversationRequest,
    SoilDataProvenance,
)
from cropnet.services.api.app.services.crop_knowledge.crop_service import CropKnowledgeService
from cropnet.services.api.app.services.agriculture_intelligence.decision_engine import (
    DeterministicDecisionEngine,
    record_decision_owner,
    get_decision_owner,
)
from cropnet.services.api.app.services.llm.explanation_service import AgriculturalExplanationService

router = APIRouter()

crop_service = CropKnowledgeService()
decision_engine = DeterministicDecisionEngine()
explanation_service = AgriculturalExplanationService(decision_engine=decision_engine)


@router.get("/seasons", response_model=List[MaharashtraSeasonCalendarResponse], tags=["Agriculture Intelligence"])
def get_maharashtra_seasons():
    """
    Get the official Maharashtra agro-climatic cropping calendar:
    - Kharif (Monsoon)
    - Rabi (Winter)
    - Zaid / Summer (Hot season)
    Provides period months, primary crop types, and moisture characteristics.
    """
    return crop_service.get_maharashtra_seasons()


def _verify_farm_access(farm_id_str: str, current_user: CurrentUser, db: Session) -> None:
    """Verify that caller has access to the specified farm."""
    try:
        farm_uuid = uuid.UUID(farm_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid farm UUID format: '{farm_id_str}'"
        )
    from cropnet.services.api.app.api.v1.endpoints.farms import _FARM_STORAGE
    from cropnet.services.api.app.models.soil_and_farm import FarmModel

    farm = _FARM_STORAGE.get(farm_uuid)
    if not farm and db is not None:
        try:
            db_farm = db.query(FarmModel).filter(FarmModel.id == str(farm_uuid)).first()
            if db_farm:
                farm = {"id": uuid.UUID(db_farm.id), "owner_id": uuid.UUID(db_farm.owner_id)}
        except Exception:
            pass

    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farm '{farm_id_str}' not found"
        )
    if farm["owner_id"] != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this farm"
        )


def _verify_decision_access(decision_id: str, current_user: CurrentUser, db: Session) -> FarmEvaluationResponse:
    """
    Verify that decision exists and caller owns it or owns the associated farm.
    Raises 404 if not found, 403 if unauthorized.
    """
    decision = decision_engine.get_decision(decision_id)
    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation decision '{decision_id}' not found."
        )

    owner_info = get_decision_owner(decision_id)
    caller_id = str(current_user.user_id)

    # 1. Direct owner match
    if owner_info and owner_info.get("user_id") == caller_id:
        return decision

    # 2. Associated farm ownership match
    farm_id = (owner_info.get("farm_id") if owner_info else None) or (
        decision.farm_context.farm_id if decision.farm_context else None
    )
    if farm_id:
        _verify_farm_access(farm_id, current_user, db)
        return decision

    # If owner was recorded and doesn't match caller:
    if owner_info and owner_info.get("user_id") != caller_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this evaluation decision"
        )

    # If no owner recorded and no farm associated, reject callers other than creator
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to access this evaluation decision"
    )


@router.post("/evaluate-farm", response_model=FarmEvaluationResponse, tags=["Agriculture Intelligence"])
def evaluate_farm_intelligence(
    payload: FarmContextInput,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Execute deterministic agricultural evaluation of candidate crops for a farm context.
    Evaluates hard constraints, Bahar water tables, and regional suitability with
    evidence gating and explicit abstention triggers.
    Dispatched via worker threadpool to prevent blocking the asyncio event loop.
    Fuses confirmed laboratory soil measurements when available for the farm.
    """
    if payload.farm_id:
        _verify_farm_access(payload.farm_id, current_user, db)

    if payload.farm_id and payload.soil_data_provenance != SoilDataProvenance.LABORATORY_MEASURED and db is not None:
        try:
            from cropnet.services.api.app.models.soil_reports import SoilTestReportModel, SoilMeasurementModel
            from cropnet.services.api.app.schemas.soil_reports import ReviewStatus, MeasurementVerificationStatus

            confirmed_measurements = (
                db.query(SoilMeasurementModel)
                .join(SoilTestReportModel, SoilMeasurementModel.report_id == SoilTestReportModel.id)
                .filter(
                    SoilMeasurementModel.farm_id == str(payload.farm_id),
                    SoilTestReportModel.review_status == ReviewStatus.CONFIRMED.value,
                    SoilMeasurementModel.verification_status == MeasurementVerificationStatus.FARMER_CONFIRMED.value
                )
                .order_by(SoilTestReportModel.report_date.desc(), SoilMeasurementModel.created_at.desc())
                .all()
            )
            if confirmed_measurements:
                latest_meas = {}
                for m in confirmed_measurements:
                    if m.parameter_key not in latest_meas:
                        latest_meas[m.parameter_key] = m

                updates = {"soil_data_provenance": SoilDataProvenance.LABORATORY_MEASURED}

                def _val(k: str) -> Optional[float]:
                    meas = latest_meas.get(k)
                    if not meas:
                        return None
                    return meas.farmer_corrected_value if meas.farmer_corrected_value is not None else (
                        meas.normalized_value if meas.normalized_value is not None else meas.original_value
                    )

                if payload.soil_ph is None and "soil_ph" in latest_meas:
                    ph_candidate = _val("soil_ph")
                    if ph_candidate is not None and 3.0 <= ph_candidate <= 11.0:
                        updates["soil_ph"] = ph_candidate
                if payload.soil_organic_carbon_pct is None and "organic_carbon" in latest_meas:
                    soc_candidate = _val("organic_carbon")
                    if soc_candidate is not None and 0.0 <= soc_candidate <= 15.0:
                        updates["soil_organic_carbon_pct"] = soc_candidate
                if payload.electrical_conductivity_ds_m is None and "electrical_conductivity" in latest_meas:
                    ec_candidate = _val("electrical_conductivity")
                    if ec_candidate is not None and 0.0 <= ec_candidate <= 30.0:
                        updates["electrical_conductivity_ds_m"] = ec_candidate
                if payload.available_nitrogen_kg_ha is None and "available_nitrogen" in latest_meas:
                    updates["available_nitrogen_kg_ha"] = _val("available_nitrogen")
                if payload.available_phosphorus_kg_ha is None and "available_phosphorus" in latest_meas:
                    updates["available_phosphorus_kg_ha"] = _val("available_phosphorus")
                if payload.available_potassium_kg_ha is None and "available_potassium" in latest_meas:
                    updates["available_potassium_kg_ha"] = _val("available_potassium")
                if payload.total_nitrogen_pct is None and "total_nitrogen" in latest_meas:
                    updates["total_nitrogen_pct"] = _val("total_nitrogen")

                rep = confirmed_measurements[0].report
                if rep and rep.report_date:
                    updates["soil_measurement_date"] = rep.report_date.date().isoformat()

                payload = payload.model_copy(update=updates)
        except Exception:
            pass

    resp = decision_engine.evaluate_farm(ctx=payload, db=db, user_id=str(current_user.user_id))
    record_decision_owner(
        resp.decision_id,
        user_id=str(current_user.user_id),
        farm_id=str(payload.farm_id) if payload.farm_id else None
    )
    return resp


@router.get("/decision/{decision_id}", response_model=FarmEvaluationResponse, tags=["Agriculture Intelligence"])
def get_evaluation_decision(
    decision_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve a previously computed farm evaluation decision by its decision ID.
    Enforces caller and farm ownership.
    """
    return _verify_decision_access(decision_id, current_user, db)


@router.post("/follow-up", response_model=FarmEvaluationResponse, tags=["Agriculture Intelligence"])
def process_decision_followup(
    payload: FollowUpAnswerRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit diagnostic follow-up answers to re-evaluate a farm context with updated parameters.
    Enforces decision ownership before allowing re-evaluation.
    """
    _verify_decision_access(payload.decision_id, current_user, db)
    updated_decision = decision_engine.process_followup_answers(
        decision_id=payload.decision_id,
        answers=payload.answers,
        db=db,
        user_id=str(current_user.user_id)
    )
    if not updated_decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation decision '{payload.decision_id}' not found to process follow-up."
        )
    record_decision_owner(
        updated_decision.decision_id,
        user_id=str(current_user.user_id),
        farm_id=str(updated_decision.farm_context.farm_id) if (updated_decision.farm_context and updated_decision.farm_context.farm_id) else None
    )
    return updated_decision


@router.post("/explain-decision", response_model=AgriculturalExplanationResponse, tags=["Agriculture Explanation & Dialogue"])
def explain_evaluation_decision(
    payload: ExplainDecisionRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a natural, farmer-friendly explanation of a validated decision in English or Marathi.
    The response is grounded in the deterministic decision payload and validated by numerical guardrails.
    Enforces caller ownership of the underlying decision.
    """
    _verify_decision_access(payload.decision_id, current_user, db)
    result = explanation_service.explain_decision(req=payload, db=db)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation decision '{payload.decision_id}' not found."
        )
    return result


@router.post("/conversation", response_model=AgriculturalExplanationResponse, tags=["Agriculture Explanation & Dialogue"])
def process_agricultural_conversation(
    payload: ConversationRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Interactive dialogue and follow-up consultation grounded in a validated agricultural decision.
    If diagnostic answers are submitted, the deterministic engine re-evaluates the farm context first.
    Enforces caller ownership of the underlying decision.
    """
    _verify_decision_access(payload.decision_id, current_user, db)
    result = explanation_service.handle_conversation(req=payload, db=db)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation decision '{payload.decision_id}' not found for conversation."
        )
    if result.decision_id:
        record_decision_owner(
            result.decision_id,
            user_id=str(current_user.user_id)
        )
    return result
