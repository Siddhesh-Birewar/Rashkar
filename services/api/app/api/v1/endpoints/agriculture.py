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
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from cropnet.services.api.app.core.database import get_db
from cropnet.services.api.app.schemas.crop import MaharashtraSeasonCalendarResponse
from cropnet.services.api.app.schemas.agriculture_intelligence import (
    FarmContextInput,
    FarmEvaluationResponse,
    FollowUpAnswerRequest,
    AgriculturalExplanationResponse,
    ExplainDecisionRequest,
    ConversationRequest
)
from cropnet.services.api.app.services.crop_knowledge.crop_service import CropKnowledgeService
from cropnet.services.api.app.services.agriculture_intelligence.decision_engine import DeterministicDecisionEngine
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


@router.post("/evaluate-farm", response_model=FarmEvaluationResponse, tags=["Agriculture Intelligence"])
def evaluate_farm_intelligence(
    payload: FarmContextInput,
    db: Session = Depends(get_db)
):
    """
    Execute deterministic agricultural evaluation of candidate crops for a farm context.
    Evaluates hard constraints, Bahar water tables, and regional suitability with
    evidence gating and explicit abstention triggers.
    Dispatched via worker threadpool to prevent blocking the asyncio event loop.
    """
    return decision_engine.evaluate_farm(ctx=payload, db=db)


@router.get("/decision/{decision_id}", response_model=FarmEvaluationResponse, tags=["Agriculture Intelligence"])
def get_evaluation_decision(
    decision_id: str
):
    """
    Retrieve a previously computed farm evaluation decision by its decision ID.
    """
    decision = decision_engine.get_decision(decision_id)
    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation decision '{decision_id}' not found."
        )
    return decision


@router.post("/follow-up", response_model=FarmEvaluationResponse, tags=["Agriculture Intelligence"])
def process_decision_followup(
    payload: FollowUpAnswerRequest,
    db: Session = Depends(get_db)
):
    """
    Submit diagnostic follow-up answers to re-evaluate a farm context with updated parameters.
    """
    updated_decision = decision_engine.process_followup_answers(
        decision_id=payload.decision_id,
        answers=payload.answers,
        db=db
    )
    if not updated_decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation decision '{payload.decision_id}' not found to process follow-up."
        )
    return updated_decision


@router.post("/explain-decision", response_model=AgriculturalExplanationResponse, tags=["Agriculture Explanation & Dialogue"])
def explain_evaluation_decision(
    payload: ExplainDecisionRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a natural, farmer-friendly explanation of a validated decision in English or Marathi.
    The response is grounded in the deterministic decision payload and validated by numerical guardrails.
    """
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
    db: Session = Depends(get_db)
):
    """
    Interactive dialogue and follow-up consultation grounded in a validated agricultural decision.
    If diagnostic answers are submitted, the deterministic engine re-evaluates the farm context first.
    """
    result = explanation_service.handle_conversation(req=payload, db=db)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation decision '{payload.decision_id}' not found for conversation."
        )
    return result
