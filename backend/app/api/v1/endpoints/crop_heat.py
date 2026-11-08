from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.crop_heat import (
    CropHeatAssessmentRequest,
    CropHeatAssessmentResponse
)
from backend.app.services.crop_heat_engine import CropHeatEngine

router = APIRouter()

@router.post("/crop-heat", response_model=CropHeatAssessmentResponse)
def assess_crop_heat_risk(
    request: CropHeatAssessmentRequest,
    db: Session = Depends(get_db)
):
    """
    Assess crop-stage-specific thermal risk and warm-night respiration penalty.
    Evaluates forecast temperatures against traceable scientific thresholds
    from ICAR and SAU research institutions.
    """
    try:
        response = CropHeatEngine.assess_crop_heat_risk(db=db, request=request)
        return response
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Crop heat assessment error: {str(e)}"
        )
