"""
Pydantic schemas for Sentinel-2 Satellite-Based Vegetation Intelligence.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class SatelliteObservationQuality(str, Enum):
    VALID_OBSERVATION = "VALID_OBSERVATION"
    CLOUD_OBSTRUCTED = "CLOUD_OBSTRUCTED"
    INSUFFICIENT_PIXELS = "INSUFFICIENT_PIXELS"
    SMALL_FARM_WARNING = "SMALL_FARM_WARNING"
    NO_IMAGERY_AVAILABLE = "NO_IMAGERY_AVAILABLE"


class SatelliteObservationItem(BaseModel):
    id: str
    farm_id: str
    observation_date: datetime
    product_id: str
    tile_id: Optional[str] = None
    sensor: str = "Sentinel-2 L2A"
    mean_ndvi: Optional[float] = Field(None, ge=-1.0, le=1.0)
    median_ndvi: Optional[float] = Field(None, ge=-1.0, le=1.0)
    min_ndvi: Optional[float] = Field(None, ge=-1.0, le=1.0)
    max_ndvi: Optional[float] = Field(None, ge=-1.0, le=1.0)
    std_ndvi: Optional[float] = None
    mean_ndmi: Optional[float] = Field(None, ge=-1.0, le=1.0)
    valid_pixel_count: int
    total_pixel_count: int
    farm_coverage_percent: float
    cloud_masked_percent: float
    spatial_resolution_meters: float = 10.0
    quality_status: SatelliteObservationQuality
    quality_notes: Optional[str] = None
    is_small_farm_warning: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SatelliteSyncRequest(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    max_cloud_cover_percent: float = Field(default=50.0, ge=0.0, le=100.0)


class SatelliteSyncResponse(BaseModel):
    success: bool
    farm_id: str
    synced_observations_count: int
    latest_observation: Optional[SatelliteObservationItem] = None
    copernicus_provider_status: str
    message: str


class VegetationTimeSeriesPoint(BaseModel):
    date: datetime
    mean_ndvi: Optional[float]
    median_ndvi: Optional[float]
    mean_ndmi: Optional[float]
    valid_pixels: int
    cloud_masked_percent: float
    quality_status: str


class VegetationTimeSeriesResponse(BaseModel):
    farm_id: str
    farm_area_hectares: float
    is_small_farm: bool
    total_observations: int
    series: List[VegetationTimeSeriesPoint]
    vegetation_interpretation: str
    scientific_disclaimer: str
