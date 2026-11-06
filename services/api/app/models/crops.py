import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship

from cropnet.services.api.app.models.soil_and_farm import Base


class AgriculturalKnowledgeSourceModel(Base):
    """
    Authoritative scientific publications, research institutes, and university references.
    """
    __tablename__ = "agricultural_knowledge_sources"

    id = Column(String(50), primary_key=True) # e.g. 'mpkv_pop_2023', 'icar_iisr_sugarcane_2022'
    organization = Column(String(150), nullable=False) # e.g. 'Mahatma Phule Krishi Vidyapeeth (MPKV), Rahuri'
    publication_title = Column(String(255), nullable=False) # e.g. 'Package of Practices for Field Crops'
    publication_year = Column(Integer, nullable=True)
    document_url_or_ref = Column(Text, nullable=True)
    section_or_pages = Column(String(100), nullable=True)
    evidence_quality = Column(String(50), default="verified_authoritative")
    last_verified_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    crops = relationship("CropCatalogModel", back_populates="primary_source")


class CropCatalogModel(Base):
    """
    Master agricultural crop catalogue.
    """
    __tablename__ = "crop_catalog"

    id = Column(String(50), primary_key=True) # e.g. 'sugarcane', 'pomegranate', 'soybean'
    common_name = Column(String(100), nullable=False)
    scientific_name = Column(String(150), nullable=False)
    marathi_name = Column(String(100), nullable=True)
    hindi_name = Column(String(100), nullable=True)
    category = Column(String(50), nullable=False, index=True) # Cash Crop, Cereal, Pulse, Oilseed, Fiber, Horticulture
    crop_type = Column(String(50), nullable=False) # Perennial, Annual Kharif, Annual Rabi
    typical_duration_days_min = Column(Integer, nullable=True)
    typical_duration_days_max = Column(Integer, nullable=True)
    recommended_varieties = Column(JSON, nullable=True) # List of MPKV/ICAR approved cultivars
    source_id = Column(String(50), ForeignKey("agricultural_knowledge_sources.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    primary_source = relationship("AgriculturalKnowledgeSourceModel", back_populates="crops")
    soil_requirements = relationship("CropSoilRequirementModel", back_populates="crop", uselist=False, cascade="all, delete-orphan")
    climate_requirements = relationship("CropClimateRequirementModel", back_populates="crop", uselist=False, cascade="all, delete-orphan")
    season_requirements = relationship("CropSeasonRequirementModel", back_populates="crop", cascade="all, delete-orphan")
    water_requirements = relationship("CropWaterRequirementModel", back_populates="crop", uselist=False, cascade="all, delete-orphan")
    regional_suitability = relationship("CropRegionalSuitabilityModel", back_populates="crop", cascade="all, delete-orphan")


class CropSoilRequirementModel(Base):
    """
    Detailed, unit-aware soil properties and tolerances for each crop.
    """
    __tablename__ = "crop_soil_requirements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    crop_id = Column(String(50), ForeignKey("crop_catalog.id"), nullable=False, unique=True, index=True)
    preferred_textures = Column(JSON, nullable=False) # List of USDA texture classes e.g. ["Clay Loam", "Clay"]
    acceptable_textures = Column(JSON, nullable=False) # Tolerable texture classes
    ph_optimum_min = Column(Float, nullable=True) # Nullable where optimum is texture-specific (deprecated as universal)
    ph_optimum_max = Column(Float, nullable=True)
    ph_best_suited_min = Column(Float, nullable=True) # Best-suited pH min for specific qualifying soil textures
    ph_best_suited_max = Column(Float, nullable=True) # Best-suited pH max for specific qualifying soil textures
    ph_tolerable_min = Column(Float, nullable=True) # Nullable for crops where lower tolerable limit is unverified
    ph_tolerable_max = Column(Float, nullable=True) # Nullable for crops where upper tolerable limit is unverified
    ph_context_notes = Column(Text, nullable=True) # Textual provenance explaining pH bounds and specific soil associations
    best_suited_soil_textures = Column(JSON, nullable=True) # Textures where best-suited pH strictly applies e.g. ["Deep Loam", "Silty Clay Loam"]
    drainage_requirement = Column(Text, nullable=False)
    salinity_sensitivity = Column(Text, nullable=False)
    min_soil_depth_cm = Column(Float, nullable=False)
    optimum_organic_carbon_g_kg = Column(Float, nullable=True)
    water_holding_capacity_pref = Column(String(100), nullable=True)
    evidence_status = Column(String(50), default="derived", nullable=True)
    unverified_parameters = Column(JSON, nullable=True)
    source_id = Column(String(50), ForeignKey("agricultural_knowledge_sources.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    crop = relationship("CropCatalogModel", back_populates="soil_requirements")


class CropClimateRequirementModel(Base):
    """
    Detailed thermal, solar, and precipitation tolerances.
    """
    __tablename__ = "crop_climate_requirements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    crop_id = Column(String(50), ForeignKey("crop_catalog.id"), nullable=False, unique=True, index=True)
    temp_optimum_min_c = Column(Float, nullable=False)
    temp_optimum_max_c = Column(Float, nullable=False)
    temp_tolerable_min_c = Column(Float, nullable=False)
    temp_tolerable_max_c = Column(Float, nullable=False)
    annual_rainfall_min_mm = Column(Float, nullable=True)
    annual_rainfall_max_mm = Column(Float, nullable=True)
    humidity_preference = Column(String(150), nullable=True)
    frost_sensitivity = Column(Text, nullable=False)
    heat_sensitivity = Column(Text, nullable=False)
    thermal_threshold_context = Column(Text, nullable=True) # Explanatory context for thermal sensitivity e.g. reproductive stage vs vegetative
    solar_radiation_requirement = Column(String(150), nullable=True)
    evidence_status = Column(String(50), default="derived", nullable=True)
    source_id = Column(String(50), ForeignKey("agricultural_knowledge_sources.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    crop = relationship("CropCatalogModel", back_populates="climate_requirements")


class CropSeasonRequirementModel(Base):
    """
    Cropping season calendar and regional planting windows across Maharashtra.
    """
    __tablename__ = "crop_season_requirements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    crop_id = Column(String(50), ForeignKey("crop_catalog.id"), nullable=False, index=True)
    season_name = Column(String(50), nullable=False, index=True) # Kharif, Rabi, Zaid, Suru, Adsali
    is_primary_season = Column(Boolean, default=True)
    planting_window_maharashtra = Column(String(150), nullable=False)
    harvesting_window_maharashtra = Column(String(150), nullable=False)
    duration_days_min = Column(Integer, nullable=False)
    duration_days_max = Column(Integer, nullable=False)
    planting_calendar_by_region = Column(JSON, nullable=True)
    source_id = Column(String(50), ForeignKey("agricultural_knowledge_sources.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    crop = relationship("CropCatalogModel", back_populates="season_requirements")


class CropWaterRequirementModel(Base):
    """
    Irrigation, water consumption, and moisture sensitivity profile.
    """
    __tablename__ = "crop_water_requirements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    crop_id = Column(String(50), ForeignKey("crop_catalog.id"), nullable=False, unique=True, index=True)
    annual_water_requirement_mm_min = Column(Float, nullable=True) # Nullable where universal mm is unsupported
    annual_water_requirement_mm_max = Column(Float, nullable=True)
    rainfed_suitable = Column(Boolean, nullable=False)
    irrigation_dependency = Column(String(255), nullable=False) # Critical / High, Supplemental, Low / Rainfed
    critical_growth_stages = Column(JSON, nullable=False)
    daily_water_table = Column(JSON, nullable=True) # Stage/Bahar/Age-specific daily irrigation (L/tree/day)
    irrigation_stages_detail = Column(JSON, nullable=True) # Separate source-grounded irrigation schedules
    evidence_status = Column(String(50), default="derived", nullable=True)
    waterlogging_sensitivity = Column(Text, nullable=False)
    drought_sensitivity = Column(Text, nullable=False)
    source_id = Column(String(50), ForeignKey("agricultural_knowledge_sources.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    crop = relationship("CropCatalogModel", back_populates="water_requirements")


class CropRegionalSuitabilityModel(Base):
    """
    Evidence-grounded regional suitability ratings for pilot talukas.
    """
    __tablename__ = "crop_regional_suitability"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    crop_id = Column(String(50), ForeignKey("crop_catalog.id"), nullable=False, index=True)
    taluka = Column(String(100), nullable=False, index=True) # Baramati, Indapur, Maval, Mulshi
    district = Column(String(100), nullable=False, default="Pune")
    suitability_status = Column(String(100), nullable=False) # Highly Suitable, Moderately Suitable, Marginal / High Input, Unsuitable
    agronomic_rationale = Column(Text, nullable=False)
    limiting_factors = Column(JSON, nullable=True)
    evidence_status = Column(String(50), default="regional_screening", nullable=True) # verified_regional_evidence, regional_screening, requires_regional_validation
    source_id = Column(String(50), ForeignKey("agricultural_knowledge_sources.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    crop = relationship("CropCatalogModel", back_populates="regional_suitability")
