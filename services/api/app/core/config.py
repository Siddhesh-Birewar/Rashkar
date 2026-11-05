import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    APP_NAME: str = "CropNet AI Backend"
    API_V1_PREFIX: str = "/api/v1"
    LOG_LEVEL: str = "INFO"

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    # Supabase Configuration
    SUPABASE_AUTH_ENABLED: bool = True
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SECRET_KEY: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None
    SUPABASE_DB_PASSWORD: Optional[str] = None
    SUPABASE_PROJECT_REF: Optional[str] = None
    
    DEV_USER_ID: str = "00000000-0000-0000-0000-000000000001"
    DEV_USER_EMAIL: str = "dev@cropnet.local"

    # Database URLs
    DATABASE_URL: str = "postgresql+asyncpg://postgres:rAO6B8K2yQzFXlw8@db.glnpmpagajfurpmlinvd.supabase.co:5432/postgres"
    SYNC_DATABASE_URL: str = "postgresql://postgres:rAO6B8K2yQzFXlw8@db.glnpmpagajfurpmlinvd.supabase.co:5432/postgres"

    # Weather Provider (OpenWeather)
    OPENWEATHER_API_KEY: Optional[str] = None
    OPENWEATHER_API_KEY_FALLBACK: Optional[str] = None

    # Map Tile Provider (MapTiler)
    MAPTILER_API_KEY: Optional[str] = None
    MAPTILER_API_KEY_FALLBACK: Optional[str] = None

    # External Soil GIS Services
    SOILGRIDS_WCS_BASE_URL: str = "https://maps.isric.org/mapserv"
    SOILGRIDS_TIMEOUT_SECONDS: int = 25
    OPENLANDMAP_BASE_URL: str = "http://s3.opengeohub.org/global-soil/global_soil_props_v20250204_mosaics"
    BHOOMI_GEOSERVER_URL: str = "https://bhoomigeoportal-nbsslup.in/geoserver"
    NATMO_PORTAL_URL: str = "https://geoportal.natmo.gov.in"

    # Feature Flags
    ENABLE_LOCAL_RASTER_CACHE: bool = True
    LOCAL_RASTER_CACHE_DIR: str = "./data_cache/rasters"
    ENABLE_ECONOMIC_RANKING: bool = False
    ENABLE_YIELD_PREDICTION: bool = False

    model_config = SettingsConfigDict(
        env_file=[
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), ".env"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), ".env"),
            ".env"
        ],
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
