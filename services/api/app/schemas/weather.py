from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class CurrentWeatherObservation(BaseModel):
    """
    Real-time observed meteorological data for farm centroid.
    """
    farm_id: str
    source: str = Field(default="OpenWeather", description="Data provider name")
    data_type: str = Field(default="observed", description="Data classification: observed | forecast | historical_reanalysis")
    observation_time: datetime = Field(..., description="Timestamp of provider measurement")
    retrieval_time: datetime = Field(default_factory=datetime.utcnow, description="Timestamp CropNet retrieved data")
    
    # Measurements in metric units
    temperature_c: float = Field(..., description="Current ambient temperature in Celsius")
    feels_like_c: float = Field(..., description="Human perceived temperature in Celsius")
    temperature_min_c: float = Field(..., description="Minimum daily temperature in Celsius")
    temperature_max_c: float = Field(..., description="Maximum daily temperature in Celsius")
    humidity_percent: float = Field(..., description="Relative humidity percentage (0-100%)")
    wind_speed_ms: float = Field(..., description="Wind speed in meters per second")
    wind_direction_deg: Optional[float] = Field(None, description="Wind direction in degrees")
    precipitation_mm: float = Field(default=0.0, description="Precipitation accumulation in mm (last 1-3 hrs)")
    
    # Conditions and Display
    weather_condition: str = Field(..., description="Primary weather condition (e.g. Clouds, Clear, Rain)")
    weather_description: str = Field(..., description="Detailed condition (e.g. scattered clouds)")
    weather_icon: str = Field(..., description="Icon identifier code")
    
    # Caching Transparency
    is_cached: bool = Field(default=False, description="Whether returned from local cache")
    cache_age_seconds: Optional[int] = Field(None, description="Seconds since observation was fetched from provider")


class WeatherForecastPoint(BaseModel):
    """
    3-hour interval forecast point.
    """
    forecast_time: datetime
    temperature_c: float
    temp_min_c: float
    temp_max_c: float
    humidity_percent: float
    wind_speed_ms: float
    precipitation_probability_pct: float
    precipitation_mm: float
    weather_condition: str
    weather_description: str
    weather_icon: str


class DailyForecastSummary(BaseModel):
    """
    Aggregated daily summary for farm forecast card.
    """
    date: str
    day_name: str
    temp_min_c: float
    temp_max_c: float
    humidity_percent: float
    weather_condition: str
    weather_description: str
    weather_icon: str
    total_rain_mm: float
    max_pop_pct: float


class FarmWeatherForecastResponse(BaseModel):
    """
    Short-term meteorological forecast response.
    """
    farm_id: str
    source: str = "OpenWeather"
    data_type: str = "forecast"
    retrieval_time: datetime = Field(default_factory=datetime.utcnow)
    forecast_period: str = "5 days (3-hour resolution)"
    daily_summaries: List[DailyForecastSummary]
    hourly_points: List[WeatherForecastPoint]
    is_cached: bool = False


class MonthlyClimatePoint(BaseModel):
    """
    Monthly climatological average for long-term planning.
    """
    month_num: int = Field(..., ge=1, le=12)
    month_name: str
    rainfall_mm: float = Field(..., description="Average monthly rainfall in mm")
    mean_temp_c: float = Field(..., description="Mean 2m temperature in Celsius")
    min_temp_c: float = Field(..., description="Average daily minimum temperature in Celsius")
    max_temp_c: float = Field(..., description="Average daily maximum temperature in Celsius")


class AgriculturalSeasonSummary(BaseModel):
    """
    Deterministic agro-climatic seasonal classification.
    """
    season_name: str # Kharif, Rabi, Zaid
    period_months: str # e.g. "June – October"
    total_rainfall_mm: float
    mean_temperature_c: float
    water_stress_status: str # "Adequate Rainfed Moisture", "Moderate Water Stress", "High Water Stress"
    description: str


class SeasonalClimateSummary(BaseModel):
    """
    Farm-specific 30-year agro-climate summary from NASA POWER.
    Input to the downstream Crop Recommendation Engine.
    """
    farm_id: str
    source: str = "NASA POWER"
    data_type: str = "historical_reanalysis"
    period_description: str = "30-year Meteorological Climatology (1991–2020)"
    retrieval_time: datetime = Field(default_factory=datetime.utcnow)
    
    # Rainfall Metrics
    annual_rainfall_mm: float
    monsoon_rainfall_mm: float
    monsoon_share_percent: float
    wet_season_months: List[str]
    dry_season_months: List[str]
    
    # Temperature Metrics
    mean_temperature_c: float
    min_temperature_c: float
    max_temperature_c: float
    temperature_range_c: float
    
    # Agro-Climatic Indicators
    rainfall_variability_index: float
    potential_water_stress_indicator: str
    
    # Monthly Breakdown & Indian Agricultural Seasons
    monthly_climate: List[MonthlyClimatePoint]
    agricultural_seasons: List[AgriculturalSeasonSummary]
    
    is_cached: bool = False
    disclaimer: str = Field(
        default="Climate summaries are derived from NASA POWER satellite reanalysis (0.5° x 0.5° grid). "
                "These values reflect 30-year regional climatological normals and are not micro-climate guarantees.",
        description="Farmer-facing transparency disclaimer."
    )


class HistoricalWeatherRecord(BaseModel):
    """
    Stored historical observation or snapshot record.
    """
    id: str
    farm_id: str
    snapshot_type: str
    source: str
    observation_time: datetime
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    wind_speed: Optional[float] = None
    precipitation_mm: Optional[float] = None
    weather_condition: Optional[str] = None
    created_at: datetime
