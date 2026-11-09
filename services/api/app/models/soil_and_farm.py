import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class FarmModel(Base):
    __tablename__ = "farms"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String(36), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    village = Column(String(100), nullable=True)
    taluka = Column(String(100), nullable=False, index=True)
    district = Column(String(100), nullable=False, default="Pune")
    state = Column(String(100), nullable=False, default="Maharashtra")
    irrigation_type = Column(String(50), default="unknown")
    water_source = Column(String(50), default="unknown")
    
    # Stored as GeoJSON in SQLite / Geometry(Polygon, 4326) in PostGIS
    geometry_geojson = Column(JSON, nullable=False)
    calculated_area_hectares = Column(Float, nullable=False)
    calculated_area_acres = Column(Float, nullable=False)
    centroid_latitude = Column(Float, nullable=True)
    centroid_longitude = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profiles = relationship("FarmSoilProfileModel", back_populates="farm", cascade="all, delete-orphan")


class SoilDataSourceModel(Base):
    __tablename__ = "soil_data_sources"

    id = Column(String(50), primary_key=True) # e.g. 'isric_soilgrids', 'openlandmap'
    name = Column(String(100), nullable=False)
    organization = Column(String(150), nullable=False)
    portal_url = Column(String(255), nullable=True)
    dataset_version = Column(String(50), nullable=False)
    license = Column(String(100), nullable=False)
    attribution = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)


class SoilMapLayerModel(Base):
    __tablename__ = "soil_map_layers"

    id = Column(String(100), primary_key=True) # e.g. 'soilgrids_phh2o_0-5cm'
    source_id = Column(String(50), ForeignKey("soil_data_sources.id"), nullable=False)
    parameter_key = Column(String(50), nullable=False, index=True)
    layer_name = Column(String(100), nullable=False)
    spatial_resolution = Column(String(50), nullable=False)
    depth_interval = Column(String(50), nullable=False)
    unit = Column(String(30), nullable=False)
    vintage_year = Column(Integer, nullable=True)
    has_uncertainty = Column(Boolean, default=False)


class FarmSoilProfileModel(Base):
    __tablename__ = "farm_soil_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    farm_id = Column(String(36), ForeignKey("farms.id"), nullable=False, index=True)
    version = Column(Integer, default=1)
    is_map_derived = Column(Boolean, default=True)
    disclaimer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    farm = relationship("FarmModel", back_populates="profiles")
    parameters = relationship("SoilParameterModel", back_populates="profile", cascade="all, delete-orphan")


class SoilParameterModel(Base):
    __tablename__ = "soil_parameters"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String(36), ForeignKey("farm_soil_profiles.id"), nullable=False, index=True)
    parameter_key = Column(String(50), nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    value = Column(Float, nullable=True)
    unit = Column(String(30), nullable=False)
    source = Column(String(100), nullable=False)
    dataset_version = Column(String(50), nullable=False)
    depth_interval = Column(String(50), nullable=False)
    spatial_resolution = Column(String(50), nullable=False)
    vintage_year = Column(Integer, nullable=True)
    uncertainty = Column(Float, nullable=True)
    verification_status = Column(String(50), nullable=False)
    availability_status = Column(String(50), nullable=False)
    farm_coverage_percent = Column(Float, default=100.0)
    scientific_note = Column(Text, nullable=True)

    profile = relationship("FarmSoilProfileModel", back_populates="parameters")


class FarmDecisionModel(Base):
    __tablename__ = "farm_decisions"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), nullable=True, index=True)
    farm_id = Column(String(64), nullable=True, index=True)
    input_validation_status = Column(String(64), nullable=True)
    target_season = Column(String(64), nullable=True)
    context_json = Column(JSON, nullable=False)
    decision_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
