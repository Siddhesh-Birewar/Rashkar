"""Heat Risk — crop heat-stress and worker heat-hazard endpoints."""
from fastapi import APIRouter, HTTPException, status

from cropnet.services.api.app.schemas.heat_risk import (
    CropHeatRequest,
    CropHeatResponse,
    WorkerHeatRequest,
    WorkerHeatResponse,
)
from cropnet.services.api.app.services.heat_risk.engine import (
    CROP_SPECIES_PHYSIOLOGY,
    CropHeatEngine,
    WorkerHeatEngine,
)

router = APIRouter()


@router.get("/crops")
def supported_crops():
    """Crops with verified heat-stress physiology in this module."""
    return {
        "crops": [
            {
                "crop_code": key,
                "common_name": spec["common_name"],
                "night_crit_c": spec["night_crit_c"],
                "stages": [s["stage_code"] for s in spec["stages"]],
            }
            for key, spec in sorted(CROP_SPECIES_PHYSIOLOGY.items())
        ]
    }


@router.post("/crop", response_model=CropHeatResponse)
def assess_crop_heat(request: CropHeatRequest):
    """Assess stage-specific crop heat stress and warm-night respiration risk."""
    try:
        result = CropHeatEngine.assess(
            crop_code=request.crop_code,
            forecast_tmax_c=request.forecast_tmax_c,
            forecast_tmin_c=request.forecast_tmin_c,
            growth_stage=request.growth_stage,
            days_after_sowing=request.days_after_sowing,
            forecast_sun_hours=request.forecast_sun_hours,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return result


@router.post("/worker", response_model=WorkerHeatResponse)
def assess_worker_heat(request: WorkerHeatRequest):
    """Assess occupational heat hazard (WBGT) for an agricultural worker."""
    return WorkerHeatEngine.assess(
        air_temp_c=request.air_temp_c,
        relative_humidity_pct=request.relative_humidity_pct,
        wind_speed_ms=request.wind_speed_ms,
        solar_irradiance_wm2=request.solar_irradiance_wm2,
        workload_category=request.workload_category,
        clothing_type=request.clothing_type,
        is_acclimatised=request.is_acclimatised,
        sun_exposure=request.sun_exposure,
    )
