"""Heat Risk — crop, worker and farm-context heat-stress endpoints."""
import uuid
from datetime import date, datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from cropnet.services.api.app.core.database import get_db
from cropnet.services.api.app.core.security import get_current_user, CurrentUser
from cropnet.services.api.app.schemas.heat_risk import (
    CropHeatRequest,
    CropHeatResponse,
    FarmHeatRiskRequest,
    FarmHeatRiskResponse,
    WorkerHeatRequest,
    WorkerHeatResponse,
)
from cropnet.services.api.app.services.heat_risk.engine import (
    CROP_SPECIES_PHYSIOLOGY,
    CropHeatEngine,
    WorkerHeatEngine,
    assess_daily_outlook,
    build_interventions,
)
from cropnet.services.api.app.services.weather_service import WeatherService

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
        return CropHeatEngine.assess(
            crop_code=request.crop_code,
            forecast_tmax_c=request.forecast_tmax_c,
            forecast_tmin_c=request.forecast_tmin_c,
            growth_stage=request.growth_stage,
            days_after_sowing=request.days_after_sowing,
            forecast_sun_hours=request.forecast_sun_hours,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


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


@router.post("/farm/{farm_id}", response_model=FarmHeatRiskResponse)
def assess_farm_heat_risk(
    farm_id: uuid.UUID,
    request: FarmHeatRiskRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Farm-level Heat Risk assessment: reuses CropNet's weather forecast and farm
    ownership, derives the crop growth stage, and returns a multi-day outlook,
    evidence-linked interventions and (optional) worker heat hazard.
    """
    # Lazy import avoids a circular import with the farms router.
    from cropnet.services.api.app.api.v1.endpoints.farms import _get_farm_and_verify_owner

    farm = _get_farm_and_verify_owner(farm_id, current_user, db)

    try:
        forecast = WeatherService().get_forecast(farm, db=db)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Live weather forecast is unavailable for this farm: {exc}",
        )

    summaries = [day.model_dump() for day in forecast.daily_summaries]
    if not summaries:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No forecast data is available for this farm; heat risk cannot be assessed.",
        )

    limitations: List[str] = []
    das = request.days_after_sowing
    if das is None and request.sowing_date:
        try:
            das = max(0, (date.today() - date.fromisoformat(request.sowing_date)).days)
        except ValueError:
            limitations.append("Invalid sowing_date; the default heat-sensitive stage was used.")

    day1 = summaries[0]
    try:
        crop_res = CropHeatEngine.assess(
            crop_code=request.crop_code,
            forecast_tmax_c=float(day1["temp_max_c"]),
            forecast_tmin_c=float(day1["temp_min_c"]),
            growth_stage=request.growth_stage,
            days_after_sowing=das,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    spec = CROP_SPECIES_PHYSIOLOGY[crop_res["crop_code"]]
    outlook = assess_daily_outlook(request.crop_code, summaries)
    if not outlook:
        limitations.append("Multi-day outlook could not be derived from the forecast payload.")

    interventions = build_interventions(
        crop_res["risk_category"], spec["common_name"], crop_res["warm_night_hazard"]
    )

    worker = None
    if request.include_worker_heat:
        try:
            worker = WorkerHeatEngine.assess(
                air_temp_c=float(day1["temp_max_c"]),
                relative_humidity_pct=float(day1.get("humidity_percent", 60.0)),
                workload_category=request.workload_category,
                is_acclimatised=request.is_acclimatised,
                sun_exposure=request.sun_exposure,
            )
            limitations.append(
                "Worker WBGT uses forecast maximum temperature and humidity with default wind/solar "
                "inputs; use the worker endpoint for measured microclimate inputs."
            )
        except Exception:
            limitations.append("Worker heat could not be computed from the forecast humidity.")

    weather_source = getattr(forecast, "source", "OpenWeather")
    return FarmHeatRiskResponse(
        farm_id=str(farm_id),
        farm_name=farm.get("name") or "Farm",
        crop_code=crop_res["crop_code"],
        crop_common_name=spec["common_name"],
        growth_stage_code=crop_res["growth_stage_code"],
        growth_stage_name=crop_res["growth_stage_name"],
        forecast_tmax_c=crop_res["forecast_tmax_c"],
        forecast_tmin_c=crop_res["forecast_tmin_c"],
        critical_tmax_c=crop_res["critical_tmax_c"],
        risk_category=crop_res["risk_category"],
        risk_label=crop_res["risk_label"],
        hours_above_critical=crop_res["hours_above_critical"],
        warm_night_hazard=crop_res["warm_night_hazard"],
        cumulative_gdd=crop_res["cumulative_gdd"],
        daily_outlook=outlook,
        interventions=interventions,
        worker_heat=worker,
        weather_source=weather_source,
        provenance=(
            f"Forecast: {weather_source} ({len(summaries)} days). Crop thresholds: ICAR-CRIDA / SAU. "
            "Worker limits: ACGIH 2023 / ISO 7243:2017."
        ),
        limitations=limitations,
        generated_at=datetime.utcnow().isoformat() + "Z",
    )
