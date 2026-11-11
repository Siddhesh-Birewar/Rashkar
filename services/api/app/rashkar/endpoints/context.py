"""RASHKAR farm context, canonical crop catalog, and crop-cycle endpoints."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

try:
    from cropnet.services.api.app.core.database import get_db
    from cropnet.services.api.app.core.security import CurrentUser, get_current_user
except ImportError:
    from app.core.database import get_db
    from app.core.security import CurrentUser, get_current_user

from ..adapters import (
    confirm_crop_stage,
    ensure_rashkar_seeded,
    get_active_crop_cycle,
    get_worker_hourly_forecast,
    list_crop_cycles,
    resolve_farm_soil_context,
    resolve_owned_farm_context,
    update_crop_cycle,
    upsert_active_crop_cycle,
)
from ..models import (
    RashkarCanonicalCropModel,
    RashkarCropHeatLogModel,
    RashkarCropStageModel,
    RashkarSavedIncomePlanModel,
    RashkarWorkerHazardAuditLogModel,
    RashkarYieldAssessmentLogModel,
)
from ..schemas.context import (
    RashkarCanonicalCropItem,
    RashkarCropCycleCreate,
    RashkarCropCycleResponse,
    RashkarCropCycleUpdate,
)
from ..timezone import to_ist_iso


router = APIRouter(tags=["RASHKAR Context & Crop Cycles"])


class StageConfirmRequest(BaseModel):
    """Payload to confirm or correct the current crop growth stage."""

    stage_code: str = Field(..., min_length=1, max_length=50)
    cycle_id: Optional[str] = Field(default=None, max_length=36)


@router.get("/crops")
def list_canonical_crops(
    include_stages: bool = Query(default=False),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """List canonical RASHKAR crops (with optional phenological stage schedules)."""
    del current_user
    ensure_rashkar_seeded(db)

    crops = (
        db.query(RashkarCanonicalCropModel)
        .order_by(
            RashkarCanonicalCropModel.is_pioneer_pilot_crop.desc(),
            RashkarCanonicalCropModel.common_name_en.asc(),
        )
        .all()
    )

    stages_by_crop: Dict[str, List[Dict[str, Any]]] = {}
    if include_stages:
        stages = (
            db.query(RashkarCropStageModel)
            .order_by(
                RashkarCropStageModel.crop_code.asc(),
                RashkarCropStageModel.sequence_order.asc(),
            )
            .all()
        )
        for stage in stages:
            stages_by_crop.setdefault(stage.crop_code, []).append(
                {
                    "stage_code": stage.stage_code,
                    "stage_name_en": stage.stage_name_en,
                    "stage_name_mr": stage.stage_name_mr,
                    "sequence_order": stage.sequence_order,
                    "typical_das_start": stage.typical_das_start,
                    "typical_das_end": stage.typical_das_end,
                    "description": stage.description,
                }
            )

    items: List[Dict[str, Any]] = []
    for crop in crops:
        item = RashkarCanonicalCropItem.model_validate(crop).model_dump()
        if include_stages:
            item["stages"] = stages_by_crop.get(crop.crop_code, [])
        items.append(item)
    return items


@router.get("/farms/{farm_id}/overview")
def get_farm_rashkar_overview(
    farm_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Return owned farm context, active crop cycle, soil, live weather preview, and log summaries."""
    ensure_rashkar_seeded(db)
    farm_ctx = resolve_owned_farm_context(farm_id, current_user, db)
    fid = farm_ctx["farm_id"]

    active_cycle = get_active_crop_cycle(fid, db)
    soil_ctx = resolve_farm_soil_context(fid, db)

    wx = get_worker_hourly_forecast(farm_ctx["latitude"], farm_ctx["longitude"])
    if wx.get("status") == "OK" and wx.get("hourly"):
        first_pt = wx["hourly"][0]
        weather_preview: Dict[str, Any] = {
            "status": "OK",
            "provider": wx.get("provider"),
            "elevation_m": wx.get("elevation_m"),
            "current_air_temp_c": first_pt.get("air_temp_c"),
            "current_relative_humidity_pct": first_pt.get("relative_humidity_pct"),
            "current_wind_speed_ms": first_pt.get("wind_speed_ms"),
            "current_solar_irradiance_wm2": first_pt.get("solar_irradiance_wm2"),
            "timestamp_ist": first_pt.get("timestamp_ist"),
        }
    else:
        weather_preview = {
            "status": "WEATHER_UNAVAILABLE",
            "provider": None,
            "error": wx.get("error") or "Live Open-Meteo feed unavailable.",
        }

    saved_plans_count = (
        db.query(RashkarSavedIncomePlanModel)
        .filter(RashkarSavedIncomePlanModel.farm_id == fid)
        .count()
    )

    latest_worker = (
        db.query(RashkarWorkerHazardAuditLogModel)
        .filter(RashkarWorkerHazardAuditLogModel.farm_id == fid)
        .order_by(RashkarWorkerHazardAuditLogModel.request_timestamp_utc.desc())
        .first()
    )
    latest_crop_heat = (
        db.query(RashkarCropHeatLogModel)
        .filter(RashkarCropHeatLogModel.farm_id == fid)
        .order_by(RashkarCropHeatLogModel.assessed_at_utc.desc())
        .first()
    )
    latest_yield = (
        db.query(RashkarYieldAssessmentLogModel)
        .filter(RashkarYieldAssessmentLogModel.farm_id == fid)
        .order_by(RashkarYieldAssessmentLogModel.assessed_at_utc.desc())
        .first()
    )

    return {
        "farm_context": farm_ctx,
        "has_active_crop": active_cycle is not None,
        "active_crop_cycle": (
            RashkarCropCycleResponse.model_validate(active_cycle).model_dump()
            if active_cycle is not None
            else None
        ),
        "soil": soil_ctx,
        "weather": weather_preview,
        "saved_income_plans_count": saved_plans_count,
        "latest_assessments": {
            "worker_heat": (
                {
                    "id": latest_worker.id,
                    "assessed_at_ist": to_ist_iso(latest_worker.request_timestamp_utc),
                    "calculated_wbgt_c": latest_worker.calculated_wbgt_c,
                    "risk_tier": latest_worker.risk_tier,
                }
                if latest_worker is not None
                else None
            ),
            "crop_heat": (
                {
                    "id": latest_crop_heat.id,
                    "assessed_at_ist": to_ist_iso(latest_crop_heat.assessed_at_utc),
                    "crop_code": latest_crop_heat.crop_code,
                    "stage_code": latest_crop_heat.stage_code,
                    "stress_tier": latest_crop_heat.stress_tier,
                    "overall_stress_score": latest_crop_heat.overall_stress_score,
                }
                if latest_crop_heat is not None
                else None
            ),
            "yield_intelligence": (
                {
                    "id": latest_yield.id,
                    "assessed_at_ist": to_ist_iso(latest_yield.assessed_at_utc),
                    "crop_code": latest_yield.crop_code,
                    "composite_risk_tier": latest_yield.composite_risk_tier,
                    "composite_risk_score": latest_yield.composite_risk_score,
                    "benchmark_tier": latest_yield.benchmark_tier,
                }
                if latest_yield is not None
                else None
            ),
        },
    }


@router.get("/farms/{farm_id}/crop-cycles", response_model=List[RashkarCropCycleResponse])
def list_farm_crop_cycles(
    farm_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[RashkarCropCycleResponse]:
    """List all crop cycles belonging to an owned CropNet farm."""
    ensure_rashkar_seeded(db)
    farm_ctx = resolve_owned_farm_context(farm_id, current_user, db)
    cycles = list_crop_cycles(farm_ctx["farm_id"], db)
    return [RashkarCropCycleResponse.model_validate(c) for c in cycles]


@router.post(
    "/farms/{farm_id}/crop-cycle",
    response_model=RashkarCropCycleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_or_activate_farm_crop_cycle(
    farm_id: str,
    payload: RashkarCropCycleCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RashkarCropCycleResponse:
    """Create a crop cycle for the owned farm (deactivating prior active cycle when active)."""
    ensure_rashkar_seeded(db)
    farm_ctx = resolve_owned_farm_context(farm_id, current_user, db)
    cycle = upsert_active_crop_cycle(
        farm_id=farm_ctx["farm_id"],
        owner_id=farm_ctx["owner_id"],
        payload=payload,
        db=db,
    )
    return RashkarCropCycleResponse.model_validate(cycle)


@router.patch(
    "/farms/{farm_id}/crop-cycle/{cycle_id}",
    response_model=RashkarCropCycleResponse,
)
def patch_farm_crop_cycle(
    farm_id: str,
    cycle_id: str,
    payload: RashkarCropCycleUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RashkarCropCycleResponse:
    """Update a specific crop cycle belonging to the owned farm."""
    ensure_rashkar_seeded(db)
    farm_ctx = resolve_owned_farm_context(farm_id, current_user, db)
    cycle = update_crop_cycle(
        farm_id=farm_ctx["farm_id"],
        cycle_id=cycle_id,
        payload=payload,
        db=db,
    )
    return RashkarCropCycleResponse.model_validate(cycle)


@router.post(
    "/farms/{farm_id}/crop-cycle/confirm-stage",
    response_model=RashkarCropCycleResponse,
)
def confirm_farm_crop_stage(
    farm_id: str,
    payload: StageConfirmRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RashkarCropCycleResponse:
    """Persist farmer-confirmed phenological stage on the farm's active (or target) crop cycle."""
    ensure_rashkar_seeded(db)
    farm_ctx = resolve_owned_farm_context(farm_id, current_user, db)
    cycle = confirm_crop_stage(
        farm_id=farm_ctx["farm_id"],
        stage_code=payload.stage_code,
        db=db,
        cycle_id=payload.cycle_id,
    )
    return RashkarCropCycleResponse.model_validate(cycle)
