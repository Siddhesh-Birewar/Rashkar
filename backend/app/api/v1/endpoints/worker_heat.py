from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.worker_heat import (
    WorkerHeatAssessmentRequest,
    WorkerHeatAssessmentResponse
)
from backend.app.services.worker_heat_engine import WorkerHeatEngine

router = APIRouter()

@router.post("/worker-hazard", response_model=WorkerHeatAssessmentResponse)
def assess_worker_heat_hazard(
    request: WorkerHeatAssessmentRequest,
    db: Session = Depends(get_db)
):
    """
    Assess agricultural worker occupational heat hazard for 0-6 hour forecast window.
    Calculates estimated outdoor and indoor WBGT via Liljegren et al. (2008),
    applies clothing adjustments (CAV) and ACGIH TLV / ISO 7243 screening thresholds.
    Logs pseudonymised audit record to database with 30-day retention.
    """
    try:
        response = WorkerHeatEngine.assess_worker_heat_hazard(request=request, db=db)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Worker heat assessment error: {str(e)}"
        )
