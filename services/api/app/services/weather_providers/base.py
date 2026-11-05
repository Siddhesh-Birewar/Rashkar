from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

from cropnet.services.api.app.schemas.weather import (
    CurrentWeatherObservation,
    FarmWeatherForecastResponse,
    SeasonalClimateSummary
)


class WeatherDataProvider(ABC):
    """
    Abstract base interface for meteorological and climate data providers.
    Ensures modularity and provider independence.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the data provider (e.g. 'OpenWeather', 'NASA POWER')"""
        pass

    @abstractmethod
    def get_current_weather(
        self,
        farm_id: str,
        latitude: float,
        longitude: float
    ) -> CurrentWeatherObservation:
        """Fetch current observed weather conditions for given coordinates."""
        pass

    @abstractmethod
    def get_forecast(
        self,
        farm_id: str,
        latitude: float,
        longitude: float
    ) -> FarmWeatherForecastResponse:
        """Fetch short-term meteorological forecast."""
        pass

    @abstractmethod
    def get_climate_summary(
        self,
        farm_id: str,
        latitude: float,
        longitude: float
    ) -> SeasonalClimateSummary:
        """Fetch multi-year historical or climatological summary."""
        pass
