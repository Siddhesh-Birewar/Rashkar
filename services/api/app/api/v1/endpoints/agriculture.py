"""
CropNet AI — Agriculture Reference & Intelligence API Endpoints.

Provides agricultural calendar reference, deterministic farm evaluation,
decision inspection, and targeted diagnostic follow-up handling.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from cropnet.services.api.app.core.database import get_db
from cropnet.services.api.app.schemas.crop import MaharashtraSeasonCalendarResponse
from cropnet.services.api.app.schemas.agriculture_intelligence import (
    FarmContextInput,
    FarmEvaluationResponse,
    FollowUpAnswerRequest
)
from cropnet.services.api.app.services.crop_knowledge.crop_service import CropKnowledgeService
from cropnet.services.api.app.services.agriculture_intelligence.decision_engine import DeterministicDecisionEngine

router = APIRouter()
crop_service = CropKnowledgeService()
decision_engine = DeterministicDecisionEngine()


@router.get("/seasons", response_model=List[MaharashtraSeasonCalendarResponse], tags=["Agricultural Reference"])
async def list_agricultural_seasons():
    """
    Standard agricultural cropping seasons in Maharashtra:
    - Kharif (Monsoon)
    - Rabi (Winter)
    - Zaid / Summer (Hot season)
    Provides period months, primary crop types, and moisture characteristics.
    """
    return crop_service.get_maharashtra_seasons()


@router.post("/evaluate-farm", response_model=FarmEvaluationResponse, tags=["Agriculture Intelligence"])
async def evaluate_farm_intelligence(
    payload: FarmContextInput,
    db: Session = Depends(get_db)
):
    """
    Execute deterministic agricultural evaluation of candidate crops for a farm context.
    Evaluates hard constraints, Bahar water tables, and regional suitability with
    evidence gating and explicit abstention triggers.
    """
    return decision_engine.evaluate_farm(ctx=payload, db=db)


@router.get("/decision/{decision_id}", response_model=FarmEvaluationResponse, tags=["Agriculture Intelligence"])
async def get_evaluation_decision(
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
async def process_decision_followup(
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
