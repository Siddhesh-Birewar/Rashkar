import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PROJECT_NAME: str = "Rashkar Climate-Smart Agriculture Platform"
    API_V1_STR: str = "/v1"
    SECRET_KEY: str = "development-secret-key-change-in-production-rashkar"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Standard Timezone
    TIMEZONE: str = "Asia/Kolkata"

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "rashkar_admin"
    POSTGRES_PASSWORD: str = "rashkar_secure_password"
    POSTGRES_DB: str = "rashkar_db"
    DATABASE_URL: Optional[str] = None
    SQLITE_DB_PATH: str = "rashkar_dev.db"

    # Redis & Celery
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # External APIs
    IMD_API_BASE_URL: str = "https://api.imd.gov.in/public"
    IMD_API_TOKEN: Optional[str] = None
    CDSAPI_URL: Optional[str] = None
    CDSAPI_KEY: Optional[str] = None

    # CropNet
    CROPNET_API_BASE_URL: str = "http://localhost:8080/api/v1"
    CROPNET_API_TOKEN: Optional[str] = None
    USE_CROPNET_MOCK: bool = True

    # Directories
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    RAW_DATA_DIR: Path = BASE_DIR / "data" / "01_raw_immutable"
    PROCESSED_DATA_DIR: Path = BASE_DIR / "data" / "02_processed"
    FEATURE_DATA_DIR: Path = BASE_DIR / "data" / "03_features"
    FIXTURES_DATA_DIR: Path = BASE_DIR / "data" / "05_fixtures"

    @property
    def sync_database_url(self) -> str:
        if self.DATABASE_URL:
            # Replace asyncpg with standard psycopg2 if present
            return self.DATABASE_URL.replace("+asyncpg", "")
        # Check if Postgres is likely available or default to SQLite for seamless local dev
        pg_url = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        return pg_url

    @property
    def fallback_sqlite_url(self) -> str:
        return f"sqlite:///{BASE_DIR / self.SQLITE_DB_PATH}"

settings = Settings()
