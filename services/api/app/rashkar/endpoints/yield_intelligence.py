"""RASHKAR Yield Risk Intelligence & DES APY historical baseline endpoints."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
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
    get_yield_weather_summary,
    resolve_farm_soil_context,
    resolve_owned_farm_context,
)
from ..engines import YieldRiskEngine
from ..models import RashkarCropCycleModel, RashkarYieldAssessmentLogModel
from ..schemas.yield_risk import HistoricalYieldBaseline, YieldRiskResponse
from ..timezone import to_ist_iso


router = APIRouter(prefix="/yield", tags=["RASHKAR Yield Intelligence"])


@router.get("/farms/{farm_id}/assessment", response_model=YieldRiskResponse)
def get_farm_yield_assessment(
    farm_id: str,
    crop_code: Optional[str] = Query(default=None, max_length=50),
    farmer_confirmed_stage: Optional[str] = Query(default=None, max_length=50),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> YieldRiskResponse:
    """Run YieldRiskEngine screening for an owned farm's active crop or pre-sowing preview."""
    ensure_rashkar_seeded(db)
    farm_ctx = resolve_owned_farm_context(farm_id, current_user, db)
    fid = farm_ctx["farm_id"]

    active_cycle = get_active_crop_cycle(fid, db)
    screening_mode = "ACTIVE_CROP"
    cycle_to_eval = active_cycle

    clean_crop_code = crop_code.strip().lower() if crop_code and crop_code.strip() else None
    if cycle_to_eval is None and clean_crop_code:
        screening_mode = "PRE_SOWING_PREVIEW"
        cycle_to_eval = RashkarCropCycleModel(
            id="pre_sowing_preview",
            farm_id=fid,
            owner_id=farm_ctx["owner_id"],
            crop_code=clean_crop_code,
            variety_name=None,
            sowing_date=None,
            season=None,
            planted_area_acres=farm_ctx.get("total_area_acres"),
            irrigation_type=farm_ctx.get("irrigation_type"),
            current_stage_code=None,
            stage_source="pre_sowing_preview",
            is_active=False,
        )

    soil_ctx = resolve_farm_soil_context(fid, db)
    weather_summary = (
        get_yield_weather_summary(
            farm_id=fid,
            lat=farm_ctx["latitude"],
            lon=farm_ctx["longitude"],
            db=db,
        )
        if cycle_to_eval is not None
        else None
    )

    response = YieldRiskEngine.assess_yield_risk(
        farm_context=farm_ctx,
        crop_cycle=cycle_to_eval,
        soil_profile=soil_ctx,
        weather_summary=weather_summary,
        db=db,
        farmer_confirmed_stage=farmer_confirmed_stage,
    )

    if screening_mode == "PRE_SOWING_PREVIEW":
        prov = dict(response.provenance or {})
        prov["screening_mode"] = "PRE_SOWING_PREVIEW"
        response.provenance = prov

    return response


@router.get("/farms/{farm_id}/history")
def get_farm_yield_history(
    farm_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Return logged yield risk assessments for an owned farm."""
    farm_ctx = resolve_owned_farm_context(farm_id, current_user, db)
    rows = (
        db.query(RashkarYieldAssessmentLogModel)
        .filter(RashkarYieldAssessmentLogModel.farm_id == farm_ctx["farm_id"])
        .order_by(RashkarYieldAssessmentLogModel.assessed_at_utc.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": row.id,
            "farm_id": row.farm_id,
            "owner_id": row.owner_id,
            "crop_code": row.crop_code,
            "district": row.district,
            "assessed_at_ist": to_ist_iso(row.assessed_at_utc),
            "benchmark_tier": row.benchmark_tier,
            "apy_mean_t_ha": row.apy_mean_t_ha,
            "apy_median_t_ha": row.apy_median_t_ha,
            "apy_sample_count": row.apy_sample_count,
            "composite_risk_score": row.composite_risk_score,
            "composite_risk_tier": row.composite_risk_tier,
            "prediction_lock_status": row.prediction_lock_status,
            "provenance_summary": row.provenance_summary,
        }
        for row in rows
    ]


@router.get("/baseline", response_model=HistoricalYieldBaseline)
def get_district_yield_baseline(
    district: str = Query(..., min_length=1, max_length=100),
    crop_code: str = Query(..., min_length=1, max_length=50),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HistoricalYieldBaseline:
    """Compute DES APY empirical district (or statewide fallback) yield baseline."""
    del current_user
    ensure_rashkar_seeded(db)
    baseline = YieldRiskEngine.calculate_apy_district_baseline(
        district=district.strip(),
        crop_code=crop_code.strip().lower(),
        db=db,
    )
    return HistoricalYieldBaseline(**baseline)
