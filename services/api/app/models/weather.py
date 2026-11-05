import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship

from cropnet.services.api.app.models.soil_and_farm import Base


class FarmWeatherSnapshotModel(Base):
    """
    Stores observed current weather and forecast snapshots for farm centroids.
    """
    __tablename__ = "farm_weather_snapshots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    farm_id = Column(String(36), ForeignKey("farms.id"), nullable=False, index=True)
    snapshot_type = Column(String(30), nullable=False, index=True) # "current", "forecast"
    source = Column(String(50), nullable=False, default="OpenWeather")
    observation_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Key meteorological metrics
    temperature = Column(Float, nullable=True) # Celsius
    feels_like = Column(Float, nullable=True)
    temperature_min = Column(Float, nullable=True)
    temperature_max = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True) # Percent
    wind_speed = Column(Float, nullable=True) # m/s
    wind_direction = Column(Float, nullable=True) # Degrees
    precipitation_mm = Column(Float, nullable=True, default=0.0) # mm
    
    weather_condition = Column(String(100), nullable=True) # e.g. "Clouds", "Rain", "Clear"
    weather_description = Column(String(255), nullable=True)
    weather_icon = Column(String(50), nullable=True)
    
    payload_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class FarmClimateSummaryModel(Base):
    """
    Stores 30-year historical and climatological summaries from NASA POWER.
    """
    __tablename__ = "farm_climate_summaries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    farm_id = Column(String(36), ForeignKey("farms.id"), nullable=False, index=True)
    source = Column(String(50), nullable=False, default="NASA POWER")
    period_description = Column(String(100), nullable=False, default="30-year Climatology")
    
    annual_rainfall_mm = Column(Float, nullable=False)
    monsoon_rainfall_mm = Column(Float, nullable=False)
    monsoon_share_percent = Column(Float, nullable=False)
    
    mean_temperature_c = Column(Float, nullable=False)
    min_temperature_c = Column(Float, nullable=False)
    max_temperature_c = Column(Float, nullable=False)
    
    rainfall_variability_index = Column(Float, nullable=True)
    potential_water_stress_indicator = Column(String(150), nullable=True)
    
    monthly_rainfall_json = Column(JSON, nullable=False)
    monthly_temperature_json = Column(JSON, nullable=False)
    wet_season_months_json = Column(JSON, nullable=False)
    dry_season_months_json = Column(JSON, nullable=False)
    agricultural_seasons_json = Column(JSON, nullable=True)
    
    payload_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
