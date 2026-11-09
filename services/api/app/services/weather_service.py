import uuid
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from shapely.geometry import shape

from cropnet.services.api.app.models.soil_and_farm import FarmModel
from cropnet.services.api.app.models.weather import (
    FarmWeatherSnapshotModel,
    FarmClimateSummaryModel
)
from cropnet.services.api.app.schemas.weather import (
    CurrentWeatherObservation,
    FarmWeatherForecastResponse,
    SeasonalClimateSummary,
    HistoricalWeatherRecord
)
from cropnet.services.api.app.services.weather_providers.openweather import OpenWeatherProvider
from cropnet.services.api.app.services.weather_providers.nasa_power import NASAPowerProvider

logger = logging.getLogger(__name__)

# In-memory caches for fast local dev & test isolation
_CURRENT_WEATHER_CACHE: Dict[str, Dict[str, Any]] = {} # farm_id -> { "data": CurrentWeatherObservation, "cached_at": datetime }
_FORECAST_CACHE: Dict[str, Dict[str, Any]] = {} # farm_id -> { "data": FarmWeatherForecastResponse, "cached_at": datetime }
_CLIMATE_CACHE: Dict[str, Dict[str, Any]] = {} # farm_id -> { "data": SeasonalClimateSummary, "cached_at": datetime }


class WeatherService:
    """
    Orchestration service for farm-specific weather, forecasts, and climate summaries.
    Enforces sensible caching policies and PostgreSQL database persistence.
    """

    CURRENT_WEATHER_TTL_MINUTES = 20
    FORECAST_TTL_HOURS = 3
    CLIMATE_TTL_DAYS = 30

    def __init__(self):
        self.openweather_provider = OpenWeatherProvider()
        self.nasa_power_provider = NASAPowerProvider()

    def _extract_farm_coordinates(self, farm: Dict[str, Any]) -> tuple[float, float]:
        """
        Extract representative centroid latitude and longitude from farm dictionary or model.
        """
        lat = farm.get("centroid_latitude") or farm.get("latitude")
        lon = farm.get("centroid_longitude") or farm.get("longitude")

        if lat is not None and lon is not None:
            return float(lat), float(lon)

        # Fallback to computing centroid from geometry if present
        geom = farm.get("geometry") or farm.get("geometry_geojson")
        if geom and "coordinates" in geom:
            try:
                poly = shape(geom)
                centroid = poly.centroid
                return round(centroid.y, 6), round(centroid.x, 6)
            except Exception as e:
                logger.warning("Failed to derive centroid from polygon geometry: %s", e)

        # Regional fallback: Baramati pilot center
        return 18.18, 74.53

    # ==========================================
    # 1. CURRENT WEATHER
    # ==========================================
    def get_current_weather(
        self,
        farm: Dict[str, Any],
        db: Optional[Session] = None,
        force_refresh: bool = False
    ) -> CurrentWeatherObservation:
        """
        Retrieve live observed weather. Uses cached snapshot if fresher than 20 minutes.
        """
        farm_id = str(farm["id"])
        now = datetime.now(timezone.utc)

        # 1. Check in-memory cache
        if not force_refresh and farm_id in _CURRENT_WEATHER_CACHE:
            entry = _CURRENT_WEATHER_CACHE[farm_id]
            cached_at = entry["cached_at"]
            age_sec = int((now - cached_at).total_seconds())
            if age_sec < (self.CURRENT_WEATHER_TTL_MINUTES * 60):
                cached_obs: CurrentWeatherObservation = entry["data"]
                return cached_obs.model_copy(update={"is_cached": True, "cache_age_seconds": age_sec})

        # 2. Check Database if available
        if not force_refresh and db is not None:
            try:
                latest_db = (
                    db.query(FarmWeatherSnapshotModel)
                    .filter(
                        FarmWeatherSnapshotModel.farm_id == farm_id,
                        FarmWeatherSnapshotModel.snapshot_type == "current"
                    )
                    .order_by(FarmWeatherSnapshotModel.observation_time.desc())
                    .first()
                )
                if latest_db:
                    db_time = latest_db.observation_time.replace(tzinfo=timezone.utc) if latest_db.observation_time.tzinfo is None else latest_db.observation_time
                    age_sec = int((now - db_time).total_seconds())
                    if age_sec < (self.CURRENT_WEATHER_TTL_MINUTES * 60):
                        obs = CurrentWeatherObservation(
                            farm_id=farm_id,
                            source=latest_db.source,
                            data_type="observed",
                            observation_time=db_time,
                            retrieval_time=now,
                            temperature_c=latest_db.temperature or 25.0,
                            feels_like_c=latest_db.feels_like or 25.0,
                            temperature_min_c=latest_db.temperature_min or 20.0,
                            temperature_max_c=latest_db.temperature_max or 30.0,
                            humidity_percent=latest_db.humidity or 50.0,
                            wind_speed_ms=latest_db.wind_speed or 2.0,
                            wind_direction_deg=latest_db.wind_direction,
                            precipitation_mm=latest_db.precipitation_mm or 0.0,
                            weather_condition=latest_db.weather_condition or "Clouds",
                            weather_description=latest_db.weather_description or "cloudy",
                            weather_icon=latest_db.weather_icon or "03d",
                            is_cached=True,
                            cache_age_seconds=age_sec
                        )
                        _CURRENT_WEATHER_CACHE[farm_id] = {"data": obs, "cached_at": now - timedelta(seconds=age_sec)}
                        return obs
            except Exception as e:
                logger.debug("DB current weather lookup error: %s", e)

        # 3. Query Provider Live
        lat, lon = self._extract_farm_coordinates(farm)
        observation = self.openweather_provider.get_current_weather(farm_id, lat, lon)

        # 4. Cache in memory
        _CURRENT_WEATHER_CACHE[farm_id] = {"data": observation, "cached_at": now}

        # 5. Persist to Database
        if db is not None:
            try:
                db_model = FarmWeatherSnapshotModel(
                    id=str(uuid.uuid4()),
                    farm_id=farm_id,
                    snapshot_type="current",
                    source=observation.source,
                    observation_time=observation.observation_time,
                    temperature=observation.temperature_c,
                    feels_like=observation.feels_like_c,
                    temperature_min=observation.temperature_min_c,
                    temperature_max=observation.temperature_max_c,
                    humidity=observation.humidity_percent,
                    wind_speed=observation.wind_speed_ms,
                    wind_direction=observation.wind_direction_deg,
                    precipitation_mm=observation.precipitation_mm,
                    weather_condition=observation.weather_condition,
                    weather_description=observation.weather_description,
                    weather_icon=observation.weather_icon,
                    created_at=datetime.utcnow()
                )
                db.add(db_model)
                db.commit()
            except Exception as e:
                logger.warning("Failed to persist weather snapshot to DB: %s", e)
                db.rollback()

        return observation

    # ==========================================
    # 2. SHORT-TERM FORECAST
    # ==========================================
    def get_forecast(
        self,
        farm: Dict[str, Any],
        db: Optional[Session] = None,
        force_refresh: bool = False
    ) -> FarmWeatherForecastResponse:
        """
        Retrieve 5-day / 3-hour forecast. Uses cached forecast if fresher than 3 hours.
        """
        farm_id = str(farm["id"])
        now = datetime.now(timezone.utc)

        # 1. Check in-memory cache
        if not force_refresh and farm_id in _FORECAST_CACHE:
            entry = _FORECAST_CACHE[farm_id]
            age_sec = (now - entry["cached_at"]).total_seconds()
            if age_sec < (self.FORECAST_TTL_HOURS * 3600):
                cached_fc: FarmWeatherForecastResponse = entry["data"]
                return cached_fc.model_copy(update={"is_cached": True})

        # 2. Query Provider Live
        lat, lon = self._extract_farm_coordinates(farm)
        forecast_resp = self.openweather_provider.get_forecast(farm_id, lat, lon)

        # 3. Cache in memory
        _FORECAST_CACHE[farm_id] = {"data": forecast_resp, "cached_at": now}

        # 4. Persist forecast snapshot to database
        if db is not None:
            try:
                first_summary = forecast_resp.daily_summaries[0] if forecast_resp.daily_summaries else None
                db_model = FarmWeatherSnapshotModel(
                    id=str(uuid.uuid4()),
                    farm_id=farm_id,
                    snapshot_type="forecast",
                    source=forecast_resp.source,
                    observation_time=forecast_resp.retrieval_time,
                    temperature=first_summary.temp_max_c if first_summary else None,
                    temperature_min=first_summary.temp_min_c if first_summary else None,
                    temperature_max=first_summary.temp_max_c if first_summary else None,
                    humidity=first_summary.humidity_percent if first_summary else None,
                    precipitation_mm=first_summary.total_rain_mm if first_summary else None,
                    weather_condition=first_summary.weather_condition if first_summary else None,
                    weather_description=first_summary.weather_description if first_summary else None,
                    weather_icon=first_summary.weather_icon if first_summary else None,
                    payload_json=forecast_resp.model_dump(mode="json"),
                    created_at=datetime.utcnow()
                )
                db.add(db_model)
                db.commit()
            except Exception as e:
                logger.debug("Failed to persist forecast to DB: %s", e)
                db.rollback()

        return forecast_resp

    # ==========================================
    # 3. SEASONAL CLIMATE SUMMARY (NASA POWER)
    # ==========================================
    def get_climate_summary(
        self,
        farm: Dict[str, Any],
        db: Optional[Session] = None,
        force_refresh: bool = False
    ) -> SeasonalClimateSummary:
        """
        Retrieve 30-year agro-climate summary from NASA POWER.
        Cached heavily (30 days) to prevent redundant queries.
        """
        farm_id = str(farm["id"])
        now = datetime.now(timezone.utc)

        # 1. Check in-memory cache
        if not force_refresh and farm_id in _CLIMATE_CACHE:
            entry = _CLIMATE_CACHE[farm_id]
            age_days = (now - entry["cached_at"]).days
            if age_days < self.CLIMATE_TTL_DAYS:
                cached_cl: SeasonalClimateSummary = entry["data"]
                return cached_cl.model_copy(update={"is_cached": True})

        # 2. Check Database
        if not force_refresh and db is not None:
            try:
                db_climate = (
                    db.query(FarmClimateSummaryModel)
                    .filter(FarmClimateSummaryModel.farm_id == farm_id)
                    .order_by(FarmClimateSummaryModel.created_at.desc())
                    .first()
                )
                if db_climate and db_climate.payload_json:
                    summary = SeasonalClimateSummary.model_validate(db_climate.payload_json)
                    _CLIMATE_CACHE[farm_id] = {"data": summary, "cached_at": now}
                    return summary.model_copy(update={"is_cached": True})
            except Exception as e:
                logger.debug("DB climate lookup error: %s", e)

        # 3. Query Provider Live
        lat, lon = self._extract_farm_coordinates(farm)
        climate_summary = self.nasa_power_provider.get_climate_summary(farm_id, lat, lon)

        # 4. Cache in memory
        _CLIMATE_CACHE[farm_id] = {"data": climate_summary, "cached_at": now}

        # 5. Persist to Database
        if db is not None:
            try:
                db_summary = FarmClimateSummaryModel(
                    id=str(uuid.uuid4()),
                    farm_id=farm_id,
                    source=climate_summary.source,
                    period_description=climate_summary.period_description,
                    annual_rainfall_mm=climate_summary.annual_rainfall_mm,
                    monsoon_rainfall_mm=climate_summary.monsoon_rainfall_mm,
                    monsoon_share_percent=climate_summary.monsoon_share_percent,
                    mean_temperature_c=climate_summary.mean_temperature_c,
                    min_temperature_c=climate_summary.min_temperature_c,
                    max_temperature_c=climate_summary.max_temperature_c,
                    rainfall_variability_index=climate_summary.rainfall_variability_index,
                    potential_water_stress_indicator=climate_summary.potential_water_stress_indicator,
                    monthly_rainfall_json={p.month_name: p.rainfall_mm for p in climate_summary.monthly_climate},
                    monthly_temperature_json={p.month_name: {"mean": p.mean_temp_c, "min": p.min_temp_c, "max": p.max_temp_c} for p in climate_summary.monthly_climate},
                    wet_season_months_json=climate_summary.wet_season_months,
                    dry_season_months_json=climate_summary.dry_season_months,
                    agricultural_seasons_json=[s.model_dump(mode="json") for s in climate_summary.agricultural_seasons],
                    payload_json=climate_summary.model_dump(mode="json"),
                    created_at=datetime.utcnow()
                )
                db.add(db_summary)
                db.commit()
            except Exception as e:
                logger.warning("Failed to persist climate summary to DB: %s", e)
                db.rollback()

        return climate_summary

    # ==========================================
    # 4. WEATHER OBSERVATION HISTORY
    # ==========================================
    def get_weather_history(
        self,
        farm_id: str,
        db: Optional[Session] = None,
        limit: int = 50
    ) -> List[HistoricalWeatherRecord]:
        """
        Retrieve stored historical weather snapshots for a farm.
        """
        records: List[HistoricalWeatherRecord] = []
        if db is not None:
            try:
                db_rows = (
                    db.query(FarmWeatherSnapshotModel)
                    .filter(FarmWeatherSnapshotModel.farm_id == farm_id)
                    .order_by(FarmWeatherSnapshotModel.observation_time.desc())
                    .limit(limit)
                    .all()
                )
                for row in db_rows:
                    records.append(HistoricalWeatherRecord(
                        id=row.id,
                        farm_id=row.farm_id,
                        snapshot_type=row.snapshot_type,
                        source=row.source,
                        observation_time=row.observation_time,
                        temperature=row.temperature,
                        humidity=row.humidity,
                        wind_speed=row.wind_speed,
                        precipitation_mm=row.precipitation_mm,
                        weather_condition=row.weather_condition,
                        created_at=row.created_at
                    ))
            except Exception as e:
                logger.debug("Failed to query weather history from DB: %s", e)

        return records
