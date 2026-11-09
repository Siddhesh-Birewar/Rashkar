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

    # SCL Class-Segregated & Radiometric Properties parsed from observation metadata
    @property
    def vegetation_pixel_count(self):
        import re
        if not self.quality_notes:
            return None
        m = re.search(r"veg_px:\s*(\d+)", self.quality_notes)
        if m:
            return int(m.group(1))
        m2 = re.search(r"(\d+)\s+vegetation canopy pixels", self.quality_notes)
        return int(m2.group(1)) if m2 else None

    @property
    def bare_soil_pixel_count(self):
        import re
        if not self.quality_notes:
            return None
        m = re.search(r"soil_px:\s*(\d+)", self.quality_notes)
        if m:
            return int(m.group(1))
        m2 = re.search(r"(\d+)\s+bare soil pixels", self.quality_notes)
        return int(m2.group(1)) if m2 else None

    @property
    def water_pixel_count(self):
        import re
        if not self.quality_notes:
            return None
        m = re.search(r"water_px:\s*(\d+)", self.quality_notes)
        return int(m.group(1)) if m else 0

    @property
    def vegetation_coverage_percent(self):
        import re
        if not self.quality_notes:
            return None
        m = re.search(r"vegetation canopy pixels\s*\(([\d\.]+)%\)", self.quality_notes)
        return float(m.group(1)) if m else None

    @property
    def bare_soil_coverage_percent(self):
        import re
        if not self.quality_notes:
            return None
        m = re.search(r"bare soil pixels\s*\(([\d\.]+)%\)", self.quality_notes)
        return float(m.group(1)) if m else None

    @property
    def water_coverage_percent(self):
        return 0.0

    @property
    def vegetation_mean_ndvi(self):
        import re
        if not self.quality_notes:
            return None
        m = re.search(r"veg_ndvi:\s*([\d\.\-]+)", self.quality_notes)
        return float(m.group(1)) if m else None

    @property
    def vegetation_mean_ndmi(self):
        import re
        if not self.quality_notes:
            return None
        m = re.search(r"veg_ndmi:\s*([\d\.\-]+)", self.quality_notes)
        return float(m.group(1)) if m else None

    @property
    def bare_soil_mean_ndvi(self):
        import re
        if not self.quality_notes:
            return None
        m = re.search(r"soil_ndvi:\s*([\d\.\-]+)", self.quality_notes)
        return float(m.group(1)) if m else None

    @property
    def polygon_area_hectares(self):
        import re
        if not self.quality_notes:
            return None
        m = re.search(r"poly_ha:\s*([\d\.]+)", self.quality_notes)
        return float(m.group(1)) if m else None

    @property
    def raster_discretized_area_hectares(self):
        import re
        if not self.quality_notes:
            return round(self.total_pixel_count * 0.01, 3) if self.total_pixel_count else None
        m = re.search(r"raster_ha:\s*([\d\.]+)", self.quality_notes)
        return float(m.group(1)) if m else (round(self.total_pixel_count * 0.01, 3) if self.total_pixel_count else None)

    @property
    def radiometric_conversion_provenance(self):
        import re
        if not self.quality_notes:
            return "HARMONIZED_COG_BOA_OFFSET_ALREADY_APPLIED"
        m = re.search(r"rad:\s*([A-Za-z0-9_]+)", self.quality_notes)
        return m.group(1) if m else "HARMONIZED_COG_BOA_OFFSET_ALREADY_APPLIED"

    @property
    def data_attribution(self):
        return "Copernicus Sentinel data [2026], processed by ESA, hosted on AWS by Element 84."
