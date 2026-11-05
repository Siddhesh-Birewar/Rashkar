import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from cropnet.services.api.app.core.security import get_current_user, CurrentUser
from cropnet.services.api.app.core.database import get_db
from cropnet.services.api.app.models.soil_and_farm import FarmModel
from cropnet.services.api.app.schemas.weather import (
    CurrentWeatherObservation,
    FarmWeatherForecastResponse,
    SeasonalClimateSummary,
    HistoricalWeatherRecord
)
from cropnet.services.api.app.services.weather_service import WeatherService
from cropnet.services.api.app.api.v1.endpoints.farms import _get_farm_and_verify_owner

router = APIRouter()
weather_service = WeatherService()


@router.get("/current", response_model=CurrentWeatherObservation)
async def get_farm_current_weather(
    farm_id: uuid.UUID,
    force_refresh: bool = Query(default=False, description="Whether to bypass cache and query OpenWeather API"),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve real-time observed meteorological data for the farm centroid.
    - Caches observations for 20 minutes to prevent redundant external API hits.
    - Enforces farm ownership authorization.
    """
    farm = _get_farm_and_verify_owner(farm_id, current_user, db)
    return weather_service.get_current_weather(farm, db=db, force_refresh=force_refresh)


@router.get("/forecast", response_model=FarmWeatherForecastResponse)
async def get_farm_weather_forecast(
    farm_id: uuid.UUID,
    force_refresh: bool = Query(default=False, description="Whether to bypass cache and query OpenWeather API"),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve 5-day / 3-hour meteorological forecast for the farm centroid.
    - Caches forecast for 3 hours.
    - Provides aggregated daily summaries and granular hourly points.
    - Enforces farm ownership authorization.
    """
    farm = _get_farm_and_verify_owner(farm_id, current_user, db)
    return weather_service.get_forecast(farm, db=db, force_refresh=force_refresh)


@router.get("/history", response_model=List[HistoricalWeatherRecord])
async def get_farm_weather_history(
    farm_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve historical weather observation snapshots stored for this farm.
    - Enforces farm ownership authorization.
    """
    _get_farm_and_verify_owner(farm_id, current_user, db)
    return weather_service.get_weather_history(str(farm_id), db=db, limit=limit)


@router.get("/climate-summary", response_model=SeasonalClimateSummary)
async def get_farm_climate_summary(
    farm_id: uuid.UUID,
    force_refresh: bool = Query(default=False, description="Whether to bypass cache and query NASA POWER API"),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve 30-year agro-climate summary and seasonal indicators from NASA POWER.
    - Caches normals for 30 days.
    - Provides monthly rainfall mm, temperature trends, and seasonal stress indicators.
    - Enforces farm ownership authorization.
    """
    farm = _get_farm_and_verify_owner(farm_id, current_user, db)
    return weather_service.get_climate_summary(farm, db=db, force_refresh=force_refresh)
