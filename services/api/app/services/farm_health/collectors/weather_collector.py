"""
Weather Intelligence Collector for Farm Health Snapshot.

Collects real-time observed meteorological data, 5-day / 3-hour forecasts,
and 30-year NASA POWER agro-climatological normals.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging
from sqlalchemy.orm import Session

from cropnet.services.api.app.schemas.farm_health import (
    DataAvailabilityState,
    WeatherDomainSummary,
    CurrentWeatherSummary,
    ForecastSummary,
    ClimateNormalsSummary,
)
from cropnet.services.api.app.services.weather_service import WeatherService
from cropnet.services.api.app.models.weather import (
    FarmWeatherSnapshotModel,
    FarmClimateSummaryModel,
)
from cropnet.services.api.app.services.farm_health.collectors.base import (
    BaseDomainCollector,
    utc_now,
)

logger = logging.getLogger(__name__)

CURRENT_WEATHER_STALE_HOURS = 2.0
FORECAST_STALE_HOURS = 12.0
CLIMATE_STALE_DAYS = 30.0


class WeatherCollector(BaseDomainCollector):
    """
    Collects current weather, short-term forecast, and agro-climatic normals.
    """

    def __init__(self):
        self.weather_service = WeatherService()

    @property
    def domain_name(self) -> str:
        return "weather"

    def collect(
        self,
        farm: Dict[str, Any],
        db: Session,
        force_refresh: bool = False,
        **kwargs
    ) -> WeatherDomainSummary:
        farm_id = str(farm["id"])
        now = utc_now()

        # 1. Fetch genuine database records if available
        db_current = None
        db_climate = None
        if db is not None:
            try:
                db_current = (
                    db.query(FarmWeatherSnapshotModel)
                    .filter(
                        FarmWeatherSnapshotModel.farm_id == farm_id,
                        FarmWeatherSnapshotModel.snapshot_type == "current",
                    )
                    .order_by(FarmWeatherSnapshotModel.observation_time.desc())
                    .first()
                )
                db_climate = (
                    db.query(FarmClimateSummaryModel)
                    .filter(FarmClimateSummaryModel.farm_id == farm_id)
                    .order_by(FarmClimateSummaryModel.created_at.desc())
                    .first()
                )
            except Exception as e:
                logger.debug("DB weather check error: %s", e)

        current_obs = None
        forecast_resp = None
        climate_resp = None

        # 2. Try weather service (which handles cache & db fallback)
        try:
            current_obs = self.weather_service.get_current_weather(
                farm, db=db, force_refresh=force_refresh
            )
        except Exception as e:
            logger.debug("Live current weather collection failed: %s", e)

        try:
            forecast_resp = self.weather_service.get_forecast(
                farm, db=db, force_refresh=force_refresh
            )
        except Exception as e:
            logger.debug("Live forecast collection failed: %s", e)

        try:
            climate_resp = self.weather_service.get_climate_summary(
                farm, db=db, force_refresh=force_refresh
            )
        except Exception as e:
            logger.debug("Live climate summary collection failed: %s", e)

        # 3. Safeguard against synthetic data and preserve existing DB observations:
        # If not force_refreshing and genuine DB records exist, use genuine DB snapshot.
        # If external provider returned a simulated fixture and genuine DB snapshot exists,
        # use the genuine DB snapshot. If no DB records exist, reject simulated fixture.
        if (not force_refresh and db_current) or (current_obs and ("(Simulated)" in getattr(current_obs, "source", "") or "Calibrated" in getattr(current_obs, "source", ""))):
            if db_current:
                from cropnet.services.api.app.schemas.weather import CurrentWeatherObservation
                temp = float(db_current.temperature if db_current.temperature is not None else 25.0)
                current_obs = CurrentWeatherObservation(
                    farm_id=farm_id,
                    observation_time=db_current.observation_time,
                    source=db_current.source or "OpenWeather",
                    temperature_c=temp,
                    feels_like_c=float(db_current.feels_like if db_current.feels_like is not None else temp),
                    temperature_min_c=float(db_current.temperature_min if db_current.temperature_min is not None else (temp - 3.0)),
                    temperature_max_c=float(db_current.temperature_max if db_current.temperature_max is not None else (temp + 3.0)),
                    humidity_percent=float(db_current.humidity if db_current.humidity is not None else 50.0),
                    wind_speed_ms=float(db_current.wind_speed if db_current.wind_speed is not None else 0.0),
                    wind_direction_deg=db_current.wind_direction,
                    precipitation_mm=float(db_current.precipitation_mm or 0.0),
                    weather_condition=db_current.weather_condition or "Clear",
                    weather_description=db_current.weather_description or "clear sky",
                    weather_icon=db_current.weather_icon or "01d",
                )
            else:
                current_obs = None

        if not db_current and not db_climate:
            current_obs = None
            forecast_resp = None
            climate_resp = None

        # Build climate normals summary directly from db_climate or climate_resp
        clim_summary = ClimateNormalsSummary()
        has_climate = False
        if db_climate:
            clim_summary = ClimateNormalsSummary(
                annual_rainfall_mm=db_climate.annual_rainfall_mm,
                monsoon_rainfall_mm=db_climate.monsoon_rainfall_mm,
                mean_temperature_c=db_climate.mean_temperature_c,
                potential_water_stress_indicator=db_climate.potential_water_stress_indicator,
            )
            has_climate = True
        elif climate_resp:
            clim_summary = ClimateNormalsSummary(
                annual_rainfall_mm=climate_resp.annual_rainfall_mm,
                monsoon_rainfall_mm=climate_resp.monsoon_rainfall_mm,
                mean_temperature_c=climate_resp.mean_temperature_c,
                potential_water_stress_indicator=climate_resp.potential_water_stress_indicator,
            )
            has_climate = True

        # Case A: ZERO genuine weather data available
        if not current_obs and not forecast_resp and not has_climate:
            return WeatherDomainSummary(
                availability_state=DataAvailabilityState.NOT_AVAILABLE,
                last_updated=None,
                current_weather=CurrentWeatherSummary(),
                forecast=ForecastSummary(),
                climate_normals=ClimateNormalsSummary(),
            )

        # Build current weather summary
        cur_summary = CurrentWeatherSummary()
        obs_time = None
        obs_age_hours = 0.0
        if current_obs:
            obs_time = current_obs.observation_time
            if obs_time:
                obs_utc = obs_time if obs_time.tzinfo else obs_time.replace(tzinfo=timezone.utc)
                obs_age_hours = max(0.0, (now - obs_utc).total_seconds() / 3600.0)
            cur_summary = CurrentWeatherSummary(
                observation_time=obs_time,
                temperature_c=current_obs.temperature_c,
                humidity_percent=current_obs.humidity_percent,
                precipitation_mm=current_obs.precipitation_mm,
                wind_speed_ms=current_obs.wind_speed_ms,
                weather_condition=current_obs.weather_condition,
                weather_description=current_obs.weather_description,
            )

        # Build forecast summary
        fc_summary = ForecastSummary()
        if forecast_resp:
            summaries = getattr(forecast_resp, "daily_summaries", []) or []
            hourlies = getattr(forecast_resp, "hourly_points", []) or []
            num_days = len(summaries)
            min_t = min((d.temp_min_c for d in summaries), default=None) if num_days > 0 else None
            max_t = max((d.temp_max_c for d in summaries), default=None) if num_days > 0 else None
            rain_48h = sum((getattr(h, "precipitation_mm", 0.0) or 0.0 for h in hourlies[:16]), 0.0)
            fc_summary = ForecastSummary(
                forecast_days_count=num_days,
                next_48h_rain_expected_mm=round(rain_48h, 2),
                temp_min_c=min_t,
                temp_max_c=max_t,
                weather_alerts=[],
            )

        # Freshness & Availability State evaluation
        last_updated = obs_time or now
        if current_obs and obs_age_hours > CURRENT_WEATHER_STALE_HOURS:
            availability_state = DataAvailabilityState.STALE
        elif not current_obs or not forecast_resp or not has_climate:
            availability_state = DataAvailabilityState.PARTIALLY_AVAILABLE
        else:
            availability_state = DataAvailabilityState.AVAILABLE

        return WeatherDomainSummary(
            availability_state=availability_state,
            last_updated=last_updated,
            current_weather=cur_summary,
            forecast=fc_summary,
            climate_normals=clim_summary,
        )
