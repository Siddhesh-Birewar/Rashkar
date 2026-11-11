"""RASHKAR Worker Heat & WBGT occupational hazard screening endpoints."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

try:
    from cropnet.services.api.app.core.database import get_db
    from cropnet.services.api.app.core.security import CurrentUser, get_current_user
except ImportError:
    from app.core.database import get_db
    from app.core.security import CurrentUser, get_current_user

from ..adapters import (
    ensure_rashkar_seeded,
    get_worker_hourly_forecast,
    resolve_owned_farm_context,
)
from ..engines import WorkerHeatEngine
from ..models import RashkarWorkerHazardAuditLogModel
from ..schemas.worker_heat import (
    WorkerHeatAssessmentRequest,
    WorkerHeatAssessmentResponse,
)
from ..timezone import to_ist_iso


router = APIRouter(prefix="/worker-heat", tags=["RASHKAR Worker Heat"])


class WorkerHeatEndpointPayload(BaseModel):
    """Request payload accepting either an owned farm_id or explicit Indian coordinates."""

    farm_id: Optional[str] = Field(default=None)
    latitude: Optional[float] = Field(default=None, ge=8.0, le=37.0)
    longitude: Optional[float] = Field(default=None, ge=68.0, le=98.0)
    taluka: Optional[str] = Field(default=None)
    workload_category: str = Field(default="moderate")
    clothing_type: str = Field(default="standard_work_clothes")
    is_acclimatised: bool = Field(default=True)
    sun_exposure: str = Field(default="direct_sun")
    exposure_duration_hours: float = Field(default=4.0, ge=0.5, le=12.0)


@router.post("/assess", response_model=WorkerHeatAssessmentResponse)
def assess_worker_heat(
    payload: WorkerHeatEndpointPayload,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkerHeatAssessmentResponse:
    """Compute Liljegren WBGT, NOAA Heat Index, UTCI, and ISO 7243 work-rest screening."""
    ensure_rashkar_seeded(db)

    if payload.farm_id:
        farm_ctx = resolve_owned_farm_context(payload.farm_id, current_user, db)
        lat = (
            float(payload.latitude)
            if payload.latitude is not None
            else float(farm_ctx["latitude"])
        )
        lon = (
            float(payload.longitude)
            if payload.longitude is not None
            else float(farm_ctx["longitude"])
        )
        resolved_farm_id = farm_ctx["farm_id"]
        taluka = payload.taluka or farm_ctx.get("taluka")
    else:
        if payload.latitude is None or payload.longitude is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Either farm_id or both latitude and longitude must be provided.",
            )
        lat = float(payload.latitude)
        lon = float(payload.longitude)
        resolved_farm_id = None
        taluka = payload.taluka
        farm_ctx = {
            "owner_id": str(current_user.user_id),
            "taluka": taluka,
            "farm_name": taluka or "Field Coordinates",
        }

    engine_request = WorkerHeatAssessmentRequest(
        farm_id=resolved_farm_id,
        latitude=lat,
        longitude=lon,
        taluka=taluka,
        workload_category=payload.workload_category,
        clothing_type=payload.clothing_type,
        is_acclimatised=payload.is_acclimatised,
        sun_exposure=payload.sun_exposure,
        exposure_duration_hours=payload.exposure_duration_hours,
    )

    wx = get_worker_hourly_forecast(lat, lon)
    if wx.get("status") == "OK":
        hourly = wx.get("hourly") or []
        provider = str(wx.get("provider") or "Open-Meteo High-Res Forecast")
        data_quality = "VERIFIED"
    else:
        hourly = None
        provider = "Unavailable"
        data_quality = "UNAVAILABLE"

    return WorkerHeatEngine.assess_worker_heat_hazard(
        request=engine_request,
        farm_context=farm_ctx,
        weather_hourly=hourly,
        db=db,
        weather_provider=provider,
        data_quality=data_quality,
    )


@router.get("/farms/{farm_id}/history")
def get_worker_heat_history(
    farm_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Return audit-logged WBGT worker heat assessments for an owned farm."""
    farm_ctx = resolve_owned_farm_context(farm_id, current_user, db)
    rows = (
        db.query(RashkarWorkerHazardAuditLogModel)
        .filter(RashkarWorkerHazardAuditLogModel.farm_id == farm_ctx["farm_id"])
        .order_by(RashkarWorkerHazardAuditLogModel.request_timestamp_utc.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": row.id,
            "farm_id": row.farm_id,
            "owner_id": row.owner_id,
            "request_timestamp_ist": to_ist_iso(row.request_timestamp_utc),
            "forecast_target_timestamp_ist": to_ist_iso(row.forecast_target_timestamp_utc),
            "weather_provider": row.weather_provider,
            "air_temp_c": row.air_temp_c,
            "relative_humidity_pct": row.relative_humidity_pct,
            "wind_speed_kmh": row.wind_speed_kmh,
            "solar_radiation_wm2": row.solar_radiation_wm2,
            "calculated_wbgt_c": row.calculated_wbgt_c,
            "calculated_heat_index_c": row.calculated_heat_index_c,
            "risk_tier": row.risk_tier,
            "workload_class": row.workload_class,
            "acclimatization_status": row.acclimatization_status,
            "applied_threshold_wbgt_c": row.applied_threshold_wbgt_c,
            "provenance_summary": row.provenance_summary,
            "advisory_issued_ids": row.advisory_issued_ids,
        }
        for row in rows
    ]
