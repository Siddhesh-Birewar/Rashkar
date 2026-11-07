"""
SQLAlchemy models for Sentinel-2 Satellite-Based Vegetation Intelligence.

Preserves:
- Copernicus Sentinel-2 Level-2A surface reflectance observations
- Spatial polygon intersection metadata
- Cloud and shadow masking (SCL classes 3, 8, 9, 10, 11)
- Computed canopy reflectance indices (NDVI at 10m, NDMI resampled at 10m)
- Farm-level statistics (mean, median, min, max, std)
- Small farm spatial representativeness safeguards (<0.5 ha / <5 pixels)
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship

try:
    from cropnet.services.api.app.models.soil_and_farm import Base, FarmModel
except ImportError:
    from .soil_and_farm import Base, FarmModel


class SatelliteVegetationObservationModel(Base):
    """
    Time-series Sentinel-2 Level-2A observation intersected with a farm boundary.
    """
    __tablename__ = "satellite_vegetation_observations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    farm_id = Column(String(36), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True)

    # Observation metadata
    observation_date = Column(DateTime, nullable=False, index=True)
    product_id = Column(String(120), nullable=False)
    tile_id = Column(String(50), nullable=True)
    sensor = Column(String(30), default="Sentinel-2 L2A", nullable=False)
    processing_baseline = Column(String(30), default="N0500", nullable=True)

    # Vegetation Indices (Canopy Reflectance)
    # NDVI = (B08 - B04) / (B08 + B04)
    mean_ndvi = Column(Float, nullable=True)
    median_ndvi = Column(Float, nullable=True)
    min_ndvi = Column(Float, nullable=True)
    max_ndvi = Column(Float, nullable=True)
    std_ndvi = Column(Float, nullable=True)

    # Normalized Difference Moisture Index (NDMI) = (B08 - B11) / (B08 + B11)
    mean_ndmi = Column(Float, nullable=True)

    # Spatial & Pixel Statistics
    valid_pixel_count = Column(Integer, nullable=False, default=0)
    total_pixel_count = Column(Integer, nullable=False, default=0)
    farm_coverage_percent = Column(Float, nullable=False, default=100.0)
    cloud_masked_percent = Column(Float, nullable=False, default=0.0)
    spatial_resolution_meters = Column(Float, nullable=False, default=10.0)

    # Quality & Agronomic Safeguard Statuses
    # Statuses: VALID_OBSERVATION, CLOUD_OBSTRUCTED, INSUFFICIENT_PIXELS, SMALL_FARM_WARNING
    quality_status = Column(String(50), nullable=False, default="VALID_OBSERVATION", index=True)
    quality_notes = Column(Text, nullable=True)
    is_small_farm_warning = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    farm = relationship("FarmModel")
