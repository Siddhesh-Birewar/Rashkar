"""RASHKAR Crop Heat physiological stress assessment endpoints."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

try:
    from cropnet.services.api.app.core.database import get_db
    from cropnet.services.api.app.core.security import CurrentUser, get_current_user
except ImportError:
    from app.core.database import get_db
    from app.core.security import CurrentUser, get_current_user

from ..adapters import (
    ensure_rashkar_seeded,
    get_active_crop_cycle,
    get_crop_heat_forecast,
    resolve_farm_soil_context,
    resolve_owned_farm_context,
)
from ..engines import CropHeatEngine
from ..models import RashkarCropHeatLogModel
from ..schemas.crop_heat import (
    CropHeatAssessmentRequest,
    CropHeatAssessmentResponse,
)
from ..timezone import to_ist_iso


router = APIRouter(prefix="/crop-heat", tags=["RASHKAR Crop Heat"])


@router.post("/assess", response_model=CropHeatAssessmentResponse)
def assess_crop_heat(
    request: CropHeatAssessmentRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CropHeatAssessmentResponse:
    """Evaluate stage-specific crop thermal stress, VPD, and 4-day heatwave outlook."""
    ensure_rashkar_seeded(db)

    if not request.farm_id or not str(request.farm_id).strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="farm_id is required for crop heat assessment.",
        )

    farm_ctx = resolve_owned_farm_context(request.farm_id, current_user, db)
    fid = farm_ctx["farm_id"]

    active_cycle = get_active_crop_cycle(fid, db)
    soil_ctx = resolve_farm_soil_context(fid, db)

    wx = get_crop_heat_forecast(farm_ctx["latitude"], farm_ctx["longitude"])
    weather_forecast = wx if wx.get("status") == "OK" else None

    response = CropHeatEngine.assess_crop_heat_risk(
        request=request,
        farm_context=farm_ctx,
        crop_cycle=active_cycle,
        weather_forecast=weather_forecast,
        soil_profile=soil_ctx,
        db=db,
    )
    if db.dirty:
        db.commit()
    return response


@router.get("/farms/{farm_id}/history")
def get_crop_heat_history(
    farm_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Return logged crop heat assessments for an owned farm."""
    farm_ctx = resolve_owned_farm_context(farm_id, current_user, db)
    rows = (
        db.query(RashkarCropHeatLogModel)
        .filter(RashkarCropHeatLogModel.farm_id == farm_ctx["farm_id"])
        .order_by(RashkarCropHeatLogModel.assessed_at_utc.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": row.id,
            "farm_id": row.farm_id,
            "owner_id": row.owner_id,
            "crop_code": row.crop_code,
            "stage_code": row.stage_code,
            "stage_source": row.stage_source,
            "assessed_at_ist": to_ist_iso(row.assessed_at_utc),
            "peak_tmax_c": row.peak_tmax_c,
            "peak_vpd_kpa": row.peak_vpd_kpa,
            "overall_stress_score": row.overall_stress_score,
            "stress_tier": row.stress_tier,
            "weather_source": row.weather_source,
            "provenance_summary": row.provenance_summary,
        }
        for row in rows
    ]
